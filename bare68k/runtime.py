"""the runtime module drives the m68k processor emulation of bare68k.
"""

import time
import logging

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
_reset_pc = None
_reset_sp = None

# logging setup
_log = logging.getLogger(__name__)

# return reasons
RETURN_OK = 0
RETURN_USER_ABORT = 1
RETURN_MEM_ACCESS = 2
RETURN_MEM_BOUNDS = 3
RETURN_ALINE_TRAP = 4

# global vars to modify run() loop
_reset_end_pc = None


class RunInfo:
  """RunInfo returns information about the CPU run last performed"""
  def __init__(self, total_time, cpu_time, total_cycles, results):
    self.total_time = total_time
    self.cpu_time = cpu_time
    self.total_cycles = total_cycles
    self.results = results
    self.py_time = total_time - cpu_time

  def __repr__(self):
    return "RunInfo({},{},{},{})".format(
      self.total_time, self.cpu_time,
      self.total_cycles, repr(self.results))

  def is_ok(self):
    return len(self.results) == 1 and self.results[0] == RETURN_OK

  def calc_cpu_mhz(self):
    """from cpu time and cycle count calc cpu clock speed of musashi"""
    return self.total_cycles / (self.cpu_time * 1000000)


def log_setup(level=logging.DEBUG):
  """setup logging of the runtime"""
  FORMAT = '%(asctime)-15s %(name)24s:%(levelname)7s:  %(message)s'
  logging.basicConfig(format=FORMAT, level=level)

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

def get_cpu_cfg():
  """access the current CPU configuration"""
  return _cpu_cfg

def get_mem_cfg():
  """access the current memory configuration"""
  return _mem_cfg

def init_quick(cpu_type=M68K_CPU_TYPE_68000, ram_pages=1):
  """a simplified init.

  In contrast to init() this call is simplified and uses a basic memory
  setup with only a RAM region starting at 0 with given number of pages.
  """
  cpu_cfg = CPUConfig(cpu_type)
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
      flags = MEM_FLAGS_RW
      if mr.traps:
        flags |= MEM_FLAGS_TRAPS
      mach.add_memory(start, size, flags)
      _log.info("memory: RAM @%04x +%04x flags=%x", start, size, flags)
    elif mt == MEM_ROM:
      flags = MEM_FLAGS_READ
      if mr.traps:
        flags |= MEM_FLAGS_TRAPS
      mach.add_memory(start, size, flags)
      data = mr.opts
      if data is not None:
        mem.w_block(mr.start_addr, mr.opts)
      _log.info("memory: ROM @%04x +%04x flags=%x", start, size, flags)
    elif mt == MEM_SPECIAL:
      r_func, w_func = mr.opts
      mach.add_special(start, size, r_func, w_func)
      _log.info("memory: spc @%04x +%04x", start, size)
  _log.info("memory: done. max_pages=%04x", mem_cfg.get_num_pages())

def shutdown():
  """shutdown runtime

  after using the runtime you have to shut it down. this frees the allocated
  resources. After that you can init() again for a new run
  """
  global _cpu_cfg, _mem_cfg
  _cpu_cfg = None
  _mem_cfg = None
  mach.shutdown()
  _log.info("shutdown")

def reset(init_pc, init_sp=0x400):
  """reset the CPU

  before you can run the CPU you have to reset it. This will write the initial
  SP and the initial PC to locations 0 and 4 in RAM and pulse a reset in the
  CPU emulation. After this operation you are free to overwrite these values
  again. Now proceed to call run().
  """
  global _reset_pc, _reset_sp
  _reset_pc = init_pc
  _reset_sp = init_sp
  # place SP and PC in memory
  mem.w32(0, init_sp)
  mem.w32(4, init_pc)
  # now pulse reset
  mach.pulse_reset()
  # clear info to reset cycle counts
  mach.clear_info()
  _log.info("reset: pc=%08x, sp=%08x", init_pc, init_sp)

def get_reset_pc():
  return _reset_pc

def get_reset_sp():
  return _reset_sp

