from ._getmach import mach

# cpu pc trace

get_pc_trace_size = mach.get_pc_trace_size
setup_pc_trace = mach.setup_pc_trace
cleanup_pc_trace = mach.cleanup_pc_trace
get_pc_trace = mach.get_pc_trace

# breakpoints

get_max_breakpoints = mach.get_max_breakpoints
get_num_breakpoints = mach.get_num_breakpoints
get_next_free_breakpoint = mach.get_next_free_breakpoint
setup_breakpoints = mach.setup_breakpoints
cleanup_breakpoints = mach.cleanup_breakpoints
set_breakpoint = mach.set_breakpoint
clear_breakpoint = mach.clear_breakpoint
enable_breakpoint = mach.enable_breakpoint
disable_breakpoint = mach.disable_breakpoint
is_breakpoint_enabled = mach.is_breakpoint_enabled
get_breakpoint_data = mach.get_breakpoint_data

# watchpoints

get_max_watchpoints = mach.get_max_watchpoints
get_num_watchpoints = mach.get_num_watchpoints
get_next_free_watchpoint = mach.get_next_free_watchpoint
setup_watchpoints = mach.setup_watchpoints
cleanup_watchpoints = mach.cleanup_watchpoints
set_watchpoint = mach.set_watchpoint
clear_watchpoint = mach.clear_watchpoint
enable_watchpoint = mach.enable_watchpoint
disable_watchpoint = mach.disable_watchpoint
is_watchpoint_enabled = mach.is_watchpoint_enabled
get_watchpoint_data = mach.get_watchpoint_data

# timers

get_max_timers = mach.get_max_timers
get_num_timers = mach.get_num_timers
get_next_free_timer = mach.get_next_free_timer
setup_timers = mach.setup_timers
cleanup_timers = mach.cleanup_timers
set_timer = mach.set_timer
clear_timer = mach.clear_timer
enable_timer = mach.enable_timer
disable_timer = mach.disable_timer
is_timer_enabled = mach.is_timer_enabled
get_timer_data = mach.get_timer_data
