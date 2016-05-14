from __future__ import print_function

import pytest
from bare68k.consts import *
from bare68k.machine import *

RESET_OPCODE = 0x4e70
NOP_OPCODE = 0x4e71

def check_aline_cpu_ex(opcode):
  w_sp(0x400)
  w32(0x28, 0x1000) # Exception Vector A-Line
  w16(0x1000, RESET_OPCODE)

  w_pc(0x100)
  w16(0x100, opcode)

  ne = execute(1000)
  assert ne == 1
  ri = get_info()
  print("TRAP", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET

def test_invalid_trap(mach):
  # callable must be given
  with pytest.raises(TypeError):
    opcode = trap_setup(TRAP_DEFAULT, None)

def test_global_disable_trap(mach):
  w_pc(0x100)
  w16(0x100, 0xa000)

  w_sp(0x400)
  w32(0x28, 0x1000) # Exception Vector A-Line
  w16(0x1000, RESET_OPCODE)

  trap_enable(0xa000)
  # disable traps
  traps_global_disable()
  ne = execute(1000)
  # assume jump to exception vector -> RESET
  assert ne == 1
  ri = get_info()
  print("DISABLE", ri)
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET
  # enable traps
  traps_global_enable()
  w_pc(0x100)
  ne = execute(1000)
  assert ne == 1
  ri = get_info()
  print("ENABLE", ri)
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_ALINE_TRAP

def test_empty_trap(mach):
  # no trap was set. return event but callback is None
  w_pc(0x100)
  w16(0x100, 0xa000)
  trap_enable(0xa000)
  ne = execute(1000)
  assert ne == 1
  ri = get_info()
  print("TRAP", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_ALINE_TRAP
  assert ev.addr == 0x100
  assert ev.data is None
  assert ev.handler is None
  # disable trap
  trap_disable(0xa000)
  check_aline_cpu_ex(0xa000)

def test_empty_trap_def_handler(mach):
  def huhu():
    print("huhu")
  event_handlers[CPU_EVENT_ALINE_TRAP] = huhu
  assert event_handlers[CPU_EVENT_ALINE_TRAP] is huhu
  w_pc(0x100)
  w16(0x100, 0xa000)
  trap_enable(0xa000)
  ne = execute(1000)
  assert ne == 1
  ri = get_info()
  print("TRAP", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_ALINE_TRAP
  assert ev.addr == 0x100
  assert ev.data is None
  assert ev.handler is huhu
  # disable trap
  trap_disable(0xa000)
  check_aline_cpu_ex(0xa000)

def test_default_trap(mach):
  def my_cb():
    print("HUHU")
  opcode = trap_setup(TRAP_DEFAULT, my_cb)
  w_pc(0x100)
  w16(0x100, opcode)
  ne = execute(1000)
  assert ne == 1
  ri = get_info()
  print("TRAP", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_ALINE_TRAP
  assert ev.addr == 0x100
  assert ev.data == my_cb
  assert ev.handler is None
  # trigger callback
  ev.data()
  # finally free trap
  trap_free(opcode)
  # after trap: aline is disabled again
  check_aline_cpu_ex(opcode)

def test_one_shot_trap(mach):
  def my_cb():
    print("HUHU")
  opcode = trap_setup(TRAP_ONE_SHOT, my_cb)
  w_pc(0x100)
  w16(0x100, opcode)
  ne = execute(1000)
  assert ne == 1
  ri = get_info()
  print("TRAP", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_ALINE_TRAP
  assert ev.addr == 0x100
  assert ev.data == my_cb
  assert ev.handler is None
  # trigger callback
  ev.data()
  # after trap: aline is empty again
  check_aline_cpu_ex(opcode)

def test_auto_rts_trap(mach):
  def do():
    # create local callback func to test ref-counting
    def my_cb():
      print("HUHU")
    return trap_setup(TRAP_AUTO_RTS, my_cb)
  opcode = do()

  # setup a stack
  w_sp(0x200)
  w32(0x200, 0x300) # return address on stack
  w16(0x300, RESET_OPCODE)

  # set test code
  w_pc(0x100)
  w16(0x100, opcode)
  ne = execute(1000)
  assert ne == 1
  ri = get_info()
  print("TRAP", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_ALINE_TRAP
  assert ev.addr == 0x100
  assert ev.data is not None
  assert ev.handler is None
  # trigger callback
  ev.data()

  # check next steps: auto rts will be performed
  ne = execute(2)
  assert ne == 1
  ri = get_info()
  print("NEXT", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET
  assert ev.addr == 0x302
  assert ev.data is None
  assert ev.handler is None
  # check that stack moved
  assert r_sp() == 0x204

  # finally free trap
  trap_free(opcode)
  # after trap: aline is empty again
  check_aline_cpu_ex(opcode)

def test_many_traps(mach):
  num_free = traps_get_num_free()
  def my_cb():
    print("HUHU")
  # allocate all traps
  tids = []
  for i in range(num_free):
    tid = trap_setup(TRAP_AUTO_RTS, my_cb)
    tids.append(tid)
  # expect error on next allocation
  with pytest.raises(MemoryError):
    trap_setup(TRAP_DEFAULT, my_cb)
  # free all
  for tid in tids:
    trap_free(tid)
