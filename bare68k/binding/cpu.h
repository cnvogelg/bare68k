/* MusashiCPU <-> vamos CPU interface
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#ifndef _CPU_H
#define _CPU_H

#include "m68k.h"
#include <stdint.h>

#define CPU_EVENT_CALLBACK_ERROR 0
#define CPU_EVENT_RESET 1
#define CPU_EVENT_ALINE_TRAP 2
#define CPU_EVENT_MEM_ACCESS 3
#define CPU_EVENT_MEM_BOUNDS 4
#define CPU_EVENT_MEM_TRACE 5
#define CPU_EVENT_MEM_SPECIAL 6
#define CPU_EVENT_INSTR_HOOK 7
#define CPU_EVENT_INT_ACK 8
#define CPU_EVENT_BREAKPOINT 9
#define CPU_EVENT_WATCHPOINT 10
#define CPU_EVENT_TIMER 11

#define CPU_NUM_EVENTS 12

#define CPU_CB_EVENT 0
#define CPU_CB_NO_EVENT 1
#define CPU_CB_ERROR -1

typedef struct {
  int         type;
  uint32_t    cycles;
  uint32_t    addr;
  uint32_t    value;
  uint32_t    flags;
  void        *data;
} event_t;

typedef struct {
  int          num_events;
  int          lost_events;
  event_t     *events;
  uint32_t     done_cycles;
  uint64_t     total_cycles;
} run_info_t;

typedef struct {
  uint32_t     dx[8];
  uint32_t     ax[8];
  uint32_t     pc;
  uint32_t     sr;
  uint32_t     usp;
  uint32_t     isp;
  uint32_t     msp;
  uint32_t     vbr;
} registers_t;

typedef void (*cleanup_event_func_t)(event_t *e);
typedef int (*instr_hook_func_t)(uint32_t pc, void **data);
typedef int (*int_ack_func_t)(int level, uint32_t pc, uint32_t *ack_ret, void **data);

extern void cpu_init(unsigned int cpu_type);
extern void cpu_free(void);
extern void cpu_reset(void);

extern int cpu_get_type(void);
extern void cpu_set_cleanup_event_func(cleanup_event_func_t func);
extern void cpu_set_instr_hook_func(instr_hook_func_t func);
extern void cpu_set_int_ack_func(int_ack_func_t func);

extern int cpu_default_instr_hook_func(uint32_t pc, void **data);

extern int cpu_execute(int num_cycles);
extern int cpu_execute_to_event(int cycles_per_run);
extern void cpu_set_irq(int level);

extern uint32_t cpu_r_reg(int reg);
extern void cpu_w_reg(int reg, uint32_t val);

extern void cpu_r_regs(registers_t *regs);
extern void cpu_w_regs(const registers_t *regs);

extern const char *cpu_get_sr_str(uint32_t val);
extern const char **cpu_get_regs_str(const registers_t *regs);
extern const char *cpu_get_instr_str(uint32_t pc);

extern void cpu_add_event(int type, uint32_t addr, uint32_t value, uint32_t flags, void *data);

extern run_info_t *cpu_get_info(void);
extern void cpu_clear_info(void);

#define CPU_FC_SHIFT 4
#define CPU_FC_MASK  0x70
extern unsigned int cpu_current_fc;

#endif
