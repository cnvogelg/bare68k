
from bare68k.debug.regdump import *

def test_rd_str_lines(rt):
  r = RegisterDump()
  l = r.get_str_lines()
  assert len(l) == 6
  assert l[0] == ' PC=00001000  SR=--S--210--------'
  assert l[1] == ' D0=00000000  D1=00000000  D2=00000000  D3=00000000'
  assert l[2] == ' D4=00000000  D5=00000000  D6=00000000  D7=00000000'
  assert l[3] == ' A0=00000000  A1=00000000  A2=00000000  A3=00000000'
  assert l[4] == ' A4=00000000  A5=00000000  A6=00000000  A7=00000800'
  assert l[5] == 'USP=00000000 ISP=00000800 MSP=00000000 VBR=00000000'
