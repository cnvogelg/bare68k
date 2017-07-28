/* MusashiCPU <-> vamos CPU interface
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "cpu.h"
#include "mem.h"
#include "tools.h"

#define DEFAULT_CYCLES 100000
#define MAX_EVENTS 8

typedef void (*event_func_t)(void);

static int cpu_type;
static event_t events[MAX_EVENTS];
static run_info_t run_info;
static event_func_t event_func;
static cleanup_event_func_t cleanup_func;
static instr_hook_func_t instr_hook_func;
static int_ack_func_t int_ack_func;
static int dont_clear;
static uint32_t last_cycles;

/* public */
unsigned int cpu_current_fc;

/* ----- Callbacks ----- */

static void reset_instr_cb(void)
{
  uint32_t pc = cpu_r_reg(M68K_REG_PC);
  cpu_add_event(CPU_EVENT_RESET, pc, 0, 0, NULL);
}

static void instr_hook_cb(void)
{
  uint32_t pc = cpu_r_reg(M68K_REG_PC);

  /* handle function */
  if(instr_hook_func != NULL) {
    void *data = NULL;
    int res = instr_hook_func(pc, &data);
    /* res == 0 generates an INSTR_HOOK event */
    if(res == CPU_CB_EVENT) {
      cpu_add_event(CPU_EVENT_INSTR_HOOK, pc, 0, 0, data);
    }
    /* res < 0 generates an CALLBACK_ERROR event */
    else if(res == CPU_CB_ERROR) {
      cpu_add_event(CPU_EVENT_CALLBACK_ERROR, pc, 0, 0, data);
    }
  }

  /* add to pc trace? */
  if(tools_pc_trace_enabled) {
    tools_update_pc_trace(pc);
  }

  /* check for breakpoints */
  if(tools_breakpoints_enabled) {
    int flags = cpu_current_fc;
    int id = tools_check_breakpoint(pc, flags);
    if(id > -1) {
      void *data = tools_get_breakpoint_data(id);
      cpu_add_event(CPU_EVENT_BREAKPOINT, pc, id, flags, data);
    }
  }

  /* timers? */
  if(tools_timers_enabled) {
    uint32_t cycles = m68k_cycles_run();
    uint32_t elapsed = cycles - last_cycles;
    last_cycles = cycles;
    tools_tick_timers(pc, elapsed);
  }
}

static int int_ack_cb(int int_level)
{
  void *data = NULL;
  uint32_t ack = M68K_INT_ACK_AUTOVECTOR;
  uint32_t pc = cpu_r_reg(M68K_REG_PC);
  int res = int_ack_func(int_level, pc, &ack, &data);
  /* res == 0 generates an INT_ACK event */
  if(res == CPU_CB_EVENT) {
    cpu_add_event(CPU_EVENT_INT_ACK, pc, ack, int_level, data);
  }
  /* res < 0 generates an CALLBACK ERROR event */
  else if(res == CPU_CB_ERROR) {
    cpu_add_event(CPU_EVENT_CALLBACK_ERROR, pc, 0, 0, data);
  }
  return ack;
}

/* map CPU function code to our mapping */
static unsigned int cpu_fc_map[] = {
  MEM_FC_INVALID,   /* 0 */
  MEM_FC_USER_DATA, /* 1 */
  MEM_FC_USER_PROG, /* 2 */
  MEM_FC_INVALID,   /* 3 */
  MEM_FC_INVALID,   /* 4 */
  MEM_FC_SUPER_DATA,/* 5 */
  MEM_FC_SUPER_PROG,/* 6 */
  MEM_FC_INT_ACK    /* 7 */
};

static void set_fc_cb(unsigned int new_fc)
{
  cpu_current_fc = cpu_fc_map[new_fc & 7];
}

/* ----- Default ----- */

int cpu_default_instr_hook_func(uint32_t pc, void **data)
{
  const char *line = cpu_get_instr_str(pc);
  puts(line);
  return 1;
}

/* ----- API ----- */

