/* Tools
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#include <stdlib.h>
#include <string.h>

#include "tools.h"
#include "cpu.h"

typedef struct {
  uint32_t *entries;
  int max;
  int offset;
  int num;
} pc_trace_t;

typedef struct {
  int enable;
  void *data;
} node_t;

typedef struct {
  node_t node;
  uint32_t addr;
  int flags;
} point_t;

typedef struct {
  node_t node;
  uint32_t interval;
  uint32_t elapsed;
} my_timer_t;

typedef struct {
  node_t *nodes;
  size_t node_size;
  int num;
  int max;
} array_t;

int tools_pc_trace_enabled;
static pc_trace_t pc_trace;

int tools_breakpoints_enabled;
static free_func_t breakpoints_free_func;
static array_t breakpoints;

int tools_watchpoints_enabled;
static free_func_t watchpoints_free_func;
static array_t watchpoints;

int tools_timers_enabled;
static free_func_t timers_free_func;
static array_t timers;

#define FLAG_ENABLE 1
#define FLAG_SETUP 2

void tools_init(void)
{
  tools_pc_trace_enabled = 0;
  tools_breakpoints_enabled = 0;
  tools_watchpoints_enabled = 0;
  tools_timers_enabled = 0;

  memset(&pc_trace, 0, sizeof(pc_trace_t));

  breakpoints_free_func = NULL;
  memset(&breakpoints, 0, sizeof(array_t));

  watchpoints_free_func = NULL;
  memset(&watchpoints, 0, sizeof(array_t));

  timers_free_func = NULL;
  memset(&timers, 0, sizeof(array_t));
}

void tools_free(void)
{
  tools_setup_pc_trace(0);
  tools_setup_breakpoints(0, NULL);
  tools_setup_watchpoints(0, NULL);
  tools_setup_timers(0, NULL);
}

/* ----- PC Trace ----- */

int tools_get_pc_trace_size(void)
{
  return pc_trace.max;
}

int tools_setup_pc_trace(int num)
{
  if(num < 0) {
    return -1;
  }

  /* cleanup old */
  if(pc_trace.entries != NULL) {
    free(pc_trace.entries);
    pc_trace.entries = NULL;
  }

  pc_trace.max = num;
  pc_trace.offset = 0;
  pc_trace.num = 0;

  tools_pc_trace_enabled = (num > 0);

  if(num > 0) {
    pc_trace.entries = (uint32_t *)malloc(sizeof(uint32_t) * num);
    if(pc_trace.entries == NULL) {
      return -1;
    }
  }
  return num;
}

uint32_t *tools_get_pc_trace(int *size)
{
  uint32_t *result;
  int i;
  int pos;
  int n = pc_trace.num;

  if(n == 0) {
    *size = 0;
    return NULL;
  }

  /* create result array */
  result = (uint32_t *)malloc(sizeof(uint32_t) * n);
  if(result == NULL) {
    *size = 0;
    return NULL;
  }

  /* copy values */
  pos = (pc_trace.offset + pc_trace.max - pc_trace.num) % pc_trace.max;
  for(i=0;i<n;i++) {
    result[i] = pc_trace.entries[pos];
    pos = (pos + 1) % pc_trace.max;
  }

  *size = n;
  return result;
}

void tools_free_pc_trace(uint32_t *data)
{
  free(data);
}

void tools_update_pc_trace(uint32_t pc)
{
  pc_trace_t *pt = &pc_trace;

  if(pt->entries != NULL) {
    pt->entries[pt->offset] = pc;
    pt->offset = (pt->offset + 1) % pt->max;
    if(pt->num < pt->max) {
      pt->num ++;
    }
  }
}

/* ----- Nodes ----- */

static int array_setup(array_t *a, int num, size_t node_size)
{
  if(num > 0) {
    size_t bytes = node_size * num;
    a->nodes = (node_t *)malloc(bytes);
    if(a->nodes == NULL) {
      return -1;
    }
    memset(a->nodes, 0, bytes);
  } else {
    a->nodes = NULL;
  }

  a->node_size = node_size;
  a->max = num;
  a->num = 0;
  return num;
}

static node_t *node_get(array_t *a, int id)
{
  if((id < 0) || (id >= a->max)) {
    return NULL;
  }
  return (node_t *)(((char *)a->nodes) + a->node_size * id);
}

