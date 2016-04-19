"""wrap machine's memory access functions"""

import bare68k.machine as mach

# memory block access for RAM/ROM
set_block = mach.set_block
copy_block = mach.copy_block
r_block = mach.r_block
w_block = mach.w_block

# special string/bcpl access
r_cstr = mach.r_cstr
w_cstr = mach.w_cstr
r_bstr = mach.r_bstr
w_bstr = mach.w_bstr
wb32 = mach.wb32
rb32 = mach.rb32

# unsigned access
w8 = mach.w8
w16 = mach.w16
w32 = mach.w32
r8 = mach.r8
r16 = mach.r16
r32 = mach.r32

# signed access
ws8 = mach.ws8
ws16 = mach.ws16
ws32 = mach.ws32
rs8 = mach.rs8
rs16 = mach.rs16
rs32 = mach.rs32