void cpu_init(unsigned int cpu_type_)
{
  int i;

  m68k_set_cpu_type(cpu_type_);
  m68k_init();
  m68k_set_reset_instr_callback(reset_instr_cb);
  m68k_set_fc_callback(set_fc_cb);
  m68k_set_instr_hook_callback(instr_hook_cb);

  /* clear regs */
  for(i=0;i<8;i++) {
    m68k_set_reg(M68K_REG_D0+i, 0);
    m68k_set_reg(M68K_REG_A0+i, 0);
  }
  m68k_set_reg(M68K_REG_SR, 0x2700);

  cpu_type = cpu_type_;
  run_info.events = events;
  run_info.total_cycles = 0;
  dont_clear = 0;
  last_cycles = 0;
}

int cpu_get_type(void)
{
  return cpu_type;
}

void cpu_free(void)
{
  cpu_clear_info();
}

void cpu_reset(void)
{
  last_cycles = 0;
  run_info.total_cycles = 0;
  m68k_pulse_reset();
}

void cpu_set_cleanup_event_func(cleanup_event_func_t func)
{
  cleanup_func = func;
}

void cpu_set_instr_hook_func(instr_hook_func_t func)
{
  instr_hook_func = func;
  /* callback is always setup */
}

void cpu_set_int_ack_func(int_ack_func_t func)
{
  int_ack_func = func;
  if(func != NULL) {
    m68k_set_int_ack_callback(int_ack_cb);
  } else {
    m68k_set_int_ack_callback(NULL);
  }
}

uint32_t cpu_r_reg(int reg)
{
  return m68k_get_reg(NULL, reg);
}

  void cpu_w_reg(int reg, uint32_t val)
{
  m68k_set_reg(reg, val);
}

void cpu_r_regs(registers_t *regs)
{
  int i;

  for(i=0;i<8;i++) {
    regs->dx[i] = m68k_get_reg(NULL, M68K_REG_D0 + i);
    regs->ax[i] = m68k_get_reg(NULL, M68K_REG_A0 + i);
  }
  regs->pc = m68k_get_reg(NULL, M68K_REG_PC);
  regs->sr = m68k_get_reg(NULL, M68K_REG_SR);

  regs->usp = m68k_get_reg(NULL, M68K_REG_USP);
  regs->isp = m68k_get_reg(NULL, M68K_REG_ISP);
  regs->msp = m68k_get_reg(NULL, M68K_REG_MSP);
  regs->vbr = m68k_get_reg(NULL, M68K_REG_VBR);
}

void cpu_w_regs(const registers_t *regs)
{
  int i;

  for(i=0;i<8;i++) {
    m68k_set_reg(M68K_REG_D0 + i, regs->dx[i]);
    m68k_set_reg(M68K_REG_A0 + i, regs->ax[i]);
  }
  m68k_set_reg(M68K_REG_PC, regs->pc);
  m68k_set_reg(M68K_REG_SR, regs->sr);

  m68k_set_reg(M68K_REG_USP, regs->usp);
  m68k_set_reg(M68K_REG_ISP, regs->isp);
  m68k_set_reg(M68K_REG_MSP, regs->msp);
  m68k_set_reg(M68K_REG_VBR, regs->vbr);
}

/*                             0123456789012345 */
static const char *sr_prot = "T?S??210???XNZVC";
static char sr_str[17];
const char *cpu_get_sr_str(uint32_t val)
{
  uint32_t mask = 0x8000;
  int i;

  for(i=0;i<16;i++) {
    if((val & mask) == mask) {
      sr_str[i] = sr_prot[i];
    } else {
      sr_str[i] = '-';
    }
    mask >>= 1;
  }
  sr_str[16] = '\0';
  return sr_str;
}

