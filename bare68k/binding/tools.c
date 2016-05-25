/* Tools
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#include <stdlib.h>
#include <strings.h>

#include "tools.h"

typedef struct {
  uint32_t *entries;
  int max;
  int offset;
  int num;
} pc_trace_t;

typedef struct {
  int enable;
  uint32_t addr;
  int flags;
  void *data;
} point_t;

typedef struct {
  point_t *points;
  int num;
  int max;
} point_array_t;

int tools_pc_trace_enabled;
static pc_trace_t pc_trace;

int tools_breakpoints_enabled;
static free_func_t breakpoints_free_func;
static point_array_t breakpoints;

#define FLAG_ENABLE 1
#define FLAG_SETUP 2

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
  int i;
  int pos = (pc_trace.offset + pc_trace.max - pc_trace.num) % pc_trace.max;
  int n = pc_trace.num;

  if(n == 0) {
    *size = 0;
    return NULL;
  }

  /* create result array */
  uint32_t *result = (uint32_t *)malloc(sizeof(uint32_t) * n);
  if(result == NULL) {
    *size = 0;
    return NULL;
  }

  /* copy values */
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

/* ----- Points ----- */

static int point_array_setup(point_array_t *a, int num)
{
  if(num > 0) {
    int bytes = sizeof(point_t) * num;
    a->points = (point_t *)malloc(bytes);
    if(a->points == NULL) {
      return -1;
    }
    bzero(a->points, bytes);
  } else {
    a->points = NULL;
  }

  a->max = num;
  a->num = 0;
  return num;
}

static int point_alloc(point_array_t *a, int id, uint32_t addr, int flags, void *data)
{
  point_t *p;

  if((id < 0) || (id >= a->max)) {
    return -1;
  }

  p = &a->points[id];

  if((p->enable & FLAG_SETUP) == FLAG_SETUP) {
    return -1;
  }

  a->num ++;

  p->enable = FLAG_SETUP | FLAG_ENABLE;
  p->addr = addr;
  p->flags = flags;
  p->data = data;

  return id;
}

static int point_free(point_array_t *a, int id, free_func_t free_func)
{
  point_t *p;

  if((id < 0) || (id >= a->max)) {
    return -1;
  }

  p = &a->points[id];

  if((p->enable & FLAG_SETUP) == 0) {
    return -1;
  }

  a->num --;

  p->enable = 0;
  p->addr = 0;
  p->flags = 0;

  if(p->data != NULL) {
    if(free_func != NULL) {
      free_func(p->data);
    }
    p->data = NULL;
  }

  return id;
}

static void point_array_cleanup(point_array_t *a, free_func_t free_func)
{
  if(a->points != NULL) {
    int i;

    for(i=0; i<a->max; i++) {
      point_t *p = &a->points[i];
      if(p->data != NULL) {
        point_free(a, i, free_func);
      }
    }
  }

  a->max = 0;
  a->num = 0;
  a->points = NULL;
}

static int point_enable(point_array_t *a, int id)
{
  point_t *p;

  if((id < 0) || (id >= a->max)) {
    return -1;
  }

  p = &a->points[id];
  if((p->enable & FLAG_SETUP) == 0) {
    return -1;
  }

  p->enable |= FLAG_ENABLE;
  return id;
}

static int point_disable(point_array_t *a, int id)
{
  point_t *p;

  if((id < 0) || (id >= a->max)) {
    return -1;
  }

  p = &a->points[id];
  if((p->enable & FLAG_SETUP) == 0) {
    return -1;
  }

  p->enable &= ~FLAG_ENABLE;
  return id;
}

static int is_point_enabled(point_array_t *a, int id)
{
  point_t *p;

  if((id < 0) || (id >= a->max)) {
    return -1;
  }

  p = &a->points[id];
  if((p->enable & FLAG_ENABLE) == 0) {
    return 0;
  } else {
    return 1;
  }
}

static int point_check(point_array_t *a, uint32_t addr, int flags)
{
  int i;

  for(i=0;i<a->max;i++) {
    point_t *p = &a->points[i];
    if(p->enable == (FLAG_ENABLE | FLAG_SETUP)) {
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

static void *point_get_data(point_array_t *a, int id)
{
  if((id < 0) || (id >= a->max)) {
    return NULL;
  }
  return a->points[id].data;
}

static int point_get_next_free(point_array_t *a)
{
  for(int i=0;i<a->max;i++) {
    point_t *p = &a->points[i];
    if((p->enable & FLAG_SETUP) == 0) {
      return i;
    }
  }
  return -1;
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
  return point_get_next_free(&breakpoints);
}

int tools_setup_breakpoints(int num, free_func_t free_func)
{
  if(num < 0) {
    return -1;
  }

  /* remove old */
  if(breakpoints.points != NULL) {
    point_array_cleanup(&breakpoints, breakpoints_free_func);
  }

  tools_breakpoints_enabled = (num > 0);
  breakpoints_free_func = free_func;

  if(num > 0) {
    return point_array_setup(&breakpoints, num);
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
  return point_free(&breakpoints, id, breakpoints_free_func);
}

int tools_enable_breakpoint(int id)
{
  return point_enable(&breakpoints, id);
}

int tools_disable_breakpoint(int id)
{
  return point_disable(&breakpoints, id);
}

int tools_is_breakpoint_enabled(int id)
{
  return is_point_enabled(&breakpoints, id);
}

int tools_check_breakpoint(uint32_t addr, int flags)
{
  return point_check(&breakpoints, addr, flags);
}

void *tools_get_breakpoint_data(int id)
{
  return point_get_data(&breakpoints, id);
}
