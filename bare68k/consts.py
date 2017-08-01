#!/usr/bin/env python
#
# m68k.py
#
# constants for musashi m68k CPU emulator
#


# cpu types

M68K_CPU_TYPE_INVALID = 0
"""invalid CPU type."""
M68K_CPU_TYPE_68000 = 1
"""Motorola 68000 CPU"""
M68K_CPU_TYPE_68010 = 2
"""Motorola 68010 CPU"""
M68K_CPU_TYPE_68EC020 = 3
"""Motorola 68EC20 CPU"""
M68K_CPU_TYPE_68020 = 4
"""Motorola 68020 CPU"""
M68K_CPU_TYPE_68030 = 5
"""Motorola 68030 CPU

Note:
    Supported by disassembler ONLY
"""
M68K_CPU_TYPE_68040 = 6
"""Motorola 68040 CPU

Note:
    Supported by disassembler ONLY
"""


# registers

M68K_REG_D0 = 0
"""Data Register D0"""
M68K_REG_D1 = 1
"""Data Register D1"""
M68K_REG_D2 = 2
"""Data Register D2"""
M68K_REG_D3 = 3
"""Data Register D3"""
M68K_REG_D4 = 4
"""Data Register D4"""
M68K_REG_D5 = 5
"""Data Register D5"""
M68K_REG_D6 = 6
"""Data Register D6"""
M68K_REG_D7 = 7
"""Data Register D7"""

M68K_REG_A0 = 8
"""Address Register A0"""
M68K_REG_A1 = 9
"""Address Register A1"""
M68K_REG_A2 = 10
"""Address Register A2"""
M68K_REG_A3 = 11
"""Address Register A3"""
M68K_REG_A4 = 12
"""Address Register A4"""
M68K_REG_A5 = 13
"""Address Register A5"""
M68K_REG_A6 = 14
"""Address Register A6"""
M68K_REG_A7 = 15
"""Address Register A7"""

M68K_REG_PC = 16
"""Program Counter PC"""
M68K_REG_SR = 17
"""Status Register SR"""
M68K_REG_SP = 18
"""The current Stack Pointer (located in A7)"""
M68K_REG_USP = 19
"""User Stack Pointer USP"""
M68K_REG_ISP = 20
"""Interrupt Stack Pointer ISP"""
M68K_REG_MSP = 21
"""Master Stack Pointer MSP"""
M68K_REG_SFC = 22
"""Source Function Code SFC"""
M68K_REG_DFC = 23
"""Destination Function Code DFC"""
M68K_REG_VBR = 24
"""Vector Base Register VBR"""
M68K_REG_CACR = 25
"""Cache Control Register CACR"""
M68K_REG_CAAR = 26
"""Cache Address Register CAAR"""

M68K_REG_PREF_ADDR = 27
"""Virtual Reg: Last prefetch address"""
M68K_REG_PREF_DATA = 28
"""Virtual Reg: Last prefetch data"""

M68K_REG_PPC = 29
"""Virtual Reg: Previous value in the program counter"""
M68K_REG_IR = 30
"""Instruction register IR"""
M68K_REG_CPU_TYPE = 31
"""Virtual Reg: Type of CPU being run"""


# int ack special values

M68K_INT_ACK_AUTOVECTOR = 0xffffffff
"""interrupt acknowledge to perform autovectoring"""
M68K_INT_ACK_SPURIOUS = 0xfffffffe
"""interrupt acknowledge to cause spurios irq"""


# memory region flags

MEM_FLAGS_READ = 1
"""a readable region"""
MEM_FLAGS_WRITE = 2
"""a writeable region"""
MEM_FLAGS_RW = 3
"""a read/write region"""
MEM_FLAGS_TRAPS = 4
"""bit flag to allow a-line traps in this region

Note:
    Or this flag with the read/write flags
"""

# memory trace

MEM_ACCESS_R8 = 0x11
"""byte read access"""
MEM_ACCESS_R16 = 0x12
"""word read access"""
MEM_ACCESS_R32 = 0x14
"""long read access"""
MEM_ACCESS_W8 = 0x21
"""byte write access"""
MEM_ACCESS_W16 = 0x22
"""word write access"""
MEM_ACCESS_W32 = 0x24
"""long write access"""
MEM_ACCESS_MASK = 0xff
"""constant mask to filter out memory access values"""

# memory function code

