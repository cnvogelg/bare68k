/* MusashiCPU <-> vamos memory interface
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mem.h"
#include "tools.h"

/* ----- Data ----- */

static page_entry_t *pages;
static uint total_pages;
static memory_entry_t *first_mem_entry;
static special_entry_t *first_special_entry;
static cpu_trace_func_t cpu_trace_func;
static api_trace_func_t api_trace_func;
static special_cleanup_func_t special_cleanup_func;

static uint32_t invalid_value = 0xffffffff;

static const uint8_t *disasm_buffer;
static uint32_t disasm_size;
static uint32_t disasm_offset;

/* ----- Event Helper ----- */
#define memory_access(access, addr, val) \
  cpu_add_event(CPU_EVENT_MEM_ACCESS, addr, val, access, NULL)

#define memory_bounds(access, addr, val) \
  cpu_add_event(CPU_EVENT_MEM_BOUNDS, addr, val, access, NULL)

#define trace_event(access, addr, val, data) \
  cpu_add_event(CPU_EVENT_MEM_TRACE, addr, val, access, data)

#define watchpoint_event(access, addr, val, data) \
  cpu_add_event(CPU_EVENT_WATCHPOINT, addr, val, access, data)

/* ----- Empty Range ----- */
static uint32_t r8_empty(struct page_entry *page, uint32_t addr)
{
  uint32_t value = page->byte_left;
  return value & 0xff;
}

static uint32_t r16_empty(struct page_entry *page, uint32_t addr)
{
  uint32_t value = page->byte_left;
  return value & 0xffff;
}

static uint32_t r32_empty(struct page_entry *page, uint32_t addr)
{
  uint32_t value = page->byte_left;
  return value;
}

static void wx_empty(page_entry_t *page, uint32_t addr, uint32_t val)
{
  /* ignore a write */
}

/* ----- Mirror Range ----- */
static uint32_t r8_mirror(struct page_entry *page, uint32_t addr)
{
  uint32_t mirror_page = page->byte_left;
  struct page_entry *mirror = &pages[mirror_page];
  read_func_t r_func = mirror->r_func[0];
  if(r_func != NULL) {
    return r_func(mirror, addr);
  } else {
    int access = MEM_ACCESS_R8 | cpu_current_fc;
    int value = invalid_value & 0xff;
    memory_access(access, addr, value);
    return value;
  }
}

static uint32_t r16_mirror(struct page_entry *page, uint32_t addr)
{
  uint32_t mirror_page = page->byte_left;
  struct page_entry *mirror = &pages[mirror_page];
  read_func_t r_func = mirror->r_func[1];
  if(r_func != NULL) {
    return r_func(mirror, addr);
  } else {
    int access = MEM_ACCESS_R16 | cpu_current_fc;
    int value = invalid_value & 0xffff;
    memory_access(access, addr, value);
    return value;
  }
}

static uint32_t r32_mirror(struct page_entry *page, uint32_t addr)
{
  uint32_t mirror_page = page->byte_left;
  struct page_entry *mirror = &pages[mirror_page];
  read_func_t r_func = mirror->r_func[2];
  if(r_func != NULL) {
    return r_func(mirror, addr);
  } else {
    int access = MEM_ACCESS_R32 | cpu_current_fc;
    int value = invalid_value;
    memory_access(access, addr, value);
    return value;
  }
}

static void w8_mirror(page_entry_t *page, uint32_t addr, uint32_t val)
{
  uint32_t mirror_page = page->byte_left;
  struct page_entry *mirror = &pages[mirror_page];
  write_func_t w_func = mirror->w_func[0];
  if(w_func != NULL) {
    w_func(mirror, addr, val);
  } else {
    int access = MEM_ACCESS_W8 | cpu_current_fc;
    memory_access(access, addr, val);
  }
}

static void w16_mirror(page_entry_t *page, uint32_t addr, uint32_t val)
{
  uint32_t mirror_page = page->byte_left;
  struct page_entry *mirror = &pages[mirror_page];
  write_func_t w_func = mirror->w_func[1];
  if(w_func != NULL) {
    w_func(mirror, addr, val);
  } else {
    int access = MEM_ACCESS_W16 | cpu_current_fc;
    memory_access(access, addr, val);
  }
}

static void w32_mirror(page_entry_t *page, uint32_t addr, uint32_t val)
{
  uint32_t mirror_page = page->byte_left;
  struct page_entry *mirror = &pages[mirror_page];
  write_func_t w_func = mirror->w_func[2];
  if(w_func != NULL) {
    w_func(mirror, addr, val);
  } else {
    int access = MEM_ACCESS_W32 | cpu_current_fc;
    memory_access(access, addr, val);
  }
}

