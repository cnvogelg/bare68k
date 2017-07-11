from libc.stdint cimport uint8_t, uint16_t, uint32_t

# mem.h
cdef extern from "glue/mem.h":
  ctypedef int (*cpu_trace_func_t)(int flag, uint32_t addr, uint32_t val, void **data)
  ctypedef void (*api_trace_func_t)(int flag, uint32_t addr, uint32_t val, uint32_t extra)
  ctypedef int (*special_read_func_t)(int access, uint32_t addr, uint32_t *val, void *in_data, void **out_data)
  ctypedef int (*special_write_func_t)(int access, uint32_t addr, uint32_t val, void *in_data, void **out_data)

  ctypedef struct memory_entry_t:
    memory_entry_t  *next
    unsigned int     start_page
    unsigned int     num_pages
    int              flags
    uint32_t         byte_size
    uint8_t         *data

  ctypedef struct special_entry_t:
    special_entry_t      *next
    special_read_func_t   r_func
    special_write_func_t  w_func
    void                 *r_data
    void                 *w_data

  ctypedef void (*special_cleanup_func_t)(special_entry_t *e)

  int  mem_init(unsigned int ram_size_kib)
  void mem_free()

  unsigned int mem_get_page_shift()
  unsigned int mem_get_num_pages()
  void mem_set_invalid_value(uint32_t value)

  memory_entry_t *mem_add_memory(unsigned int start_page, unsigned int num_pages, int flags)

  void mem_set_special_cleanup(special_cleanup_func_t f)
  special_entry_t *mem_add_special(unsigned int start_page, unsigned int num_pages,
                           special_read_func_t read_func, void *read_data,
                           special_write_func_t write_func, void *write_data)

  int mem_add_empty(unsigned int start_page, unsigned int num_pages, int flags, uint32_t value)
  int mem_add_mirror(unsigned int start_page, unsigned int num_pages, int flags, unsigned int base_page)

  void mem_set_cpu_trace_func(cpu_trace_func_t func)
  void mem_set_api_trace_func(api_trace_func_t func)

  int mem_default_cpu_trace_func(int access, uint32_t addr, uint32_t val, void **data)
  void mem_default_api_trace_func(int access, uint32_t addr, uint32_t val, uint32_t extra)

  const char *mem_get_cpu_fc_str(int access)
  const char *mem_get_cpu_access_str(int access)
  const char *mem_get_cpu_mem_str(int access, uint32_t address, uint32_t value)
  const char *mem_get_api_access_str(int access)
  const char *mem_get_api_mem_str(int access, uint32_t address, uint32_t value, uint32_t extra, int *ret_size)

  uint8_t *mem_get_range(uint32_t address, uint32_t size)
  uint8_t *mem_get_max_range(uint32_t address, uint32_t *size)

  int mem_set_block(uint32_t address, uint32_t size, uint8_t value)
  int mem_copy_block(uint32_t src_addr, uint32_t tgt_addr, uint32_t size)
  const uint8_t *mem_r_block(uint32_t address, uint32_t size)
  int mem_w_block(uint32_t address, uint32_t size, const uint8_t *src_data)

  const uint8_t *mem_r_cstr(uint32_t address, uint32_t *length)
  int mem_w_cstr(uint32_t address, const uint8_t *str, uint32_t length)

  const uint8_t *mem_r_bstr(uint32_t address, uint32_t *length)
  int mem_w_bstr(uint32_t address, const uint8_t *str, uint32_t length)

  int mem_rb32(uint32_t address, uint32_t *value)
  int mem_wb32(uint32_t address, uint32_t value)

  int mem_r8(uint32_t address, uint8_t *value)
  int mem_r16(uint32_t address, uint16_t *value)
  int mem_r32(uint32_t address, uint32_t *value)

  int mem_w8(uint32_t address, uint8_t value)
  int mem_w16(uint32_t address, uint16_t value)
  int mem_w32(uint32_t address, uint32_t value)

  void mem_disasm_buffer(const uint8_t *buf, uint32_t size, uint32_t offset)
  void mem_disasm_memory()

  unsigned int m68k_read_memory_8(unsigned int address)
  unsigned int m68k_read_memory_16(unsigned int address)
  unsigned int m68k_read_memory_32(unsigned int address)

  void m68k_write_memory_8(unsigned int address, unsigned int value)
  void m68k_write_memory_16(unsigned int address, unsigned int value)
  void m68k_write_memory_32(unsigned int address, unsigned int value)

  unsigned int m68k_read_disassembler_16(unsigned int address)
  unsigned int m68k_read_disassembler_32(unsigned int address)
