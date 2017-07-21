from __future__ import print_function

import pytest

from bare68k.consts import *
from bare68k.machine import *

def test_disassemble(mach):
  w16(0x100, 0x4e75) # rts
  pc, words, line = disassemble(0x100)
  print(words, line)
  w1 = [0x4e75]
  l1 = "rts"
  assert words == w1
  assert line == l1
  assert pc == 0x100

  w16(0x102, 0x4eb9) # jsr
  w32(0x104, 0xdeadbeef)
  pc, words, line = disassemble(0x102)
  print(words, line)
  w2 = [0x4eb9, 0xdead, 0xbeef]
  l2 = "jsr     $deadbeef.l"
  assert words == w2
  assert line == l2
  assert pc == 0x102

  # test range
  res = disassemble_range(0x100, 0x108)
  print("range:", res)
  assert res == [(0x100, w1, l1), (0x102, w2, l2)]


def test_disassemble_api(mach):
  w16(0x100, 0x4e75) # rts
  pc, words, line = disassemble(0x100)
  print(words, line)
  w1 = [0x4e75]
  l1 = "rts"
  assert words == w1
  assert line == l1
  assert pc == 0x100

  w16(0x102, 0x4eb9) # jsr
  w32(0x104, 0xdeadbeef)
  pc, words, line = disassemble(0x102)
  print(words, line)
  w2 = [0x4eb9, 0xdead, 0xbeef]
  l2 = "jsr     $deadbeef.l"
  assert words == w2
  assert line == l2
  assert pc == 0x102

  # test range
  res = disassemble_range(0x100, 0x108)
  print("range:", res)
  assert res == [(0x100, w1, l1), (0x102, w2, l2)]



def test_disassemble_buffer(mach):
  buf1 = b"\x4e\x75"
  disassemble_buffer(buf1)
  pc, words, line = disassemble(0)
  print(words, line)
  w1 = [0x4e75]
  l1 = "rts"
  assert words == w1
  assert line == l1
  assert pc == 0

  buf2 = b"\x4e\xb9\xde\xad\xbe\xef"
  disassemble_buffer(buf2)
  pc, words, line = disassemble(0)
  print(words, line)
  w2 = [0x4eb9, 0xdead, 0xbeef]
  l2 = "jsr     $deadbeef.l"
  assert words == w2
  assert line == l2
  assert pc == 0

  # test range
  buf3 = buf1 + buf2
  disassemble_buffer(buf3)
  res = disassemble_range(0,8)
  assert res == [(0, w1, l1), (2, w2, l2)]

  # back to mem disassembly
  disassemble_memory()
  pc, words, line = disassemble(0)
  print(words, line)
  assert words == [0, 0]
  assert line == "ori.b   #$0, D0"
  assert pc == 0


def test_disassemble_buffer_api(mach):
  buf1 = b"\x4e\x75"
  disassemble_buffer(buf1)
  pc, words, line = disassemble(0)
  print(words, line)
  w1 = [0x4e75]
  l1 = "rts"
  assert words == w1
  assert line == l1
  assert pc == 0

  buf2 = b"\x4e\xb9\xde\xad\xbe\xef"
  disassemble_buffer(buf2)
  pc, words, line = disassemble(0)
  print(words, line)
  w2 = [0x4eb9, 0xdead, 0xbeef]
  l2 = "jsr     $deadbeef.l"
  assert words == w2
  assert line == l2
  assert pc == 0

  # test range
  buf3 = buf1 + buf2
  disassemble_buffer(buf3)
  res = disassemble_range(0,8)
  assert res == [(0, w1, l1), (2, w2, l2)]

  # back to mem disassembly
  disassemble_memory()
  pc, words, line = disassemble(0)
  print(words, line)
  assert words == [0, 0]
  assert line == "ori.b   #$0, D0"
  assert pc == 0

def test_disassemble_is_valid(mach):
  op1 = 0x4e75
  assert disassemble_is_valid(op1) == True
  if get_type() == M68K_CPU_TYPE_68000:
    op2 = 0x8380 # unpk
    assert disassemble_is_valid(op2) == False