/* ----- Special Access ----- */
static uint32_t r8_special(struct page_entry *page, uint32_t addr)
{
  uint32_t result = 0;
  void *out_data = NULL;
  special_entry_t *se = page->special_entry;
  int access = MEM_ACCESS_R8 | cpu_current_fc;
  int res = se->r_func(access, addr, &result, se->r_data, &out_data);
  if(res == CPU_CB_EVENT) {
    cpu_add_event(CPU_EVENT_MEM_SPECIAL, addr, result, access, out_data);
  }
  else if(res == CPU_CB_ERROR) {
    cpu_add_event(CPU_EVENT_CALLBACK_ERROR, addr, 0, 0, out_data);
  }
  return result;
}

static uint32_t r16_special(struct page_entry *page, uint32_t addr)
{
  uint32_t result = 0;
  void *out_data = NULL;
  special_entry_t *se = page->special_entry;
  int access = MEM_ACCESS_R16 | cpu_current_fc;
  int res = se->r_func(access, addr, &result, se->r_data, &out_data);
  if(res == CPU_CB_EVENT) {
    cpu_add_event(CPU_EVENT_MEM_SPECIAL, addr, result, access, out_data);
  }
  else if(res == CPU_CB_ERROR) {
    cpu_add_event(CPU_EVENT_CALLBACK_ERROR, addr, 0, 0, out_data);
  }
  return result;
}

static uint32_t r32_special(struct page_entry *page, uint32_t addr)
{
  uint32_t result = 0;
  void *out_data = NULL;
  special_entry_t *se = page->special_entry;
  int access = MEM_ACCESS_R32 | cpu_current_fc;
  int res = se->r_func(access, addr, &result, se->r_data, &out_data);
  if(res == CPU_CB_EVENT) {
    cpu_add_event(CPU_EVENT_MEM_SPECIAL, addr, result, access, out_data);
  }
  else if(res == CPU_CB_ERROR) {
    cpu_add_event(CPU_EVENT_CALLBACK_ERROR, addr, 0, 0, out_data);
  }
  return result;
}

static void w8_special(struct page_entry *page, uint32_t addr, uint32_t value)
{
  void *out_data = NULL;
  special_entry_t *se = page->special_entry;
  int access = MEM_ACCESS_W8 | cpu_current_fc;
  int res = se->w_func(access, addr, value, se->w_data, &out_data);
  if(res == CPU_CB_EVENT) {
    cpu_add_event(CPU_EVENT_MEM_SPECIAL, addr, value, access, out_data);
  }
  else if(res == CPU_CB_ERROR) {
    cpu_add_event(CPU_EVENT_CALLBACK_ERROR, addr, 0, 0, out_data);
  }
}

static void w16_special(struct page_entry *page, uint32_t addr, uint32_t value)
{
  void *out_data = NULL;
  special_entry_t *se = page->special_entry;
  int access = MEM_ACCESS_W16 | cpu_current_fc;
  int res = se->w_func(access, addr, value, se->w_data, &out_data);
  if(res == CPU_CB_EVENT) {
    cpu_add_event(CPU_EVENT_MEM_SPECIAL, addr, value, access, out_data);
  }
  else if(res == CPU_CB_ERROR) {
    cpu_add_event(CPU_EVENT_CALLBACK_ERROR, addr, 0, 0, out_data);
  }
}

static void w32_special(struct page_entry *page, uint32_t addr, uint32_t value)
{
  void *out_data = NULL;
  special_entry_t *se = page->special_entry;
  int access = MEM_ACCESS_W32 | cpu_current_fc;
  int res = se->w_func(access, addr, value, se->w_data, &out_data);
  if(res == CPU_CB_EVENT) {
    cpu_add_event(CPU_EVENT_MEM_SPECIAL, addr, value, access, out_data);
  }
  else if(res == CPU_CB_ERROR) {
    cpu_add_event(CPU_EVENT_CALLBACK_ERROR, addr, 0, 0, out_data);
  }
}

/* ----- RAM access ----- */

/* Read */
static uint32_t r8_mem(page_entry_t *page, uint32_t addr)
{
  uint8_t *data = page->data;
  uint32_t off = addr & MEM_PAGE_MASK;

  return data[off];
}

static uint32_t r16_mem(page_entry_t *page, uint32_t addr)
{
  uint8_t *data = page->data;
  uint32_t off = addr & MEM_PAGE_MASK;

  return (data[off] << 8) | data[off+1];
}

static uint32_t r32_mem(page_entry_t *page, uint32_t addr)
{
  uint8_t *data = page->data;
  uint32_t off = addr & MEM_PAGE_MASK;

  return (data[off] << 24) | (data[off+1] << 16) |
         (data[off+2] << 8) | (data[off+3]);
}

