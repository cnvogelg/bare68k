"""memory and CPU trace support"""

import logging

import bare68k.machine as mach
import bare68k.cpu as cpu
import bare68k.mem as mem
import bare68k.dump as dump
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

# ----- instruction trace -----

def handle_instr_trace(pc):
  _log_instr.info(dump.disassemble_line(pc))

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
