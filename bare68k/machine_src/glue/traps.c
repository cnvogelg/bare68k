/* a dispatcher for a-line opcodes to be used as traps in vamos
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#include <string.h>

#include "traps.h"
#include "cpu.h"
#include "mem.h"
#include "m68k.h"

#define NUM_TRAPS  0x1000
#define TRAP_MASK  0x0fff

struct entry {
  void *data;
  struct entry *next;
  struct entry *prev;
  int flags;
};
typedef struct entry entry_t;

static entry_t traps[NUM_TRAPS];
static entry_t *first_free;
static int global_enable = 1;
static int num_free = 0;

static int trap_aline(uint opcode, uint pc)
{
  int mem_flags;
  uint off;
  int flags;
  void *data;

  /* global disable */
  if(!global_enable) {
    return M68K_ALINE_EXCEPT;
  }

  /* mem flags? */
  mem_flags = mem_get_memory_flags(pc);
  if((mem_flags & MEM_FLAGS_TRAPS) == 0) {
    return M68K_ALINE_EXCEPT;
  }

  off = opcode & TRAP_MASK;

  /* enabled? */
  flags = traps[off].flags;
  if((flags & TRAP_ENABLE) == 0) {
    return M68K_ALINE_EXCEPT;
  }

  /* process aline trap */
  data = traps[off].data;

  /* auto clean one shot trap */
  if(flags & TRAP_ONE_SHOT) {
    trap_free(off);
  }

  /* set event when cpu execute() returns */
  cpu_add_event(CPU_EVENT_ALINE_TRAP, pc, opcode, flags, data);

  if(flags & TRAP_AUTO_RTS) {
    return M68K_ALINE_RTS;
  } else {
    return M68K_ALINE_NONE;
  }
}

void traps_init(void)
{
  int i;

  /* setup free list */
  first_free = &traps[0];
  traps[0].next = &traps[1];
  traps[0].prev = NULL;
  traps[0].data = NULL;
  traps[0].flags = 0;
  for(i=1;i<(NUM_TRAPS-1);i++) {
    traps[i].next = &traps[i+1];
    traps[i].prev = &traps[i-1];
    traps[i].data = NULL;
    traps[i].flags = 0;
  }
  traps[NUM_TRAPS-1].next = NULL;
  traps[NUM_TRAPS-1].prev = &traps[NUM_TRAPS-2];
  traps[NUM_TRAPS-1].data = NULL;
  traps[NUM_TRAPS-1].flags = 0;
  num_free = NUM_TRAPS;

  /* setup my trap handler */
  m68k_set_aline_hook_callback(trap_aline);

  global_enable = 1;
}

int traps_get_num_free(void)
{
  return num_free;
}

int traps_shutdown(void)
{
  /* remove trap handler */
  m68k_set_aline_hook_callback(NULL);

  /* return non-freed traps */
  return NUM_TRAPS - traps_get_num_free();
}

uint16_t trap_setup(int flags, void *data)
{
  int id;

  /* no more traps available? */
  if(first_free == NULL) {
    return TRAP_INVALID;
  }

  id = (int)(first_free - traps);

  return trap_setup_abs(id, flags, data);
}

uint16_t trap_setup_abs(uint16_t id, int flags, void *data)
{
  /* allow both trap id and opcode */
  id &= TRAP_MASK;

  /* is given trap free? */
  if(traps[id].flags != 0) {
    return TRAP_INVALID;
  }

  /* was first free? */
  if(first_free == &traps[id]) {
    first_free = traps[id].next;
  }
  if(traps[id].next != NULL) {
    traps[id].next->prev = traps[id].prev;
  }
  if(traps[id].prev != NULL) {
    traps[id].prev->next = traps[id].next;
  }

  /* store trap data */
  traps[id].next = NULL;
  traps[id].prev = NULL;
  traps[id].data = data;
  traps[id].flags = flags | TRAP_SETUP | TRAP_ENABLE;

  num_free--;

  return id | 0xa000;
}

void *trap_free(uint16_t opcode)
{
  void *data;

  uint16_t id = opcode & TRAP_MASK;
  /* invalid trap */
  if(traps[id].flags == 0) {
    return NULL;
  }
  data = traps[id].data;
  /* insert trap into free list */
  traps[id].next = first_free;
  if(first_free != NULL) {
    first_free->prev = &traps[id];
  }
  first_free = &traps[id];
  /* cleanup data */
  traps[id].data = NULL;
  traps[id].flags = 0;

  num_free++;

  return data;
}

void trap_enable(uint16_t opcode)
{
  uint16_t id = opcode & TRAP_MASK;
  traps[id].flags |= TRAP_ENABLE;
}

void trap_disable(uint16_t opcode)
{
  uint16_t id = opcode & TRAP_MASK;
  traps[id].flags &= ~TRAP_ENABLE;
}

void traps_global_enable(void)
{
  global_enable = 1;
}

void traps_global_disable(void)
{
  global_enable = 0;
}
