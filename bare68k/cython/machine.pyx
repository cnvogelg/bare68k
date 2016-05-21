from libc.stdlib cimport malloc, free
from libc.stdint cimport uint64_t, uint32_t, uint16_t, uint8_t, int8_t, int16_t, int32_t
from cpython cimport Py_INCREF, Py_DECREF
from cpython cimport bool
from cpython.exc cimport PyErr_CheckSignals

cimport musashi
cimport cpu
cimport mem
cimport traps
cimport tools

import sys

cdef class Event:
  cdef readonly int ev_type
  cdef readonly int cycles
  cdef readonly uint32_t addr
  cdef readonly uint32_t value
  cdef readonly uint32_t flags
  cdef readonly object data
  cdef readonly object handler

  def __init__(self, int ev_type, uint32_t cycles, uint32_t addr,
               uint32_t value, uint32_t flags, object data, object handler):
    self.ev_type = ev_type
    self.cycles = cycles
    self.addr = addr
    self.value = value
    self.flags = flags
    self.data = data
    self.handler = handler

  def __repr__(self):
    return "Event[t=%d,cyc=%d,@$%08x,=$%08x,f=$%x,%s,%s]" % \
      (self.ev_type, self.cycles,
       self.addr, self.value, self.flags,
       self.data, self.handler)

event_handlers = [None] * cpu.CPU_NUM_EVENTS

cdef Event create_event(cpu.event_t *event):
  global event_handlers
  cdef int ev_type = event.type
  cdef object data = None
  # lookup handler
  cdef object handler = event_handlers[ev_type]

  # extract python object
  if event.data != NULL:
    data = <object>event.data

  return Event(ev_type, event.cycles,
               event.addr, event.value, event.flags,
               data, handler)

cdef void cleanup_event(cpu.event_t *event):
  cdef int ev_type = event.type
  cdef object data = None
  cdef int decref = 1

  if event.data != NULL:
    data = <object>event.data
    # non one-shot traps will be kept!
    if ev_type == cpu.CPU_EVENT_ALINE_TRAP and \
       event.flags & traps.TRAP_ONE_SHOT == 0:
        decref = 0
    if decref:
      Py_DECREF(data)


cdef class RunInfo:
  cdef readonly int num_events
  cdef readonly int lost_events
  cdef readonly uint32_t done_cycles
  cdef readonly uint64_t total_cycles
  cdef readonly list events

  def __init__(self, int num_events, int lost_events,
               uint32_t done_cycles, uint64_t total_cycles,
               list events):
    self.num_events = num_events
    self.lost_events = lost_events
    self.done_cycles = done_cycles
    self.total_cycles = total_cycles
    self.events = events

  def __repr__(self):
    return "RunInfo{ev:%d,lost:%d,cyc:%d,total:%d,%s}" % \
      (self.num_events, self.lost_events,
       self.done_cycles, self.total_cycles,
       self.events)

cdef RunInfo create_run_info(cpu.run_info_t *raw_info):
  cdef int n = raw_info.num_events
  cdef cpu.event_t *raw_ev
  cdef Event ev
  cdef list events = list()
  for i in range(n):
    raw_ev = &raw_info.events[i]
    ev = create_event(raw_ev)
    events.append(ev)
  return RunInfo(n, raw_info.lost_events,
                 raw_info.done_cycles, raw_info.total_cycles,
                 events)


cdef class CPUContext:
  cdef uint8_t *data
  cdef unsigned int size

  def __cinit__(self, unsigned int size):
    self.data = <uint8_t *>malloc(size)
    if self.data == NULL:
      raise MemoryError()
    self.size = size

  cdef uint8_t *get_data(self):
    return self.data

  def r_reg(self, int reg):
    return musashi.m68k_get_reg(<void *>self.data, <musashi.m68k_register_t>reg)

  def __dealloc__(self):
    free(self.data)


cdef class Registers:
  cdef cpu.registers_t registers

  def read(self):
    cpu.cpu_r_regs(&self.registers)

  def write(self):
    cpu.cpu_w_regs(&self.registers)

  def __repr__(self):
    return "\n".join(self.get_lines())

  def get_lines(self):
    cdef list lines = list()
    cdef const char **raw_lines = cpu.cpu_get_regs_str(&self.registers)
    cdef bytes line
    while raw_lines[0] != NULL:
      line = raw_lines[0]
      raw_lines += 1
      lines.append(line)
    return lines

  def r_dx(self, int idx):
    return self.registers.dx[idx]

  def r_ax(self, int idx):
    return self.registers.ax[idx]

  def r_pc(self):
    return self.registers.pc

  def r_sr(self):
    return self.registers.sr

  def w_dx(self, int idx, uint32_t val):
    self.registers.dx[idx] = val

  def w_ax(self, int idx, uint32_t val):
    self.registers.ax[idx] = val

  def w_pc(self, uint32_t val):
    self.registers.pc = val

  def w_sr(self, uint32_t val):
    self.registers.sr = val


