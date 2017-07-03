# traps

def trap_setup(int flags, object call not None):
  cdef uint16_t op
  op = traps.trap_setup(flags, <void *>call)
  if op != traps.TRAP_INVALID:
    Py_INCREF(call)
    return op
  else:
    raise MemoryError("no more traps!")

def trap_setup_abs(uint16_t tid, int flags, object call not None):
  cdef uint16_t op
  op = traps.trap_setup_abs(tid, flags, <void *>call)
  if op != traps.TRAP_INVALID:
    Py_INCREF(call)
    return op
  else:
    raise MemoryError("no more traps!")

def trap_free(uint16_t tid):
  cdef void *data
  cdef object callable
  data = traps.trap_free(tid)
  Py_DECREF(<object>data)

def trap_enable(uint16_t tid):
  traps.trap_enable(tid)

def trap_disable(uint16_t tid):
  traps.trap_disable(tid)

def traps_get_num_free():
  return traps.traps_get_num_free()

def traps_global_enable():
  traps.traps_global_enable()

def traps_global_disable():
  traps.traps_global_disable()