MEM_FC_MASK = 0xff00
"""constant mask to filter out memory access function code"""
MEM_FC_USER_DATA = 0x1100
"""access of user data"""
MEM_FC_USER_PROG = 0x1200
"""access of user program"""
MEM_FC_SUPER_DATA = 0x2100
"""access of supervisor data"""
MEM_FC_SUPER_PROG = 0x2200
"""access of supervisor program"""
MEM_FC_INT_ACK = 0x4000
"""access during interrupt acknowledge"""

# masks
MEM_FC_DATA_MASK = 0x0100
"""constant mask for user or supervisor data access"""
MEM_FC_PROG_MASK = 0x0200
"""constant mask for user or supervisor program access"""
MEM_FC_USER_MASK = 0x1000
"""constant mask for user data or program access"""
MEM_FC_SUPER_MASK = 0x2000
"""constant mask for supervisor data or program access"""
MEM_FC_INT_MASK = 0x4000
"""constant mask for interrupt acknowledge"""

# memory flags for api

MEM_ACCESS_R_BLOCK = 0x1100
"""read memory block"""
MEM_ACCESS_W_BLOCK = 0x1200
"""write memory block"""
MEM_ACCESS_R_CSTR = 0x2100
"""read C-string"""
MEM_ACCESS_W_CSTR = 0x2200
"""write C-string"""
MEM_ACCESS_R_BSTR = 0x3100
"""read BCPL-string"""
MEM_ACCESS_W_BSTR = 0x3200
"""write BCPL-string"""
MEM_ACCESS_R_B32 = 0x4100
"""read BPCL long (shifted to left one bit)"""
MEM_ACCESS_W_B32 = 0x4200
"""write BCPL long (shifted to right one bit)"""
MEM_ACCESS_BSET = 0x5400
"""set a memory block to a value"""
MEM_ACCESS_BCOPY = 0x6400
"""copy a memory block"""


# traps

TRAP_DEFAULT = 0
"""a default A-Line trap, multi shot, no rts"""
TRAP_ONE_SHOT = 1
"""flag, a one shot trap, is auto-removed after invocation"""
TRAP_AUTO_RTS = 2
"""flag, automatically perform a RTS after trap processing"""


# cpu events

CPU_EVENT_CALLBACK_ERROR = 0
"""a Python callback triggered by the CPU emulator caused an Error or Exception"""
CPU_EVENT_RESET = 1
"""a RESET opcode was encountered"""
CPU_EVENT_ALINE_TRAP = 2
"""an A-Line Trap opcode was executed"""
CPU_EVENT_MEM_ACCESS = 3
"""a memory region was accessed with invalid op.

E.g. a read-only region was written to
"""
CPU_EVENT_MEM_BOUNDS = 4
"""a memory access beyond the allocated page range occurred"""
CPU_EVENT_MEM_TRACE = 5
"""a memory trace callback in Python returned some value"""
CPU_EVENT_MEM_SPECIAL = 6
"""a special range memory region was triggered and the handler returned a value"""
CPU_EVENT_INSTR_HOOK = 7
"""the instruction trace handler was triggered and returned a value"""
CPU_EVENT_INT_ACK = 8
"""interrupt acknowledge handler was triggered and returned a value"""
CPU_EVENT_BREAKPOINT = 9
"""a breakpoint was hit"""
CPU_EVENT_WATCHPOINT = 10
"""a watchpoint was hit"""
CPU_EVENT_TIMER = 11
"""a timer fired"""

CPU_NUM_EVENTS = 12
"""total number of machine CPU events"""

# extra events (created by runtime)
CPU_EVENT_USER_ABORT = 12
"""runtime flag, user aborted run with a ``KeyboardInterrupt``"""
CPU_EVENT_DONE = 13
"""runtime flag, reached end of processing.

E.g. a RESET opcode was encountered.
"""

# names for all events
CPU_EVENT_NAMES = (
    "CALLBACK_ERROR",  # 0
    "RESET",  # 1
    "ALINE_TRAP",  # 2
    "MEM_ACCESS",  # 3
    "MEM_BOUNDS",  # 4
    "MEM_TRACE",  # 5
    "MEM_SPECIAL",  # 6
    "INSTR_HOOK",  # 7
    "INT_ACK",  # 8
    "BREAKPOINT",  # 9
    "WATCHPOINT",  # 10
    "TIMER",  # 11
    "USER_ABORT",  # 12
    "DONE",  # 13
)
