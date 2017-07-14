from future.utils import raise_
import logging

from bare68k.consts import *
import bare68k.api.mem as mem


class RunConfig(object):
  """define the runtime configuration"""

  def __init__(self, catch_kb_intr=True, cycles_per_run=0,
               with_labels=True, pc_trace_size=8,
               log_channel=None):
    self._catch_kb_intr = catch_kb_intr
    self._cycles_per_run = cycles_per_run
    self._with_labels = with_labels
    self._pc_trace_size = pc_trace_size

  def __repr__(self):
    return "RunConfg(catch_kb_intr={}, cycles_per_run={}, " \
      "with_labels={}, pc_trace_size={})".format(
          self._catch_kb_intr, self._cycles_per_run,
          self._with_labels, self._pc_trace_size
        )

  def get_catch_kb_intr(self):
    return self._catch_kb_intr

  def get_cycles_per_run(self):
    return self._cycles_per_run

  def get_with_labels(self):
    return self._with_labels

  def get_pc_trace_size(self):
    return self._pc_trace_size
