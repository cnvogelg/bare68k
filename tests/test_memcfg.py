from __future__ import print_function

import pytest

from bare68k import *
from bare68k.consts import *
from bare68k.errors import *
from bare68k.memcfg import *


def test_int_str_size():
    memcfg = MemoryConfig()
    # string to size conversion
    assert memcfg._get_str_size("23", 10) == (23, 10)
    assert memcfg._get_str_size("23k", 11) == (23, 1024)
    assert memcfg._get_str_size("23m", 12) == (23, 1024 * 1024)
    assert memcfg._get_str_size("23g", 13) == (23, 1024 * 1024 * 1024)
    assert memcfg._get_str_size("23p", 14) == (23, 64 * 1024)


def test_int_page_size():
    memcfg = MemoryConfig()
    with pytest.raises(ConfigError):
        # 1k is not a page
        memcfg._get_num_pages(1, 1024)
    assert memcfg._get_num_pages(1, 64 * 1024) == 1
    assert memcfg._get_num_pages(64, 1024) == 1
    assert memcfg._get_num_pages("1p", 1024) == 1


def test_ram_ranges():
    memcfg = MemoryConfig()
    assert memcfg.get_range_list() == []
    # add a range starting at page 1 with 2 pages size
    memcfg.add_ram_range(1, 2)
    pl = memcfg.get_range_list()
    assert len(pl) == 1
    assert pl[0] == MemoryRange(1, 2, MEM_RAM)
    assert memcfg.get_num_pages() == 3
    # add another range
    memcfg.add_ram_range(4, 3)
    pl = memcfg.get_range_list()
    assert len(pl) == 2
    assert pl[0] == MemoryRange(1, 2, MEM_RAM)
    assert pl[1] == MemoryRange(4, 3, MEM_RAM)
    assert memcfg.get_num_pages() == 7
    print("PL=", memcfg.get_page_list_str())
    # overlapping range gives error
    with pytest.raises(ConfigError):
        memcfg.add_ram_range(2, 4)


def test_ram_check():
    memcfg = MemoryConfig()
    memcfg.add_ram_range(0, 4)
    # check range
    memcfg.check()
    with pytest.raises(ConfigError):
        memcfg.check(max_pages=2)


def test_ram_not_sparse():
    memcfg = MemoryConfig()
    memcfg.add_reserve_range(1, 1)
    memcfg.add_reserve_range(3, 1)
    with pytest.raises(ConfigError):
        memcfg.add_ram_range(0, 4)


def test_ram_sparse():
    memcfg = MemoryConfig()
    mrl1 = memcfg.add_reserve_range(1, 1)
    assert len(mrl1) == 1
    assert mrl1[0] == MemoryRange(1, 1, MEM_RESERVE)
    mrl2 = memcfg.add_reserve_range(3, 1)
    assert len(mrl2) == 1
    assert mrl2[0] == MemoryRange(3, 1, MEM_RESERVE)
    mrl3 = memcfg.add_ram_range(0, 4, sparse=True)
    assert len(mrl3) == 3
    print(memcfg.get_page_list_str())
    pl = memcfg.get_range_list()
    assert len(pl) == 5
    assert pl[0] == mrl3[0]
    assert pl[1] == mrl1[0]
    assert pl[2] == mrl3[1]
    assert pl[3] == mrl2[0]
    assert pl[4] == mrl3[2]


def test_memtypes():
    memcfg = MemoryConfig()
    # RAM
    memcfg.add_ram_range(0, 1)
    # ROM (page aligned)
    data = bytes([0] * PAGE_BYTES)
    memcfg.add_rom_range(1, 1, data)
    # ROM (not aligned)
    data2 = bytes([0] * 1234)
    with pytest.raises(ConfigError):
        memcfg.add_rom_range(2, 1, data2)
    memcfg.add_rom_range(2, 1, data2, pad=True)
    memcfg.add_rom_range(3, 1, data2, pad=0xff)
    # special

    def r(*args):
        pass
    memcfg.add_special_range(4, 1, r, None)
    # reserver
    memcfg.add_reserve_range(5, 1)
    # empty
    memcfg.add_empty_range(6, 1)
    # mirror
    memcfg.add_mirror_range(7, 1, 0)
