import pytest
from bare68k import *
from bare68k.consts import *
from bare68k.errors import *

def test_cpu_default():
  c = CPUConfig()
  assert c.get_cpu_type() == M68K_CPU_TYPE_68000
  assert c.get_cpu_type_str() == "68000"

def test_set_cpu():
  c = CPUConfig()
  c.set_cpu_type(68010)
  assert c.get_cpu_type() == M68K_CPU_TYPE_68010
  assert c.get_addr_bus_width() == 24
  c.set_cpu_type(20)
  assert c.get_cpu_type() == M68K_CPU_TYPE_68020
  assert c.get_addr_bus_width() == 32
  c.set_cpu_type("10")
  assert c.get_cpu_type() == M68K_CPU_TYPE_68010
  assert c.get_addr_bus_width() == 24
  c.set_cpu_type("68020")
  assert c.get_cpu_type() == M68K_CPU_TYPE_68020
  assert c.get_addr_bus_width() == 32
  c.set_cpu_type("EC20")
  assert c.get_cpu_type() == M68K_CPU_TYPE_68EC020
  assert c.get_addr_bus_width() == 32
  with pytest.raises(ConfigError):
    c.set_cpu_type("bla")
