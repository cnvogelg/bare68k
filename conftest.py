import pytest
from bare68k.consts import *
from bare68k.machine import *

@pytest.fixture(params=[M68K_CPU_TYPE_68000, M68K_CPU_TYPE_68020],
                ids=["68000", "68020"])
def mach(request):
  cpu = request.param
  init(cpu, 4)
  request.addfinalizer(shutdown)
  add_memory(0, 1, MEM_FLAGS_RW | MEM_FLAGS_TRAPS)
  pulse_reset()
