from libc.stdint cimport uint32_t, uint64_t

# cpu.h
cdef extern from "glue/cpu.h":

  cdef enum:
    CPU_EVENT_CALLBACK_ERROR = 0
    CPU_EVENT_RESET = 1
    CPU_EVENT_ALINE_TRAP = 2
    CPU_EVENT_MEM_ACCESS = 3
    CPU_EVENT_MEM_BOUNDS = 4
    CPU_EVENT_MEM_TRACE = 5
    CPU_EVENT_MEM_SPECIAL = 6
    CPU_EVENT_INSTR_HOOK = 7
    CPU_EVENT_INT_ACK = 8
    CPU_EVENT_BREAKPOINT = 9
    CPU_EVENT_WATCHPOINT = 10
    CPU_EVENT_TIMER = 11

    CPU_NUM_EVENTS = 12

  cdef enum:
    CPU_CB_NO_EVENT = 0
    CPU_CB_EVENT = 1
    CPU_CB_ERROR = -1

  ctypedef struct event_t:
    int         type
    uint32_t    cycles
    uint32_t    addr
    uint32_t    value
    uint32_t    flags
    void        *data

  ctypedef struct run_info_t:
    int          num_events
    int          lost_events
    event_t     *events
    uint32_t     done_cycles
    uint64_t     total_cycles

  ctypedef struct registers_t:
    uint32_t     dx[8]
    uint32_t     ax[8]
    uint32_t     pc
    uint32_t     sr

  ctypedef void (*cleanup_event_func_t)(event_t *e)
  ctypedef int (*instr_hook_func_t)(uint32_t pc, void **data)
  ctypedef int (*int_ack_func_t)(int level, uint32_t pc, uint32_t *ack_ret, void **data)

  void cpu_init(unsigned int cpu_type)
  void cpu_free()
  void cpu_reset()
  int cpu_get_type()

  void cpu_set_cleanup_event_func(cleanup_event_func_t func)
  void cpu_set_instr_hook_func(instr_hook_func_t func)
  void cpu_set_int_ack_func(int_ack_func_t func)

  int cpu_default_instr_hook_func(uint32_t pc, void **data)

  int cpu_execute(int num_cycles)
  int cpu_execute_to_event(int cycles_per_run)

  void cpu_set_irq(int level)

  run_info_t *cpu_get_info()
  void cpu_clear_info()

  uint32_t cpu_r_reg(int reg)
  void cpu_w_reg(int reg, uint32_t val)

  void cpu_r_regs(registers_t *regs)
  void cpu_w_regs(const registers_t *regs)

  const char *cpu_get_sr_str(uint32_t val)
  const char **cpu_get_regs_str(const registers_t *regs)
  const char *cpu_get_instr_str(uint32_t pc)
