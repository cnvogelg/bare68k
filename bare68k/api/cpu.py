"""wrap machine's CPU access functions"""

import bare68k.machine as mach

# context handling
get_cpu_context = mach.get_cpu_context
set_cpu_context = mach.set_cpu_context

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

# debug
get_sr_str = mach.get_sr_str
get_regs = mach.get_regs
get_instr_str = mach.get_instr_str
get_type = mach.get_type

# hooks
set_instr_hook_func = mach.set_instr_hook_func

# irq handling
set_irq = mach.set_irq
set_int_ack_func = mach.set_int_ack_func

# run
pulse_reset = mach.pulse_reset
execute = mach.execute
execute_to_event = mach.execute
execute_to_event_checked = mach.execute_to_event_checked

# run info
get_info = mach.get_info
get_num_events = mach.get_num_events
get_event = mach.get_event
get_done_cycles = mach.get_done_cycles
get_total_cycles = mach.get_total_cycles
clear_info = mach.clear_info

# events
set_event_handler = mach.set_event_handler
get_event_handler = mach.get_event_handler
clear_event_handlers = mach.clear_event_handlers
