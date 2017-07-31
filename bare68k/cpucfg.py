from bare68k.consts import *
from bare68k.errors import *


class CPUConfig(object):
    """Configure the emulated CPU.
    """

    cpu_types = (
        M68K_CPU_TYPE_68000,
        M68K_CPU_TYPE_68010,
        M68K_CPU_TYPE_68020,
        M68K_CPU_TYPE_68EC020
    )

    def __init__(self, cpu_type=M68K_CPU_TYPE_68000):
        self.cpu_type = cpu_type

    def get_cpu_type(self):
        return self.cpu_type

    def get_cpu_type_str(self):
        ct = self.cpu_type
        if ct == M68K_CPU_TYPE_68000:
            return "68000"
        elif ct == M68K_CPU_TYPE_68010:
            return "68010"
        elif ct == M68K_CPU_TYPE_68020:
            return "68020"
        elif ct == M68K_CPU_TYPE_68EC020:
            return "68EC020"

    def get_addr_bus_width(self):
        """get address bus width of selected CPU: either 24 or 32 bits"""
        if self.cpu_type in (M68K_CPU_TYPE_68000, M68K_CPU_TYPE_68010):
            return 24
        else:
            return 32

    def get_max_pages(self):
        if self.get_addr_bus_width() == 24:
            return 256
        else:
            return 256 * 256

    def set_cpu_type(self, val):
        if type(val) is str:
            if val in ('68000', '000', '00'):
                self.cpu_type = M68K_CPU_TYPE_68000
            elif val in ('68010', '010', '10'):
                self.cpu_type = M68K_CPU_TYPE_68010
            elif val in ('68020', '020', '20'):
                self.cpu_type = M68K_CPU_TYPE_68020
            elif val.lower() in ('68ec020', 'ec020', 'ec20'):
                self.cpu_type = M68K_CPU_TYPE_68EC020
            else:
                raise ConfigError("Invalid CPU Type: " + val)
        elif type(val) is int:
            if val in self.cpu_types:
                self.cpu_type = val
            elif val in (68000, 0):
                self.cpu_type = M68K_CPU_TYPE_68000
            elif val in (68010, 10):
                self.cpu_type = M68K_CPU_TYPE_68010
            elif val in (68020, 20):
                self.cpu_type = M68K_CPU_TYPE_68020
            else:
                raise ConfigError("Invalid CPU Type: " + str(val))
        else:
            raise ConfigError("Invalid CPU Type: " + str(val))
