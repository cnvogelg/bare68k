# label.pyx

# custom types

cdef class Label:
  cdef label.label_entry_t *entry

  @staticmethod
  cdef create(label.label_entry_t *e):
    l = Label()
    l.entry = e
    return l

  def addr(Label self):
    return self.entry.addr

  def end(Label self):
    return self.entry.end

  def size(Label self):
    return self.entry.size

  def data(Label self):
    return <object>self.entry.data

  def __repr__(Label self):
    return "Label[@%08x+%08x,%08x,%s]" % \
      (self.entry.addr, self.entry.size, self.entry.end, <object>self.entry.data)

  def __richcmp__(Label self, Label other, int op):
    if op == 2: # __eq__
      return self.entry == other.entry
    else:
      err_msg = "op {0} isn't implemented yet".format(op)
      raise NotImplementedError(err_msg)

# helper funcs

cdef void cleanup_label(label.label_entry_t *entry):
  if entry.data != NULL:
    pydata = <object>entry.data
    Py_DECREF(pydata)

# API funcs

def get_num_labels():
  return label.label_get_num_labels()

def get_num_page_labels(uint32_t page):
  return label.label_get_num_page_labels(page)

def get_all_labels():
  cdef label.label_entry_t **result
  cdef label.uint res_size
  result = label.label_get_all(&res_size)
  if result == NULL:
    return None
  cdef label.uint i
  res = []
  for i in range(res_size):
    res.append(Label.create(result[i]))
  free(result)
  return res

def get_page_labels(uint32_t page):
  cdef label.label_entry_t **result
  cdef label.uint res_size
  result = label.label_get_for_page(page, &res_size)
  if result == NULL:
    return None
  cdef label.uint i
  res = []
  for i in range(res_size):
    res.append(Label.create(result[i]))
  free(result)
  return res

def add_label(uint32_t addr, uint32_t size, data):
  cdef label.label_entry_t *e
  cdef void *cdata = NULL

  if data is not None:
    Py_INCREF(data)
    cdata = <void *>data

  e = label.label_add(addr, size, cdata)
  if e == NULL:
    raise MemoryError("no label memory!")

  return Label.create(e)

def remove_label(Label l):
  if l is None:
    raise ValueError("no label given!")
  cdef label.label_entry_t *entry = l.entry
  if entry != NULL:
    if label.label_remove(entry) == 0:
      raise ValueError("can't remove label!")

def remove_labels_inside(uint32_t addr, uint32_t size):
  return label.label_remove_inside(addr, size)

def find_label(uint32_t addr):
  cdef label.label_entry_t *e
  e = label.label_find(addr)
  if e == NULL:
    return None
  else:
    return Label.create(e)

def find_intersecting_labels(uint32_t addr, uint32_t size):
  cdef label.label_entry_t **result
  cdef label.uint res_size
  result = label.label_find_intersecting(addr, size, &res_size)
  if result == NULL:
    return None
  cdef label.uint i
  res = []
  for i in range(res_size):
    res.append(Label.create(result[i]))
  free(result)
  return res
