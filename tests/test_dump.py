from __future__ import print_function

import pytest

from bare68k import *
from bare68k.consts import *

def test_get_current_pc_line(mach):
    line = dump.get_current_pc_line()
    print(line)

def test_get_reg_dump(mach):
    lines = dump.get_reg_dump()
    print("\n".join(lines))

def test_get_cpu_state(mach):
    lines = dump.get_cpu_state()
    print("\n".join(lines))
