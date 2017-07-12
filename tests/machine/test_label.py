from __future__ import print_function

import pytest
import traceback
import random

from bare68k.consts import *
from bare68k.machine import *

use_labels = True

def test_label_init_exit(mach):
  pass

def test_label_add_remove_simple(mach):
  print("all:",get_all_labels())
  assert 0 == get_num_labels()
  l = add_label(0,100,"huhu")
  print("label:",l)
  print("all:",get_all_labels())
  assert 1 == get_num_labels()
  remove_label(l)
  print("all:",get_all_labels())
  assert 0 == get_num_labels()

def _create_random(num, size, seed=42):
  seq = list(range(num))
  random.seed(seed)
  random.shuffle(seq)
  labels = [None] * num
  num = 0
  for i in seq:
    addr = i * size
    l = add_label(addr, size, "@%d:%d" % (i,num))
    labels[i] = l
    num += 1
  # check order
  for i in range(num):
    addr = i * size
    assert labels[i].addr() == addr
  # check size
  assert get_num_labels() == num
  return labels

def _delete_random(labels, seed=21):
  num = len(labels)
  seq = list(range(num))
  random.seed(seed)
  random.shuffle(seq)
  assert get_num_labels() == num
  for i in seq:
    remove_label(labels[i])
  # check final size
  assert get_num_labels() == 0

def _check_find(labels):
  num = len(labels)
  size = labels[0].size()
  for i in range(num):
    # begin range
    addr = i * size
    l = find_label(addr)
    assert l == labels[i]
    # end range
    addr = i * size + size - 1
    l = find_label(addr)
    assert l == labels[i]

def test_label_stress_add_remove(mach):
  labels = _create_random(2048, 64)
  _check_find(labels)
  _delete_random(labels)

def test_label_stress_add_remove_large(mach):
  labels = _create_random(1024, 128)
  _check_find(labels)
  _delete_random(labels)

def test_label_add_only(mach):
  assert None == get_all_labels()
  assert None == get_page_labels(0)
  assert 0 == get_num_labels()
  assert 0 == get_num_page_labels(0)
  l = add_label(0x0000, 0x2000, "label")
  assert 1 == get_num_labels()
  assert 1 == get_num_page_labels(0)
  assert [l] == get_all_labels()
  assert [l] == get_page_labels(0)

def test_label_add_remove(mach):
  assert None == get_all_labels()
  assert None == get_page_labels(0)
  assert 0 == get_num_labels()
  assert 0 == get_num_page_labels(0)
  l = add_label(0xf000, 0x2000, "label")
  assert 1 == get_num_labels()
  assert 1 == get_num_page_labels(0)
  assert [l] == get_all_labels()
  assert [l] == get_page_labels(0)
  remove_label(l)
  assert 0 == get_num_labels()
  assert 0 == get_num_page_labels(0)
  assert None == get_all_labels()
  assert None == get_page_labels(0)

def test_label_cross_add_only(mach):
  assert None == get_all_labels()
  assert None == get_page_labels(0)
  assert None == get_page_labels(1)
  l = add_label(0xf000, 0x2000, "cross")
  assert 1 == get_num_labels()
  assert [l] == get_all_labels()
  assert [l] == get_page_labels(0)
  assert [l] == get_page_labels(1)

def test_label_cross_add_remove(mach):
  assert None == get_all_labels()
  assert None == get_page_labels(0)
  assert None == get_page_labels(1)
  l = add_label(0xf000, 0x2000, "cross")
  assert 1 == get_num_labels()
  assert [l] == get_all_labels()
  assert [l] == get_page_labels(0)
  assert [l] == get_page_labels(1)
  remove_label(l)
  assert 0 == get_num_labels()
  assert None == get_all_labels()
  assert None == get_page_labels(0)
  assert None == get_page_labels(1)

def test_label_remove_inside(mach):
  labels = _create_random(1024, 128)
  assert 1024 == get_num_labels()
  remove_labels_inside(128, 128*2)
  assert 1022 == get_num_labels()

def test_label_find_intersecting(mach):
  labels = _create_random(1024, 128)
  l1 = find_intersecting_labels(128, 128)
  assert l1 == [labels[1]]
  l2 = find_intersecting_labels(128, 129)
  assert l2 == [labels[1], labels[2]]
  l3 = find_intersecting_labels(150, 128)
  assert l3 == [labels[1], labels[2]]
