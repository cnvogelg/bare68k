from __future__ import print_function

import pytest
import traceback

from bare68k import *
from bare68k.consts import *

RESET_OPCODE = 0x4e70
NOP_OPCODE = 0x4e71

MOVEM_TO_SP = 0x48e7fffe
MOVEM_FROM_SP = 0x4cdf7fff

def _setup_code():
  PROG_BASE = runtime.get_reset_pc()
  mem.w32(PROG_BASE, MOVEM_TO_SP)
  mem.w32(PROG_BASE+4, MOVEM_FROM_SP)
  mem.w16(PROG_BASE+8, RESET_OPCODE)
  mem.w16(PROG_BASE+10, RESET_OPCODE)

def test_trace_instr(rt):
  _setup_code()
  # with trace
  trace.enable_instr_trace()
  rt.run()
  # without trace
  trace.disable_instr_trace()
  rt.run()

def test_trace_annotate_instr(rt):
  _setup_code()
  # with trace
  def anno(pc, num_bytes):
    return "HUHU:%08x" % pc
  trace.set_instr_annotate_func(anno)
  trace.enable_instr_trace()
  rt.run()
  # without trace
  trace.disable_instr_trace()
  rt.run()

def test_trace_annotate_exc(rt):
  _setup_code()
  # with trace
  def anno(pc, num_bytes):
    raise ValueError("anno test fail!")
  trace.set_instr_annotate_func(anno)
  trace.enable_instr_trace()
  with pytest.raises(ValueError):
    rt.run()

def test_trace_annotate_catch(rt):
  _setup_code()
  # with trace
  def anno(pc, num_bytes):
    raise ValueError("anno test fail!")
  trace.set_instr_annotate_func(anno)
  trace.enable_instr_trace()
  try:
    rt.run()
  except ValueError as e:
    traceback.print_exc()

def test_trace_cpu_mem(rt):
  _setup_code()
  trace.enable_cpu_mem_trace()
  rt.run()

def test_trace_api_mem(rt):
  trace.enable_api_mem_trace()
  _setup_code()
  rt.run()
