/* Label
 *
 * manage memory labels attached to the pages
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#ifndef _LABEL_H
#define _LABEL_H

#include <stdint.h>

#ifndef UINT_TYPE
#define UINT_TYPE
typedef unsigned int uint;
#endif

struct label_node;

typedef struct label_entry
{
  uint                addr;
  uint                size;
  uint                end;
  void               *data;
  struct label_node  *node;
} label_entry_t;

typedef void (*label_cleanup_func_t)(label_entry_t *);

extern int  label_init(uint num_pages, uint page_shift);
extern void label_free(void);

extern int  label_get_num_labels(void);
extern int  label_get_num_page_labels(uint page);
extern label_entry_t **label_get_all(uint *res_num);
extern label_entry_t **label_get_for_page(uint page, uint *res_num);

extern void label_set_cleanup_func(label_cleanup_func_t func);

extern label_entry_t *label_add(uint addr, uint size, void *data);
extern int label_remove(label_entry_t *label);
extern int label_remove_inside(uint addr, uint size);

extern label_entry_t *label_find(uint addr);
extern label_entry_t **label_find_intersecting(uint addr, uint size, uint *res_offset);

#endif
