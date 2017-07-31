"""the runtime module drives the m68k processor emulation of bare68k.
"""

import time
import logging

import bare68k.api.machine as mach
import bare68k.api.cpu as cpu
import bare68k.api.mem as mem
import bare68k.api.tools as tools

from bare68k.consts import *
from bare68k.errors import *
from bare68k.cpucfg import *
from bare68k.memcfg import *
from bare68k.runcfg import RunConfig
from bare68k.label import *
from bare68k.handler import EventHandler


class EventStats(object):
    """Store statistics on called events"""

    def __init__(self):
        self.total_events = 0
        self.event_counts = [0] * CPU_NUM_EVENTS

    def count(self, ev_num):
        if ev_num >= 0 and ev_num < CPU_NUM_EVENTS:
            self.event_counts[ev_num] += 1
            self.total_events += 1
        else:
            raise ValueError("invalid event number")

    def get_total_events(self):
        return self.total_events

    def get_event_count(self, ev_num):
        if ev_num >= 0 and ev_num < CPU_NUM_EVENTS:
            return self.event_counts[ev_num]
        else:
            raise ValueError("invalid event number")

    def __repr__(self):
        vals = map(str, self.event_counts)
        return "EventStats(#%d:%s)" % (self.total_events, ",".join(vals))


class RunInfo(object):
    """RunInfo returns information about the CPU run last performed"""

    def __init__(self, total_time, cpu_time, total_cycles, results, stats):
        self.total_time = total_time
        self.cpu_time = cpu_time
        self.total_cycles = total_cycles
        self.results = results
        self.stats = stats
        self.py_time = total_time - cpu_time

    def __repr__(self):
        return "RunInfo({},{},{},{},{})".format(
            self.total_time, self.cpu_time,
            self.total_cycles, repr(self.results),
            repr(self.stats))

    def is_done(self):
        return self.get_last_result() == CPU_EVENT_DONE

    def get_results(self):
        return self.results

    def get_event(self, pos):
        return self.results[pos][1]

    def get_result(self, pos):
        return self.results[pos][0]

    def get_last_result(self):
        if len(self.results) > 0:
            return self.results[-1][0]
        else:
            return None

    def get_last_event(self):
        if len(self.results) > 0:
            return self.results[-1][1]
        else:
            return None

    def get_stats(self):
        return self.stats

    def calc_cpu_mhz(self):
        """from cpu time and cycle count calc cpu clock speed of musashi"""
        if self.cpu_time > 0:
            return self.total_cycles / (self.cpu_time * 1000000)
        else:
            return 0


def log_setup(level=logging.DEBUG):
    """setup logging of the runtime"""
    FORMAT = '%(asctime)-15s %(name)24s:%(levelname)7s:  %(message)s'
    logging.basicConfig(format=FORMAT, level=level)


def init_quick(cpu_type=M68K_CPU_TYPE_68000, ram_pages=1):
    """a simplified init.

    Create a Runtime() instance which is simplified and uses a basic memory
    setup with only a RAM region starting at 0 with given number of pages.
    """
    cpu_cfg = CPUConfig(cpu_type)
    mem_cfg = MemoryConfig()
    mem_cfg.add_ram_range(0, ram_pages)
    run_cfg = RunConfig()
    return Runtime(cpu_cfg, mem_cfg, run_cfg)


