/* MusashiCPU <-> vamos memory interface
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#ifndef _MEM_H
#define _MEM_H

#include "m68k.h"
#include "cpu.h"
#include <stdint.h>

/* ------ Types ----- */
#ifndef UINT_TYPE
#define UINT_TYPE
typedef unsigned int uint;
#endif

#define MEM_PAGE_SIZE 0x10000
#define MEM_PAGE_MASK 0x0ffff
#define MEM_PAGE_SHIFT 16

#define MEM_FLAGS_READ    1
#define MEM_FLAGS_WRITE   2
#define MEM_FLAGS_TRAPS   4

/* Use Bits 0,1,2 to signal 8, 16, 32 bit access.
   Bit 4 is set for read operations.
   Bit 5 is set for write operations.
*/
#define MEM_ACCESS_READ    0x10
#define MEM_ACCESS_WRITE   0x20
#define MEM_ACCESS_WIDTH   0x0f

#define MEM_ACCESS_R8      0x11
#define MEM_ACCESS_R16     0x12
#define MEM_ACCESS_R32     0x14
#define MEM_ACCESS_W8      0x21
#define MEM_ACCESS_W16     0x22
#define MEM_ACCESS_W32     0x24

#define MEM_ACCESS_MASK    0xff

/* cpu access flag also holds function code */
#define MEM_FC_MASK        0xff00
#define MEM_FC_USER_DATA   0x1100
#define MEM_FC_USER_PROG   0x1200
#define MEM_FC_SUPER_DATA  0x2100
#define MEM_FC_SUPER_PROG  0x2200
#define MEM_FC_INT_ACK     0x4000
#define MEM_FC_INVALID     0x8000
/* masks */
#define MEM_FC_DATA_MASK   0x0100
#define MEM_FC_PROG_MASK   0x0200
#define MEM_FC_USER_MASK   0x1000
#define MEM_FC_SUPER_MASK  0x2000
#define MEM_FC_INT_MASK    0x4000

/* special mem access for API trace */
#define MEM_ACCESS_SPECIAL 0xff00
#define MEM_ACCESS_SREAD   0x0100
#define MEM_ACCESS_SWRITE  0x0200
#define MEM_ACCESS_EXTRA   0x0400
#define MEM_ACCESS_TYPE    0xf000

#define MEM_ACCESS_R_BLOCK 0x1100
#define MEM_ACCESS_W_BLOCK 0x1200
#define MEM_ACCESS_R_CSTR  0x2100
#define MEM_ACCESS_W_CSTR  0x2200
#define MEM_ACCESS_R_BSTR  0x3100
#define MEM_ACCESS_W_BSTR  0x3200
#define MEM_ACCESS_R_B32   0x4100
#define MEM_ACCESS_W_B32   0x4200
#define MEM_ACCESS_BSET    0x5400
#define MEM_ACCESS_BCOPY   0x6400

#define MEM_ACCESS_BLOCK   0x1000
#define MEM_ACCESS_CSTR    0x2000
#define MEM_ACCESS_BSTR    0x3000
#define MEM_ACCESS_B32     0x4000

typedef struct memory_entry
{
  struct memory_entry *next;
  uint     start_page;
  uint     num_pages;
  int      flags;
  uint32_t byte_size;
  uint8_t  *data;
} memory_entry_t;

struct page_entry;
struct special_entry;

typedef uint32_t (*read_func_t)(struct page_entry *page, uint32_t addr);
typedef void (*write_func_t)(struct page_entry *page, uint32_t addr, uint32_t value);
typedef int (*special_read_func_t)(int access, uint32_t addr, uint32_t *val, void *in_data, void **out_data);
typedef int (*special_write_func_t)(int access, uint32_t addr, uint32_t val, void *in_data, void **out_data);
typedef void (*special_cleanup_func_t)(struct special_entry *);
typedef int (*cpu_trace_func_t)(int access, uint32_t addr, uint32_t val, void **data);
typedef void (*api_trace_func_t)(int access, uint32_t addr, uint32_t val, uint32_t extra);

