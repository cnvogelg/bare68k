Contants
========

Various functions in :mod:`bare68k` require a constant value. All the
constants are found in the :mod:`bare68k.consts` module.

.. module:: bare68k.consts

CPU Types
---------

.. autodata:: M68K_CPU_TYPE_INVALID
.. autodata:: M68K_CPU_TYPE_68000
.. autodata:: M68K_CPU_TYPE_68010
.. autodata:: M68K_CPU_TYPE_68EC020
.. autodata:: M68K_CPU_TYPE_68020
.. autodata:: M68K_CPU_TYPE_68030
.. autodata:: M68K_CPU_TYPE_68040

CPU Registers
-------------

Data Registers
^^^^^^^^^^^^^^

.. autodata:: M68K_REG_D0
.. autodata:: M68K_REG_D1
.. autodata:: M68K_REG_D2
.. autodata:: M68K_REG_D3
.. autodata:: M68K_REG_D4
.. autodata:: M68K_REG_D5
.. autodata:: M68K_REG_D6
.. autodata:: M68K_REG_D7

Address Registers
^^^^^^^^^^^^^^^^^

.. autodata:: M68K_REG_A0
.. autodata:: M68K_REG_A1
.. autodata:: M68K_REG_A2
.. autodata:: M68K_REG_A3
.. autodata:: M68K_REG_A4
.. autodata:: M68K_REG_A5
.. autodata:: M68K_REG_A6
.. autodata:: M68K_REG_A7

Special Registers
^^^^^^^^^^^^^^^^^

.. autodata:: M68K_REG_PC
.. autodata:: M68K_REG_SR
.. autodata:: M68K_REG_SP
.. autodata:: M68K_REG_USP
.. autodata:: M68K_REG_ISP
.. autodata:: M68K_REG_MSP
.. autodata:: M68K_REG_SFC
.. autodata:: M68K_REG_DFC
.. autodata:: M68K_REG_VBR
.. autodata:: M68K_REG_CACR
.. autodata:: M68K_REG_CAAR

Virtual Registers
^^^^^^^^^^^^^^^^^

.. autodata:: M68K_REG_PREF_ADDR
.. autodata:: M68K_REG_PREF_DATA
.. autodata:: M68K_REG_PPC
.. autodata:: M68K_REG_IR
.. autodata:: M68K_REG_CPU_TYPE


Interrupt Ack Special Values
----------------------------

.. autodata:: M68K_INT_ACK_AUTOVECTOR
.. autodata:: M68K_INT_ACK_SPURIOUS

Memory Flags
------------

Memory Range Create Flags
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autodata:: MEM_FLAGS_READ
.. autodata:: MEM_FLAGS_WRITE
.. autodata:: MEM_FLAGS_RW
.. autodata:: MEM_FLAGS_TRAPS

Memory Access Type
^^^^^^^^^^^^^^^^^^

.. autodata:: MEM_ACCESS_R8
.. autodata:: MEM_ACCESS_R16
.. autodata:: MEM_ACCESS_R32
.. autodata:: MEM_ACCESS_W8
.. autodata:: MEM_ACCESS_W16
.. autodata:: MEM_ACCESS_W32
.. autodata:: MEM_ACCESS_MASK

Access Function Code
^^^^^^^^^^^^^^^^^^^^

.. autodata:: MEM_FC_MASK
.. autodata:: MEM_FC_USER_DATA
.. autodata:: MEM_FC_USER_PROG
.. autodata:: MEM_FC_SUPER_DATA
.. autodata:: MEM_FC_SUPER_PROG
.. autodata:: MEM_FC_INT_ACK

Function Code Masks
^^^^^^^^^^^^^^^^^^^

.. autodata:: MEM_FC_DATA_MASK
.. autodata:: MEM_FC_PROG_MASK
.. autodata:: MEM_FC_USER_MASK
.. autodata:: MEM_FC_SUPER_MASK
.. autodata:: MEM_FC_INT_MASK

API Special Memory Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autodata:: MEM_ACCESS_R_BLOCK
.. autodata:: MEM_ACCESS_W_BLOCK
.. autodata:: MEM_ACCESS_R_CSTR
.. autodata:: MEM_ACCESS_W_CSTR
.. autodata:: MEM_ACCESS_R_BSTR
.. autodata:: MEM_ACCESS_W_BSTR
.. autodata:: MEM_ACCESS_R_B32
.. autodata:: MEM_ACCESS_W_B32
.. autodata:: MEM_ACCESS_BSET
.. autodata:: MEM_ACCESS_BCOPY

Trap Create Flags
-----------------

.. autodata:: TRAP_DEFAULT
.. autodata:: TRAP_ONE_SHOT
.. autodata:: TRAP_AUTO_RTS

CPU Events
----------

.. autodata:: CPU_EVENT_CALLBACK_ERROR
.. autodata:: CPU_EVENT_RESET
.. autodata:: CPU_EVENT_ALINE_TRAP
.. autodata:: CPU_EVENT_MEM_ACCESS
.. autodata:: CPU_EVENT_MEM_BOUNDS
.. autodata:: CPU_EVENT_MEM_TRACE
.. autodata:: CPU_EVENT_MEM_SPECIAL
.. autodata:: CPU_EVENT_INSTR_HOOK
.. autodata:: CPU_EVENT_INT_ACK
.. autodata:: CPU_EVENT_WATCHPOINT
.. autodata:: CPU_EVENT_TIMER
.. autodata:: CPU_NUM_EVENTS
.. autodata:: CPU_EVENT_USER_ABORT
.. autodata:: CPU_EVENT_DONE