class Runtime(object):
    """The runtime controls the CPU emulation run and dispatches events.

    The central entry point for every system emulation done with bare68k is
    the Runtime. First you configure it by passing in a CPU, memory layout and
    runtime configuration.

    Add an optional event handler to control the processing of incoming
    events. Configure an optional Logger to receive all incoming traces.

    Args:
         cpu_cfg (:obj:`bare68k.CPUConfig`): the CPU configuration
         mem_cfg (:obj:`bare68k.MemoryConfig`): the memory layout for the emulation
         run_cfg (:obj:`bare68k.RunConfig`): runtime options
         event_handler (:obj:`bare68k.EventHandler`, optional): event handler that
             receives all returned events from the CPU emulation. By
             default the :class:`bare68k.EventHandler` is used.
         log_channel (:obj:`logging.Logger`, optional): a logger that
             logs all runtime events. By default a logger with ``__name__``
             of the module is created.
    """

    def __init__(self, cpu_cfg, mem_cfg, run_cfg,
                 event_handler=None, log_channel=None):
        # setup logging
        if log_channel is None:
            self._log = logging.getLogger(__name__)
        else:
            self._log = log_channel

        # remember configs
        self._cpu_cfg = cpu_cfg
        self._mem_cfg = mem_cfg
        self._run_cfg = run_cfg

        # setup event handler backref to runtime
        if event_handler is None:
            self._event_handler = EventHandler()
        else:
            self._event_handler = event_handler

        # check mem config
        max_pages = cpu_cfg.get_max_pages()
        mem_cfg.check(max_pages=max_pages)

        # init machine
        with_labels = run_cfg._with_labels
        cpu = cpu_cfg.get_cpu_type()
        num_pages = mem_cfg.get_num_pages()
        mach.init(cpu, num_pages, with_labels)

        # realize mem config
        self._setup_mem(mem_cfg)
        # setup cpu event handlers
        self._setup_handlers()

        # clear state
        self._reset_pc = None
        self._reset_sp = None
        self._end_pcs = []
        self._cpu_states = []

        # setup label mgr
        if with_labels:
            self._label_mgr = LabelMgr()
        else:
            self._label_mgr = DummyLabelMgr()

        # finally attach runtime to handler
        self._event_handler.attach_runtime(self)

    def get_with_labels(self):
        """Check is memory labels are enabled for the runtime.

        The runtime can be either configured to enable or disable memory
        labels via the :class:`RunConfig`. This function returns True if
        labels are enabled otherwise False.

        Returns:
            bool: True if labels are enabled, otherwise False
        """
        return self._run_cfg._with_labels

    def get_label_mgr(self):
        """Get the label manager associated with the runtime.

        If labels are enabled a real :class:`LabelMgr` is returned. If
        labels are disabled then a fake :class:`DummyLabelMgr` is available.
        It provides the same interface but does nothing.

        Returns:
            :obj:`LabelMgr` or :obj:`DummyLabelMgr`: active label manager
        """
        return self._label_mgr

    def get_cpu_cfg(self):
        """access the current CPU configuration"""
        return self._cpu_cfg

    def get_mem_cfg(self):
        """access the current memory configuration"""
        return self._mem_cfg

    def get_run_cfg(self):
        """access the current run configuration"""
        return self._run_cfg

    def get_cpu(self):
        """return cpu API 'object'"""
        return cpu

    def get_mem(self):
        """return mem API 'object'"""
        return mem

    def get_event_handler(self):
        return self._event_handler

    def _setup_mem(self, mem_cfg):
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
                mem.add_memory(start, size, flags)
                self._log.info(
                    "memory: RAM @%04x +%04x flags=%x", start, size, flags)
            elif mt == MEM_ROM:
                flags = MEM_FLAGS_READ
                if mr.traps:
                    flags |= MEM_FLAGS_TRAPS
                mem.add_memory(start, size, flags)
                data = mr.opts
                if data is not None:
                    mem.w_block(mr.start_addr, data)
                self._log.info(
                    "memory: ROM @%04x +%04x flags=%x", start, size, flags)
            elif mt == MEM_SPECIAL:
                r_func, w_func = mr.opts
                mem.add_special(start, size, r_func, w_func)
                self._log.info("memory: spc @%04x +%04x", start, size)
            elif mt == MEM_EMPTY:
                value = mr.opts
                mem.add_empty(start, size, MEM_FLAGS_RW, value)
                self._log.info("memory: --- @%04x +%04x: %08x",
                               start, size, value)
            elif mt == MEM_MIRROR:
                base_page = mr.opts
                mem.add_mirror(start, size, MEM_FLAGS_RW, base_page)
                self._log.info("memory: mir @%04x +%04x: <- %04x",
                               start, size, base_page)
            elif mt == MEM_NOALLOC:
                self._log.info("memory: ??? @%04x +%04x", start, size)
            elif mt == MEM_RESERVE:
                self._log.info("memory: XXX @%04x +%04x", start, size)
            else:
                raise ValueError("Invalid memory type: %d" % mt)
        self._log.info("memory: done. max_pages=%04x", mem_cfg.get_num_pages())

    def shutdown(self):
        """shutdown runtime

        after using the runtime you have to shut it down. this frees the allocated
        resources. After that you can init() again for a new run
        """
        self._cpu_cfg = None
        self._mem_cfg = None
        self._run_cfg = None
        mach.shutdown()
        self._log.info("shutdown")

    def reset(self, init_pc, init_sp=0x800):
        """reset the CPU

        before you can run the CPU you have to reset it. This will write the initial
        SP and the initial PC to locations 0 and 4 in RAM and pulse a reset in the
        CPU emulation. After this operation you are free to overwrite these values
        again. Now proceed to call run().
        """
        self._reset_pc = init_pc
        self._reset_sp = init_sp
        # place SP and PC in memory
        mem.w32(0, init_sp)
        mem.w32(4, init_pc)
        # now pulse reset
        cpu.pulse_reset()
        # clear info to reset cycle counts
        cpu.clear_info()
        self._log.info("reset: pc=%08x, sp=%08x", init_pc, init_sp)

    def get_reset_pc(self):
        return self._reset_pc

    def get_reset_sp(self):
        return self._reset_sp

    def get_top_end_pc(self):
        if len(self._end_pcs) == 0:
            return None
        else:
            return self._end_pcs[-1]

    def run(self, reset_end_pc=None, start_pc=None, start_sp=None):
        """run the CPU until emulation ends

        This is the main loop of your emulation. The CPU emulation is run and
        events are processed. The events are dispatched and the associated handlers
        are called. If a reset opcode is encountered then the execution is terminated.

        Returns a RunInfo instance giving you timing information.
        """
        # get some config values
        catch_kb_intr = self._run_cfg._catch_kb_intr
        cycles_per_run = self._run_cfg._cycles_per_run
        pc_trace_size = self._run_cfg._pc_trace_size
        instr_trace = self._run_cfg._instr_trace
        cpu_mem_trace = self._run_cfg._cpu_mem_trace
        api_mem_trace = self._run_cfg._api_mem_trace

        # recursive run() call? if yes then store cpu state
        rec_depth = len(self._end_pcs)
        if rec_depth > 0:
            cpu_state = cpu.get_cpu_context()
        else:
            cpu_state = None

        # set start pc/sp if requested
        if start_pc is not None:
            cpu.w_pc(start_pc)
        if start_sp is not None:
            cpu.w_sp(start_sp)

        # keep end pc
        self._end_pcs.append(reset_end_pc)

        # timer function
        timer = time.time

        # stats
        stats = EventStats()
        start_cycles = cpu.get_total_cycles()

        # pc trace?
        tools.setup_pc_trace(pc_trace_size)

        # instr trace?
        evh = self._event_handler
        if instr_trace:
            cpu.set_instr_hook_func(evh.handle_instr_trace)
        if cpu_mem_trace:
            mem.mach.set_mem_cpu_trace_func(
                evh.handle_cpu_mem_trace, as_str=True)
        if api_mem_trace:
            mem.mach.set_mem_api_trace_func(
                evh.handle_api_mem_trace, as_str=True)

        cpu_time = 0

        # main loop
        self._log.debug("enter run loop #%d", rec_depth)
        total_start = timer()

        results = []
        stay = True
        while stay:
            try:
                start = timer()
                # execute CPU code until event occurs
                num_events = cpu.execute_to_event_checked(cycles_per_run)
            except KeyboardInterrupt as e:
                # either abort execution (default) or re-raise exception
                self._log.debug("keyboard interrupt")
                if not catch_kb_intr:
                    raise e
                results.append((CPU_EVENT_USER_ABORT, None))
                break
            finally:
                end = timer()
                cpu_time += end - start

            # dispatch events
            run_info = cpu.get_info()
            results = []
            for event in run_info.events:
                handler = event.handler
                stats.count(event.ev_type)
                if handler is not None:
                    self._log.debug("trigger handler: %s",
                                    CPU_EVENT_NAMES[event.ev_type])
                    result = handler(event)
                    # handler wants to exit run loop
                    if result is not None:
                        results.append((result, event))
                        stay = False
                        self._log.debug("run loop exit #%d: result=%s"
                                        " (event=%r)",
                                        rec_depth, CPU_EVENT_NAMES[result],
                                        event)
                        # user abort terminates event loop
                        if result == CPU_EVENT_USER_ABORT:
                            break
                else:
                    self._log.warning("no handler: result=%s (event=%r)",
                                      CPU_EVENT_NAMES[event.ev_type], event)

        total_end = timer()
        self._log.debug("leave run loop #%d", rec_depth)

        # pop end pc
        self._end_pcs.pop()

        # restore cpu
        if cpu_state is not None:
            cpu.set_cpu_context(cpu_state)

        # instr trace
        if instr_trace:
            cpu.set_instr_hook_func(None)
        if cpu_mem_trace:
            mem.set_mem_cpu_trace_func(None)
        if api_mem_trace:
            mem.set_mem_api_trace_func(None)

        # final timing
        total_time = total_end - total_start
        end_cycles = cpu.get_total_cycles()
        total_cycles = end_cycles - start_cycles

        # create run info result
        ri = RunInfo(total_time, cpu_time, total_cycles, results, stats)
        self._log.debug("run info: %s", ri)
        return ri

    def _setup_handlers(self):
        """internal setter for all machine event handlers"""
        cfg = self._event_handler
        eh = {
            CPU_EVENT_CALLBACK_ERROR: cfg.handle_cb_error,
            CPU_EVENT_RESET: cfg.handle_reset,
            CPU_EVENT_ALINE_TRAP: cfg.handle_aline_trap,
            CPU_EVENT_MEM_ACCESS: cfg.handle_mem_access,
            CPU_EVENT_MEM_BOUNDS: cfg.handle_mem_bounds,
            CPU_EVENT_MEM_TRACE: cfg.handle_mem_trace,
            CPU_EVENT_MEM_SPECIAL: cfg.handle_mem_special,
            CPU_EVENT_INSTR_HOOK: cfg.handle_instr_hook,
            CPU_EVENT_INT_ACK: cfg.handle_int_ack,
            CPU_EVENT_BREAKPOINT: cfg.handle_breakpoint,
            CPU_EVENT_WATCHPOINT: cfg.handle_watchpoint,
            CPU_EVENT_TIMER: cfg.handle_timer
        }
        for e in eh:
            cpu.set_event_handler(e, eh[e])

    def set_handler(self, event_type, handler):
        """set a custom handler for an event type
           and overwrite default handler"""
        cpu.set_event_handler(event_type, handler)