/* Write */
static void w8_mem(page_entry_t *page, uint32_t addr, uint32_t val)
{
  uint8_t *data = page->data;
  uint32_t off = addr & MEM_PAGE_MASK;

  data[off] = val;
}

static void w16_mem(page_entry_t *page, uint32_t addr, uint32_t val)
{
  uint8_t *data = page->data;
  uint32_t off = addr & MEM_PAGE_MASK;

  data[off] = val >> 8;
  data[off+1] = val & 0xff;
}

static void w32_mem(page_entry_t *page, uint32_t addr, uint32_t val)
{
  uint8_t *data = page->data;
  uint32_t off = addr & MEM_PAGE_MASK;

  data[off]   = val >> 24;
  data[off+1] = (val >> 16) & 0xff;
  data[off+2] = (val >> 8) & 0xff;
  data[off+3] = val & 0xff;
}

/* ---------- Musashi Binding ---------- */

/* m68k access helper macros */

#define TRACE_FUNC(the_value) \
  if(cpu_trace_func != NULL) { \
    void *data = NULL; \
    int res = cpu_trace_func(access, address, the_value, &data); \
    if(res==CPU_CB_EVENT) { \
      trace_event(access, address, the_value, data); \
    } \
    else if(res==CPU_CB_ERROR) { \
      cpu_add_event(CPU_EVENT_CALLBACK_ERROR, address, 0, 0, data); \
    } \
  }

#define WATCHPOINT_CHECK() \
  if(tools_watchpoints_enabled) { \
    int id = tools_check_watchpoint(address, access); \
    if(id != NO_POINT) { \
      void *data = tools_get_watchpoint_data(id); \
      watchpoint_event(access, address, id, data); \
    } \
  }

/* CPU Read */

uint m68k_read_memory_8(uint address)
{
  uint result = 0;
  uint page_no = address >> MEM_PAGE_SHIFT;
  int access = MEM_ACCESS_R8 | cpu_current_fc;
  if(page_no >= total_pages) {
    result = invalid_value & 0xff;
    memory_bounds(access, address, result);
  } else {
    page_entry_t *page = &pages[page_no];
    read_func_t rf = page->r_func[0];
    if(rf == NULL) {
      result = invalid_value & 0xff;
      memory_access(access, address, result);
    } else {
      result = rf(page, address);
    }
  }
  TRACE_FUNC(result)
  WATCHPOINT_CHECK()
  return result;
}

uint m68k_read_memory_16(uint address)
{
  uint result = 0;
  uint page_no = address >> MEM_PAGE_SHIFT;
  int access = MEM_ACCESS_R16 | cpu_current_fc;
  if(page_no >= total_pages) {
    result = invalid_value & 0xffff;
    memory_bounds(access, address, result);
  } else {
    page_entry_t *page = &pages[page_no];
    read_func_t rf = page->r_func[1];
    if(rf == NULL) {
      result = invalid_value & 0xffff;
      memory_access(access, address, result);
    } else {
      result = rf(page, address);
    }
  }
  TRACE_FUNC(result)
  WATCHPOINT_CHECK()
  return result;
}

uint m68k_read_memory_32(uint address)
{
  uint result = 0;
  uint page_no = address >> MEM_PAGE_SHIFT;
  int access = MEM_ACCESS_R32 | cpu_current_fc;
  if(page_no >= total_pages) {
    result = invalid_value;
    memory_bounds(access, address, result);
  } else {
    page_entry_t *page = &pages[page_no];
    read_func_t rf = page->r_func[2];
    if(rf == NULL) {
      result = invalid_value;
      memory_access(access, address, result);
    } else {
      result = rf(page, address);
    }
  }
  TRACE_FUNC(result)
  WATCHPOINT_CHECK()
  return result;
}

/* CPU Write */

void m68k_write_memory_8(uint address, uint value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  int access = MEM_ACCESS_W8 | cpu_current_fc;
  if(page_no >= total_pages) {
    memory_bounds(access, address, value);
  } else {
    page_entry_t *page = &pages[page_no];
    write_func_t wf = page->w_func[0];
    if(wf == NULL) {
      memory_access(access, address, value);
    } else {
      wf(page, address, value);
    }
  }
  TRACE_FUNC(value)
  WATCHPOINT_CHECK()
}

void m68k_write_memory_16(uint address, uint value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  int access = MEM_ACCESS_W16 | cpu_current_fc;
  if(page_no >= total_pages) {
    memory_bounds(access, address, value);
  } else {
    page_entry_t *page = &pages[page_no];
    write_func_t wf = page->w_func[1];
    if(wf == NULL) {
      memory_access(access, address, value);
    } else {
      wf(page, address, value);
    }
  }
  TRACE_FUNC(value)
  WATCHPOINT_CHECK()
}

