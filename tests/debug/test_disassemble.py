import os
from bare68k.debug.disassemble import *


def test_da_init_memory(rt):
    da = Disassembler()
    da.shutdown()


def test_da_init_buffer(rt):
    buf = b"\x00\x00"
    da = Disassembler(buf)
    da.shutdown()


CODE_ORG = 0x1000


def read_code_file():
    data_file = os.path.abspath(os.path.join(
        __file__, "..", "..", "..", "samples", "ppunpack", "unpack.bin"))
    fh = open(data_file, "rb")
    data = fh.read()
    fh.close()
    return data


def test_da_str_file(rt):
    data = read_code_file()
    size = len(data)
    da = Disassembler(data, CODE_ORG)
    pc = CODE_ORG
    end = CODE_ORG + size
    while pc < end:
        op, arg, pc = da.disassemble_str(pc)
        print(op, arg, pc)


def test_da_file(rt):
    data = read_code_file()
    size = len(data)
    da = Disassembler(data, CODE_ORG)
    pc = CODE_ORG
    end = CODE_ORG + size
    lf = InstrLineFormatter()
    while pc < end:
        li, pc = da.disassemble(pc)
        print(lf.format(li))


def test_da_aline(rt):
    mem = rt.get_mem()
    mem.w16(0, 0xa042)
    da = Disassembler()
    li, pc = da.disassemble(0)
    assert li.opcode == 'aline'
    assert li.args == '#$042'


def test_da_label(rt):
    lm = rt.get_label_mgr()
    l = lm.add_label(0, 2, "huhu")
    mem = rt.get_mem()
    mem.w16(0, 0xa042)
    da = Disassembler()
    da.set_label_mgr(lm)
    li, pc = da.disassemble(0)
    assert li.label == l


def test_da_annotation(rt):
    def annotator(li):
        return "#" + li.opcode
    mem = rt.get_mem()
    mem.w16(0, 0xa042)
    da = Disassembler()
    da.set_annotator(annotator)
    li, pc = da.disassemble(0)
    assert li.annotation == "#" + li.opcode
