"""wrap machine's memory access functions"""

from ._getmach import mach

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

# configure mem
set_invalid_value = mach.set_invalid_value
add_memory = mach.add_memory
add_special = mach.add_special
add_empty = mach.add_empty
add_mirror = mach.add_mirror

# trace
set_mem_cpu_trace_func = mach.set_mem_cpu_trace_func
set_mem_api_trace_func = mach.set_mem_api_trace_func

# dump
get_cpu_fc_str = mach.get_cpu_fc_str
get_cpu_access_str = mach.get_cpu_access_str
get_cpu_mem_str = mach.get_cpu_mem_str
get_api_access_str = mach.get_api_access_str
get_api_mem_str = mach.get_api_mem_str

# testing cpu access
cpu_w8 = mach.cpu_w8
cpu_w16 = mach.cpu_w16
cpu_w32 = mach.cpu_w32
cpu_r8 = mach.cpu_r8
cpu_r16 = mach.cpu_r16
cpu_r32 = mach.cpu_r32
