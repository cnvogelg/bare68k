from __future__ import print_function

import pytest
import traceback

from bare68k.consts import *
from bare68k.machine import *

@pytest.fixture(params=[1,2,3],
                ids=["@$1000", "@$2000","@$3000"])
def mem_rw(mach, request):
  page_no = request.param
  return add_memory(page_no, 1, MEM_FLAGS_RW)

@pytest.fixture(params=[1,2,3],
                ids=["@$1000", "@$2000","@$3000"])
def mem_ro(mach, request):
  page_no = request.param
  return add_memory(page_no, 1, MEM_FLAGS_READ)


def test_invalid_add_memory(mach):
  # invalid memory range (outside of total_pages)
  with pytest.raises(ValueError):
    add_memory(10, 1, MEM_FLAGS_RW)

def test_invalid_rw(mach):
  with pytest.raises(ValueError):
    w8(0x10000, 0)
  with pytest.raises(ValueError):
    w16(0x10000, 0)
  with pytest.raises(ValueError):
    w32(0x10000, 0)
  with pytest.raises(ValueError):
    r8(0x10000)
  with pytest.raises(ValueError):
    r16(0x10000)
  with pytest.raises(ValueError):
    r32(0x10000)

def test_rw_vs_cpu(mem_rw):
  print("test_rw: %08x" % mem_rw)
  for a in xrange(16):
    addr = mem_rw + a
    # write with API and check with CPU
    w8(addr, 42)
    assert r8(addr) == 42
    assert cpu_r8(addr) == 42
    w16(addr, 0xdead)
    assert r16(addr) == 0xdead
    assert cpu_r16(addr) == 0xdead
    w32(addr, 0xcafebabe)
    assert r32(addr) == 0xcafebabe
    assert cpu_r32(addr) == 0xcafebabe
    # write with CPU and check with API
    w8(addr, 42)
    cpu_w8(addr, 43)
    assert r8(addr) == 43
    assert cpu_r8(addr) == 43
    w16(addr, 0xdead)
    cpu_w16(addr, 0xdeaf)
    assert r16(addr) == 0xdeaf
    assert cpu_r16(addr) == 0xdeaf
    w32(addr, 0xcafebabe)
    cpu_w32(addr, 0xcaf0bab0)
    assert r32(addr) == 0xcaf0bab0
    assert cpu_r32(addr) == 0xcaf0bab0

def test_ro_vs_cpu(mem_ro):
  print("test_ro: %08x" % mem_ro)
  for a in xrange(16):
    addr = mem_ro + a
    # write with API and check with CPU
    w8(addr, 42)
    assert r8(addr) == 42
    assert cpu_r8(addr) == 42
    w16(addr, 0xdead)
    assert r16(addr) == 0xdead
    assert cpu_r16(addr) == 0xdead
    w32(addr, 0xcafebabe)
    assert r32(addr) == 0xcafebabe
    assert cpu_r32(addr) == 0xcafebabe
    # write with CPU and check with API
    # no change here as it is read only!
    w8(addr, 42)
    cpu_w8(addr, 43)
    assert r8(addr) == 42
    assert cpu_r8(addr) == 42
    w16(addr, 0xdead)
    cpu_w16(addr, 0xdeaf)
    assert r16(addr) == 0xdead
    assert cpu_r16(addr) == 0xdead
    w32(addr, 0xcafebabe)
    cpu_w32(addr, 0xcaf0bab0)
    assert r32(addr) == 0xcafebabe
    assert cpu_r32(addr) == 0xcafebabe

def test_memory_io(mem_rw):
  # regular access
  w8(mem_rw, 42)
  assert r8(mem_rw) == 42
  w16(mem_rw, 0xdead)
  assert r16(mem_rw) == 0xdead
  w32(mem_rw, 0xcafebabe)
  assert r32(mem_rw) == 0xcafebabe
  # out of bounds
  with pytest.raises(OverflowError):
    w8(mem_rw, -1)
  with pytest.raises(OverflowError):
    w8(mem_rw, 0x100)
  with pytest.raises(OverflowError):
    w16(mem_rw, -1)
  with pytest.raises(OverflowError):
    w16(mem_rw, 0x10000)
  with pytest.raises(OverflowError):
    w32(mem_rw, -1)
  with pytest.raises(OverflowError):
    w32(mem_rw, 0x100000000)
  # signed access
  ws8(mem_rw, -1)
  assert rs8(mem_rw) == -1
  assert r8(mem_rw) == 0xff
  ws16(mem_rw, -1)
  assert rs16(mem_rw) == -1
  assert r16(mem_rw) == 0xffff
  ws32(mem_rw, -1)
  assert rs32(mem_rw) == -1
  assert r32(mem_rw) == 0xffffffff
  # signed out of bounds
  with pytest.raises(OverflowError):
    ws8(mem_rw, -129)
  with pytest.raises(OverflowError):
    ws8(mem_rw, 128)
  with pytest.raises(OverflowError):
    ws16(mem_rw, -2**15 - 1)
  with pytest.raises(OverflowError):
    ws16(mem_rw, 2**15)
  with pytest.raises(OverflowError):
    ws32(mem_rw, -2**31 -1)
  with pytest.raises(OverflowError):
    ws32(mem_rw, 2**31)