void m68k_write_memory_32(uint address, uint value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  int access = MEM_ACCESS_W32 | cpu_current_fc;
  if(page_no >= total_pages) {
    memory_bounds(access, address, value);
  } else {
    page_entry_t *page = &pages[page_no];
    write_func_t wf = page->w_func[2];
    if(wf == NULL) {
      memory_access(access, address, value);
    } else {
      wf(page, address, value);
    }
  }
  TRACE_FUNC(value)
  WATCHPOINT_CHECK()
}

/* Disassemble */

uint m68k_read_disassembler_16(uint address)
{
  uint16_t val = 0;
  if(disasm_buffer == NULL) {
    mem_r16(address, &val);
  } else {
    if(address >= disasm_offset) {
      address -= disasm_offset;
      if(address <= (disasm_size-2)) {
        val = (disasm_buffer[address] << 8) | disasm_buffer[address+1];
      }
    }
  }
  return val;
}

uint m68k_read_disassembler_32(uint address)
{
  uint32_t val = 0;
  if(disasm_buffer == NULL) {
    mem_r32(address, &val);
  } else {
    if(address >= disasm_offset) {
      address -= disasm_offset;
      if(address <= (disasm_size-4)) {
        val = (disasm_buffer[address] << 24) | (disasm_buffer[address+1] << 16) |
              (disasm_buffer[address+2] << 8) | disasm_buffer[address+3];
      }
    }
  }
  return val;
}

void mem_disasm_buffer(const uint8_t *buf, uint32_t size, uint32_t offset)
{
  disasm_buffer = buf;
  disasm_size = size;
  disasm_offset = offset;
}

void mem_disasm_memory(void)
{
  disasm_buffer = NULL;
  disasm_size = 0;
  disasm_offset = 0;
}

/* ---------- API ---------- */

int mem_init(uint num_pages)
{
  /* allocate page entries */
  size_t bytes = sizeof(page_entry_t) * num_pages;
  pages = (page_entry_t *)malloc(bytes);
  if(pages == NULL) {
    return 0;
  }
  total_pages = num_pages;
  memset(pages, 0, bytes);

  mem_set_invalid_value(0xffffffff);
  return 1;
}

void mem_free(void)
{
  memory_entry_t *me;
  special_entry_t *se;

  /* free pages */
  if(pages != NULL) {
    free(pages);
  }
  total_pages = 0;

  /* free memory entries and associated memory */
  me = first_mem_entry;
  while(me != NULL) {
    memory_entry_t *next = me->next;
    free(me->data);
    free(me);
    me = next;
  }
  first_mem_entry = NULL;

  /* free special entries */
  se = first_special_entry;
  while(se != NULL) {
    special_entry_t *next = se->next;
    if(special_cleanup_func != NULL) {
      special_cleanup_func(se);
    }
    free(se);
    se = next;
  }
  first_special_entry = NULL;

  /* reset trace func */
  cpu_trace_func = NULL;
  api_trace_func = NULL;
}

uint mem_get_num_pages(void)
{
  return total_pages;
}

uint mem_get_page_shift(void)
{
  return MEM_PAGE_SHIFT;
}

void mem_set_invalid_value(uint32_t val)
{
  invalid_value = val;
}

memory_entry_t *mem_add_memory(uint start_page, uint num_pages, int flags)
{
  size_t byte_size;
  uint8_t *data;
  size_t me_size;
  memory_entry_t *me;
  page_entry_t *page;
  uint32_t offset;
  uint32_t remain;
  int i;

  /* check parameters */
  if((start_page + num_pages) > total_pages) {
    return NULL;
  }
  if(num_pages == 0) {
    return NULL;
  }

  /* alloc memory */
  byte_size = num_pages * MEM_PAGE_SIZE;
  data = (uint8_t *)malloc(byte_size);
  if(data == NULL) {
    return NULL;
  }

  /* clear memory */
  memset(data, 0, byte_size);

  /* first alloc mem entry */
  me_size = sizeof(memory_entry_t);
  me = (memory_entry_t *)malloc(me_size);
  if(me == NULL) {
    free(data);
    return NULL;
  }
  memset(me, 0, me_size);

  /* link to mem list */
  me->next = first_mem_entry;
  first_mem_entry = me;

  /* fill mem entry */
  me->start_page = start_page;
  me->num_pages = num_pages;
  me->data = data;
  me->byte_size = byte_size;
  me->flags = flags;

  /* fill in page entries */
  page = &pages[start_page];
  offset = 0;
  remain = byte_size;
  for(i=0;i<num_pages;i++) {
    /* setup read pointers */
    if((flags & MEM_FLAGS_READ) == MEM_FLAGS_READ) {
      page->r_func[0] = r8_mem;
      page->r_func[1] = r16_mem;
      page->r_func[2] = r32_mem;
    } else {
      page->r_func[0] = NULL;
      page->r_func[1] = NULL;
      page->r_func[2] = NULL;
    }

    /* setup write pointers */
    if((flags & MEM_FLAGS_WRITE) == MEM_FLAGS_WRITE) {
      page->w_func[0] = w8_mem;
      page->w_func[1] = w16_mem;
      page->w_func[2] = w32_mem;
    } else {
      page->w_func[0] = NULL;
      page->w_func[1] = NULL;
      page->w_func[2] = NULL;
    }

    page->memory_entry = me;
    page->special_entry = NULL;
    page->data = &data[offset];
    page->byte_left = remain;
    offset += MEM_PAGE_SIZE;
    remain -= MEM_PAGE_SIZE;

    page++;
  }

  return me;
}

