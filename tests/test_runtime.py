import pytest
import traceback

from bare68k import *
from bare68k.api import *
from bare68k.consts import *

RESET_OPCODE = 0x4e70
NOP_OPCODE = 0x4e71

def test_runtime_init_shutdown():
  cpu_cfg = CPUConfig()
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, 1)
  run_cfg = RunConfig()
  rt = Runtime(cpu_cfg, mem_cfg, run_cfg)
  rt.shutdown()

def test_runtime_init_quick_shutdown():
  rt = runtime.init_quick()
  rt.shutdown()

def test_runtime_memcfg():
  cpu_cfg = CPUConfig()
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, 1)
  mem_cfg.add_rom_range(1, 1, b"hallo", pad=True)
  def r_func():
    pass
  def w_func():
    pass
  mem_cfg.add_special_range(2, 1, r_func, w_func)
  mem_cfg.add_empty_range(3, 1, 0x11223344)
  mem_cfg.add_mirror_range(4, 1, 0)
  mem_cfg.add_reserve_range(5, 1)
  run_cfg = RunConfig()
  rt = Runtime(cpu_cfg, mem_cfg, run_cfg)
  rt.shutdown()

def test_runtime_init(rt):
  print(rt.get_run_cfg())

def test_rt_mem_cpu(rt):
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, RESET_OPCODE)
  cpu.w_reg(M68K_REG_D0, 0)

# --- test reset ---

def test_rt_reset_quit_on_first(rt):
  is_68k = rt.get_cpu_cfg().get_cpu_type() == M68K_CPU_TYPE_68000
  reset_cycles = 132 if is_68k else 518
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, RESET_OPCODE)
  ri = rt.run()
  assert ri.total_cycles == reset_cycles
  assert cpu.r_pc() == PROG_BASE + 2
  assert ri.get_last_result() == CPU_EVENT_DONE

def test_rt_reset_quit_on_pc(rt):
  is_68k = rt.get_cpu_cfg().get_cpu_type() == M68K_CPU_TYPE_68000
  reset_cycles = 132 if is_68k else 518
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, RESET_OPCODE)
  mem.w16(PROG_BASE+2, RESET_OPCODE)
  ri = rt.run(reset_end_pc=PROG_BASE + 4)
  assert ri.total_cycles == reset_cycles
  assert cpu.r_pc() == PROG_BASE + 2
  assert ri.get_last_result() == CPU_EVENT_RESET

# --- test cb error ---

def test_rt_cb_error_abort(rt):
  def hook(pc):
    raise KeyboardInterrupt()
  cpu.set_instr_hook_func(hook)
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, RESET_OPCODE)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_USER_ABORT

def test_rt_cb_error_exc(rt):
  def hook(pc):
    raise MemoryError()
  cpu.set_instr_hook_func(hook)
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, RESET_OPCODE)
  with pytest.raises(MemoryError):
    ri = rt.run()

# --- memory events ---

def test_rt_mem_access(rt):
  # access between RAM and ROM
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, 0x23c0) # move.l d0,<32b_addr>
  mem.w32(PROG_BASE+2, 0x10000)
  mem.w16(PROG_BASE+6, RESET_OPCODE)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_DONE
  assert ri.get_stats().get_event_count(CPU_EVENT_MEM_ACCESS) == 1

def test_rt_mem_bounds(rt):
  # access beyond max pages
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, 0x23c0) # move.l d0,<32b_addr>
  mem.w32(PROG_BASE+2, 0x100000)
  mem.w16(PROG_BASE+6, RESET_OPCODE)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_DONE
  assert ri.get_stats().get_event_count(CPU_EVENT_MEM_BOUNDS) == 1

def test_rt_mem_access_code(rt):
  # access between RAM and ROM
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, 0x4ef9) # jmp <32b_addr>
  mem.w32(PROG_BASE+2, 0x10000)
  mem.w16(PROG_BASE+6, RESET_OPCODE)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_MEM_ACCESS

def test_rt_mem_bounds_code(rt):
  # access beyond max pages
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, 0x4ef9) # jmp <32b_addr>
  mem.w32(PROG_BASE+2, 0x100000)
  mem.w16(PROG_BASE+6, RESET_OPCODE)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_MEM_ACCESS

# --- memory trace

def test_rt_mem_trace_return(rt):
  def handler(s, v):
    return "s=%s,v=%s" % (s, v)
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, 0x23c0) # move.l d0,<32b_addr>
  mem.w32(PROG_BASE+2, 0)
  mem.w16(PROG_BASE+6, RESET_OPCODE)
  mem.set_mem_cpu_trace_func(handler, as_str=True)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_MEM_TRACE