# ----- API -----

def init(int cpu_type, int num_pages):
  cpu.cpu_init(cpu_type)
  mem.mem_init(num_pages)
  traps.traps_init()

  cpu.cpu_set_cleanup_event_func(cleanup_event)
  mem.mem_set_special_cleanup(mem_special_cleanup)

  # clear handlers
  global event_handlers
  for i in range(len(event_handlers)):
    event_handlers[i] = None

def shutdown():
  set_mem_cpu_trace_func(None)
  set_mem_api_trace_func(None)
  set_instr_hook_func(None)
  set_int_ack_func(None)
  set_irq(0)

  cpu.cpu_free()
  mem.mem_free()
  traps.traps_shutdown()

# cpu control

def pulse_reset():
  cpu.cpu_reset()

def execute(int num_cycles):
  return cpu.cpu_execute(num_cycles)

def execute_to_event(int cycles_per_run=0):
  return cpu.cpu_execute_to_event(cycles_per_run)

def execute_to_event_checked(int cycles_per_run=0):
  cdef int num_events = 0
  while num_events == 0:
    num_events = cpu.cpu_execute(cycles_per_run)
    PyErr_CheckSignals()
  return num_events

def get_info():
  cdef cpu.run_info_t *raw_info = cpu.cpu_get_info()
  return create_run_info(raw_info)

def get_num_events():
  cdef cpu.run_info_t *raw_info = cpu.cpu_get_info()
  return raw_info.num_events

def get_event(int idx):
  cdef cpu.run_info_t *raw_info = cpu.cpu_get_info()
  if idx < 0 or idx >= raw_info.num_events:
    raise IndexError("Invalid event index")
  return create_event(&raw_info.events[idx])

def get_done_cycles():
  cdef cpu.run_info_t *raw_info = cpu.cpu_get_info()
  return raw_info.done_cycles

def get_total_cycles():
  cdef cpu.run_info_t *raw_info = cpu.cpu_get_info()
  return raw_info.total_cycles

def clear_info():
  cpu.cpu_clear_info()

def disassemble(uint32_t pc):
  cdef char line[80]
  cdef unsigned int size
  size = musashi.m68k_disassemble(line, pc, cpu.cpu_get_type())
  return (size, line)

# irq

cdef object int_ack_func = None
cdef int int_ack_adapter(int level, uint32_t pc, uint32_t *ack_ret, void **data):
  global int_ack_func
  try:
    # cb returns tuple (int_num, data)
    pair = int_ack_func(level, pc)
    ack_ret[0] = pair[0]
    res = pair[1]
    if res is None:
      return cpu.CPU_CB_NO_EVENT
    else:
      Py_INCREF(res)
      data[0] = <void *>res
      return cpu.CPU_CB_EVENT
  except:
    exc_info = sys.exc_info()
    Py_INCREF(exc_info)
    data[0] = <void *>exc_info
    return cpu.CPU_CB_ERROR

def set_int_ack_func(object cb):
  global int_ack_func
  int_ack_func = cb
  if cb is not None:
    cpu.cpu_set_int_ack_func(int_ack_adapter)
  else:
    cpu.cpu_set_int_ack_func(NULL)

def set_irq(unsigned int level):
  cpu.cpu_set_irq(level)

# cpu pc trace

def setup_pc_trace(uint32_t pc):
  tools.tools_setup_pc_trace(pc)

def get_pc_trace():
  cdef uint32_t *data
  cdef int size
  cdef int i
  data = tools.tools_get_pc_trace(&size)
  if data == NULL:
    return None
  a = []
  for i in range(size):
    a.append(data[i])
  tools.tools_free_pc_trace(data)
  return a

# cpu context

def get_cpu_context():
  cdef unsigned int size = musashi.m68k_context_size()
  cdef CPUContext ctx = CPUContext(size)
  cdef uint8_t *data = ctx.get_data()
  musashi.m68k_get_context(data)
  return ctx

def set_cpu_context(CPUContext ctx):
  musashi.m68k_set_context(ctx.get_data())

# cpu access

def r_reg(int reg):
  return cpu.cpu_r_reg(reg)

def w_reg(int reg, uint32_t val):
  cpu.cpu_w_reg(reg, val)

def rs_reg(int reg):
  cdef int32_t signed_val = <int32_t>cpu.cpu_r_reg(reg)
  return signed_val

def ws_reg(int reg, int32_t val):
  cdef uint32_t unsigned_val = <uint32_t>val
  cpu.cpu_w_reg(reg, unsigned_val)

def r_dx(int reg):
  reg &= 0xf
  return cpu.cpu_r_reg(musashi.M68K_REG_D0 + reg)

def w_dx(int reg, uint32_t val):
  reg &= 0xf
  cpu.cpu_w_reg(musashi.M68K_REG_D0 + reg, val)

def r_ax(int reg):
  reg &= 0xf
  return cpu.cpu_r_reg(musashi.M68K_REG_A0 + reg)

