# cython: c_string_type=str, c_string_encoding=ascii, embedsignature=True

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
cimport label

import sys

# globals

cdef object event_handlers = [None] * cpu.CPU_NUM_EVENTS
cdef int is_init = 0
cdef bool got_labels

# ---- handler access -----

cpdef clear_event_handlers():
  global event_handlers
  for i in range(len(event_handlers)):
    event_handlers[i] = None

cpdef set_event_handler(int offset, object handler):
  global event_handlers
  if offset < 0 or offset >= cpu.CPU_NUM_EVENTS:
    raise ValueError("invalid handler offset")
  event_handlers[offset] = handler

cpdef get_event_handler(int offset):
  global event_handlers
  if offset < 0 or offset >= cpu.CPU_NUM_EVENTS:
    raise ValueError("invalid handler offset")
  return event_handlers[offset]

# ----- API -----

def init(int cpu_type, int num_pages, bool with_labels=False):
  global is_init
  if is_init == 1:
    raise RuntimeError("already init called")
  is_init = 1

  cpu.cpu_init(cpu_type)
  mem.mem_init(num_pages)
  traps.traps_init()
  tools.tools_init()

  global got_labels
  got_labels = with_labels
  if with_labels:
    label.label_init(mem.mem_get_num_pages(), mem.mem_get_page_shift())
    label.label_set_cleanup_func(cleanup_label)

  cpu.cpu_set_cleanup_event_func(cleanup_event)
  mem.mem_set_special_cleanup(mem_special_cleanup)

  clear_event_handlers()

def shutdown():
  global is_init
  if is_init == 0:
    raise RuntimeError("call init first")
  is_init = 0

  set_mem_cpu_trace_func(None)
  set_mem_api_trace_func(None)
  set_instr_hook_func(None)
  set_int_ack_func(None)
  set_irq(0)

  global got_labels
  if got_labels:
    label.label_free()

  cpu.cpu_free()
  mem.mem_free()
  traps.traps_shutdown()
  tools.tools_free()

  clear_event_handlers()

def is_initialized():
  return <bint>is_init

# modules
include "cpu.pyx"
include "mem.pyx"
include "traps.pyx"
include "tools.pyx"
include "disasm.pyx"
include "label.pyx"