extern void mem_set_special_cleanup(special_cleanup_func_t f)
{
  special_cleanup_func = f;
}

special_entry_t *mem_add_special(uint start_page, uint num_pages,
                    special_read_func_t read_func, void *read_data,
                    special_write_func_t write_func, void *write_data)
{
  size_t se_size;
  special_entry_t *se;
  page_entry_t *page;
  int i;

  /* check parameters */
  if((start_page + num_pages) > total_pages) {
    return NULL;
  }
  if(num_pages == 0) {
    return NULL;
  }

  /* first alloc special entry */
  se_size = sizeof(special_entry_t);
  se = (special_entry_t *)malloc(se_size);
  if(se == NULL) {
    return NULL;
  }
  memset(se, 0, se_size);

  /* link to mem list */
  se->next = first_special_entry;
  first_special_entry = se;

  /* fill special entry */
  se->r_func = read_func;
  se->r_data = read_data;
  se->w_func = write_func;
  se->w_data = write_data;

  /* setup pages */
  page = &pages[start_page];
  for(i=0;i<num_pages;i++) {
    /* setup read pointers */
    if(read_func != NULL) {
      page->r_func[0] = r8_special;
      page->r_func[1] = r16_special;
      page->r_func[2] = r32_special;
    } else {
      page->r_func[0] = NULL;
      page->r_func[1] = NULL;
      page->r_func[2] = NULL;
    }

    /* setup write pointers */
    if(write_func != NULL) {
      page->w_func[0] = w8_special;
      page->w_func[1] = w16_special;
      page->w_func[2] = w32_special;
    } else {
      page->w_func[0] = NULL;
      page->w_func[1] = NULL;
      page->w_func[2] = NULL;
    }

    page->data = NULL;
    page->byte_left = 0;
    page->memory_entry = NULL;
    page->special_entry = se;
    page++;
  }
  return se;
}

int mem_add_empty(uint start_page, uint num_pages, int flags, uint32_t value)
{
  page_entry_t *page;
  int i;

  /* check parameters */
  if((start_page + num_pages) > total_pages) {
    return 0;
  }
  if(num_pages == 0) {
    return 0;
  }

  /* setup pages */
  page = &pages[start_page];
  for(i=0;i<num_pages;i++) {
    /* setup read pointers */
    if((flags & MEM_FLAGS_READ) == MEM_FLAGS_READ) {
      page->r_func[0] = r8_empty;
      page->r_func[1] = r16_empty;
      page->r_func[2] = r32_empty;
    } else {
      page->r_func[0] = NULL;
      page->r_func[1] = NULL;
      page->r_func[2] = NULL;
    }

    /* setup write pointers */
    if((flags & MEM_FLAGS_WRITE) == MEM_FLAGS_WRITE) {
      page->w_func[0] = wx_empty;
      page->w_func[1] = wx_empty;
      page->w_func[2] = wx_empty;
    } else {
      page->w_func[0] = NULL;
      page->w_func[1] = NULL;
      page->w_func[2] = NULL;
    }

    page->data = NULL;
    page->byte_left = value;
    page->memory_entry = NULL;
    page->special_entry = NULL;
    page++;
  }
  return 1;
}

int mem_add_mirror(uint start_page, uint num_pages, int flags, uint base_page)
{
  page_entry_t *page;
  int i;

  /* check parameters */
  if((start_page + num_pages) > total_pages) {
    return 0;
  }
  if(num_pages == 0) {
    return 0;
  }
  if((base_page + num_pages) > total_pages) {
    return 0;
  }
  if(start_page == base_page) {
    return 0;
  }

  /* setup pages */
  page = &pages[start_page];
  for(i=0;i<num_pages;i++) {
    /* setup read pointers */
    if((flags & MEM_FLAGS_READ) == MEM_FLAGS_READ) {
      page->r_func[0] = r8_mirror;
      page->r_func[1] = r16_mirror;
      page->r_func[2] = r32_mirror;
    } else {
      page->r_func[0] = NULL;
      page->r_func[1] = NULL;
      page->r_func[2] = NULL;
    }

    /* setup write pointers */
    if((flags & MEM_FLAGS_WRITE) == MEM_FLAGS_WRITE) {
      page->w_func[0] = w8_mirror;
      page->w_func[1] = w16_mirror;
      page->w_func[2] = w32_mirror;
    } else {
      page->w_func[0] = NULL;
      page->w_func[1] = NULL;
      page->w_func[2] = NULL;
    }

    page->data = NULL;
    page->byte_left = base_page + i;
    page->memory_entry = NULL;
    page->special_entry = NULL;
    page++;
  }
  return 1;
}

