"""wrap machine's CPU access functions"""

import bare68k.machine as mach

# context handling
get_context = mach.get_cpu_context
set_context = mach.set_cpu_context

# register access
r_reg = mach.r_reg
w_reg = mach.w_reg
rs_reg = mach.rs_reg
ws_reg = mach.ws_reg
r_dx = mach.r_dx
w_dx = mach.w_dx
r_ax = mach.r_ax
w_ax = mach.w_ax
r_pc = mach.r_pc
w_pc = mach.w_pc
r_sp = mach.r_sp
w_sp = mach.w_sp
r_sr = mach.r_sr
w_sr = mach.w_sr
