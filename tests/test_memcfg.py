import pytest
from bare68k import *
from bare68k.consts import *
from bare68k.errors import *

@pytest.fixture(params=[M68K_CPU_TYPE_68000, M68K_CPU_TYPE_68020],
                ids=["68000", "68020"])
def memcfg(request):
  cpu = request.param
  cpu_cfg = CPUConfig(cpu)
  mem_cfg = MemoryConfig(cpu_cfg)
  return mem_cfg

def test_int_str_size(memcfg):
  # string to size conversion
  assert memcfg._get_str_size("23",10) == (23,10)
  assert memcfg._get_str_size("23k",11) == (23,1024)
  assert memcfg._get_str_size("23m",12) == (23,1024 * 1024)
  assert memcfg._get_str_size("23g",13) == (23,1024 * 1024 * 1024)
  assert memcfg._get_str_size("23p",14) == (23,64 * 1024)

def test_int_page_size(memcfg):
  with pytest.raises(ConfigError):
    # 1k is not a page
    memcfg._get_num_pages(1,1024)
  assert memcfg._get_num_pages(1,64 * 1024) == 1
  assert memcfg._get_num_pages(64, 1024) == 1
  assert memcfg._get_num_pages("1p", 1024) == 1

def test_ram_ranges(memcfg):
  assert memcfg.get_page_list() == []
  # add a range starting at page 1 with 2 pages size
  memcfg.add_ram_range(1,2)
  pl = memcfg.get_page_list()
  assert len(pl) == 3
  assert pl[0] == (memcfg.EMPTY_FLAG, None)
  assert pl[1] == (memcfg.RAM_FLAG, None)
  assert pl[2] == (memcfg.RAM_FLAG, None)
  # add another range
  memcfg.add_ram_range(4,3)
  pl = memcfg.get_page_list()
  assert len(pl) == 7
  assert pl[3] == (memcfg.EMPTY_FLAG, None)
  assert pl[4] == (memcfg.RAM_FLAG, None)
  assert pl[5] == (memcfg.RAM_FLAG, None)
  assert pl[6] == (memcfg.RAM_FLAG, None)
  print(memcfg.get_page_list_str())
  # overlapping range gives error
  with pytest.raises(ConfigError):
    memcfg.add_ram_range(2,4)
