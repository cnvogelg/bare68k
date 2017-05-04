from __future__ import print_function

import struct

import bare68k.machine as mach
import bare68k.cpu as cpu
import bare68k.mem as mem

def default_instr_annotate(pc, words):
  # get raw words
  hw = map(lambda x: "%04x" % x, words)
  return "%-20s" % " ".join(hw)

_instr_annotate = default_instr_annotate

def set_instr_annotate_func(f):
  """set instr annotation function"""
  global _instr_annotate
  _instr_annotate = f

def reset_instr_annotate_func():
  global _instr_annotate
  _instr_annotate = default_instr_annotate

def disassemble_line(pc):
  """callback for instruction trace"""
  pc, words, line = mach.disassemble(pc)
  if _instr_annotate is not None:
    annotation = _instr_annotate(pc, words)
  else:
    annotation = ""
  return "%08x: %s %s" % (pc, annotation, line)

def get_reg_dump():
    regs = mach.get_regs()
    return regs.get_lines()

def get_cycles_str(cycles):
    sub_cycles = cycles % 1000000
    top_cycles = cycles / 1000000
    return "%8d.%08d" % (top_cycles, sub_cycles)

def get_total_cycles_str():
    return get_cycles_str(mach.get_total_cycles())

def get_done_cycles_str():
    return get_cycles_str(mach.get_done_cycles())

def get_current_pc_line():
    pc = cpu.r_pc()
    return disassemble_line(pc)

def get_pc_trace_lines():
    pcs = mach.get_pc_trace()
    lines = []
    if pcs is not None:
        for pc in pcs:
            lines.append(disassemble_line(pc))
    else:
        lines.append(get_current_pc_line())
    return lines

def get_cpu_state(with_pc_trace=True):
    if with_pc_trace:
        lines = get_pc_trace_lines()
    else:
        lines = [get_current_pc_line()]
    lines += get_reg_dump()
    lines.append("done  cycles: " + get_done_cycles_str())
    lines.append("total cycles: " + get_total_cycles_str())
    return lines

def print_cpu_state(out=print, with_pc_trace=True):
    lines = get_cpu_state(with_pc_trace)
    for line in lines:
        out(line)