def test_set_block(mem_rw):
  set_block(mem_rw, 0x10000, 42)
  assert r8(mem_rw) == 42
  assert r8(mem_rw + 0xffff) == 42

def test_copy_block(mem_rw):
  addr = mem_rw + 0x8000
  set_block(mem_rw, 0x8000, 42)
  assert r8(addr) == 0
  copy_block(mem_rw, addr, 0x8000)
  assert r8(addr) == 42

def test_rw_block(mem_rw):
  set_block(mem_rw, 0x100, 1)
  blk = r_block(mem_rw, 0x100)
  assert len(blk) == 0x100
  w_block(mem_rw + 0x100, blk)
  blk2 = r_block(mem_rw + 0x100, 0x100)
  assert blk == blk2

def test_c_str(mem_rw):
  s = "hello, world!"
  w_cstr(mem_rw, s)
  assert r_cstr(mem_rw) == s

def test_b_str(mem_rw):
  s = "hello, world!"
  w_bstr(mem_rw, s)
  assert r_bstr(mem_rw) == s

def test_cpu_trace_func(mem_rw):
  class Tester:
    value = None
    def set(self, *args):
      self.value = args
    def get(self):
      v = self.value
      print(get_cpu_mem_str(*v))
      return (v[0] & MEM_ACCESS_MASK, v[1], v[2])
  t = Tester()
  set_mem_cpu_trace_func(t.set)
  cpu_w8(mem_rw, 42)
  assert t.get() == (MEM_ACCESS_W8, mem_rw, 42)
  cpu_r8(mem_rw)
  assert t.get() == (MEM_ACCESS_R8, mem_rw, 42)
  cpu_w16(mem_rw, 0xdead)
  assert t.get() == (MEM_ACCESS_W16, mem_rw, 0xdead)
  cpu_r16(mem_rw)
  assert t.get() == (MEM_ACCESS_R16, mem_rw, 0xdead)
  cpu_w32(mem_rw, 0xcafebabe)
  assert t.get() == (MEM_ACCESS_W32, mem_rw, 0xcafebabe)
  cpu_r32(mem_rw)
  assert t.get() == (MEM_ACCESS_R32, mem_rw, 0xcafebabe)

def test_cpu_trace_func_str(mem_rw):
  class Tester:
    value = None
    def set(self, s, v):
      self.value = s
  t = Tester()
  set_mem_cpu_trace_func(t.set, as_str=True)
  cpu_w8(mem_rw, 42)
  assert t.value == "W08:SP @%08x: 0000002a" % mem_rw
  cpu_r8(mem_rw)
  assert t.value == "R08:SP @%08x: 0000002a" % mem_rw
  cpu_w16(mem_rw, 0xdead)
  assert t.value == "W16:SP @%08x: 0000dead" % mem_rw
  cpu_r16(mem_rw)
  assert t.value == "R16:SP @%08x: 0000dead" % mem_rw
  cpu_w32(mem_rw, 0xcafebabe)
  assert t.value == "W32:SP @%08x: cafebabe" % mem_rw
  cpu_r32(mem_rw)
  assert t.value == "R32:SP @%08x: cafebabe" % mem_rw

def test_cpu_trace_func_default(mem_rw):
  set_mem_cpu_trace_func(default=True)
  cpu_w8(mem_rw, 42)
  cpu_r8(mem_rw)
  cpu_w16(mem_rw, 0xdead)
  cpu_r16(mem_rw)
  cpu_w32(mem_rw, 0xcafebabe)
  cpu_r32(mem_rw)

