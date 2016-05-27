from libc.stdlib cimport malloc, free
from libc.stdint cimport uint64_t, uint32_t, uint16_t, uint8_t, int8_t, int16_t, int32_t
from cpython cimport Py_INCREF, Py_DECREF
from cpython cimport bool
from cpython.exc cimport PyErr_CheckSignals

cimport musashi
cimport cpu
cimport mem
cimport traps
cimport tools

import sys

# globals

event_handlers = [None] * cpu.CPU_NUM_EVENTS

# ----- API -----

def init(int cpu_type, int num_pages):
  cpu.cpu_init(cpu_type)
  mem.mem_init(num_pages)
  traps.traps_init()
  tools.tools_init()

  cpu.cpu_set_cleanup_event_func(cleanup_event)
  mem.mem_set_special_cleanup(mem_special_cleanup)

  # clear handlers
  global event_handlers
  for i in range(len(event_handlers)):
    event_handlers[i] = None

def shutdown():
  set_mem_cpu_trace_func(None)
  set_mem_api_trace_func(None)
  set_instr_hook_func(None)
  set_int_ack_func(None)
  set_irq(0)

  cpu.cpu_free()
  mem.mem_free()
  traps.traps_shutdown()
  tools.tools_free()

# modules
include "cpu.pyx"
include "mem.pyx"
include "traps.pyx"
include "tools.pyx"
