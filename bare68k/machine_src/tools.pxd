from libc.stdint cimport uint32_t

# tools.h
cdef extern from "glue/tools.h":

  ctypedef void (*free_func_t)(void *data)

  void tools_init()
  void tools_free()

  int tools_get_pc_trace_size()
  int tools_setup_pc_trace(int num)
  uint32_t *tools_get_pc_trace(int *size)
  void tools_free_pc_trace(uint32_t *data)

  int tools_get_num_breakpoints()
  int tools_get_max_breakpoints()
  int tools_get_next_free_breakpoint()
  int tools_setup_breakpoints(int num, free_func_t free_func)
  int tools_create_breakpoint(int id, uint32_t addr, int flags, void *data)
  int tools_free_breakpoint(int id)
  int tools_enable_breakpoint(int id)
  int tools_disable_breakpoint(int id)
  int tools_is_breakpoint_enabled(int id)
  void *tools_get_breakpoint_data(int id)
  int tools_check_breakpoint(uint32_t addr, int flags)

  int tools_get_num_watchpoints()
  int tools_get_max_watchpoints()
  int tools_get_next_free_watchpoint()
  int tools_setup_watchpoints(int num, free_func_t free_func)
  int tools_create_watchpoint(int id, uint32_t addr, int flags, void *data)
  int tools_free_watchpoint(int id)
  int tools_enable_watchpoint(int id)
  int tools_disable_watchpoint(int id)
  int tools_is_watchpoint_enabled(int id)
  void *tools_get_watchpoint_data(int id)
  int tools_check_watchpoint(uint32_t addr, int flags)

  int tools_get_num_timers()
  int tools_get_max_timers()
  int tools_get_next_free_timer()
  int tools_setup_timers(int num, free_func_t free_func)
  int tools_create_timer(int id, uint32_t interval, void *data)
  int tools_free_timer(int id)
  int tools_enable_timer(int id)
  int tools_disable_timer(int id)
  int tools_is_timer_enabled(int id)
  void *tools_get_timer_data(int id)
  int tools_tick_timers(uint32_t pc, uint32_t elapsed)