def run(cycles_per_run=0, reset_end_pc=None, catch_kb_intr=True, max_cycles=None):
  """run the CPU until emulation ends

  This is the main loop of your emulation. The CPU emulation is run and
  events are processed. The events are dispatched and the associated handlers
  are called. If a reset opcode is encountered then the execution is terminated.

  Returns a RunInfo instance giving you timing information.
  """
  global _reset_end_pc

  # timer function
  timer = time.time

  cpu_time = 0
  _reset_end_pc = reset_end_pc

  # main loop
  _log.debug("enter main loop")
  total_start = timer()

  results = []
  stay = True
  while stay:
    try:
      start = timer()
      if max_cycles is None:
        # execute CPU code until event occurs
        num_events = mach.execute_to_event_checked(cycles_per_run)
      else:
        # run for a given number of cycles
        num_events = mach.execute(max_cycles)
        stay = False
    except KeyboardInterrupt as e:
      # either abort execution (default) or re-raise exception
      results.append(RETURN_USER_ABORT)
      if not catch_kb_intr:
        raise e
      break
    finally:
      end = timer()
      cpu_time += end - start

    # dispatch events
    run_info = mach.get_info()
    results = []
    for event in run_info.events:
      handler = event.handler
      if handler is not None:
        result = handler(event)
        # handler wants to
        if result is not None:
          results.append(result)
          stay = False
          _log.debug("leave run loop: reason=%d", result)
      else:
        _log.warning("no handler for event: %s", event)

  total_end = timer()
  _log.debug("leave main loop")

  # final timing
  total_time = total_end - total_start
  return RunInfo(total_time, cpu_time, mach.get_total_cycles(), results)

def _setup_handlers():
  """internal setter for all machine event handlers"""
  eh = mach.event_handlers
  eh[CPU_EVENT_CALLBACK_ERROR] = handler_cb_error
  eh[CPU_EVENT_RESET] = handler_reset
  eh[CPU_EVENT_ALINE_TRAP] = handler_aline_trap
  eh[CPU_EVENT_MEM_ACCESS] = handler_mem_access
  eh[CPU_EVENT_MEM_BOUNDS] = handler_mem_bounds

def set_handler(event_type, handler):
  """set a custom handler for an event type and overwrite default handler"""
  if event_type < 0 or event_type >= CPU_NUM_EVENTS:
    raise ValueError("Invalid event type")
  mach.event_handlers[event_type] = handler

def handler_cb_error(event):
  """a callback running your code raised an exception"""
  # re-raise
  exc_info = event.data
  _log.error("handle CALLBACK raised: %s", exc_info[1])
  raise exc_info[0], exc_info[1], exc_info[2]

def handler_reset(event):
  """default handler for reset opcode"""
  global _reset_end_pc
  pc = event.addr
  _log.info("handle RESET @%08x", pc)
  # check if final PC reached to end run loop
  if _reset_end_pc is None or _reset_end_pc == pc:
    # quit run loop:
    return RETURN_OK

def handler_aline_trap(event):
  """an unbound aline trap was encountered"""
  # bound handler?
  bound_handler = event.data
  pc = event.addr
  op = event.value
  if bound_handler is not None:
    _log.debug("bound ALINE handler: @%08x: %04x -> %r", pc, op, bound_handler)
    bound_handler(event)
  else:
    _log.warn("unbound ALINE encountered: @%08x: %04x", pc, op)
    return RETURN_ALINE_TRAP

def handler_mem_access(event):
  """default handler for invalid memory accesses"""
  mem_str = mach.get_cpu_mem_str(event.flags, event.addr, event.value)
  _log.error("MEM ACCESS: %s", mem_str)
  # quit run loop:
  return RETURN_MEM_ACCESS

def handler_mem_bounds(event):
  """default handler for invalid memory accesses beyond max pages"""
  mem_str = mach.get_cpu_mem_str(event.flags, event.addr, event.value)
  _log.error("MEM BOUNDS: %s", mem_str)
  # quit run loop:
  return RETURN_MEM_BOUNDS
