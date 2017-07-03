from libc.stdint cimport uint16_t

# traps.h
cdef extern from "glue/traps.h":

  cdef enum:
    TRAP_DEFAULT  = 0
    TRAP_ONE_SHOT = 1
    TRAP_AUTO_RTS = 2

  cdef enum:
    TRAP_INVALID = 0xffff

  void traps_init()
  int traps_shutdown()

  int traps_get_num_free()

  uint16_t trap_setup(int flags, void *data)
  uint16_t trap_setup_abs(uint16_t tid, int flags, void *data)
  void *trap_free(uint16_t tid)

  void trap_enable(uint16_t opcode)
  void trap_disable(uint16_t opcode)

  void traps_global_enable()
  void traps_global_disable()
