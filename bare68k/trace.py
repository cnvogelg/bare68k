"""memory and CPU trace support"""

import logging
import struct

import bare68k.machine as mach
import bare68k.cpu as cpu
import bare68k.mem as mem

# globals
_log_instr = logging.getLogger(__name__ + ".instr")
_log_mem_cpu = logging.getLogger(__name__ + ".mem_cpu")
_log_mem_api = logging.getLogger(__name__ + ".mem_api")
_instr_annotate = None

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

def set_instr_annotate_func(f):
  """set instr annotation function"""
  global _instr_annotate
  _instr_annotate = f

def handle_instr_trace(pc):
  """callback for instruction trace"""
  num_bytes, line = mach.disassemble(pc)
  # get raw words
  data = mem.r_block(pc, num_bytes)
  words = " ".join(_get_words(data))
  if _instr_annotate is not None:
    annotation = _instr_annotate(pc)
  else:
    annotation = ""
  _log_instr.info("%08x: %-20s %s  %s" % (pc, words, line, annotation))

def enable_instr_trace():
  """enable instruction tracing"""
  _log_instr.setLevel(logging.INFO)
  mach.set_instr_hook_func(handle_instr_trace)

def disable_instr_trace():
  """disable instruction tracing"""
  mach.set_instr_hook_func(None)