def test_cpu_trace_func_exc(mem_rw):
  # if trace func raises an exception then generate trace event
  ve = ValueError("bohoo")
  def bork(*args):
    raise ve
  set_mem_cpu_trace_func(bork)
  clear_info()
  cpu_w8(mem_rw, 21)
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_TRACE
  assert ev.data[1] == ve
  traceback.print_exception(*ev.data)

def test_cpu_trace_func_val(mem_rw):
  # if trace func returns a value then generate trace event
  val = 42
  def bork(*args):
    return val
  set_mem_cpu_trace_func(bork)
  clear_info()
  cpu_w8(mem_rw, 21)
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_TRACE
  assert ev.data == val

def test_cpu_trace_func_none(mem_rw):
  # if trace func returns None then don't generate an event
  def bork(*args):
    return None
  set_mem_cpu_trace_func(bork)
  clear_info()
  cpu_w8(mem_rw, 21)
  ri = get_info()
  assert ri.num_events == 0

def test_special(mach):
  class special:
    w_val = None
    def r(self, mode, addr):
      print("read", mode, addr)
      return (21, None)
    def w(self, mode, addr, val):
      print("write", mode, addr, val)
      self.w_val = val
  s = special()
  add_special(0, 1, s.r, s.w)
  # test if read func is triggered (without events)
  assert r8(0) == 21
  ri = get_info()
  assert ri.num_events == 0
  # test if write func is triggered (without events)
  w8(1, 11)
  assert s.w_val == 11
  ri = get_info()
  assert ri.num_events == 0

def test_special_with_event(mach):
  class special:
    w_val = None
    def r(self, mode, addr):
      print("read", mode, addr)
      return (21, "r!")
    def w(self, mode, addr, val):
      print("write", mode, addr, val)
      self.w_val = val
      return "w!"
  s = special()
  add_special(0, 1, s.r, s.w)
  # test if read func is triggered (without events)
  assert r8(0) == 21
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_SPECIAL
  assert ev.data == "r!"
  clear_info()
  # test if write func is triggered (without events)
  w8(1, 11)
  assert s.w_val == 11
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_SPECIAL
  assert ev.data == "w!"

def test_special_exc(mach):
  e1 = ValueError("read fault")
  e2 = ValueError("write fault")
  def r(mode, addr):
    raise e1
  def w(mode, addr, val):
    raise e2
  add_special(0, 1, r, w)
  # test read fail
  assert r8(0) == 0
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_CALLBACK_ERROR
  assert ev.data[1] == e1
  traceback.print_exception(*ev.data)
  clear_info()
  # test write fail
  w8(0, 11)
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_CALLBACK_ERROR
  assert ev.data[1] == e2
  traceback.print_exception(*ev.data)

def test_special_none(mach):
  add_special(0, 1, None, None)
  # test read fail
  assert r8(0) == 0
  ri = get_info()
  assert ri.num_events == 0
  clear_info()
  # test write fail
  w8(0, 11)
  ri = get_info()
  assert ri.num_events == 0

def test_empty_val(mach):
  add_empty(0, 1, MEM_FLAGS_READ, 0x40302010)
  assert r8(0) == 0x10
  assert r16(0) == 0x2010
  assert r32(0) == 0x40302010

def test_empty_ro(mach):
  add_empty(0, 1, MEM_FLAGS_READ, 0xffffffff)
  assert r8(0) == 0xff
  assert r16(0) == 0xffff
  assert r32(0) == 0xffffffff
  # w8 fails
  cpu_w8(0, 21)
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_ACCESS
  assert ev.addr == 0
  assert ev.value == 21
  assert ev.flags == MEM_ACCESS_W8 | MEM_FC_SUPER_PROG
  clear_info()
  # w16 fails
  cpu_w16(0, 0x1234)
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_ACCESS
  assert ev.addr == 0
  assert ev.value == 0x1234
  assert ev.flags == MEM_ACCESS_W16 | MEM_FC_SUPER_PROG
  clear_info()
  # w32 fails
  cpu_w32(0, 0x12345678)
  ri = get_info()
  assert ri.num_events == 1
  ev = ri.events[0]
  assert ev.ev_type == CPU_EVENT_MEM_ACCESS
  assert ev.addr == 0
  assert ev.value == 0x12345678
  assert ev.flags == MEM_ACCESS_W32 | MEM_FC_SUPER_PROG

