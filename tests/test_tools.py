from __future__ import print_function

import pytest
import traceback

from bare68k.consts import *
from bare68k.machine import *

RESET_OPCODE = 0x4e70
NOP_OPCODE = 0x4e71

# ----- pc trace -----

def test_pc_no_trace(mach):
  assert get_pc_trace_size() == 0
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, NOP_OPCODE)
  w16(0x106, NOP_OPCODE)
  w16(0x108, RESET_OPCODE)
  # no trace enabled by default
  w_pc(0x100)
  ne = execute(100)
  assert ne == 1
  ri = get_info()
  print("PC_TRACE", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET
  trace = get_pc_trace()
  assert trace == None

def test_pc_trace(mach):
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, NOP_OPCODE)
  w16(0x106, NOP_OPCODE)
  w16(0x108, RESET_OPCODE)
  # no trace enabled by default
  w_pc(0x100)
  assert get_pc_trace_size() == 0
  setup_pc_trace(16)
  assert get_pc_trace_size() == 16
  ne = execute(100)
  assert ne == 1
  ri = get_info()
  print("PC_TRACE", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET
  trace = get_pc_trace()
  assert trace == [256, 258, 260, 262, 264]
  cleanup_pc_trace()
  assert get_pc_trace_size() == 0

def test_pc_trace_short(mach):
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, NOP_OPCODE)
  w16(0x106, NOP_OPCODE)
  w16(0x108, RESET_OPCODE)
  # no trace enabled by default
  w_pc(0x100)
  assert get_pc_trace_size() == 0
  setup_pc_trace(3)
  assert get_pc_trace_size() == 3
  ne = execute(100)
  assert ne == 1
  ri = get_info()
  print("PC_TRACE", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET
  trace = get_pc_trace()
  assert trace == [260, 262, 264]
  cleanup_pc_trace()
  assert get_pc_trace_size() == 0

# ----- breakpoints -----

def test_bp_setup(mach):
  assert get_num_breakpoints() == 0
  assert get_max_breakpoints() == 0
  setup_breakpoints(8)
  assert get_num_breakpoints() == 0
  assert get_max_breakpoints() == 8
  # invalid breakpoint
  with pytest.raises(ValueError):
    set_breakpoint(-1, 0, 0, None)
  # add empty breakpoint
  assert get_next_free_breakpoint() == 0
  set_breakpoint(0, 0x100, 0, None)
  assert get_next_free_breakpoint() == 1
  assert get_breakpoint_data(0) == None
  assert get_num_breakpoints() == 1
  # add non empty bp
  set_breakpoint(1, 0x200, 0, "hallo")
  assert get_next_free_breakpoint() == 2
  assert get_breakpoint_data(1) == "hallo"
  assert get_num_breakpoints() == 2
  # remove invalid
  with pytest.raises(ValueError):
    clear_breakpoint(2)
  # remove first
  clear_breakpoint(0)
  assert get_next_free_breakpoint() == 0
  assert get_num_breakpoints() == 1
  # remove last
  clear_breakpoint(1)
  assert get_num_breakpoints() == 0
  # remove breakpoints
  cleanup_breakpoints()
  assert get_num_breakpoints() == 0
  assert get_max_breakpoints() == 0
  assert get_next_free_breakpoint() == -1

def test_bp_enable(mach):
  setup_breakpoints(1)
  set_breakpoint(0, 0x100, 0, None)
  assert is_breakpoint_enabled(0) == True
  disable_breakpoint(0)
  assert is_breakpoint_enabled(0) == False
  enable_breakpoint(0)
  assert is_breakpoint_enabled(0) == True

def test_bp_check(mach):
  setup_breakpoints(4)
  set_breakpoint(0, 0x100, 1, None)
  set_breakpoint(1, 0x102, 2, None)
  set_breakpoint(2, 0x100, 3, None)
  set_breakpoint(3, 0x102, 4, None)
  assert check_breakpoint(0x104, 7) == None
  assert check_breakpoint(0x100, 7) == 0
  assert check_breakpoint(0x100, 2) == 2

def test_bp_check(mach):
  setup_breakpoints(4)
  set_breakpoint(0, 0x100, MEM_FC_USER_MASK, "hello")
  set_breakpoint(1, 0x102, MEM_FC_SUPER_MASK, "world")
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, NOP_OPCODE)
  w16(0x106, NOP_OPCODE)
  w16(0x108, RESET_OPCODE)
  w_pc(0x100)
  ne = execute(100)
  assert ne == 1
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_BREAKPOINT
  assert ev.addr == 0x102
  assert ev.value == 1 # bp id
  assert ev.flags == MEM_FC_SUPER_PROG
  assert ev.data == "world"
