from future.utils import raise_
import logging

from bare68k.consts import *
import bare68k.api.mem as mem


class RunConfig(object):
    """define the runtime configuration"""

    def __init__(self, catch_kb_intr=True, cycles_per_run=0,
                 with_labels=True, pc_trace_size=8,
                 instr_trace=False, cpu_mem_trace=False, api_mem_trace=False):
        self._catch_kb_intr = catch_kb_intr
        self._cycles_per_run = cycles_per_run
        self._with_labels = with_labels
        self._pc_trace_size = pc_trace_size
        self._instr_trace = instr_trace
        self._cpu_mem_trace = cpu_mem_trace
        self._api_mem_trace = api_mem_trace

    def __repr__(self):
        return "RunConfg(catch_kb_intr={}, cycles_per_run={}, " \
            "with_labels={}, pc_trace_size={}, instr_trace={}, " \
            "cpu_mem_trace={}, api_mem_trace={})".format(
                self._catch_kb_intr, self._cycles_per_run,
                self._with_labels, self._pc_trace_size,
                self._instr_trace, self._cpu_mem_trace, self._api_mem_trace
            )

    def get_catch_kb_intr(self):
        return self._catch_kb_intr

    def get_cycles_per_run(self):
        return self._cycles_per_run

    def get_with_labels(self):
        return self._with_labels

    def get_pc_trace_size(self):
        return self._pc_trace_size

    def get_instr_trace(self):
        return self._instr_trace

    def get_cpu_mem_trace(self):
        return self._cpu_mem_trace

    def get_api_mem_trace(self):
        return self._api_mem_trace

    def set_catch_kb_instr(self, on):
        self._catch_kb_intr = on

    def set_cycles_per_run(self, n):
        self._cycles_per_run = n

    def set_pc_trace_size(self, n):
        self._pc_trace_size = n

    def set_instr_trace(self, on):
        self._instr_trace = on

    def set_cpu_mem_trace(self, on):
        self._cpu_mem_trace = on

    def set_api_mem_trace(self, on):
        self._api_mem_trace = on
