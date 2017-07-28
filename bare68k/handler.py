from future.utils import raise_
import logging

from bare68k.consts import *
import bare68k.api.mem as mem
from bare68k.debug.cpusnapshot import *


class EventHandler(object):
    """define the event handling of the runtime"""

    def __init__(self, logger=None, snap_create=None, snap_formatter=None,
                 instr_logger=None, mem_logger=None):
        # setup log channel
        if logger is None:
            self._log = logging.getLogger(__name__)
        else:
            self._log = logger
        # setup snapshot creator
        if snap_create is None:
            self._snap_create = CPUSnapshotCreator()
        else:
            self._snap_create = snap_create
        # setup snapshot formatter
        if snap_formatter is None:
            self._snap_formatter = CPUSnapshotFormatter()
        else:
            self._snap_formatter = snap_formatter
        # setup instr log channel
        if instr_logger is None:
            self._instr_log = logging.getLogger("bare68k.instr")
        else:
            self._instr_log = instr_logger
        # setup mem log channel
        if mem_logger is None:
            self._mem_log = logging.getLogger("bare68k.mem")
        else:
            self._mem_log = mem_logger
        # derive disassembler and formatter
        self._disasm = self._snap_create.get_disassembler()
        self._il_formatter = self._snap_formatter.get_instr_line_formatter()
        # the runtime backref will be set when attached to runtime
        self._runtime = None

    def attach_runtime(self, runtime):
        self._runtime = runtime
        # if label manager is used attach it to disassembler, too
        if runtime.get_with_labels():
            label_mgr = runtime.get_label_mgr()
            self._disasm.set_label_mgr(label_mgr)

    def set_instr_logger(self, logger):
        self._instr_log = logger

    def set_mem_logger(self, logger):
        self._mem_log = logger

    def set_logger(self, logger):
        self._log = logger

    def handle_cb_error(self, event):
        """a callback running your code raised an exception"""
        # get exception info
        exc_info = event.data
        # keyboard interrupt
        if exc_info[0] is KeyboardInterrupt:
            if self._runtime._run_cfg._catch_kb_intr:
                self._log.debug("keyboard interrupt (in callback)")
                return CPU_EVENT_USER_ABORT
        # re-raise other error
        self._log.error("handle CALLBACK raised: %s", exc_info[0].__name__)
        raise_(*exc_info)

    def handle_reset(self, event):
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

    def handle_aline_trap(self, event):
        """an unbound aline trap was encountered"""
        # bound handler?
        bound_handler = event.data
        pc = event.addr
        op = event.value
        if bound_handler is not None:
            self._log.debug(
                "bound ALINE handler: @%08x: %04x -> %r",
                pc, op, bound_handler)
            bound_handler(event)
        else:
            self._log.warn("unbound ALINE encountered: @%08x: %04x", pc, op)
            return CPU_EVENT_ALINE_TRAP

    def handle_mem_access(self, event):
        """default handler for invalid memory accesses"""
        mem_str = mem.get_cpu_mem_str(event.flags, event.addr, event.value)
        self._log.error("MEM ACCESS: %s", mem_str)
        # abort run loop if access was by caused by code
        if event.flags & MEM_FC_PROG_MASK == MEM_FC_PROG_MASK:
            return CPU_EVENT_MEM_ACCESS

    def handle_mem_bounds(self, event):
        """default handler for invalid memory accesses beyond max pages"""
        mem_str = mem.get_cpu_mem_str(event.flags, event.addr, event.value)
        self._log.error("MEM BOUNDS: %s", mem_str)
        # abort run loop if access was by caused by code
        if event.flags & MEM_FC_PROG_MASK == MEM_FC_PROG_MASK:
            return CPU_EVENT_MEM_ACCESS

    def handle_mem_trace(self, event):
        """a cpu mem trace handler returned a value != None"""
        mem_str = mem.get_cpu_mem_str(event.flags, event.addr, event.value)
        self._log.info("MEM_TRACE: %s -> %s", mem_str, event.data)
        return CPU_EVENT_MEM_TRACE

    def handle_mem_special(self, event):
        """a memory special handler returned a value != None"""
        mem_str = mem.get_cpu_mem_str(event.flags, event.addr, event.value)
        self._log.info("MEM_SPECIAL: %s -> %s", mem_str, event.data)
        return CPU_EVENT_MEM_SPECIAL

    def handle_instr_hook(self, event):
        """an instruction hook handler returned a value != None"""
        self._log.info("INSTR_HOOK: pc=@%08x -> %s", event.addr, event.data)
        return CPU_EVENT_INSTR_HOOK

    def handle_int_ack(self, event):
        """int ack handler did return a value != None"""
        self._log.info("INT_ACK: pc=@%08x int=%d -> %s",
                       event.addr, event.flags, event.data)
        return CPU_EVENT_INT_ACK

    def handle_breakpoint(self, event):
        addr = event.addr
        bp_id = event.value
        mem_flags = event.flags
        mf_str = mem.get_cpu_fc_str(mem_flags)
        user_data = event.data
        self._log.info("BREAKPOINT: @%08x #%d flags=%s data=%s",
                       addr, bp_id, mf_str, user_data)
        return CPU_EVENT_BREAKPOINT

    def handle_watchpoint(self, event):
        addr = event.addr
        bp_id = event.value
        mem_flags = event.flags
        mf_str = mem.get_cpu_access_str(mem_flags)
        user_data = event.data
        self._log.info("WATCHPOINT: @%08x #%d flags=%s data=%s",
                       addr, bp_id, mf_str, user_data)
        return CPU_EVENT_WATCHPOINT

    def handle_timer(self, event):
        self._log.info("TIMER")

    # debug handler

    def handle_instr_trace(self, pc):
        # disassemble pc
        il, _ = self._disasm.disassemble(pc)
        # format
        line = self._il_formatter.format(il)
        # and log
        self._instr_log.info(line)

    def handle_cpu_mem_trace(self, msg, flag_addr_val):
        flags = flag_addr_val[0]
        # log only data access (not program)
        if flags & MEM_FC_DATA_MASK == MEM_FC_DATA_MASK:
            self._mem_log.info(msg)

    def handle_api_mem_trace(self, msg, flag_addr_val):
        self._mem_log.info(msg)
