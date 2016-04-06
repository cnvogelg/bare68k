from bare68k.consts import *

class CPUConfig(object):
  """Configuraiton class helper for CPU specific parameters of bare68k"""

  cpu_types = (
    M68K_CPU_TYPE_68000,
    M68K_CPU_TYPE_68010,
    M68K_CPU_TYPE_68020,
    M68K_CPU_TYPE_68EC020
  )

  def __init__(self):
    self.cpu_type = M68K_CPU_TYPE_68000

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
        raise ValueError("Invalid CPU Type: " + val)
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
        raise ValueError("Invalid CPU Type: " + str(val))
    else:
      raise ValueError("Invalid CPU Type: " + str(val))
