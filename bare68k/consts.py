#!/usr/bin/env python
#
# m68k.py
#
# constants for musashi m68k CPU emulator
#

# cpu type
M68K_CPU_TYPE_INVALID = 0
M68K_CPU_TYPE_68000 = 1
M68K_CPU_TYPE_68010 = 2
M68K_CPU_TYPE_68EC020 = 3
M68K_CPU_TYPE_68020 = 4
M68K_CPU_TYPE_68030 = 5 # Supported by disassembler ONLY
M68K_CPU_TYPE_68040	= 6 # Supported by disassembler ONLY

# registers
M68K_REG_D0 = 0
M68K_REG_D1 = 1
M68K_REG_D2 = 2
M68K_REG_D3 = 3
M68K_REG_D4 = 4
M68K_REG_D5 = 5
M68K_REG_D6 = 6
M68K_REG_D7 = 7
M68K_REG_A0 = 8
M68K_REG_A1 = 9
M68K_REG_A2 = 10
M68K_REG_A3 = 11
M68K_REG_A4 = 12
M68K_REG_A5 = 13
M68K_REG_A6 = 14
M68K_REG_A7 = 15
M68K_REG_PC = 16 # Program Counter
M68K_REG_SR = 17 # Status Register
M68K_REG_SP = 18 #The current Stack Pointer (located in A7)
M68K_REG_USP = 19 # User Stack Pointer
M68K_REG_ISP = 20 # Interrupt Stack Pointer
M68K_REG_MSP = 21 # Master Stack Pointer
M68K_REG_SFC = 22 # Source Function Code
M68K_REG_DFC = 23 # Destination Function Code
M68K_REG_VBR = 24 # Vector Base Register
M68K_REG_CACR = 25 # Cache Control Register
M68K_REG_CAAR = 26 # Cache Address Register

M68K_REG_PREF_ADDR = 27 # Virtual Reg: Last prefetch address
M68K_REG_PREF_DATA = 28 # Virtual Reg: Last prefetch data

M68K_REG_PPC = 29 # Previous value in the program counter
M68K_REG_IR = 30 # Instruction register
M68K_REG_CPU_TYPE = 31 # Type of CPU being run

# aline callback
M68K_ALINE_NONE   = 0
M68K_ALINE_EXCEPT = 1
M68K_ALINE_RTS    = 2

# int ack special values
M68K_INT_ACK_AUTOVECTOR = 0xffffffff
M68K_INT_ACK_SPURIOUS   = 0xfffffffe

# memory
MEM_FLAGS_READ  = 1
MEM_FLAGS_WRITE = 2
MEM_FLAGS_RW    = 3
MEM_FLAGS_TRAPS = 4

# memory trace
MEM_ACCESS_R8    = 1
MEM_ACCESS_R16   = 2
MEM_ACCESS_R32   = 4
MEM_ACCESS_W8    = 9
MEM_ACCESS_W16   = 10
MEM_ACCESS_W32   = 12
MEM_ACCESS_MASK  = 0x0f

# memory function code
MEM_FC_SHIFT       = 4
MEM_FC_MASK        = 0x1F0
MEM_FC_USER_DATA   = 0x050
MEM_FC_USER_PROG   = 0x060
MEM_FC_SUPER_DATA  = 0x090
MEM_FC_SUPER_PROG  = 0x0a0
MEM_FC_INT_ACK     = 0x100
# masks
MEM_FC_DATA_MASK   = 0x010
MEM_FC_PROG_MASK   = 0x020
MEM_FC_USER_MASK   = 0x040
MEM_FC_SUPER_MASK  = 0x080
MEM_FC_INT_MASK    = 0x100

# memory flags for api
MEM_ACCESS_R_BLOCK = 0x010
MEM_ACCESS_W_BLOCK = 0x090
MEM_ACCESS_R_CSTR  = 0x020
MEM_ACCESS_W_CSTR  = 0x0a0
MEM_ACCESS_R_BSTR  = 0x030
MEM_ACCESS_W_BSTR  = 0x0b0
MEM_ACCESS_R_B32   = 0x040
MEM_ACCESS_W_B32   = 0x0c0
MEM_ACCESS_BSET    = 0x100
MEM_ACCESS_BCOPY   = 0x110

# traps
TRAP_DEFAULT  = 0
TRAP_ONE_SHOT = 1
TRAP_AUTO_RTS = 2

# event
CPU_EVENT_CALLBACK_ERROR = 0
CPU_EVENT_RESET = 1
CPU_EVENT_ALINE_TRAP = 2
CPU_EVENT_MEM_ACCESS = 3
CPU_EVENT_MEM_BOUNDS = 4
CPU_EVENT_MEM_TRACE = 5
CPU_EVENT_MEM_SPECIAL = 6
CPU_EVENT_INSTR_HOOK = 7
CPU_EVENT_INT_ACK = 8
CPU_EVENT_BREAKPOINT = 9
CPU_EVENT_WATCHPOINT = 10
CPU_EVENT_TIMER = 11

CPU_NUM_EVENTS = 12

# extra events (created by runtime)
CPU_EVENT_USER_ABORT = 12
CPU_EVENT_DONE = 13

# names for all events
CPU_EVENT_NAMES = (
    "CALLBACK_ERROR", #0
    "RESET", #1
    "ALINE_TRAP", #2
    "MEM_ACCESS", #3
    "MEM_BOUNDS", #4
    "MEM_TRACE", #5
    "MEM_SPECIAL", #6
    "INSTR_HOOK", #7
    "INT_ACK", #8
    "BREAKPOINT", #9
    "WATCHPOINT", #10
    "TIMER", #11
    "USER_ABORT", #13
    "DONE", #14
)
