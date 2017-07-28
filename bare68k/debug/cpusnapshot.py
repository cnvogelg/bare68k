from __future__ import print_function

import bare68k.api.cpu as cpu
import bare68k.api.mem as mem
import bare68k.api.tools as tools
from bare68k.debug.disassemble import *
from bare68k.debug.regdump import *


class CPUSnapshot(object):
    """save the current CPU state for debugging purposes"""

    def __init__(self, regs, pc_trace, reason, total_cycles, done_cycles):
        self.regs = regs
        self.pc_trace = pc_trace
        self.reason = reason
        self.total_cycles = total_cycles
        self.done_cycles = done_cycles


class CPUSnapshotCreator(object):
    """take snapshots if desired"""

    def __init__(self, disassembler=None, pc_trace_size=0):
        if disassembler is None:
            self._disasm = Disassembler()
        else:
            self._disasm = disassembler
        if pc_trace_size < 1:
            self._pc_trace_size = tools.get_pc_trace_size()
        else:
            self._pc_trace_size = pc_trace_size

    def get_disassembler(self):
        return self._disasm

    def create(self, reason=None):
        """create a snapshot of the current CPU state"""
        regs = cpu.get_regs()
        pc_trace = self._get_pc_trace(regs, self._pc_trace_size)
        # disassemble pc trace:
        pc_il = []
        for pc in pc_trace:
            il, _ = self._disasm.disassemble(pc)
            pc_il.append(il)
        # register dump
        rd = RegisterDump(regs)
        # cycles
        total_cycles = cpu.get_total_cycles()
        done_cycles = cpu.get_done_cycles()
        # create snapshot
        return CPUSnapshot(rd, pc_il, reason, total_cycles, done_cycles)

    def _get_pc_trace(self, regs, size=1):
        pc_trace = tools.get_pc_trace()
        if pc_trace is None:
            return [regs.r_pc()]
        n = len(pc_trace)
        if n == 0:
            return [regs.r_pc()]
        elif n <= size:
            return pc_trace
        else:
            off = size - n
            return pc_trace[off:]


class CPUSnapshotFormatter(object):

    def __init__(self, with_pc_trace=True, with_regs=True, with_cycles=True,
                 instr_line_formatter=None):
        self.with_pc_trace = with_pc_trace
        self.with_regs = with_regs
        self.with_cycles = with_cycles
        if instr_line_formatter is None:
            self.il_formatter = InstrLineFormatter()
        else:
            self.il_formatter = instr_line_formatter

    def get_instr_line_formatter(self):
        return self.il_formatter

    def format(self, cpu_snap):
        """convert the snapshot to an array of string lines and return it"""
        res = []
        # reason
        if cpu_snap.reason is None:
            res.append("CPUSnapshot")
        else:
            res.append(cpu_snap.reason)
        # pc trace
        if self.with_pc_trace:
            for il in cpu_snap.pc_trace:
                line = self.il_formatter.format(il)
                res.append(line)
        # reg dump
        if self.with_regs:
            lines = cpu_snap.regs.get_str_lines()
            for l in lines:
                res.append(l)
        # cycles
        if self.with_cycles:
            done_str = self.il_formatter.get_cycles_str(cpu_snap.done_cycles)
            total_str = self.il_formatter.get_cycles_str(cpu_snap.total_cycles)
            line = "cycles: done={}, total={}".format(done_str, total_str)
            res.append(line)
        # result
        return res

    def print(self, cpu_snap, func=print):
        """convenience function to print formatted snapshot"""
        lines = self.format(cpu_snap)
        for l in lines:
            func(l)

    def log(self, cpu_snap, log, level):
        """convenience function to log formatted snapshot"""
        lines = self.format(cpu_snap)
        for l in lines:
            log.log(level, l)


def print_cpu_snapshot(reason=None):
    """helper that creates a cpu state and prints it with a formatter"""
    c = CPUSnapshotCreator()
    f = CPUSnapshotFormatter()
    s = c.create(reason)
    f.print(s)


def log_cpu_snapshot(log, level, reason=None):
    """helper that creates a cpu state and prints it with a formatter"""
    c = CPUSnapshotCreator()
    f = CPUSnapshotFormatter()
    s = c.create(reason)
    f.log(s, log, level)
