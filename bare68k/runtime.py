"""the runtime module drives the m68k processor emulation of bare68k.
"""

import time

import bare68k.machine as mach
import bare68k.cpu as cpu
import bare68k.mem as mem
from bare68k.memcfg import *
from bare68k.consts import *
from bare68k.errors import *
from bare68k.cpucfg import CPUConfig
from bare68k.memcfg import MemoryConfig

# globals
_cpu_cfg = None
_mem_cfg = None

class RunInfo:
  """RunInfo returns information about the CPU run last performed"""
  def __init__(self, total_time, cpu_time, total_cycles, aborted):
    self.total_time = total_time
    self.cpu_time = cpu_time
    self.total_cycles = total_cycles
    self.aborted = aborted
    self.py_time = total_time - cpu_time

  def __repr__(self):
    return "RunInfo({},{},{},{})".format(
      self.total_time, self.cpu_time,
      self.total_cycles, self.aborted)


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
  # setup machine event handlers
  _setup_handlers()

def init_quick(cpu_type=M68K_CPU_TYPE_68000, ram_pages=1):
  """a simplified init.

  In contrast to init() this call is simplified and uses a basic memory
  setup with only a RAM region starting at 0 with given pages.
  """
  cpu_cfg = CPUConfig()
  mem_cfg = MemoryConfig()
  mem_cfg.add_ram_range(0, ram_pages)
  init(cpu_cfg, mem_cfg)

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

def reset(init_pc, init_sp=0x400):
  """reset the CPU

  before you can run the CPU you have to reset it. This will write the initial
  SP and the initial PC to locations 0 and 4 in RAM and pulse a reset in the
  CPU emulation. After this operation you are free to overwrite these values
  again. Now proceed to call run().
  """
  # place SP and PC in memory
  mem.w32(0, init_sp)
  mem.w32(4, init_pc)
  # now pulse reset
  mach.pulse_reset()
  # clear info to reset cycle counts
  mach.clear_info()

def run(cycles_per_run=0, reset_end_pc=None, catch_kb_intr=True):
  """run the CPU until emulation ends

  This is the main loop of your emulation. The CPU emulation is run and
  events are processed. The events are dispatched and the associated handlers
  are called. If a reset opcode is encountered then the execution is terminated.

  Returns a RunInfo instance giving you timing information.
  """
  # timer function
  timer = time.time

  cpu_time = 0
  aborted = False

  total_start = timer()

  # main loop
  while True:
    try:
      # execute CPU code until event occurs
      start = timer()
      num_events = mach.execute_to_event_checked(cycles_per_run)
    except KeyboardInterrupt as e:
      # either abort execution (default) or re-raise exception
      aborted = True
      if not catch_kb_intr:
        raise e
      break
    finally:
      end = timer()
      cpu_time += end - start

    # dispatch events
    if not _dispatch_events(reset_end_pc):
      break

  # final timing
  total_end = timer()
  total_time = total_end - total_start
  return RunInfo(total_time, cpu_time, mach.get_total_cycles(), aborted)

def _dispatch_events(reset_end_pc):
  """internal event dispatcher"""
  # get run info
  run_info = mach.get_info()
  for event in run_info.events:
    et = event.ev_type

    # check for reset event
    if et == CPU_EVENT_RESET:
      pc = event.addr
      # end condition?
      if reset_end_pc == pc or reset_end_pc is None:
        return False

    # execute a handler?
    handler = event.handler
    if handler is not None:
      handler(event)
    else:
      raise InternalError("Unhandled Event: " + str(event))

  return True

def _setup_handlers():
  """internal setter for all machine event handlers"""
  eh = mach.event_handlers
  eh[CPU_EVENT_RESET] = def_handler_reset

def def_handler_reset(event):
  """default handler for reset opcode"""
  pass