static node_t *node_alloc(array_t *a, int id, void *data)
{
  node_t *n = node_get(a, id);
  if(n == NULL) {
    return NULL;
  }

  if((n->enable & FLAG_SETUP) == FLAG_SETUP) {
    return NULL;
  }

  a->num ++;

  n->enable = FLAG_SETUP | FLAG_ENABLE;
  n->data = data;

  return n;
}

static int node_free(array_t *a, int id, free_func_t free_func)
{
  node_t *n = node_get(a, id);
  if(n == NULL) {
    return -1;
  }

  if((n->enable & FLAG_SETUP) == 0) {
    return -1;
  }

  a->num --;

  n->enable = 0;

  if(n->data != NULL) {
    if(free_func != NULL) {
      free_func(n->data);
    }
    n->data = NULL;
  }

  return id;
}

static void array_cleanup(array_t *a, free_func_t free_func)
{
  if(a->nodes != NULL) {
    int i;

    for(i=0; i<a->max; i++) {
      node_t *n = node_get(a, i);
      if(n->data != NULL) {
        node_free(a, i, free_func);
      }
    }
  }

  a->max = 0;
  a->num = 0;
  a->nodes = NULL;
}

static int node_enable(array_t *a, int id)
{
  node_t *n = node_get(a, id);
  if(n == NULL) {
    return -1;
  }

  if((n->enable & FLAG_SETUP) == 0) {
    return -1;
  }

  n->enable |= FLAG_ENABLE;
  return id;
}

static int node_disable(array_t *a, int id)
{
  node_t *n = node_get(a, id);
  if(n == NULL) {
    return -1;
  }

  if((n->enable & FLAG_SETUP) == 0) {
    return -1;
  }

  n->enable &= ~FLAG_ENABLE;
  return id;
}

static int is_node_enabled(array_t *a, int id)
{
  node_t *n = node_get(a, id);
  if(n == NULL) {
    return -1;
  }

  if((n->enable & FLAG_ENABLE) == 0) {
    return 0;
  } else {
    return 1;
  }
}

static void *node_get_data(array_t *a, int id)
{
  node_t *n = node_get(a, id);
  if(n == NULL) {
    return NULL;
  }
  return n->data;
}

static int node_get_next_free(array_t *a)
{
  int i;
  for(i=0;i<a->max;i++) {
    node_t *n = node_get(a, i);
    if((n->enable & FLAG_SETUP) == 0) {
      return i;
    }
  }
  return -1;
}

/* ----- Points ------ */

static int point_alloc(array_t *a, int id, uint32_t addr, int flags, void *data)
{
  point_t *p = (point_t *)node_alloc(a, id, data);
  if(p == NULL) {
    return -1;
  }
  p->addr = addr;
  p->flags = flags;
  return id;
}

static int point_check(array_t *a, uint32_t addr, int flags)
{
  int i;

  for(i=0;i<a->max;i++) {
    point_t *p = (point_t *)node_get(a, i);
    if(p->node.enable == (FLAG_ENABLE | FLAG_SETUP)) {
      /* first check address */
      int p_addr = p->addr;
      if(p_addr == addr) {
        /* then check flags */
        int p_flags = p->flags;
        if((p_flags & flags) != 0) {
          return i;
        }
      }
    }
  }
  return NO_POINT;
}

/* ---- Breakpoints ----- */

int tools_get_num_breakpoints(void)
{
  return breakpoints.num;
}

int tools_get_max_breakpoints(void)
{
  return breakpoints.max;
}

int tools_get_next_free_breakpoint(void)
{
  return node_get_next_free(&breakpoints);
}

int tools_setup_breakpoints(int num, free_func_t free_func)
{
  if(num < 0) {
    return -1;
  }

  /* remove old */
  if(breakpoints.nodes != NULL) {
    array_cleanup(&breakpoints, breakpoints_free_func);
  }

  tools_breakpoints_enabled = (num > 0);
  breakpoints_free_func = free_func;

  if(num > 0) {
    return array_setup(&breakpoints, num, sizeof(point_t));
  } else {
    return 0;
  }
}

int tools_create_breakpoint(int id, uint32_t addr, int flags, void *data)
{
  return point_alloc(&breakpoints, id, addr, flags, data);
}

