from libc.stdint cimport uint16_t

# traps.h
cdef extern from "binding/traps.h":

  cdef enum:
    TRAP_DEFAULT  = 0
    TRAP_ONE_SHOT = 1
    TRAP_AUTO_RTS = 2

  void traps_init()
  uint16_t trap_setup(int flags, void *data)
  void *trap_free(uint16_t tid)