def test_empty_rw(mach):
  add_empty(0, 1, MEM_FLAGS_RW, 0xffffffff)
  assert r8(0) == 0xff
  assert r16(0) == 0xffff
  assert r32(0) == 0xffffffff
  # no events. simply ignored
  cpu_w8(0, 21)
  ri = get_info()
  assert ri.num_events == 0
  cpu_w16(0, 0x1234)
  ri = get_info()
  assert ri.num_events == 0
  cpu_w32(0, 0x12345678)
  ri = get_info()
  assert ri.num_events == 0


def test_api_trace_func(mach):
  class Tester:
    value = None
    def cb(self, flag, addr, val, extra):
      self.value = (flag, addr, val, extra)
  t = Tester()
  set_mem_api_trace_func(t.cb)
  assert t.value == None
  # writes
  w8(0, 13)
  assert t.value == (MEM_ACCESS_W8, 0, 13, 0)
  w16(0x10, 123)
  assert t.value == (MEM_ACCESS_W16, 0x10, 123, 0)
  w32(0x100, 12345)
  assert t.value == (MEM_ACCESS_W32, 0x100, 12345, 0)
  # reads
  r8(0)
  assert t.value == (MEM_ACCESS_R8, 0, 13, 0)
  r16(0x10)
  assert t.value == (MEM_ACCESS_R16, 0x10, 123, 0)
  r32(0x100)
  assert t.value == (MEM_ACCESS_R32, 0x100, 12345, 0)
  # block
  val = "hallo"
  w_block(0x200, val)
  assert t.value == (MEM_ACCESS_W_BLOCK, 0x200, 5, 0)
  val2 = r_block(0x200, 5)
  assert t.value == (MEM_ACCESS_R_BLOCK, 0x200, 5, 0)
  assert val == val2
  set_block(0x400, 32, 0xff)
  assert t.value == (MEM_ACCESS_BSET, 0x400, 32, 0xff)
  copy_block(0x400, 0x500, 64)
  assert t.value == (MEM_ACCESS_BCOPY, 0x500, 64, 0x400)
  # c_str
  s = "hello, world!"
  n = len(s)
  w_cstr(0x100, s)
  assert t.value == (MEM_ACCESS_W_CSTR, 0x100, n, 0)
  s2 = r_cstr(0x100)
  assert t.value == (MEM_ACCESS_R_CSTR, 0x100, n, 0)
  assert s2 == s
  # b_str
  w_bstr(0x200, s)
  assert t.value == (MEM_ACCESS_W_BSTR, 0x200, n, 0)
  s2 = r_bstr(0x200)
  assert t.value == (MEM_ACCESS_R_BSTR, 0x200, n, 0)
  assert s2 == s
  # b32
  wb32(0x10, 0xf0)
  assert t.value == (MEM_ACCESS_W_B32, 0x10, 0xf0, 0)
  rb32(0x10)
  assert t.value == (MEM_ACCESS_R_B32, 0x10, 0xf0, 0)

def test_api_trace_func_str(mach):
  class Tester:
    value = None
    def cb(self, s, v):
      self.value = s
  t = Tester()
  set_mem_api_trace_func(t.cb, as_str=True)
  assert t.value == None
  # writes
  w8(0, 13)
  assert t.value == "w08    @00000000: 0000000d"
  w16(0x10, 123)
  assert t.value == "w16    @00000010: 0000007b"
  w32(0x100, 12345)
  assert t.value == "w32    @00000100: 00003039"
  # reads
  r8(0)
  assert t.value == "r08    @00000000: 0000000d"
  r16(0x10)
  assert t.value == "r16    @00000010: 0000007b"
  r32(0x100)
  assert t.value == "r32    @00000100: 00003039"
  # block
  val = "hallo"
  w_block(0x200, val)
  assert t.value == "wblock @00000200: 00000005"
  val2 = r_block(0x200, 5)
  assert t.value == "rblock @00000200: 00000005"
  assert val == val2
  set_block(0x400, 32, 0xff)
  assert t.value == "bset   @00000400: 00000020, 000000ff"
  copy_block(0x400, 0x500, 64)
  assert t.value == "bcopy  @00000500: 00000040, 00000400"
  # c_str
  s = "hello, world!"
  n = len(s)
  w_cstr(0x100, s)
  assert t.value == "wcstr  @00000100: 0000000d"
  s2 = r_cstr(0x100)
  assert t.value == "rcstr  @00000100: 0000000d"
  assert s2 == s
  # b_str
  w_bstr(0x200, s)
  assert t.value == "wbstr  @00000200: 0000000d"
  s2 = r_bstr(0x200)
  assert t.value == "rbstr  @00000200: 0000000d"
  assert s2 == s
  # b32
  wb32(0x10, 0xf0)
  assert t.value == "wb32   @00000010: 000000f0"
  rb32(0x10)
  assert t.value == "rb32   @00000010: 000000f0"

