import logging

from bare68k.consts import *
import bare68k.api.mem as mem


class RunConfig(object):
  """define the runtime configuration"""

  def __init__(self, catch_kb_intr=True, cycles_per_run=0, log_channel=None):
    self._catch_kb_intr = catch_kb_intr
    self._cycles_per_run = cycles_per_run
    if log_channel is None:
      self._log = logging.getLogger(__name__)
    else:
      self._log = log_channel
    # the runtime backref will be set when attached to runtime
    self._runtime = None

  def handler_cb_error(self, event):
    """a callback running your code raised an exception"""
    # get exception info
    exc_info = event.data
    # keyboard interrupt
    if exc_info[0] is KeyboardInterrupt:
      if self._catch_kb_intr:
        self._log.debug("keyboard interrupt (in callback)")
        return CPU_EVENT_USER_ABORT
    # re-raise other error
    self._log.error("handle CALLBACK raised: %s", exc_info[0])
    raise exc_info[0], exc_info[1], exc_info[2]

  def handler_reset(self, event):
    """default handler for reset opcode"""
    global _reset_end_pc
    pc = event.addr
    self._log.info("handle RESET @%08x", pc)
    # check if final PC reached to end run loop
    top_pc = self._runtime.get_top_end_pc()
    if top_pc is None or top_pc == pc:
      # quit run loop:
      return CPU_EVENT_DONE
    else:
      return CPU_EVENT_RESET

  def handler_aline_trap(self, event):
    """an unbound aline trap was encountered"""
    # bound handler?
    bound_handler = event.data
    pc = event.addr
    op = event.value
    if bound_handler is not None:
      self._log.debug("bound ALINE handler: @%08x: %04x -> %r", pc, op, bound_handler)
      bound_handler(event)
    else:
      self._log.warn("unbound ALINE encountered: @%08x: %04x", pc, op)
      return CPU_EVENT_ALINE_TRAP

  def handler_mem_access(self, event):
    """default handler for invalid memory accesses"""
    mem_str = mem.get_cpu_mem_str(event.flags, event.addr, event.value)
    self._log.error("MEM ACCESS: %s", mem_str)
    # abort run loop if access was by caused by code
    if event.flags & MEM_FC_PROG_MASK == MEM_FC_PROG_MASK:
      return CPU_EVENT_MEM_ACCESS

  def handler_mem_bounds(self, event):
    """default handler for invalid memory accesses beyond max pages"""
    mem_str = mem.get_cpu_mem_str(event.flags, event.addr, event.value)
    self._log.error("MEM BOUNDS: %s", mem_str)
    # abort run loop if access was by caused by code
    if event.flags & MEM_FC_PROG_MASK == MEM_FC_PROG_MASK:
      return CPU_EVENT_MEM_ACCESS

  def handler_mem_trace(self, event):
    pass

  def handler_mem_special(self, event):
    pass

  def handler_instr_hook(self, event):
    pass

  def handler_int_ack(self, event):
    pass

  def handler_breakpoint(self, event):
    addr = event.addr
    bp_id = event.value
    mem_flags = event.flags
    mf_str = mem.get_cpu_fc_str(mem_flags)
    user_data = event.data
    self._log.info("BREAKPOINT: @%08x #%d flags=%s data=%s",
                   addr, bp_id, mf_str, user_data)
    return CPU_EVENT_BREAKPOINT

  def handler_watchpoint(self, event):
    addr = event.addr
    bp_id = event.value
    mem_flags = event.flags
    mf_str = mem.get_cpu_access_str(mem_flags)
    user_data = event.data
    self._log.info("WATCHPOINT: @%08x #%d flags=%s data=%s",
                   addr, bp_id, mf_str, user_data)
    return CPU_EVENT_WATCHPOINT

  def handler_timer(self, event):
    self._log.info("TIMER")
