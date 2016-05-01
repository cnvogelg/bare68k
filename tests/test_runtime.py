from bare68k import *

def test_init_shutdown():
  cpu_cfg = CPUConfig()
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, 1)
  runtime.init(cpu_cfg, mem_cfg)
  runtime.shutdown()

def test_init_quick_shutdown():
  runtime.init_quick()
  runtime.shutdown()
