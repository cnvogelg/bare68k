from __future__ import print_function

import pytest

from bare68k import *
from bare68k.consts import *

RESET_OPCODE = 0x4e70
NOP_OPCODE = 0x4e71

def test_trace_instr(rt):
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, RESET_OPCODE)
  mem.w16(PROG_BASE+2, RESET_OPCODE)
  # with trace
  trace.enable_instr_trace()
  rt.run()
  # without trace
  trace.disable_instr_trace()
  rt.run()

def test_trace_instr_annotate(rt):
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, RESET_OPCODE)
  mem.w16(PROG_BASE+2, RESET_OPCODE)
  # with trace
  def anno(pc):
    return "HUHU:%08x" % pc
  trace.set_instr_annotate_func(anno)
  trace.enable_instr_trace()
  rt.run()
  # without trace
  trace.disable_instr_trace()
  rt.run()
