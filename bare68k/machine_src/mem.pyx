# configure memory

def add_memory(uint16_t start_page, uint16_t num_pages, int flags):
  cdef mem.memory_entry_t *me
  me = mem.mem_add_memory(start_page, num_pages, flags)
  if me == NULL:
    raise ValueError("Invalid memory: start=%d, num=%d" % (start_page, num_pages))
  return <uint32_t>(start_page << 16)

# configure special range

cdef void mem_special_cleanup(mem.special_entry_t *e):
  if e.r_data != NULL:
    rfunc = <object>e.r_data
    Py_DECREF(rfunc)
  if e.w_data != NULL:
    wfunc = <object>e.w_data
    Py_DECREF(wfunc)

cdef int mem_special_adapter_w(int access, uint32_t addr, uint32_t val, void *pfunc, void **out_data):
  try:
    if pfunc != NULL:
      f = <object>pfunc
      result = f(access, addr, val)
      if result is None:
        return cpu.CPU_CB_NO_EVENT
      else:
        Py_INCREF(result)
        out_data[0] = <void *>result
        return cpu.CPU_CB_EVENT
    else:
      return cpu.CPU_CB_NO_EVENT
  except:
    exc_info = sys.exc_info()
    Py_INCREF(exc_info)
    out_data[0] = <void *>exc_info
    return cpu.CPU_CB_ERROR

cdef int mem_special_adapter_r(int access, uint32_t addr, uint32_t *val, void *pfunc, void **out_data):
  try:
    if pfunc != NULL:
      f = <object>pfunc
      pair = f(access, addr)
      if type(pair) is tuple:
        val[0] = pair[0]
        result = pair[1]
        if result is None:
          return cpu.CPU_CB_NO_EVENT
        else:
          Py_INCREF(result)
          out_data[0] = <void *>result
          return cpu.CPU_CB_EVENT
      else:
        val[0] = pair
        return cpu.CPU_CB_NO_EVENT
    else:
      return cpu.CPU_CB_NO_EVENT
  except:
    exc_info = sys.exc_info()
    Py_INCREF(exc_info)
    out_data[0] = <void *>exc_info
    return cpu.CPU_CB_ERROR

def add_special(uint16_t start_page, uint16_t num_pages, read_func, write_func):
  cdef mem.special_entry_t *se
  cdef void *r_func = NULL
  cdef void *w_func = NULL

  if read_func is not None:
    Py_INCREF(read_func)
    r_func = <void *>read_func

  if write_func is not None:
    Py_INCREF(write_func)
    w_func = <void *>write_func

  se = mem.mem_add_special(start_page, num_pages,
                           mem_special_adapter_r, r_func,
                           mem_special_adapter_w, w_func)
  if se == NULL:
    raise ValueError("Invalid special: start=%d, num=%d" % (start_page, num_pages))
  return <uint32_t>(start_page << 16)

def set_invalid_value(uint32_t val):
  mem.mem_set_invalid_value(val)

def add_empty(uint16_t start_page, uint16_t num_pages, int flags, uint32_t value):
  cdef int res = mem.mem_add_empty(start_page, num_pages, flags, value)
  if res == -1:
    raise ValueError("Invalid empty: start=%d, num=%d" % (start_page, num_pages))
  return <uint32_t>(start_page << 16)

def add_mirror(uint16_t start_page, uint16_t num_pages, int flags, uint16_t base_page):
  cdef int res = mem.mem_add_mirror(start_page, num_pages, flags, base_page)
  if res == -1:
    raise ValueError("Invalid mirror: start=%d, num=%d, base=%d" % (start_page, num_pages, base_page))
  return <uint32_t>(start_page << 16)

# memory trace cpu

cdef object mem_cpu_trace_func = None

cdef int mem_cpu_trace_adapter(int flag, uint32_t addr, uint32_t val, void **data):
  global mem_cpu_trace_func
  try:
    result = mem_cpu_trace_func(flag, addr, val)
    if result is None:
      return cpu.CPU_CB_NO_EVENT
    else:
      Py_INCREF(result)
      data[0] = <void *>result
      return cpu.CPU_CB_EVENT
  except:
    exc_info = sys.exc_info()
    Py_INCREF(exc_info)
    data[0] = <void *>exc_info
    return cpu.CPU_CB_ERROR