def w_ax(int reg, uint32_t val):
  reg &= 0xf
  cpu.cpu_w_reg(musashi.M68K_REG_A0 + reg, val)

def r_pc():
  return cpu.cpu_r_reg(musashi.M68K_REG_PC)

def w_pc(uint32_t addr):
  cpu.cpu_w_reg(musashi.M68K_REG_PC, addr)

def r_sp():
  return cpu.cpu_r_reg(musashi.M68K_REG_SP)

def w_sp(uint32_t addr):
  cpu.cpu_w_reg(musashi.M68K_REG_SP, addr)

def r_sr():
  return cpu.cpu_r_reg(musashi.M68K_REG_SR)

def w_sr(uint32_t addr, uint32_t val):
  cpu.cpu_w_reg(musashi.M68K_REG_SR, val)

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
      val[0] = pair[0]
      result = pair[1]
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

# cpu trace

cdef object instr_hook_func

cdef int instr_hook_func_wrapper(uint32_t pc, void **data):
  global instr_hook_func
  try:
    result = instr_hook_func(pc)
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

cdef int instr_hook_func_str_wrapper(uint32_t pc, void **data):
  cdef bytes s
  global instr_hook_func
  try:
    s = get_instr_str(pc)
    result = instr_hook_func(s, pc)
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

def set_instr_hook_func(object cb=None, bool default=False, bool as_str=False):
  global instr_hook_func
  instr_hook_func = cb
  if default:
    cpu.cpu_set_instr_hook_func(cpu.cpu_default_instr_hook_func)
  elif cb is None:
    cpu.cpu_set_instr_hook_func(NULL)
  elif as_str:
    cpu.cpu_set_instr_hook_func(instr_hook_func_str_wrapper)
  else:
    cpu.cpu_set_instr_hook_func(instr_hook_func_wrapper)

# memory trace cpu

cdef object mem_cpu_trace_func = None

cdef int mem_cpu_trace_adapter(int flag, uint32_t addr, uint32_t val, void **data):
  global mem_cpu_trace_func
  try:
    result = mem_cpu_trace_func(flag, addr, val)
    if result is None:
      return 1
    else:
      Py_INCREF(result)
      data[0] = <void *>result
      return 0
  except:
    exc_info = sys.exc_info()
    Py_INCREF(exc_info)
    data[0] = <void *>exc_info
    return 0

cdef int mem_cpu_trace_adapter_str(int flag, uint32_t addr, uint32_t val, void **data):
  cdef bytes s
  global mem_cpu_trace_func
  try:
    v = (flag, addr, val)
    s = get_cpu_mem_str(flag, addr, val)
    result = mem_cpu_trace_func(s, v)
    if result is None:
      return 1
    else:
      Py_INCREF(result)
      data[0] = <void *>result
      return 0
  except:
    exc_info = sys.exc_info()
    Py_INCREF(exc_info)
    data[0] = <void *>exc_info
    return 0

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
  cdef bytes s
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
    return bytes(data[:size])

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
    return bytes(cstr[:length])

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
    return bytes(cstr[:length])

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

# traps

def trap_setup(int flags, object call not None):
  cdef uint16_t tid
  tid = traps.trap_setup(flags, <void *>call)
  if tid != traps.TRAP_INVALID:
    Py_INCREF(call)
    return tid
  else:
    raise MemoryError("no more traps!")

def trap_free(uint16_t tid):
  cdef void *data
  cdef object callable
  data = traps.trap_free(tid)
  Py_DECREF(<object>data)

def trap_enable(uint16_t tid):
  traps.trap_enable(tid)

def trap_disable(uint16_t tid):
  traps.trap_disable(tid)

def traps_get_num_free():
  return traps.traps_get_num_free()

def traps_global_enable():
  traps.traps_global_enable()

def traps_global_disable():
  traps.traps_global_disable()

# tools

def get_cpu_access_str(int access):
  cdef const char *s = mem.mem_get_cpu_access_str(access)
  return <bytes>s[:6]

cpdef get_cpu_mem_str(int access, uint32_t address, uint32_t value):
  cdef const char *s = mem.mem_get_cpu_mem_str(access, address, value)
  return <bytes>s[:26]

def get_api_access_str(int access):
  cdef const char *s = mem.mem_get_api_access_str(access)
  return <bytes>s[:6]

cpdef get_api_mem_str(int access, uint32_t address, uint32_t value, uint32_t extra):
  cdef int size
  cdef const char *s = mem.mem_get_api_mem_str(access, address, value, extra, &size)
  return <bytes>s[:size]

def get_sr_str(uint32_t sr):
  cdef const char *s = cpu.cpu_get_sr_str(sr)
  return <bytes>s[:16]

def get_regs():
  cdef Registers r = Registers()
  r.read()
  return r

cpdef get_instr_str(uint32_t pc):
  cdef const char *s = cpu.cpu_get_instr_str(pc)
  return <bytes>s
