from __future__ import print_function

import pytest
import traceback

from bare68k.consts import *
from bare68k.machine import *

use_labels = True

def test_label_init_exit(mach):
  pass

def test_label_add_remove(mach):
  print("all:",get_all_labels())
  l = add_label(0,100,"huhu")
  print("label:",l)
  print("all:",get_all_labels())
  remove_label(l)
  print("all:",get_all_labels())

