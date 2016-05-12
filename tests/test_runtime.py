import pytest
import traceback

from bare68k import *
from bare68k.consts import *

PROG_BASE = 0x1000
STACK = 0x800

RESET_OPCODE = 0x4e70
NOP_OPCODE = 0x4e71

@pytest.fixture(params=[M68K_CPU_TYPE_68000, M68K_CPU_TYPE_68020],
                ids=["68000", "68020"])
def rt(request):
  runtime.log_setup()
  cpu_cfg = CPUConfig(request.param)
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, 1)
  mem_cfg.add_rom_range(2, 1)
  runtime.init(cpu_cfg, mem_cfg)
  request.addfinalizer(runtime.shutdown)
  runtime.reset(PROG_BASE, STACK)
  return runtime


def test_init_shutdown():
  cpu_cfg = CPUConfig()
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, 1)
  runtime.init(cpu_cfg, mem_cfg)
  runtime.shutdown()

def test_init_quick_shutdown():
  runtime.init_quick()
  runtime.shutdown()

def test_runtime_init(rt):
  pass

def test_mem_cpu(rt):
  mem.w16(PROG_BASE, RESET_OPCODE)
  cpu.w_reg(M68K_REG_D0, 0)

def test_reset_quit_on_first(rt):
  is_68k = rt.get_cpu_cfg().get_cpu_type() == M68K_CPU_TYPE_68000
  reset_cycles = 132 if is_68k else 518
  mem.w16(PROG_BASE, RESET_OPCODE)
  ri = rt.run()
  assert ri.total_cycles == reset_cycles
  assert cpu.r_pc() == PROG_BASE + 2
  assert ri.results == [rt.RETURN_OK]

def test_reset_quit_on_pc(rt):
  is_68k = rt.get_cpu_cfg().get_cpu_type() == M68K_CPU_TYPE_68000
  reset_cycles = 132 if is_68k else 518
  mem.w16(PROG_BASE, RESET_OPCODE)
  mem.w16(PROG_BASE+2, RESET_OPCODE)
  ri = rt.run(reset_end_pc=PROG_BASE + 4)
  assert ri.total_cycles == reset_cycles * 2
  assert cpu.r_pc() == PROG_BASE + 4
  assert ri.results == [rt.RETURN_OK]

def test_mem_access(rt):
  # access between RAM and ROM
  cpu.w_pc(0x10000)
  ri = rt.run()
  assert ri.results == [rt.RETURN_MEM_ACCESS]

def test_mem_bounds(rt):
  # access beyond max pages
  cpu.w_pc(0x100000)
  ri = rt.run()
  assert ri.results == [rt.RETURN_MEM_BOUNDS]

# --- traps ---

def test_rt_trap_cpu(rt):
  """an unbound trap causing a CPU exception vector"""
  mem.w16(PROG_BASE, 0xa000)
  mem.w32(0x28, PROG_BASE + 10)
  mem.w16(PROG_BASE + 10, RESET_OPCODE)
  ri = rt.run()
  assert ri.results == [rt.RETURN_OK]

def test_rt_trap_unbound(rt):
  """enable unbound trap and get a ALINE_TRAP event"""
  traps.enable(0xa000)
  mem.w16(PROG_BASE, 0xa000)
  ri = rt.run()
  assert ri.results == [rt.RETURN_ALINE_TRAP]

class TrapHelper:
  def __init__(self):
    self.event = None
  def __call__(self, event):
    self.event = event

def test_rt_trap_setup(rt):
  """setup a bound trap that gets called automatically"""
  th = TrapHelper()
  op = traps.setup(TRAP_DEFAULT, th)
  mem.w16(PROG_BASE, op)
  mem.w16(PROG_BASE + 2, RESET_OPCODE)
  ri = rt.run()
  assert ri.results == [rt.RETURN_OK]
  assert th.event is not None

def test_rt_trap_fail(rt):
  """the trap callback raises an exception"""
  def fail(event):
    raise ValueError("failed!")
  op = traps.setup(TRAP_DEFAULT, fail)
  mem.w16(PROG_BASE, op)
  mem.w16(PROG_BASE + 2, RESET_OPCODE)
  with pytest.raises(ValueError):
    ri = rt.run()

def test_rt_trap_catch(rt):
  """the trap callback raises an exception"""
  def fail(event):
    raise ValueError("failed!")
  op = traps.setup(TRAP_DEFAULT, fail)
  mem.w16(PROG_BASE, op)
  mem.w16(PROG_BASE + 2, RESET_OPCODE)
  try:
    ri = rt.run()
  except Exception as e:
    traceback.print_exc()