def test_rt_mem_trace_kb_intr(rt):
  def handler(s, v):
    raise KeyboardInterrupt
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, 0x23c0) # move.l d0,<32b_addr>
  mem.w32(PROG_BASE+2, 0)
  mem.w16(PROG_BASE+6, RESET_OPCODE)
  mem.set_mem_cpu_trace_func(handler, as_str=True)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_USER_ABORT

def test_rt_mem_trace_exc(rt):
  def handler(s, v):
    raise MemoryError
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, 0x23c0) # move.l d0,<32b_addr>
  mem.w32(PROG_BASE+2, 0)
  mem.w16(PROG_BASE+6, RESET_OPCODE)
  mem.set_mem_cpu_trace_func(handler, as_str=True)
  with pytest.raises(MemoryError):
    ri = rt.run()

# --- traps ---

def test_rt_trap_cpu(rt):
  """an unbound trap causing a CPU exception vector"""
  PROG_BASE = rt.get_reset_pc()
  mem.w16(PROG_BASE, 0xa000)
  mem.w32(0x28, PROG_BASE + 10)
  mem.w16(PROG_BASE + 10, RESET_OPCODE)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_DONE

def test_rt_trap_unbound(rt):
  """enable unbound trap and get a ALINE_TRAP event"""
  PROG_BASE = rt.get_reset_pc()
  traps.trap_enable(0xa000)
  mem.w16(PROG_BASE, 0xa000)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_ALINE_TRAP

class TrapHelper:
  def __init__(self):
    self.event = None
  def __call__(self, event):
    self.event = event

def test_rt_trap_setup(rt):
  """setup a bound trap that gets called automatically"""
  PROG_BASE = rt.get_reset_pc()
  th = TrapHelper()
  op = traps.trap_setup(TRAP_DEFAULT, th)
  mem.w16(PROG_BASE, op)
  mem.w16(PROG_BASE + 2, RESET_OPCODE)
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_DONE
  assert th.event is not None

def test_rt_trap_fail(rt):
  """the trap callback raises an exception"""
  PROG_BASE = rt.get_reset_pc()
  def fail(event):
    raise ValueError("failed!")
  op = traps.trap_setup(TRAP_DEFAULT, fail)
  mem.w16(PROG_BASE, op)
  mem.w16(PROG_BASE + 2, RESET_OPCODE)
  with pytest.raises(ValueError):
    ri = rt.run()

def test_rt_trap_catch(rt):
  """the trap callback raises an exception"""
  PROG_BASE = rt.get_reset_pc()
  def fail(event):
    raise ValueError("failed!")
  op = traps.trap_setup(TRAP_DEFAULT, fail)
  mem.w16(PROG_BASE, op)
  mem.w16(PROG_BASE + 2, RESET_OPCODE)
  try:
    ri = rt.run()
  except Exception as e:
    traceback.print_exc()

def test_rt_breakpoint(rt):
  """test breakpoints"""
  PROG_BASE = rt.get_reset_pc()
  # loop endless
  # 0x1000: jmp.w 0x1000
  mem.w16(PROG_BASE, 0x4ef8)
  mem.w16(PROG_BASE+2, PROG_BASE)
  tools.setup_breakpoints(1)
  tools.set_breakpoint(0, PROG_BASE, MEM_FC_SUPER_MASK, "bla")
  ri = rt.run()

def test_rt_watchpoint(rt):
  """test watchpoints"""
  PROG_BASE = rt.get_reset_pc()
  # loop endless
  # 0x1000: jmp.w 0x1000
  mem.w16(PROG_BASE, 0x4ef8)
  mem.w16(PROG_BASE+2, PROG_BASE)
  tools.setup_watchpoints(1)
  tools.set_watchpoint(0, PROG_BASE, MEM_FC_SUPER_MASK, "bla")
  ri = rt.run()

MOVEM_TO_SP = 0x48e7fffe
MOVEM_FROM_SP = 0x4cdf7fff

def test_rt_recursive_run(rt):
  """run a sub call inside a trap"""
  PROG_BASE = rt.get_reset_pc()
  def trap_cb(event):
    # recursive run
    ri = rt.run(start_pc=PROG_BASE+4)
    assert ri.get_last_result() == CPU_EVENT_DONE
  op = traps.trap_setup(TRAP_DEFAULT, trap_cb)
  # main code
  mem.w16(PROG_BASE, op)
  mem.w16(PROG_BASE + 2, RESET_OPCODE)
  # sub code
  mem.w32(PROG_BASE+4, MOVEM_TO_SP)
  mem.w32(PROG_BASE+8, MOVEM_FROM_SP)
  mem.w16(PROG_BASE+12, RESET_OPCODE)
  # run
  ri = rt.run()
  assert ri.get_last_result() == CPU_EVENT_DONE