void mem_set_cpu_trace_func(cpu_trace_func_t func)
{
  cpu_trace_func = func;
}

void mem_set_api_trace_func(api_trace_func_t func)
{
  api_trace_func = func;
}

uint8_t *mem_get_range(uint32_t address, uint32_t size)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return NULL;
  } else {
    page_entry_t *page = &pages[page_no];
    if(page->memory_entry != NULL) {
      /* check size */
      uint32_t offset = address & MEM_PAGE_MASK;
      uint32_t left = page->byte_left - offset;
      if(size <= left) {
        return page->data + offset;
      } else {
        return NULL;
      }
    } else {
      return NULL;
    }
  }
}

uint8_t *mem_get_max_range(uint32_t address, uint32_t *size)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return NULL;
  } else {
    page_entry_t *page = &pages[page_no];
    if(page->memory_entry != NULL) {
      uint32_t offset = address & MEM_PAGE_MASK;
      *size = page->byte_left - offset;
      return page->data + offset;
    } else {
      return NULL;
    }
  }
}

int mem_get_memory_flags(uint32_t address)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return 0;
  } else {
    page_entry_t *page = &pages[page_no];
    memory_entry_t *mem = page->memory_entry;
    if(mem != NULL) {
      return mem->flags;
    } else {
      return 0;
    }
  }
}

/* ----- API mem access ----- */

int mem_set_block(uint32_t address, uint32_t size, uint8_t value)
{
  uint8_t *data = mem_get_range(address, size);
  if(data == NULL) {
    return 0;
  }
  memset(data, value, size);
  if(api_trace_func != NULL) {
    api_trace_func(MEM_ACCESS_BSET, address, size, value);
  }
  return 1;
}

int mem_copy_block(uint32_t src_addr, uint32_t tgt_addr, uint32_t size)
{
  uint8_t *src_data = mem_get_range(src_addr, size);
  uint8_t *tgt_data = mem_get_range(tgt_addr, size);
  if((src_data == NULL)||(tgt_data == NULL)) {
    return 0;
  }
  memcpy(tgt_data, src_data, size);
  if(api_trace_func != NULL) {
    api_trace_func(MEM_ACCESS_BCOPY, tgt_addr, size, src_addr);
  }
  return 1;
}

const uint8_t *mem_r_block(uint32_t address, uint32_t size)
{
  uint8_t *data = mem_get_range(address, size);
  if((data != NULL) && (api_trace_func != NULL)) {
    api_trace_func(MEM_ACCESS_R_BLOCK, address, size, 0);
  }
  return data;
}

int mem_w_block(uint32_t address, uint32_t size, const uint8_t *src_data)
{
  uint8_t *tgt_data;

  if(src_data == NULL) {
    return 0;
  }
  tgt_data = mem_get_range(address, size);
  if(tgt_data == NULL) {
    return 0;
  }
  memcpy(tgt_data, src_data, size);
  if(api_trace_func != NULL) {
    api_trace_func(MEM_ACCESS_W_BLOCK, address, size, 0);
  }
  return 1;
}

const uint8_t *mem_r_cstr(uint32_t address, uint32_t *ret_length)
{
  uint32_t length;
  uint8_t *ptr;

  /* get max range in memory */
  uint32_t size;
  uint8_t *data = mem_get_max_range(address, &size);
  if(data == NULL) {
    return NULL;
  }
  /* make sure string fits in memory */
  length = 0;
  ptr = data;
  while(length < size) {
    if(*ptr == 0) {
      *ret_length = length;
      if(api_trace_func != NULL) {
        api_trace_func(MEM_ACCESS_R_CSTR, address, length, 0);
      }
      return data;
    }
    length++;
    ptr++;
  }
  return NULL;
}

int mem_w_cstr(uint32_t address, const uint8_t *str, uint32_t length)
{
  uint32_t size;
  uint8_t *data;

  if(str == NULL) {
    return 0;
  }
  /* get max memory range */
  data = mem_get_max_range(address, &size);
  if(data == NULL) {
    return 0;
  }
  /* does string fit */
  if((length+1) <= size) {
    memcpy(data, str, length);
    data[length] = '\0';
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_W_CSTR, address, length, 0);
    }
    return 1;
  } else {
    return 0;
  }
}

