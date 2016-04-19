from __future__ import print_function

import pytest
from bare68k.consts import *
from bare68k.machine import *

RESET_OPCODE = 0x4e70
NOP_OPCODE = 0x4e71

def test_machine_init_exit(mach):
  pass

def test_register_access(mach):
  # regulare rw
  w_reg(M68K_REG_D0, 42)
  assert r_reg(M68K_REG_D0) == 42
  assert r_dx(0) == 42
  w_dx(1, 23)
  assert r_reg(M68K_REG_D1) == 23
  assert r_dx(1) == 23
  # unsigned limits
  w_reg(M68K_REG_D0, 0xffffffff)
  assert r_reg(M68K_REG_D0) == 0xffffffff
  # signed access
  ws_reg(M68K_REG_D0, -1)
  assert rs_reg(M68K_REG_D0) == -1
  assert r_reg(M68K_REG_D0) == 0xffffffff
  # signed limits
  ws_reg(M68K_REG_D0, -2**31)
  assert rs_reg(M68K_REG_D0) == -2**31
  assert r_reg(M68K_REG_D0) == 0x80000000
  ws_reg(M68K_REG_D0, 2**31 - 1)
  assert rs_reg(M68K_REG_D0) == 2**31 - 1
  assert r_reg(M68K_REG_D0) == 0x7fffffff
  # overflow: unsigned
  with pytest.raises(OverflowError):
    w_reg(M68K_REG_D0, -1)
  with pytest.raises(OverflowError):
    w_reg(M68K_REG_D0, 0x100000000)
  # overflow: signed
  with pytest.raises(OverflowError):
    ws_reg(M68K_REG_D0, -2**31 -1)
  with pytest.raises(OverflowError):
    ws_reg(M68K_REG_D0, 2**31)

def test_memory_access(mach):
  w8(0,42)
  assert r8(0) == 42
  w16(12,0xdead)
  assert r16(12) == 0xdead
  w32(16,0xcafebabe)
  assert r32(16) == 0xcafebabe

def test_nop(mach):
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, NOP_OPCODE)
  w16(0x106, NOP_OPCODE)
  assert r16(0x100) == NOP_OPCODE
  w_pc(0x100)
  ne = execute(2)
  assert ne == 0
  ri = get_info()
  print("NOP", ri)
  assert ri.num_events == 0
  assert ri.done_cycles in (2, 4)
  assert ri.total_cycles == ri.done_cycles
  # check alternative access
  assert get_num_events() == 0
  assert get_done_cycles() in (2, 4)
  assert get_total_cycles() == get_done_cycles()
  # check increasing total cycles
  ne = execute(2)
  assert ne == 0
  ri = get_info()
  print("NOP2", ri)
  assert ri.num_events == 0
  assert ri.done_cycles in (2, 4)
  assert ri.total_cycles == ri.done_cycles * 2
  # check alternative access
  assert get_num_events() == 0
  assert get_done_cycles() in (2, 4)
  assert get_total_cycles() == get_done_cycles() * 2