def test_api_trace_func_exc(mach):
  exc = ValueError("my value err")
  def bork(*args):
    raise exc
  set_mem_api_trace_func(bork)
  # raise exception
  with pytest.raises(ValueError) as e:
    w8(0, 42)
    assert e[1] == exc
  with pytest.raises(ValueError) as e:
    r8(0)
    assert e[1] == exc

def test_api_trace_func_default(mach):
  set_mem_api_trace_func(default=True)
  # writes
  w8(0, 13)
  w16(0x10, 123)
  w32(0x100, 12345)
  # reads
  r8(0)
  r16(0x10)
  r32(0x100)
  # block
  val = "hallo"
  w_block(0x200, val)
  val2 = r_block(0x200, 5)
  assert val == val2
  set_block(0x400, 32, 0xff)
  copy_block(0x400, 0x500, 64)
  # c_str
  s = "hello, world!"
  n = len(s)
  w_cstr(0x100, s)
  s2 = r_cstr(0x100)
  assert s2 == s
  # b_str
  w_bstr(0x200, s)
  s2 = r_bstr(0x200)
  assert s2 == s
  # b32
  wb32(0x10, 0xf0)
  v = rb32(0x10)
  assert v == 0xf0

def test_cpu_access_str():
  s = get_cpu_access_str(MEM_ACCESS_R8 | MEM_FC_USER_DATA)
  assert s == "R08:UD"
  s = get_cpu_access_str(MEM_ACCESS_R16 | MEM_FC_USER_PROG)
  assert s == "R16:UP"
  s = get_cpu_access_str(MEM_ACCESS_R32 | MEM_FC_SUPER_DATA)
  assert s == "R32:SD"
  s = get_cpu_access_str(MEM_ACCESS_W8 | MEM_FC_SUPER_PROG)
  assert s == "W08:SP"
  s = get_cpu_access_str(MEM_ACCESS_W16 | MEM_FC_INT_ACK)
  assert s == "W16:IA"
  s = get_cpu_access_str(MEM_ACCESS_W32 | 0x10)
  assert s == "W32:??"
  s = get_cpu_access_str(0x10)
  assert s == "R??:??"

def test_cpu_fc_str():
  s = get_cpu_fc_str(MEM_FC_USER_DATA)
  assert s == "UD"
  s = get_cpu_fc_str(MEM_FC_USER_PROG)
  assert s == "UP"
  s = get_cpu_fc_str(MEM_FC_SUPER_DATA)
  assert s == "SD"
  s = get_cpu_fc_str(MEM_FC_SUPER_PROG)
  assert s == "SP"
  s = get_cpu_fc_str(MEM_FC_INT_ACK)
  assert s == "IA"
  s = get_cpu_fc_str(0x10)
  assert s == "??"

def test_api_access_str():
  s = get_api_access_str(MEM_ACCESS_R8)
  assert s == "r08   "
  s = get_api_access_str(MEM_ACCESS_R16)
  assert s == "r16   "
  s = get_api_access_str(MEM_ACCESS_R32)
  assert s == "r32   "
  s = get_api_access_str(MEM_ACCESS_W8)
  assert s == "w08   "
  s = get_api_access_str(MEM_ACCESS_W16)
  assert s == "w16   "
  s = get_api_access_str(MEM_ACCESS_W32)
  assert s == "w32   "
  s = get_api_access_str(0)
  assert s == "r??   "
  s = get_api_access_str(MEM_ACCESS_BCOPY)
  assert s == "bcopy "
  s = get_api_access_str(MEM_ACCESS_BSET)
  assert s == "bset  "
  s = get_api_access_str(MEM_ACCESS_R_BLOCK)
  assert s == "rblock"
  s = get_api_access_str(MEM_ACCESS_W_BLOCK)
  assert s == "wblock"
  s = get_api_access_str(MEM_ACCESS_R_CSTR)
  assert s == "rcstr "
  s = get_api_access_str(MEM_ACCESS_W_CSTR)
  assert s == "wcstr "
  s = get_api_access_str(MEM_ACCESS_R_B32)
  assert s == "rb32  "
  s = get_api_access_str(MEM_ACCESS_W_B32)
  assert s == "wb32  "
