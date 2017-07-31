"""wrap machine's trap functions"""

from ._getmach import mach

trap_setup = mach.trap_setup
trap_setup_abs = mach.trap_setup_abs
trap_free = mach.trap_free

traps_get_num_free = mach.traps_get_num_free

trap_enable = mach.trap_enable
trap_disable = mach.trap_disable

traps_global_enable = mach.traps_global_enable
traps_global_disable = mach.traps_global_disable
