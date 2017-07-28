#!/usr/bin/env python
# ppunpack.py
#
# a bare68k sample that runs the RNC propack unpacker in a simulated 68k
# environment to extract crunched data
#
# files:
#   unpack.bin    rnc_1.s unpack code assembled at 0x1000
#   data.bin      crunched data: here the rnc_1.s file itself

from __future__ import print_function

import os

from bare68k import *
from bare68k.api import *
from bare68k.consts import *


def ppunpack(data, unpacker_code, do_trace=False):
    """unpack the given data blob and return the unpacked data"""
    unpacker_size = len(unpacker_code)

    # setup bare68k
    runtime.log_setup()
    rt = runtime.init_quick(ram_pages=1)

    # write unpacker code to simulated RAM
    code_addr = 0x1000
    stack_addr = 0x0f00
    mem.w_block(code_addr, unpacker_code)

    # write packed data
    data_in_addr = code_addr + unpacker_size
    data_in_size = len(data)
    mem.w_block(data_in_addr, data)

    # calc location for output data
    data_out_addr = data_in_addr + data_in_size

    # perform reset of virtual CPU
    rt.reset(code_addr, stack_addr)

    # place a RESET opcode at address 0 so the RTS in the code jumps to
    # this end of run()
    RESET_OPCODE = 0x4e70
    mem.w16(0, RESET_OPCODE)

    # setup registers for unpacker
    cpu.w_reg(M68K_REG_D0, data_in_size)
    cpu.w_reg(M68K_REG_A0, data_in_addr)
    cpu.w_reg(M68K_REG_A1, data_out_addr)

    data_out = None

    # enable tracing?
    if do_trace:
        trace.enable_instr_trace()
        trace.enable_cpu_mem_trace()

    # pc trace with 16 entries in backlog
    tools.setup_pc_trace(16)

    # go!
    ri = rt.run()
    if ri.is_done():
        print(ri, "CPU MHZ=", ri.calc_cpu_mhz())
        # get result in reg D0
        result = cpu.r_reg(M68K_REG_D0)
        if result <= 0:
            print("UNPACK ERROR:", result)
        else:
            data_out = mem.r_block(data_out_addr, result)

    # dump final CPU state
    debug.cpusnapshot.print_cpu_snapshot("final state:")

    # clean up bare68k environment
    rt.shutdown()

    return data_out


def check_unpack(input_file, ref_output_file, unpacker_file="unpack.bin",
                 trace=False):
    """check unpack operation by unpacking input file and comparing with
       rerence output file"""
    dir_path = os.path.dirname(__file__)
    input_path = os.path.join(dir_path, input_file)
    ref_output_path = os.path.join(dir_path, ref_output_file)
    unpacker_path = os.path.join(dir_path, unpacker_file)

    # read input data
    f = open(input_path, "rb")
    data = f.read()
    f.close()
    print("reading input data:", input_file, ", size=", len(data))

    # read reference output file
    f = open(ref_output_path, "rb")
    ref_data = f.read()
    f.close()
    print("reading reference output data:", input_file, ", size=", len(data))

    # read reference output file
    f = open(unpacker_path, "rb")
    unpacker_code = f.read()
    f.close()
    print("reading unpacker code:", input_file, ", size=", len(data))

    # unpack
    out_data = ppunpack(data, unpacker_code, trace)
    assert out_data == ref_data


# run when script is called
if __name__ == '__main__':
    check_unpack("data.bin", "rnc_1.s", trace=False)