int tools_free_breakpoint(int id)
{
  return node_free(&breakpoints, id, breakpoints_free_func);
}

int tools_enable_breakpoint(int id)
{
  return node_enable(&breakpoints, id);
}

int tools_disable_breakpoint(int id)
{
  return node_disable(&breakpoints, id);
}

int tools_is_breakpoint_enabled(int id)
{
  return is_node_enabled(&breakpoints, id);
}

void *tools_get_breakpoint_data(int id)
{
  return node_get_data(&breakpoints, id);
}

int tools_check_breakpoint(uint32_t addr, int flags)
{
  return point_check(&breakpoints, addr, flags);
}

/* ---- Watchpoints ----- */

int tools_get_num_watchpoints(void)
{
  return watchpoints.num;
}

int tools_get_max_watchpoints(void)
{
  return watchpoints.max;
}

int tools_get_next_free_watchpoint(void)
{
  return node_get_next_free(&watchpoints);
}

int tools_setup_watchpoints(int num, free_func_t free_func)
{
  if(num < 0) {
    return -1;
  }

  /* remove old */
  if(watchpoints.nodes != NULL) {
    array_cleanup(&watchpoints, watchpoints_free_func);
  }

  tools_watchpoints_enabled = (num > 0);
  watchpoints_free_func = free_func;

  if(num > 0) {
    return array_setup(&watchpoints, num, sizeof(point_t));
  } else {
    return 0;
  }
}

int tools_create_watchpoint(int id, uint32_t addr, int flags, void *data)
{
  return point_alloc(&watchpoints, id, addr, flags, data);
}

int tools_free_watchpoint(int id)
{
  return node_free(&watchpoints, id, watchpoints_free_func);
}

int tools_enable_watchpoint(int id)
{
  return node_enable(&watchpoints, id);
}

int tools_disable_watchpoint(int id)
{
  return node_disable(&watchpoints, id);
}

int tools_is_watchpoint_enabled(int id)
{
  return is_node_enabled(&watchpoints, id);
}

void *tools_get_watchpoint_data(int id)
{
  return node_get_data(&watchpoints, id);
}

int tools_check_watchpoint(uint32_t addr, int flags)
{
  return point_check(&watchpoints, addr, flags);
}

/* ----- Timers ----- */

int tools_get_num_timers(void)
{
  return timers.num;
}

int tools_get_max_timers(void)
{
  return timers.max;
}

int tools_get_next_free_timer(void)
{
  return node_get_next_free(&timers);
}

int tools_setup_timers(int num, free_func_t free_func)
{
  if(num < 0) {
    return -1;
  }

  /* remove old */
  if(timers.nodes != NULL) {
    array_cleanup(&timers, timers_free_func);
  }

  tools_timers_enabled = (num > 0);
  timers_free_func = free_func;

  if(num > 0) {
    return array_setup(&timers, num, sizeof(my_timer_t));
  } else {
    return 0;
  }
}

int tools_create_timer(int id, uint32_t interval, void *data)
{
  my_timer_t *t = (my_timer_t *)node_alloc(&timers, id, data);
  if(t == NULL) {
    return -1;
  }
  t->interval = interval;
  t->elapsed = 0;
  return id;
}

int tools_free_timer(int id)
{
  return node_free(&timers, id, timers_free_func);
}

int tools_enable_timer(int id)
{
  return node_enable(&timers, id);
}

int tools_disable_timer(int id)
{
  return node_disable(&timers, id);
}

int tools_is_timer_enabled(int id)
{
  return is_node_enabled(&timers, id);
}

void *tools_get_timer_data(int id)
{
  return node_get_data(&timers, id);
}

int tools_tick_timers(uint32_t pc, uint32_t elapsed)
{
  int i;
  int num_events = 0;
  for(i=0;i<timers.max;i++) {
    my_timer_t *t = (my_timer_t *)node_get(&timers, i);
    /* is timer enabled */
    if(t->node.enable == (FLAG_ENABLE | FLAG_SETUP)) {
      t->elapsed += elapsed;
      while(t->elapsed >= t->interval) {
        t->elapsed -= t->interval;
        cpu_add_event(CPU_EVENT_TIMER, pc, i, t->elapsed, t->node.data);
        num_events++;
      }
    }
  }
  return num_events;
}
