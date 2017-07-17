
from __future__ import print_function

from bare68k.debug.cpusnapshot import *

def test_css_empty(rt):
  c = CPUSnapshotCreator()
  f = CPUSnapshotFormatter()
  snap = c.create()
  f.print(snap)

def run_prog(rt):
  PROG_BASE = rt.get_reset_pc()
  addr = PROG_BASE
  for i in range(16):
    mem.w16(addr, 0x4ef8)
    mem.w16(addr+2, addr+6)
    addr += 6
  mem.w16(addr, 0x4e70) # reset
  rt.run()

def test_css_real(rt):
  run_prog(rt)
  c = CPUSnapshotCreator()
  f = CPUSnapshotFormatter()
  snap = c.create()
  f.print(snap)

def test_css_simple(rt):
  run_prog(rt)
  print_cpu_snapshot()