cdef int mem_cpu_trace_adapter_str(int flag, uint32_t addr, uint32_t val, void **data):
  cdef str s
  global mem_cpu_trace_func
  try:
    v = (flag, addr, val)
    s = get_cpu_mem_str(flag, addr, val)
    result = mem_cpu_trace_func(s, v)
    if result is None:
      return cpu.CPU_CB_NO_EVENT
    else:
      Py_INCREF(result)
      data[0] = <void *>result
      return cpu.CPU_CB_EVENT
  except:
    exc_info = sys.exc_info()
    Py_INCREF(exc_info)
    data[0] = <void *>exc_info
    return cpu.CPU_CB_ERROR

def set_mem_cpu_trace_func(object cb=None, bool default=False, bool as_str=False):
  global mem_cpu_trace_func
  mem_cpu_trace_func = cb
  if default:
    mem.mem_set_cpu_trace_func(mem.mem_default_cpu_trace_func)
  elif cb is None:
    mem.mem_set_cpu_trace_func(NULL)
  elif as_str:
    mem.mem_set_cpu_trace_func(mem_cpu_trace_adapter_str)
  else:
    mem.mem_set_cpu_trace_func(mem_cpu_trace_adapter)

# memory trace api

cdef object mem_api_trace_func = None
cdef object mem_api_exc_info = None

cdef void mem_api_trace_adapter(int flag, uint32_t addr, uint32_t val, uint32_t extra):
  global mem_api_trace_func
  global mem_api_exc_info
  try:
    mem_api_trace_func(flag, addr, val, extra)
  except:
    mem_api_exc_info = sys.exc_info()

cdef void mem_api_trace_adapter_str(int flag, uint32_t addr, uint32_t val, uint32_t extra):
  cdef str s
  global mem_api_trace_func
  global mem_api_exc_info
  try:
    v = (flag, addr, val, extra)
    s = get_api_mem_str(flag, addr, val, extra)
    mem_api_trace_func(s, v)
  except:
    mem_api_exc_info = sys.exc_info()

def set_mem_api_trace_func(object cb=None, bool default=False, bool as_str=False):
  global mem_api_trace_func
  mem_api_trace_func = cb
  if default:
    mem.mem_set_api_trace_func(mem.mem_default_api_trace_func)
  elif cb is None:
    mem.mem_set_api_trace_func(NULL)
  elif as_str:
    mem.mem_set_api_trace_func(mem_api_trace_adapter_str)
  else:
    mem.mem_set_api_trace_func(mem_api_trace_adapter)

cdef _handle_api_exc():
  global mem_api_exc_info
  if mem_api_exc_info is not None:
    ex = mem_api_exc_info
    mem_api_exc_info = None
    raise ex[0], ex[1], ex[2]

# block access

def set_block(uint32_t addr, uint32_t size, uint8_t value):
  cdef int res = mem.mem_set_block(addr, size, value)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()

def copy_block(uint32_t src_addr, uint32_t tgt_addr, uint32_t size):
  cdef int res = mem.mem_copy_block(src_addr, tgt_addr, size)
  if res == 0:
    raise ValueError("Invalid address $%08x/$%08x" % (src_addr, tgt_addr))
  else:
    _handle_api_exc()

def r_block(uint32_t addr, uint32_t size):
  cdef const uint8_t *data = mem.mem_r_block(addr, size)
  if data == NULL:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()
    return <bytes>data[:size]

def w_block(uint32_t addr, bytes data):
  cdef uint32_t size = len(data)
  cdef uint8_t *raw = data
  cdef int res = mem.mem_w_block(addr, size, raw)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()

# special access

def r_cstr(uint32_t addr):
  cdef uint32_t length
  cdef const uint8_t *cstr = mem.mem_r_cstr(addr, &length)
  if cstr == NULL:
    raise ValueError("Invalid cstr at $%08x" % addr)
  else:
    _handle_api_exc()
    return <bytes>cstr[:length]

def w_cstr(uint32_t addr, bytes pstr):
  cdef uint32_t length = len(pstr)
  cdef uint8_t *cstr = pstr
  cdef int res = mem.mem_w_cstr(addr, cstr, length)
  if res == 0:
    raise ValueError("Invalid cstr at $%08x" % addr)
  else:
    _handle_api_exc()