typedef struct special_entry {
  struct special_entry *next;
  special_read_func_t   r_func;
  special_write_func_t  w_func;
  void                 *r_data;
  void                 *w_data;
} special_entry_t;

typedef struct page_entry {
  read_func_t    r_func[3];
  write_func_t   w_func[3];
  memory_entry_t *memory_entry;
  special_entry_t *special_entry;
  uint8_t        *data; /* if memory then pointer to mem of this page */
  uint32_t       byte_left; /* if memory then remaining bytes */
} page_entry_t;


/* ----- API ----- */
extern int  mem_init(uint num_pages);
extern void mem_free(void);

extern uint mem_get_page_shift(void);
extern uint mem_get_num_pages(void);

extern void mem_set_invalid_value(uint32_t value);

extern memory_entry_t *mem_add_memory(uint start_page, uint num_pages, int flags);

extern void mem_set_special_cleanup(special_cleanup_func_t f);
extern special_entry_t *mem_add_special(uint start_page, uint num_pages,
                           special_read_func_t read_func, void *read_data,
                           special_write_func_t write_func, void *write_data);

extern int mem_add_empty(uint start_page, uint num_pages, int flags, uint32_t value);
extern int mem_add_mirror(uint start_page, uint num_pages, int flags, uint base_page);

extern void mem_set_cpu_trace_func(cpu_trace_func_t func);
extern void mem_set_api_trace_func(api_trace_func_t func);

extern int mem_default_cpu_trace_func(int access, uint32_t addr, uint32_t val, void **data);
extern void mem_default_api_trace_func(int access, uint32_t addr, uint32_t val, uint32_t extra);

extern uint8_t *mem_get_range(uint32_t address, uint32_t size);
extern uint8_t *mem_get_max_range(uint32_t address, uint32_t *size);

extern int mem_get_memory_flags(uint32_t address);

extern int mem_set_block(uint32_t address, uint32_t size, uint8_t value);
extern int mem_copy_block(uint32_t src_addr, uint32_t tgt_addr, uint32_t size);
extern const uint8_t *mem_r_block(uint32_t address, uint32_t size);
extern int mem_w_block(uint32_t address, uint32_t size, const uint8_t *src_data);

extern const char *mem_get_cpu_access_str(int access);
extern const char *mem_get_cpu_fc_str(int access);
extern const char *mem_get_cpu_mem_str(int access, uint32_t address, uint32_t value);
extern const char *mem_get_api_access_str(int access);
extern const char *mem_get_api_mem_str(int access, uint32_t address, uint32_t value, uint32_t extra, int *ret_size);

extern int mem_r8(uint32_t address, uint8_t *value);
extern int mem_r16(uint32_t address, uint16_t *value);
extern int mem_r32(uint32_t address, uint32_t *value);

extern int mem_w8(uint32_t address, uint8_t value);
extern int mem_w16(uint32_t address, uint16_t value);
extern int mem_w32(uint32_t address, uint32_t value);

/* special access */
extern const uint8_t *mem_r_cstr(uint32_t address, uint32_t *length);
extern int mem_w_cstr(uint32_t address, const uint8_t *str, uint32_t length);

extern const uint8_t *mem_r_bstr(uint32_t address, uint32_t *length);
extern int mem_w_bstr(uint32_t address, const uint8_t *str, uint32_t length);

extern int mem_rb32(uint32_t address, uint32_t *value);
extern int mem_wb32(uint32_t address, uint32_t value);

/* support disassembling a buffer */
extern void mem_disasm_buffer(const uint8_t *buf, uint32_t size, uint32_t offset);
extern void mem_disasm_memory(void);

/* ----- Musashi Binding ----- */
extern uint m68k_read_memory_8(uint address);
extern uint m68k_read_memory_16(uint address);
extern uint m68k_read_memory_32(uint address);

extern void m68k_write_memory_8(uint address, uint value);
extern void m68k_write_memory_16(uint address, uint value);
extern void m68k_write_memory_32(uint address, uint value);

extern uint m68k_read_disassembler_16(uint address);
extern uint m68k_read_disassembler_32(uint address);

#endif
