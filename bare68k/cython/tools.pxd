from libc.stdint cimport uint32_t

# tools.h
cdef extern from "binding/tools.h":

  ctypedef void (*free_func_t)(void *data)

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
  int tools_check_breakpoint(uint32_t addr, int flags)
  void *tools_get_breakpoint_data(int id)
