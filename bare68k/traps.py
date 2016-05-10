"""wrap machine's trap functions"""

import bare68k.machine as mach

setup = mach.trap_setup
free = mach.trap_free

get_num_free = mach.traps_get_num_free

enable = mach.trap_enable
disable = mach.trap_disable

global_enable = mach.traps_global_enable
global_disable = mach.traps_global_disable
