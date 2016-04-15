from bare68k.consts import *
from bare68k.errors import *

class MemoryConfig(object):
  """Configuration class for the memory layout of your m68k system"""

  EMPTY_FLAG = '_'
  RAM_FLAG = 'a'
  ROM_FLAG = 'o'
  SPECIAL_FLAG = 'S'
  RESERVE_FLAG = 'X'

  def __init__(self, cpu_cfg, enforce_zero_page_ram=True, auto_align=False):
    """setup default memory config"""
    # make sure we have RAM in zero page (vector area)
    self.enforce_zero_page_ram = enforce_zero_page_ram
    # auto align size requests that are not page aligned
    self.auto_align = auto_align

    # check bus width for max pages
    bus_width = cpu_cfg.get_addr_bus_width()
    # on 24 bit you can use up to 256 64k pages: xx yyyy
    if bus_width == 24:
      self.max_pages = 256
    # on 32 bit you can use up to 65536 64k pages: xxxx yyyy
    else:
      self.max_pages = 65536

    # auto reserve ram of size?
    self.ram_pages = None
    self.num_pages = None
    # layout
    self.ram_ranges = []
    self.rom_ranges = []
    self.spc_ranges = []
    self.page_list = []

  def _get_str_size(self, size_str, def_units):
    """get a size value from a string an honor K,M,G units

       returns (size_int, units_int)
    """
    n = len(size_str)
    if n < 1:
      raise ConfigError("Invalid size given: " + size_str)
    all_digits = size_str.isdigit()
    if all_digits:
      size = int(size_str)
      return (size, def_units)
    else:
      unit_str = size_str[-1].lower()
      if unit_str == 'k':
        units = 1024
      elif unit_str == 'm':
        units = 1024 * 1024
      elif unit_str == 'g':
        units = 1024 * 1024 * 1024
      elif unit_str == 'p': # for pages
        units = 64 * 1024
      else:
        raise ConfigError("Unknown size units: " + unit_str)
      size_str = size_str[:-1]
      if not size_str.isdigit():
        raise ConfigError("Invalid size given: " + size_str)
      size = int(size_str)
      return(size, units)

  def _get_num_pages(self, size, units):
    """get a size value and make sure its page aligned and return the pages"""
    if type(size) is str:
      n_size, n_units = self._get_str_size(size, units)
      total = n_size * n_units
    else:
      total = size * units
    # is 64k page aligned?
    if total & 0xffff != 0:
      if self.auto_align:
        pages = (total + 0xffff) >> 16
      else:
        raise ConfigError("Size value %s (units %s) is not page aligned!" % (size, units))
    else:
      pages = total >> 16
    return pages

  def _get_page_addr(self, addr):
    """convert an absolute address to a page number"""
    return self._get_num_pages(addr, 1)

  def _store_page_range(self, begin_page, num_pages, flag, opts=None):
    """make sure the given page range fits in the page list"""
    # first check if the last_page fits in our address space
    next_page = begin_page + num_pages
    if next_page > self.max_pages:
      raise ConfigError("Page range @%s+%s does not fit in address range of CPU!" % (begin_page, end_page))
    # ensure list size
    l = self.page_list
    while len(l) < next_page:
      l.append((self.EMPTY_FLAG, None))
    # now fill list
    for page in range(begin_page, next_page):
      entry = l[page]
      e_flag = entry[0]
      # make sure entry is empty
      if e_flag != self.EMPTY_FLAG:
        raise ConfigError("Page @%s already occupied: has %s want %s" % (page, e_flag, flag))
      # store new entry
      l[page] = (flag, opts)

  def set_ram_size(self, ram_size=2048, units=1024):
    """set total ram size

       if you do not specify ram ranges you can give a total RAM size here
       and it will automatically allocate page ranges starting from zero
       with RAM.
    """
    self.ram_pages = self._get_num_pages(ram_size, units)

  def set_num_pages(self, pages, units=64*1024):
    """set a custom top of the page range"""
    self.num_pages = self._get_num_pages(pages, units)

  def add_ram_range_addr(self, begin_addr, size, units=1024):
    begin_page = self._get_page_addr(begin_addr)
    num_pages = self._get_num_pages(size, units)
    return self.add_ram_range(begin_page, num_pages)

  def add_ram_range(self, begin_page, num_pages):
    self._store_page_range(begin_page, num_pages, self.RAM_FLAG)

  def add_rom_range_addr(self, data, begin_addr, size, units=1024):
    begin_page = self._get_page_addr(begin_addr)
    num_pages = self._get_num_pages(size, units)
    return self.add_rom_range(data, begin_page, num_pages)

  def add_rom_range(self, data, begin_page, num_pages):
    self._store_page_range(begin_page, num_pages, self.ROM_FLAG, data)

  def add_special_range_addr(self, r_func, w_func, begin_addr, size, units=1024):
    begin_page = self._get_page_addr(begin_addr)
    num_pages = self._get_num_pages(size, units)
    return self.add_special_range(r_func, w_func, begin_page, num_pages)

  def add_special_range(self, r_func, w_func, begin_page, num_pages):
    opts = (r_func, w_func)
    self._store_page_range(begin_page, num_pages, self.SPECIAL_FLAG, opts)

  def add_reserve_range_addr(self, begin_addr, size, units=1024):
    begin_page = self._get_page_addr(begin_addr)
    num_pages = self._get_num_pages(size, units)
    return self.add_reserve_range(begin_page, num_pages)

  def add_reserve_range(self, r_func, w_func, begin_page, num_pages):
    self._store_page_range(begin_page, num_pages, self.RESERVE_FLAG)

  def get_page_list(self):
    return self.page_list

  def get_page_list_str(self):
    return "".join(map(lambda x : x[0], self.page_list))

  def calc_layout(self):
    pass
