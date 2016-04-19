"""the runtime module drives the m68k processor emulation of bare68k.
"""

import bare68k.machine as mach
import bare68k.cpu as cpu
import bare68k.mem as mem
from bare68k.memcfg import *
from bare68k.consts import *

# globals
_cpu_cfg = None
_mem_cfg = None

def init(cpu_cfg, mem_cfg):
  """setup runtime.

  before you can run your system emulation you have to init() the system
  by providing a configuration for the CPU and the memory layout
  """
  global _cpu_cfg, _mem_cfg
  _cpu_cfg = cpu_cfg
  _mem_cfg = mem_cfg
  # check mem config
  max_pages = cpu_cfg.get_max_pages()
  mem_cfg.check(max_pages=max_pages)
  # init machine
  cpu = cpu_cfg.get_cpu_type()
  num_pages = mem_cfg.get_num_pages()
  mach.init(cpu, num_pages)
  # realize mem config
  _setup_mem(mem_cfg)

def _setup_mem(mem_cfg):
  """internal helper to realize the memory configuration"""
  mem_ranges = mem_cfg.get_range_list()
  for mr in mem_ranges:
    mt = mr.mem_type
    start = mr.start_page
    size = mr.num_pages
    if mt == MEM_RAM:
      mach.add_memory(start, size, MEM_FLAGS_RW)
    elif mt == MEM_ROM:
      mach.add_memory(start, size, MEM_FLAGS_READ)
    elif mt == MEM_SPECIAL:
      r_func, w_func = mr.opts
      mach.add_special(start, size, r_func, w_func)

def shutdown():
  """shutdown runtime

  after using the runtime you have to shut it down. this frees the allocated
  resources. After that you can init() again for a new run
  """
  global _cpu_cfg, _mem_cfg
  _cpu_cfg = None
  _mem_cfg = None
  mach.shutdown()

def run(init_pc, init_sp=0x400, cycles_per_run=0):
  """run the CPU until emulation ends

  this is the main loop of your emulation. it starts by setting up initial
  PC and stack pointer at addresses 4 and 0 and pulses a CPU reset to fetch
  these values. Then the CPU runs code from the virtual system's memory
  until an event happens. The event is processed and code execution is
  coninued until a termination condition is reached.
  """
  # place SP and PC in memory
  mem.w32(0, init_sp)
  mem.w32(4, init_pc)
  # now pulse reset
  mach.pulse_reset()
  # main loop
  while True:
    num_events = mach.execute_to_event_checked(cycles_per_run)
    print(num_events)
