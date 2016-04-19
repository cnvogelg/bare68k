from bare68k import *

def test_setup_shutdown_runtime():
  cpu_cfg = CPUConfig()
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, 1)
  runtime.init(cpu_cfg, mem_cfg)
  runtime.shutdown()