def test_reset(mach):
  w16(0x100, RESET_OPCODE)
  assert r16(0x100) == RESET_OPCODE
  w_pc(0x100)
  ne = execute(1000)
  assert ne == 1
  ri = get_info()
  print("RESET", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET
  assert ev.addr == 0x102
  assert ev.data is None
  assert ev.handler is None
  # check alternative access
  assert get_num_events() == 1
  ev2 = get_event(0)
  assert ev2.ev_type == CPU_EVENT_RESET
  assert ev2.addr == 0x102
  assert ev2.data is None
  assert ev2.handler is None

def test_reset_def_handler(mach):
  def bla():
    print("bla")
  event_handlers[CPU_EVENT_RESET] = bla
  w16(0x100, RESET_OPCODE)
  assert r16(0x100) == RESET_OPCODE
  w_pc(0x100)
  ne = execute(1000)
  assert ne == 1
  ri = get_info()
  print("RESET", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET
  assert ev.addr == 0x102
  assert ev.data is None
  assert ev.handler is bla

def test_execute_to_event(mach):
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, RESET_OPCODE)
  w16(0x106, NOP_OPCODE)
  w16(0x108, NOP_OPCODE)
  w16(0x10a, RESET_OPCODE)
  w_pc(0x100)
  set_instr_hook_func(default=True)
  ne = execute_to_event(0)
  assert ne == 1
  ri = get_info()
  print("TO_EV", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET
  assert ev.addr == 0x106
  ne = execute_to_event(0)
  assert ne == 1
  ri = get_info()
  print("TO_EV2", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_RESET
  assert ev.addr == 0x10c

def test_instr_hook(mach):
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, NOP_OPCODE)
  w16(0x106, NOP_OPCODE)
  assert r16(0x100) == NOP_OPCODE
  class hook:
    pcs = []
    def func(self, pc):
      print("pc=$%08x" % pc)
      self.pcs.append(pc)
  # with hook
  h = hook()
  set_instr_hook_func(h.func)
  w_pc(0x100)
  ne = execute(2)
  assert ne == 0
  ri = get_info()
  print("INSTR_HOOK1", ri)
  assert ri.num_events == 0
  assert h.pcs == [0x100]
  # without hook
  set_instr_hook_func(None)
  ne = execute(2)
  assert ne == 0
  ri = get_info()
  print("INSTR_HOOK2", ri)
  assert ri.num_events == 0
  assert h.pcs == [0x100]

def test_instr_hook_str(mach):
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, NOP_OPCODE)
  w16(0x106, NOP_OPCODE)
  class hook:
    pcs = []
    def func(self, s, pc):
      self.pcs.append(s)
  # with hook
  h = hook()
  set_instr_hook_func(h.func, as_str=True)
  w_pc(0x100)
  ne = execute(2)
  assert ne == 0
  ri = get_info()
  print("INSTR_HOOK1", ri)
  assert ri.num_events == 0
  assert h.pcs == ["00000100: nop"]
  # without hook
  set_instr_hook_func(None)
  ne = execute(2)
  assert ne == 0
  ri = get_info()
  print("INSTR_HOOK2", ri)
  assert ri.num_events == 0
  assert h.pcs == ["00000100: nop"]

def test_instr_hook_exc(mach):
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, NOP_OPCODE)
  w16(0x106, NOP_OPCODE)
  assert r16(0x100) == NOP_OPCODE
  e = ValueError("ouch")
  def hook(pc):
    raise e
  set_instr_hook_func(hook)
  w_pc(0x100)
  ne = execute(2)
  assert ne == 1
  ri = get_info()
  print("INSTR_HOOK_EXC", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_CALLBACK_ERROR
  assert ev.data == e

def test_instr_hook_value(mach):
  w16(0x100, NOP_OPCODE)
  w16(0x102, NOP_OPCODE)
  w16(0x104, NOP_OPCODE)
  w16(0x106, NOP_OPCODE)
  assert r16(0x100) == NOP_OPCODE
  def hook(pc):
    return 42
  set_instr_hook_func(hook)
  w_pc(0x100)
  ne = execute(2)
  assert ne == 1
  ri = get_info()
  print("INSTR_HOOK_EXC", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_INSTR_HOOK
  assert ev.data == 42

def test_context(mach):
  w_pc(0x100)
  ctx = get_cpu_context()
  w_pc(0x200)
  assert r_pc() == 0x200
  assert ctx.r_reg(M68K_REG_PC) == 0x100
  set_cpu_context(ctx)
  assert r_pc() == 0x100

def test_irq_autovec_nofunc(mach):
  def func(pc):
    print("pc=$%08x" % pc)
  set_instr_hook_func(func)
  def mem(mode, addr, val):
    print("mem: %d @%08x =%08x" % (mode, addr, val))
  set_mem_cpu_trace_func(mem)
  # set autovec of level 7 to memfault
  w32(0x7c, 0x10000)
  w16(0x100, NOP_OPCODE)
  w_pc(0x100)
  w_sp(0x400)
  set_irq(7)
  ne = execute(2)
  assert ne == 1
  ri = get_info()
  print("IRQ", ri)
  ri = get_info()
  # check for memfault
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_ACCESS
  assert ev.addr == 0x10000

def test_irq_autovec_func(mach):
  def func(pc):
    print("pc=$%08x" % pc)
  set_instr_hook_func(func)
  def mem(mode, addr, val):
    print("mem: %d @%08x =%08x" % (mode, addr, val))
  set_mem_cpu_trace_func(mem)
  def int_ack(level, pc):
    print("int_ack:", level)
    return (M68K_INT_ACK_AUTOVECTOR, "huhu")
  # set autovec of level 7
  w32(0x7c, 0x200)
  w_sp(0x10000)
  w16(0x100, NOP_OPCODE)
  w_pc(0x100)
  set_int_ack_func(int_ack)
  set_irq(7)
  ne = execute(2)
  assert ne == 1
  ri = get_info()
  print("IRQ", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_INT_ACK
  assert ev.flags == 7 # int_level
  assert ev.value == M68K_INT_ACK_AUTOVECTOR
  assert ev.data == "huhu"

def test_irq_vec_func(mach):
  def func(pc):
    print("pc=$%08x" % pc)
  set_instr_hook_func(func)
  def mem(mode, addr, val):
    print("mem: %d @%08x =%08x" % (mode, addr, val))
  set_mem_cpu_trace_func(mem)
  def int_ack(level, pc):
    print("int_ack:", level)
    return (2, "hello") # return vector 2 and generate event
  # set vector 2
  w32(0x8, 0x200)
  w_sp(0x10000)
  w16(0x100, NOP_OPCODE)
  w_pc(0x100)
  set_int_ack_func(int_ack)
  set_irq(7)
  ne = execute(2)
  assert ne == 1
  ri = get_info()
  print("IRQ", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_INT_ACK
  assert ev.flags == 7 # int_level
  assert ev.value == 2 # vector 2
  assert ev.data == "hello"

def test_irq_vec_exc(mach):
  def func(pc):
    print("pc=$%08x" % pc)
  set_instr_hook_func(func)
  def mem(mode, addr, val):
    print("mem: %d @%08x =%08x" % (mode, addr, val))
  set_mem_cpu_trace_func(mem)
  e = ValueError("blurp")
  def int_ack(level, pc):
    raise e
  # set vector 2
  w32(0x8, 0x200)
  w_sp(0x10000)
  w16(0x100, NOP_OPCODE)
  w_pc(0x100)
  set_int_ack_func(int_ack)
  set_irq(7)
  ne = execute(2)
  assert ne == 1
  ri = get_info()
  print("IRQ_EX", ri)
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_CALLBACK_ERROR
  assert ev.data == e

def test_get_sr_str(mach):
  sr = r_sr()
  s = get_sr_str(sr)
  assert s == "--S--210--------"

def test_get_regs(mach):
  r = get_regs()
  # test printout
  l = r.get_lines()
  assert len(l) == 3
  # now change some value
  r.w_pc(0xdeadbeef)
  assert r.r_pc() == 0xdeadbeef
  r.w_dx(0, 42)
  assert r.r_dx(0) == 42
  r.w_ax(1, 0x1000)
  assert r.r_ax(1) == 0x1000
  r.w_sr(0)
  assert r.r_sr() == 0
  # realize change in CPU
  r.write()
  assert r_pc() == r.r_pc()
  assert r_sr() == r.r_sr()
  assert r_dx(0) == r.r_dx(0)
  assert r_ax(1) == r.r_ax(1)

def test_mem_access(mach):
  JMP_OP = 0x4ef9
  w16(0x100, JMP_OP)
  w32(0x102, 0x30000) # invalid mem access (page not ram)
  w_pc(0x100)
  ne = execute(100)
  assert ne >= 1
  ri = get_info()
  print("MEM_ACCESS", ri)
  assert ri.num_events >= 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_ACCESS
  assert ev.flags == 0x62 # SUPER+PROG + R16
  assert ev.addr == 0x30000

def test_mem_bounds(mach):
  JMP_OP = 0x4ef9
  w16(0x100, JMP_OP)
  w32(0x102, 0x40000) # invalid mem access (page not ram)
  w_pc(0x100)
  ne = execute(100)
  assert ne >= 1
  ri = get_info()
  print("MEM_ACCESS", ri)
  assert ri.num_events >= 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_BOUNDS
  assert ev.flags == 0x62 # SUPER+PROG + R16
  assert ev.addr == 0x40000
