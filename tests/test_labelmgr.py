import pytest

from bare68k import *
from bare68k.consts import *
from bare68k.machine import *

PROG_BASE = 0x1000
STACK = 0x800

@pytest.fixture
def lm(request):
  runtime.log_setup()
  cpu_cfg = CPUConfig(M68K_CPU_TYPE_68000)
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, 1)
  mem_cfg.add_rom_range(2, 1)
  run_cfg = RunConfig(with_labels=True)
  rt = Runtime(cpu_cfg, mem_cfg, run_cfg)
  rt.reset(PROG_BASE, STACK)
  yield rt.get_label_mgr()
  rt.shutdown()

@pytest.fixture
def lmd(request):
  runtime.log_setup()
  cpu_cfg = CPUConfig(M68K_CPU_TYPE_68000)
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, 1)
  mem_cfg.add_rom_range(2, 1)
  run_cfg = RunConfig(with_labels=False)
  rt = Runtime(cpu_cfg, mem_cfg, run_cfg)
  rt.reset(PROG_BASE, STACK)
  yield rt.get_label_mgr()
  rt.shutdown()


def test_lm_setup(lm):
  # make sure we get a label mgr
  assert lm is not None

def test_lm_add_find_remove(lm):
  assert lm.get_num_labels() == 0
  assert lm.get_num_page_labels(0) == 0
  assert lm.get_all_labels() is None
  assert lm.get_page_labels(0) is None
  # add
  data = "hello, world!"
  l = lm.add_label(0, 100, data)
  assert l is not None
  assert l.addr() == 0
  assert l.size() == 100
  assert l.data() == data
  assert lm.get_num_labels() == 1
  assert lm.get_num_page_labels(0) == 1
  assert lm.get_all_labels() == [l]
  assert lm.get_page_labels(0) == [l]
  # find
  l2 = lm.find_label(50)
  assert l2 == l
  # remove
  lm.remove_label(l)
  assert lm.get_num_labels() == 0
  assert lm.get_num_page_labels(0) == 0
  assert lm.get_all_labels() is None
  assert lm.get_page_labels(0) is None

def test_lm_find_intersecting(lm):
  l1 = lm.add_label(0, 100, "l1")
  l2 = lm.add_label(200, 100, "l2")
  assert lm.get_num_labels() == 2
  res = lm.find_intersecting_labels(50,200)
  assert res == [l1, l2]
  res2 = lm.find_intersecting_labels(300,100)
  assert res2 is None

def test_lm_remove_inside(lm):
  l1 = lm.add_label(0, 100, "l1")
  l2 = lm.add_label(200, 100, "l2")
  assert lm.get_num_labels() == 2
  num = lm.remove_labels_inside(300,300)
  assert num == 0
  num = lm.remove_labels_inside(0,300)
  assert num == 2
  assert lm.get_num_labels() == 0

def test_lm_dummy(lmd):
  assert lmd.get_num_labels() == 0
  assert lmd.get_num_page_labels(0) == 0
  assert lmd.get_all_labels() is None
  assert lmd.get_page_labels(0) is None
  assert lmd.add_label(0, 100, "hello") is None
  assert lmd.remove_label(None) is None
  assert lmd.remove_labels_inside(0, 100) == 0
  assert lmd.find_label(50) is None
  assert lmd.find_intersecting_labels(0,100) is None