const uint8_t *mem_r_bstr(uint32_t address, uint32_t *ret_length)
{
  uint32_t length;

  uint32_t size;
  uint8_t *data = mem_get_max_range(address, &size);
  if(data == NULL) {
    return NULL;
  }
  if(size == 0) {
    return NULL;
  }
  length = *data;
  if((length+1) <= size) {
    *ret_length = length;
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_R_BSTR, address, length, 0);
    }
    return data+1;
  } else {
    return NULL;
  }
}

int mem_w_bstr(uint32_t address, const uint8_t *str, uint32_t length)
{
  uint32_t size;
  uint8_t *data;

  if(str == NULL) {
    return 0;
  }
  if(length > 255) {
    return 0;
  }
  /* get max range */
  data = mem_get_max_range(address, &size);
  if(data == NULL) {
    return 0;
  }
  if((length +1) <= size) {
    *data = (uint8_t)length;
    memcpy(data+1, str, length);
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_W_BSTR, address, length, 0);
    }
    return 1;
  } else {
    return 0;
  }
}

/* ----- RAM access from API ----- */

int mem_r8(uint32_t address, uint8_t *value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return 0;
  } else {
    page_entry_t *page = &pages[page_no];
    read_func_t func = page->r_func[0];
    if(func != NULL) {
      *value = (uint8_t)func(page, address);
    } else if(page->memory_entry != NULL) {
      *value = (uint8_t)r8_mem(page, address);
    } else {
      return 0;
    }
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_R8, address, *value, 0);
    }
    return 1;
  }
}

int mem_r16(uint32_t address, uint16_t *value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return 0;
  } else {
    page_entry_t *page = &pages[page_no];
    read_func_t func = page->r_func[1];
    if(func != NULL) {
      *value = (uint16_t)func(page, address);
    } else if(page->memory_entry != NULL) {
      *value = (uint16_t)r16_mem(page, address);
    } else {
      return 0;
    }
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_R16, address, *value, 0);
    }
    return 1;
  }
}

int mem_r32(uint32_t address, uint32_t *value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return 0;
  } else {
    page_entry_t *page = &pages[page_no];
    read_func_t func = page->r_func[2];
    if(func != NULL) {
      *value = func(page, address);
    } else if(page->memory_entry != NULL) {
      *value = r32_mem(page, address);
    } else {
      return 0;
    }
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_R32, address, *value, 0);
    }
    return 1;
  }
}

int mem_rb32(uint32_t address, uint32_t *value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return 0;
  } else {
    page_entry_t *page = &pages[page_no];
    read_func_t func = page->r_func[2];
    uint32_t v;
    if(func != NULL) {
      v = func(page, address);
    } else if(page->memory_entry != NULL) {
      v = r32_mem(page, address);
    } else {
      return 0;
    }
    *value = v << 2;
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_R_B32, address, *value, 0);
    }
    return 1;
  }
}

int mem_w8(uint32_t address, uint8_t value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return 0;
  } else {
    page_entry_t *page = &pages[page_no];
    write_func_t func = page->w_func[0];
    if(func != NULL) {
      func(page, address, value);
    } else if(page->memory_entry != NULL) {
      w8_mem(page, address, value);
    } else {
      return 0;
    }
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_W8, address, value, 0);
    }
    return 1;
  }
}

int mem_w16(uint32_t address, uint16_t value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return 0;
  } else {
    page_entry_t *page = &pages[page_no];
    write_func_t func = page->w_func[1];
    if(func != NULL) {
      func(page, address, value);
    } else if(page->memory_entry != NULL) {
      w16_mem(page, address, value);
    } else {
      return 0;
    }
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_W16, address, value, 0);
    }
    return 1;
  }
}

int mem_w32(uint32_t address, uint32_t value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return 0;
  } else {
    page_entry_t *page = &pages[page_no];
    write_func_t func = page->w_func[2];
    if(func != NULL) {
      func(page, address, value);
    } else if(page->memory_entry != NULL) {
      w32_mem(page, address, value);
    } else {
      return 0;
    }
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_W32, address, value, 0);
    }
    return 1;
  }
}

int mem_wb32(uint32_t address, uint32_t value)
{
  uint page_no = address >> MEM_PAGE_SHIFT;
  if(page_no >= total_pages) {
    return 0;
  } else {
    page_entry_t *page = &pages[page_no];
    write_func_t func = page->w_func[2];
    if(func != NULL) {
      func(page, address, value >> 2);
    } else if(page->memory_entry != NULL) {
      w32_mem(page, address, value >> 2);
    } else {
      return 0;
    }
    if(api_trace_func != NULL) {
      api_trace_func(MEM_ACCESS_W_B32, address, value, 0);
    }
    return 1;
  }
}

