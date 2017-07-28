from bare68k import *
from bare68k.consts import *


def test_run():
    # configure logging
    runtime.log_setup()

    # configure CPU: emulate a classic m68k
    cpu_cfg = CPUConfig(M68K_CPU_TYPE_68000)

    # now define the memory layout of the system
    mem_cfg = MemoryConfig()
    # let's create a RAM page (64k) starting at address 0
    mem_cfg.add_ram_range(0, 1)
    # let's create a ROM page (64k) starting at address 0x20000
    mem_cfg.add_rom_range(2, 1)

    # use a default run configuration (no debugging enabled)
    run_cfg = RunConfig()

    # combine everythin into a Runtime instance for your system
    rt = Runtime(cpu_cfg, mem_cfg, run_cfg)

    # fill in some code
    PROG_BASE = 0x1000
    STACK = 0x800
    mem = rt.get_mem()
    mem.w16(PROG_BASE, 0x23c0)  # move.l d0,<32b_addr>
    mem.w32(PROG_BASE + 2, 0)
    mem.w16(PROG_BASE + 6, 0x4e70)  # reset

    # setup CPU
    cpu = rt.get_cpu()
    cpu.w_reg(M68K_REG_D0, 0x42)

    # reset your virtual CPU to start at PROG_BASE and setup initial stack
    rt.reset(PROG_BASE, STACK)

    # now run the CPU emulation until an event occurrs
    # here the RESET opcode is the event we are waiting for
    rt.run()

    # read back some memory
    val = mem.r32(0)
    assert val == 0x42

    # finally shutdown runtime if its no longer used
    # and free resources like the allocated RAM, ROM memory
    rt.shutdown()


if __name__ == '__main__':
    test_run()
