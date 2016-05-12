"""memory and CPU trace support"""

import logging
import struct

import bare68k.machine as mach
import bare68k.cpu as cpu
import bare68k.mem as mem
from bare68k.consts import *

# globals
_log_instr = logging.getLogger(__name__ + ".instr")
_log_mem_cpu = logging.getLogger(__name__ + ".mem_cpu")
_log_mem_api = logging.getLogger(__name__ + ".mem_api")

def set_log_output(instr=None, mem_cpu=None, mem_api=None):
  """set custom channels for log output"""
  global _log_instr, _log_mem_cpu, _log_mem_api
  if instr is not None:
    _log_instr = instr
  if mem_cpu is not None:
    _log_mem_cpu = mem_cpu
  if mem_api is not None:
    _log_mem_api = mem_api

def _get_words(data):
  num_words = len(data) >> 1
  off = 0
  res = []
  for i in range(num_words):
    d = struct.unpack_from(">H", data, off)
    res.append("%04x" % d)
    off += 2
  return res

# ----- instruction trace -----

def default_instr_annotate(pc, num_bytes):
  # get raw words
  data = mem.r_block(pc, num_bytes)
  return "%-20s" % " ".join(_get_words(data))

_instr_annotate = default_instr_annotate

def set_instr_annotate_func(f):
  """set instr annotation function"""
  global _instr_annotate
  _instr_annotate = f

def handle_instr_trace(pc):
  """callback for instruction trace"""
  num_bytes, line = mach.disassemble(pc)
  if _instr_annotate is not None:
    annotation = _instr_annotate(pc, num_bytes)
  else:
    annotation = ""
  _log_instr.info("%08x: %s %s" % (pc, annotation, line))

def enable_instr_trace():
  """enable instruction tracing"""
  _log_instr.setLevel(logging.INFO)
  mach.set_instr_hook_func(handle_instr_trace)

def disable_instr_trace():
  """disable instruction tracing"""
  mach.set_instr_hook_func(None)

# ----- CPU memory trace -----

# only data accesses are traced
_cpu_mem_fc_mask = MEM_FC_DATA_MASK

def handle_cpu_mem_trace(s, v):
  flags = v[0]
  if flags & _cpu_mem_fc_mask == _cpu_mem_fc_mask:
    _log_mem_cpu.info(s)

def enable_cpu_mem_trace(fc_mask=None):
  global _cpu_mem_fc_mask
  if fc_mask is not None:
    _cpu_mem_fc_mask = fc_mask
  _log_mem_cpu.setLevel(logging.INFO)
  mach.set_mem_cpu_trace_func(handle_cpu_mem_trace, as_str=True)

def disable_cpu_mem_trace():
  mach.set_mem_cpu_trace_func(None)

# ----- API memory trace -----

def handle_api_mem_trace(s, v):
  _log_mem_api.info(s)

def enable_api_mem_trace():
  _log_mem_api.setLevel(logging.INFO)
  mach.set_mem_api_trace_func(handle_api_mem_trace, as_str=True)

def disable_cpu_mem_trace():
  mach.set_mem_api_trace_func(None)