/* tools */

static char mem_str[] = "W32:UD @00000000: 00000000, 00000000";

const char *mem_get_cpu_mem_str(int access, uint32_t address, uint32_t value)
{
  mem_get_cpu_access_str(access);
  sprintf(&mem_str[6], " @%08x: %08x", address, value);
  return mem_str;
}

const char *mem_get_cpu_fc_str(int access)
{
  const char *ptr = mem_get_cpu_access_str(access);
  return ptr + 4;
}

const char *mem_get_cpu_access_str(int access)
{
  int width;
  int fc;
  char *s = mem_str;

  if((access & MEM_ACCESS_WRITE) == MEM_ACCESS_WRITE) {
    s[0] = 'W';
  }
  else if((access & MEM_ACCESS_READ) == MEM_ACCESS_READ) {
    s[0] = 'R';
  }

  width = access & MEM_ACCESS_WIDTH;
  if(width == 1) {
    s[1] = '0';
    s[2] = '8';
  }
  else if(width == 2) {
    s[1] = '1';
    s[2] = '6';
  }
  else if(width == 4) {
    s[1] = '3';
    s[2] = '2';
  }
  else {
    s[1] = '?';
    s[2] = '?';
  }

  s[3] = ':';

  fc = access & MEM_FC_MASK;
  switch(fc) {
    case MEM_FC_INT_ACK:
      s[4] = 'I';
      s[5] = 'A';
      break;
    case MEM_FC_USER_DATA:
      s[4] = 'U';
      s[5] = 'D';
      break;
    case MEM_FC_USER_PROG:
      s[4] = 'U';
      s[5] = 'P';
      break;
    case MEM_FC_SUPER_DATA:
      s[4] = 'S';
      s[5] = 'D';
      break;
    case MEM_FC_SUPER_PROG:
      s[4] = 'S';
      s[5] = 'P';
      break;
    default:
      s[4] = '?';
      s[5] = '?';
      break;
  }

  s[6] = '\0';
  return s;
}

int mem_default_cpu_trace_func(int access, uint32_t addr, uint32_t val, void **data)
{
  const char *str = mem_get_cpu_mem_str(access, addr, val);
  puts(str);
  return 1;
}

const char *mem_get_api_access_str(int access)
{
  char *s = mem_str;

  if((access & MEM_ACCESS_SPECIAL) != 0) {
    if(access == MEM_ACCESS_BSET) {
      sprintf(s, "bset  ");
    } else if(access == MEM_ACCESS_BCOPY) {
      sprintf(s, "bcopy ");
    } else {
      if((access & MEM_ACCESS_SWRITE) == MEM_ACCESS_SWRITE) {
        s[0] = 'w';
      } else {
        s[0] = 'r';
      }
      s++;
      access &= MEM_ACCESS_TYPE;
      switch(access) {
        case MEM_ACCESS_BLOCK:
          sprintf(s, "block");
          break;
        case MEM_ACCESS_CSTR:
          sprintf(s, "cstr ");
          break;
        case MEM_ACCESS_BSTR:
          sprintf(s, "bstr ");
          break;
        case MEM_ACCESS_B32:
          sprintf(s, "b32  ");
          break;
        default:
          sprintf(s, "??   ");
          break;
      }
    }
  } else {
    int width;

     if((access & MEM_ACCESS_WRITE) == MEM_ACCESS_WRITE) {
        s[0] = 'w';
      } else {
        s[0] = 'r';
      }

      width = access & MEM_ACCESS_WIDTH;
      if(width == 1) {
        s[1] = '0';
        s[2] = '8';
      }
      else if(width == 2) {
        s[1] = '1';
        s[2] = '6';
      }
      else if(width == 4) {
        s[1] = '3';
        s[2] = '2';
      }
      else {
        s[1] = '?';
        s[2] = '?';
      }
      sprintf(s+3, "   ");
  }

  return mem_str;
}

const char *mem_get_api_mem_str(int access, uint32_t address, uint32_t value, uint32_t extra, int *ret_size)
{
  mem_get_api_access_str(access);
  if((access & MEM_ACCESS_EXTRA) == MEM_ACCESS_EXTRA) {
    sprintf(&mem_str[6], " @%08x: %08x, %08x", address, value, extra);
    *ret_size = 36;
  } else {
    sprintf(&mem_str[6], " @%08x: %08x", address, value);
    *ret_size = 26;
  }
  return mem_str;
}

void mem_default_api_trace_func(int access, uint32_t addr, uint32_t val, uint32_t extra)
{
  int size;
  const char *s = mem_get_api_mem_str(access, addr, val, extra, &size);
  puts(s);
}
