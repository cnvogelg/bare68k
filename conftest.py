import pytest

from bare68k import *
from bare68k.consts import *
from bare68k.machine import *

@pytest.fixture(params=[M68K_CPU_TYPE_68000, M68K_CPU_TYPE_68020],
                ids=["68000", "68020"])
def mach(request):
  use_labels = getattr(request.module, "use_labels", False)
  if use_labels:
    print("Using labels")
  cpu = request.param
  init(cpu, 4, use_labels)
  add_memory(0, 1, MEM_FLAGS_RW | MEM_FLAGS_TRAPS)
  pulse_reset()
  yield
  shutdown(use_labels)

PROG_BASE = 0x1000
STACK = 0x800

@pytest.fixture(params=[M68K_CPU_TYPE_68000, M68K_CPU_TYPE_68020],
                ids=["68000", "68020"])
def rt(request):
  runtime.log_setup()
  cpu_cfg = CPUConfig(request.param)
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, 1)
  mem_cfg.add_rom_range(2, 1)
  run_cfg = RunConfig()
  rt = Runtime(cpu_cfg, mem_cfg, run_cfg)
  rt.reset(PROG_BASE, STACK)
  yield rt
  rt.shutdown()