static char pc_line[40];
static char dx1_line[60];
static char dx2_line[60];
static char ax1_line[60];
static char ax2_line[60];
static char sp_line[60];
static char *reg_lines[] = { pc_line, dx1_line, dx2_line, ax1_line, ax2_line, sp_line, NULL };
const char ** cpu_get_regs_str(const registers_t *regs)
{
  int n;
  const char *sr;
  char *ax1;
  char *ax2;
  char *dx1;
  char *dx2;
  int i;

  n = sprintf(pc_line, " PC=%08x  SR=", regs->pc);
  sr = cpu_get_sr_str(regs->sr);
  strcpy(pc_line + n, sr);

  ax1 = ax1_line;
  ax2 = ax2_line;
  dx1 = dx1_line;
  dx2 = dx2_line;
  for(i=0;i<4;i++) {
    int j = i + 4;
    sprintf(dx1, " D%d=%08x ", i, regs->dx[i]);
    sprintf(ax1, " A%d=%08x ", i, regs->ax[i]);
    sprintf(dx2, " D%d=%08x ", j, regs->dx[j]);
    sprintf(ax2, " A%d=%08x ", j, regs->ax[j]);
    dx1 += 13;
    ax1 += 13;
    dx2 += 13;
    ax2 += 13;
  }
  *(--dx1) = 0;
  *(--ax1) = 0;
  *(--dx2) = 0;
  *(--ax2) = 0;

  sprintf(sp_line, "USP=%08x ISP=%08x MSP=%08x VBR=%08x",
          regs->usp, regs->isp, regs->msp, regs->vbr);
  return (const char **)reg_lines;
}

static char instr_line[80];
const char *cpu_get_instr_str(uint32_t pc)
{
  sprintf(instr_line, "%08x: ", pc);
  m68k_disassemble(instr_line+10, pc, cpu_type);
  return instr_line;
}

void cpu_add_event(int type, uint32_t addr, uint32_t value, uint32_t flags, void *data)
{
  int n;

  n = run_info.num_events;
  if(n == MAX_EVENTS) {
    run_info.lost_events++;
  } else {
    event_t *cur_event = &events[n];
    cur_event->type = type;
    cur_event->cycles = m68k_cycles_run();
    cur_event->addr = addr;
    cur_event->value = value;
    cur_event->flags = flags;
    cur_event->data = data;
    run_info.num_events++;

    /* call event func on first event */
    if((n == 0) && (event_func != NULL)) {
      event_func();
    }
  }
}

run_info_t *cpu_get_info(void)
{
  return &run_info;
}

void cpu_clear_info(void)
{
  if(cleanup_func != NULL) {
    int n = run_info.num_events;
    int i;
    for(i = 0; i < n; i++) {
      event_t *e = &events[i];
      cleanup_func(e);
    }
  }

  run_info.num_events = 0;
  run_info.lost_events = 0;
  run_info.done_cycles = 0;
}

void cpu_set_irq(int level)
{
  cpu_clear_info();
  m68k_set_irq(level);
  dont_clear = 1;
}

int cpu_execute(int num_cycles)
{
  if(num_cycles == 0) {
    num_cycles = DEFAULT_CYCLES;
  }

  if(!dont_clear) {
    cpu_clear_info();
  } else {
    dont_clear = 0;
  }

  /* set event function */
  event_func = m68k_end_timeslice;

  /* run 68k! */
  run_info.done_cycles = m68k_execute(num_cycles);
  run_info.total_cycles += run_info.done_cycles;

  /* remove event func */
  event_func = NULL;

  return run_info.num_events;
}

int cpu_execute_to_event(int cycles_per_run)
{
  int done_cycles = 0;

  if(cycles_per_run == 0) {
    cycles_per_run = DEFAULT_CYCLES;
  }

  if(!dont_clear) {
    cpu_clear_info();
  } else {
    dont_clear = 0;
  }

  /* set event function */
  event_func = m68k_end_timeslice;

  /* run 68k! */
  while(run_info.num_events == 0) {
    done_cycles += m68k_execute(cycles_per_run);
  }

  /* account cycles */
  run_info.done_cycles = done_cycles;
  run_info.total_cycles += run_info.done_cycles;

  /* no event happened. report cycles event */
  event_func = NULL;

  return run_info.num_events;
}

/* ----- PC Trace ----- */