def r_bstr(uint32_t addr):
  cdef uint32_t length
  cdef const uint8_t *cstr = mem.mem_r_bstr(addr, &length)
  if cstr == NULL:
    raise ValueError("Invalid bstr at $%08x" % addr)
  else:
    _handle_api_exc()
    return <bytes>cstr[:length]

def w_bstr(uint32_t addr, bytes pstr):
  cdef uint32_t length = len(pstr)
  cdef uint8_t *cstr = pstr
  cdef int res = mem.mem_w_bstr(addr, cstr, length)
  if res == 0:
    raise ValueError("Invalid bstr at $%08x" % addr)
  else:
    _handle_api_exc()

def wb32(uint32_t addr, uint32_t val):
  cdef int res = mem.mem_wb32(addr, val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()

def rb32(uint32_t addr):
  cdef uint32_t val
  cdef int res = mem.mem_rb32(addr, &val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()
    return val

# common read/write

def w8(uint32_t addr, uint8_t val):
  cdef int res = mem.mem_w8(addr, val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()

def w16(uint32_t addr, uint16_t val):
  cdef int res = mem.mem_w16(addr, val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()

def w32(uint32_t addr, uint32_t val):
  cdef int res = mem.mem_w32(addr, val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()

def r8(uint32_t addr):
  cdef uint8_t val
  cdef int res = mem.mem_r8(addr, &val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()
    return val

def r16(uint32_t addr):
  cdef uint16_t val
  cdef int res = mem.mem_r16(addr, &val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()
    return val

def r32(uint32_t addr):
  cdef uint32_t val
  cdef int res = mem.mem_r32(addr, &val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()
    return val

# signed data access

def ws8(uint32_t addr, int8_t val):
  cdef uint8_t uval = <uint8_t>val
  cdef int res = mem.mem_w8(addr, uval)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()

def ws16(uint32_t addr, int16_t val):
  cdef uint16_t uval = <uint16_t>val
  cdef int res = mem.mem_w16(addr, uval)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()

def ws32(uint32_t addr, int32_t val):
  cdef uint32_t uval = <uint32_t>val
  cdef int res = mem.mem_w32(addr, uval)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()

def rs8(uint32_t addr):
  cdef uint8_t val
  cdef int8_t sval
  cdef int res = mem.mem_r8(addr, &val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()
    sval = <int8_t>val
    return sval

def rs16(uint32_t addr):
  cdef uint16_t val
  cdef int16_t sval
  cdef int res = mem.mem_r16(addr, &val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()
    sval = <int16_t>val
    return sval

def rs32(uint32_t addr):
  cdef uint32_t val
  cdef int res = mem.mem_r32(addr, &val)
  if res == 0:
    raise ValueError("Invalid address $%08x" % addr)
  else:
    _handle_api_exc()
    sval = <int32_t>val
    return sval

# CPU reads/writes with side effects (only useful for testing purposes!)

def cpu_w8(uint32_t addr, uint8_t val):
  mem.m68k_write_memory_8(addr, val)

def cpu_w16(uint32_t addr, uint16_t val):
  mem.m68k_write_memory_16(addr, val)

def cpu_w32(uint32_t addr, uint32_t val):
  mem.m68k_write_memory_32(addr, val)

def cpu_r8(uint32_t addr):
  return mem.m68k_read_memory_8(addr)

def cpu_r16(uint32_t addr):
  return mem.m68k_read_memory_16(addr)

def cpu_r32(uint32_t addr):
  return mem.m68k_read_memory_32(addr)

# dump tools

def get_cpu_fc_str(int access):
  cdef const char *s = mem.mem_get_cpu_fc_str(access)
  return <str>s[:2]

def get_cpu_access_str(int access):
  cdef const char *s = mem.mem_get_cpu_access_str(access)
  return <str>s[:6]

cpdef get_cpu_mem_str(int access, uint32_t address, uint32_t value):
  cdef const char *s = mem.mem_get_cpu_mem_str(access, address, value)
  return <str>s[:26]

def get_api_access_str(int access):
  cdef const char *s = mem.mem_get_api_access_str(access)
  return <str>s[:6]

cpdef get_api_mem_str(int access, uint32_t address, uint32_t value, uint32_t extra):
  cdef int size
  cdef const char *s = mem.mem_get_api_mem_str(access, address, value, extra, &size)
  return <str>s[:size]
