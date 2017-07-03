# cpu pc trace

def get_pc_trace_size():
  return tools.tools_get_pc_trace_size()

def setup_pc_trace(uint32_t num_traces):
  if tools.tools_setup_pc_trace(num_traces) < 0:
    raise MemoryError("No PC Trace memory!")

def cleanup_pc_trace():
  tools.tools_setup_pc_trace(0)

def get_pc_trace():
  cdef uint32_t *data
  cdef int size
  cdef int i
  data = tools.tools_get_pc_trace(&size)
  if data == NULL:
    return None
  a = []
  for i in range(size):
    a.append(data[i])
  tools.tools_free_pc_trace(data)
  return a

# breakpoints

def get_max_breakpoints():
  return tools.tools_get_max_breakpoints()

def get_num_breakpoints():
  return tools.tools_get_num_breakpoints()

def get_next_free_breakpoint():
  return tools.tools_get_next_free_breakpoint()

cdef void free_breakpoint_cb(void *data):
  if data != NULL:
    Py_DECREF(<object>data)

def setup_breakpoints(uint32_t num_bp):
  if tools.tools_setup_breakpoints(num_bp, free_breakpoint_cb) < 0:
    raise MemoryError("No breakpoints memory!")

def cleanup_breakpoints():
  tools.tools_setup_breakpoints(0, NULL)

def set_breakpoint(int bp_id, uint32_t addr, int flags, object data):
  cdef void *cdata
  if data is not None:
    cdata = <void *>data
  else:
    cdata = NULL
  if tools.tools_create_breakpoint(bp_id, addr, flags, cdata) < 0:
    raise ValueError("Invalid breakpoint index!")
  if data is not None:
    Py_INCREF(data)

def clear_breakpoint(int bp_id):
  if tools.tools_free_breakpoint(bp_id) < 0:
    raise ValueError("Invalid breakpoint index!")

def enable_breakpoint(int bp_id):
  if tools.tools_enable_breakpoint(bp_id) < 0:
    raise ValueError("Invalid breakpoint index!")

def disable_breakpoint(int bp_id):
  if tools.tools_disable_breakpoint(bp_id) < 0:
    raise ValueError("Invalid breakpoint index!")

def is_breakpoint_enabled(int bp_id):
  cdef res
  res = tools.tools_is_breakpoint_enabled(bp_id)
  if res < 0:
    raise ValueError("Invalid breakpoint index!")
  elif res == 0:
    return False
  else:
    return True

def get_breakpoint_data(int bp_id):
  cdef void *cdata
  cdata = tools.tools_get_breakpoint_data(bp_id)
  if cdata != NULL:
    return <object>cdata
  else:
    return None

def check_breakpoint(uint32_t addr, int flags):
  cdef int bp_id = tools.tools_check_breakpoint(addr, flags)
  if bp_id < 0:
    return None
  else:
    return bp_id

# watchpoints

def get_max_watchpoints():
  return tools.tools_get_max_watchpoints()

def get_num_watchpoints():
  return tools.tools_get_num_watchpoints()

def get_next_free_watchpoint():
  return tools.tools_get_next_free_watchpoint()

cdef void free_watchpoint_cb(void *data):
  if data != NULL:
    Py_DECREF(<object>data)

def setup_watchpoints(uint32_t num_bp):
  if tools.tools_setup_watchpoints(num_bp, free_watchpoint_cb) < 0:
    raise MemoryError("No watchpoints memory!")

def cleanup_watchpoints():
  tools.tools_setup_watchpoints(0, NULL)

def set_watchpoint(int bp_id, uint32_t addr, int flags, object data):
  cdef void *cdata
  if data is not None:
    cdata = <void *>data
  else:
    cdata = NULL
  if tools.tools_create_watchpoint(bp_id, addr, flags, cdata) < 0:
    raise ValueError("Invalid watchpoint index!")
  if data is not None:
    Py_INCREF(data)

def clear_watchpoint(int bp_id):
  if tools.tools_free_watchpoint(bp_id) < 0:
    raise ValueError("Invalid watchpoint index!")

def enable_watchpoint(int bp_id):
  if tools.tools_enable_watchpoint(bp_id) < 0:
    raise ValueError("Invalid watchpoint index!")

def disable_watchpoint(int bp_id):
  if tools.tools_disable_watchpoint(bp_id) < 0:
    raise ValueError("Invalid watchpoint index!")

def is_watchpoint_enabled(int bp_id):
  cdef res
  res = tools.tools_is_watchpoint_enabled(bp_id)
  if res < 0:
    raise ValueError("Invalid watchpoint index!")
  elif res == 0:
    return False
  else:
    return True

def get_watchpoint_data(int bp_id):
  cdef void *cdata
  cdata = tools.tools_get_watchpoint_data(bp_id)
  if cdata != NULL:
    return <object>cdata
  else:
    return None

def check_watchpoint(uint32_t addr, int flags):
  cdef int bp_id = tools.tools_check_watchpoint(addr, flags)
  if bp_id < 0:
    return None
  else:
    return bp_id

# timers

def get_max_timers():
  return tools.tools_get_max_timers()

def get_num_timers():
  return tools.tools_get_num_timers()

def get_next_free_timer():
  return tools.tools_get_next_free_timer()

cdef void free_timer_cb(void *data):
  if data != NULL:
    Py_DECREF(<object>data)

def setup_timers(uint32_t num_bp):
  if tools.tools_setup_timers(num_bp, free_timer_cb) < 0:
    raise MemoryError("No timers memory!")

def cleanup_timers():
  tools.tools_setup_timers(0, NULL)

def set_timer(int bp_id, uint32_t interval, object data):
  cdef void *cdata
  if data is not None:
    cdata = <void *>data
  else:
    cdata = NULL
  if tools.tools_create_timer(bp_id, interval, cdata) < 0:
    raise ValueError("Invalid timer index!")
  if data is not None:
    Py_INCREF(data)

def clear_timer(int bp_id):
  if tools.tools_free_timer(bp_id) < 0:
    raise ValueError("Invalid timer index!")

def enable_timer(int bp_id):
  if tools.tools_enable_timer(bp_id) < 0:
    raise ValueError("Invalid timer index!")

def disable_timer(int bp_id):
  if tools.tools_disable_timer(bp_id) < 0:
    raise ValueError("Invalid timer index!")

def is_timer_enabled(int bp_id):
  cdef res
  res = tools.tools_is_timer_enabled(bp_id)
  if res < 0:
    raise ValueError("Invalid timer index!")
  elif res == 0:
    return False
  else:
    return True

def get_timer_data(int bp_id):
  cdef void *cdata
  cdata = tools.tools_get_timer_data(bp_id)
  if cdata != NULL:
    return <object>cdata
  else:
    return None

def tick_timers(uint32_t pc, uint32_t elapsed):
  return tools.tools_tick_timers(pc, elapsed)
