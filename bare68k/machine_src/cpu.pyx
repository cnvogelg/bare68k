# custom types

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

cdef Event create_event(cpu.event_t *event):
  cdef int ev_type = event.type
  cdef object data = None
  # lookup handler
  cdef object handler = get_event_handler(ev_type)

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
    elif ev_type == cpu.CPU_EVENT_BREAKPOINT:
      decref = 0
    elif ev_type == cpu.CPU_EVENT_WATCHPOINT:
      decref = 0
    elif ev_type == cpu.CPU_EVENT_TIMER:
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
    cdef str line
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

def get_type():
  return cpu.cpu_get_type()

# irq

cdef object int_ack_func = None
cdef int int_ack_adapter(int level, uint32_t pc, uint32_t *ack_ret, void **data):
  global int_ack_func
  try:
    # cb returns tuple (int_num, data) or int_num
    pair = int_ack_func(level, pc)
    if type(pair) is tuple:
      ack_ret[0] = pair[0]
      res = pair[1]
      if res is None:
        return cpu.CPU_CB_NO_EVENT
      else:
        Py_INCREF(res)
        data[0] = <void *>res
        return cpu.CPU_CB_EVENT
    else:
      res = pair
      return cpu.CPU_CB_NO_EVENT
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
  cdef str s
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

# dump tools

def get_sr_str(uint32_t sr):
  cdef const char *s = cpu.cpu_get_sr_str(sr)
  return <str>s[:16]

def get_regs():
  cdef Registers r = Registers()
  r.read()
  return r

cpdef get_instr_str(uint32_t pc):
  cdef const char *s = cpu.cpu_get_instr_str(pc)
  return <str>s
