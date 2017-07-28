/* memory labels
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#include <string.h>
#include <stdlib.h>
#include <assert.h>

#include "label.h"

/* ----- types ----- */
struct label_list;

typedef struct label_node
{
  struct label_node  *next;
  struct label_node  *prev;
  struct label_node  *page_link;
  struct label_list  *list;
  label_entry_t      *entry;
} label_node_t;

typedef struct label_list
{
  label_node_t       *first;
  label_node_t       *last;
  uint                num_nodes;
} label_list_t;

/* ----- globals ----- */
static label_list_t *page_lists;
static uint page_shift;
static uint num_pages;
static label_cleanup_func_t cleanup_func;
static uint total_labels;

/* ----- list helpers ----- */
label_node_t *node_create(label_list_t *l, label_entry_t *e)
{
  label_node_t *n = (label_node_t *)malloc(sizeof(label_node_t));
  if(n == NULL) {
    return NULL;
  }

  /* double link entry and node - only store first node of node chain in entry */
  if(e->node == NULL) {
    e->node = n;
  }
  n->entry = e;
  /* no node chain since its a single node entry */
  n->page_link = NULL;
  n->list = l;
  n->prev = NULL;
  n->next = NULL;

  return n;
}

label_node_t *list_add_sorted(label_list_t *l, label_entry_t *e)
{
  label_node_t *n = node_create(l, e);
  if(n == NULL) {
    return NULL;
  }

  /* first entry? */
  if(l->first == NULL) {
    l->first = n;
    l->last = n;
    l->num_nodes = 1;
  }
  else {
    /* find existing node after this one */
    label_node_t *ln = l->first;
    while(ln != NULL) {
      if(ln->entry->addr > e->addr) {
        break;
      }
      ln = ln->next;
    }

    /* add to end */
    if(ln == NULL) {
      l->last->next = n;
      n->prev = l->last;
      l->last = n;
    }
    /* add to front */
    else if(ln->prev==NULL) {
      ln->prev = n;
      n->next = ln;
      l->first = n;
    }
    /* add in-between */
    else {
      n->next = ln;
      ln->prev->next = n;
      n->prev = ln->prev;
      ln->prev = n;
    }
    l->num_nodes++;
  }
  return n;
}

label_node_t *list_add_first(label_list_t *l, label_entry_t *e)
{
  label_node_t *n = node_create(l, e);
  if(n == NULL) {
    return NULL;
  }

  /* empty list? */
  if(l->first == NULL) {
    l->first = n;
    l->last = n;
    l->num_nodes = 1;
  }
  /* non-empty list */
  else {
    l->first->prev = n;
    n->next = l->first;
    l->first = n;
    l->num_nodes++;
  }
  return n;
}

void list_remove_node(label_list_t *l, label_node_t *n)
{
  assert(n->list == l);
  if(l->first == n) {
    l->first = n->next;
  }
  if(l->last == n) {
    l->last = n->prev;
  }
  if(n->prev != NULL) {
    n->prev->next = n->next;
  }
  if(n->next != NULL) {
    n->next->prev = n->prev;
  }
  l->num_nodes--;
}

/* ----- API ----- */
int label_init(uint np, uint ps)
{
  size_t num_bytes;

  num_pages = np;
  page_shift = ps;

  /* alloce list array */
  num_bytes = sizeof(label_list_t) * num_pages;
  page_lists = (label_list_t *)malloc(num_bytes);
  if(page_lists == NULL) {
    return 0;
  }
  memset(page_lists, 0, num_bytes);
  return 1;
}

void label_free(void)
{
  uint i;
  for(i=0;i<num_pages;i++) {
    label_list_t *list = &page_lists[i];
    label_node_t *node = list->first;
    while(node != NULL) {
      label_node_t *next = node->next;

      /* remove attached entry only at beginning of chain */
      if(node->page_link == NULL) {
        label_entry_t *entry = node->entry;
        if(entry != NULL) {
          if(cleanup_func != NULL) {
            cleanup_func(entry);
          }
          free(entry);
        }
      }

      free(node);
      node = next;
    }
  }
  free(page_lists);
  page_lists = NULL;
  total_labels = 0;
}

int label_get_num_labels(void)
{
  return total_labels;
}

int label_get_num_page_labels(uint page)
{
  label_list_t *list;

  if(page >= num_pages) {
    return 0;
  }
  list = &page_lists[page];
  return list->num_nodes;
}

label_entry_t **label_get_all(uint *res_num)
{
  label_entry_t **result;
  uint off = 0;
  uint i;

  if(total_labels == 0) {
    *res_num = 0;
    return NULL;
  }

  /* alloc array for label pointers */
  result = (label_entry_t **)malloc(sizeof(label_entry_t *) * total_labels);
  if(result == NULL) {
    *res_num = 0;
    return NULL;
  }

  /* run throug all label lists and visit all nodes.
     pick the last one in the node chains and store their entries */
  for(i=0;i<num_pages;i++) {
    label_list_t *list = &page_lists[i];
    label_node_t *node = list->first;
    while(node != NULL) {
      label_entry_t *entry = node->entry;
      /* only account first node(page_link==0) of this entry in the page chain */
      if((entry != NULL) && (node->page_link == NULL)) {
        result[off++] = entry;
      }
      node = node->next;
    }
  }

  assert(off == total_labels);

  *res_num = total_labels;
  return result;
}

label_entry_t **label_get_for_page(uint page, uint *res_num)
{
  label_list_t *list;
  uint n;
  uint off = 0;
  label_entry_t **result;
  label_node_t *node;

  if(page >= num_pages) {
    *res_num = 0;
    return NULL;
  }
  list = &page_lists[page];

  /* no entries in list? */
  n = list->num_nodes;
  if(n == 0) {
    *res_num = 0;
    return NULL;
  }

  /* create result array */
  result = (label_entry_t **)malloc(sizeof(label_entry_t *) * n);
  if(result == NULL) {
    *res_num = 0;
    return NULL;
  }

  /* fill result */
  node = list->first;
  while(node != NULL) {
    result[off++] = node->entry;
    node = node->next;
  }

  assert(off == n);

  *res_num = n;
  return result;
}

void label_set_cleanup_func(label_cleanup_func_t func)
{
  cleanup_func = func;
}

label_entry_t *label_add(uint addr, uint size, void *data)
{
  uint end;
  uint start_page;
  uint end_page;
  label_entry_t *entry;

  if(size == 0) {
    return NULL;
  }

  end = addr + size - 1;

  /* get page range the entry covers */
  start_page = addr >> page_shift;
  end_page = end >> page_shift;
  if(end_page >= num_pages) {
    return NULL;
  }

  /* create new entry */
  entry = (label_entry_t *)malloc(sizeof(label_entry_t));
  if(entry == NULL) {
    return NULL;
  }
  entry->addr = addr;
  entry->size = size;
  entry->end = end;
  entry->data = data;
  entry->node = NULL;

  if(start_page == end_page) {
    /* single page entry */
    label_list_t *list = &page_lists[start_page];
    label_node_t *n = list_add_sorted(list, entry);
    if(n != NULL) {
      entry->node = n;
      total_labels++;
      return entry;
    } else {
      free(entry);
      return NULL;
    }
  } else {
    label_node_t *last;
    /* multi page entry */
    uint page = start_page;
    /* first page node is added with sorting */
    label_list_t *list = &page_lists[page];
    label_node_t *n = list_add_sorted(list, entry);
    if(n == NULL) {
      free(entry);
      return NULL;
    }
    last = n;
    page++;
    /* other page nodes are added to front of list */
    while(page <= end_page) {
      list = &page_lists[page];
      n = list_add_first(list, entry);
      if(n==NULL) {
        label_remove(entry);
        return NULL;
      }
      /* node chain linking for this entry */
      n->page_link = last;
      last = n;
      page++;
    }
    /* store last node as begin of chain */
    entry->node = n;
    total_labels++;
    return entry;
  }
}

int label_remove(label_entry_t *label)
{
  label_node_t *node;

  if(label == NULL) {
    return 0;
  }

  /* get node chain of entry */
  node = label->node;
  while(node != NULL) {
    label_node_t *next_node;
    /* get associated list */
    label_list_t *list = node->list;
    assert(list != NULL);
    list_remove_node(list, node);
    next_node = node->page_link;
    free(node);
    node = next_node;
  }

  /* finally free entry */
  if(cleanup_func != NULL) {
    cleanup_func(label);
  }
  free(label);

  total_labels--;
  return 1;
}

int label_remove_inside(uint addr, uint size)
{
  uint end;
  uint start_page;
  uint end_page;
  uint num = 0;
  uint page;

  /* invalid size */
  if(size == 0) {
    return 0;
  }

  end = addr + size - 1;

  start_page = addr >> page_shift;
  end_page = addr >> page_shift;

  num = 0;
  for(page=start_page;page<=end_page;page++) {
    /* get page list */
    label_list_t *list = &page_lists[page];

    label_node_t *node = list->first;
    while(node != NULL) {
      label_node_t *next_node = node->next;

      label_entry_t *entry = node->entry;
      assert(entry != NULL);

      /* is entry inside? */
      if((entry->addr >= addr) && (entry->end <= end)) {
        label_remove(entry);
        num++;
      }

      node = next_node;
    }
  }

  return num;
}

label_entry_t *label_find(uint addr)
{
  label_list_t *list;
  label_node_t *node;

  uint page = addr >> page_shift;
  if(page >= num_pages) {
    return NULL;
  }

  /* get associated page label list */
  list = &page_lists[page];

  /* run through list */
  node = list->first;
  while(node != NULL) {
    uint e_end;
    label_entry_t *entry = node->entry;
    uint e_addr = entry->addr;

    /* label starts after given addr -> abort since list is sorted by addr */
    if(e_addr > addr) {
      break;
    }

    e_end = entry->end;

    /* addr inside label entry? gotcha! */
    if((e_addr <= addr) && (addr <= e_end)) {
      return entry;
    }

    node = node->next;
  }

  /* nothing found! */
  return NULL;
}

static uint count_intersects(uint page, uint addr, uint end)
{
   /* get associated page label list */
  label_list_t *list = &page_lists[page];

  uint num = 0;

  /* run through list */
  label_node_t *node = list->first;
  while(node != NULL) {
    /* only first entry in chain */
    if(node->page_link == NULL) {
      uint e_end;
      label_entry_t *entry = node->entry;
      uint e_addr = entry->addr;

      /* label starts after given addr -> abort since list is sorted by addr */
      if(e_addr > end) {
        break;
      }

      e_end = entry->end;

      /* does label intersect? */
      if((e_addr <= end) && (addr <= e_end)) {
        num++;
      }
    }
    node = node->next;
  }

  return num;
}

static int store_intersects(uint page, uint addr, uint end, label_entry_t **result)
{
   /* get associated page label list */
  label_list_t *list = &page_lists[page];

  uint num = 0;

  /* run through list */
  label_node_t *node = list->first;
  while(node != NULL) {
    /* only first entry in chain */
    if(node->page_link == NULL) {
      uint e_end;
      label_entry_t *entry = node->entry;
      uint e_addr = entry->addr;

      /* label starts after given addr -> abort since list is sorted by addr */
      if(e_addr > end) {
        break;
      }

      e_end = entry->end;

      /* does label intersect? */
      if((e_addr <= end) && (addr <= e_end)) {
        result[num++] = entry;
      }
    }
    node = node->next;
  }

  return num;
}

label_entry_t **label_find_intersecting(uint addr, uint size, uint *res_size)
{
  uint end;
  uint start_page;
  uint end_page;
  uint num = 0;
  uint page;
  label_entry_t **result;
  uint got = 0;

  if(size == 0) {
    *res_size = 0;
    return NULL;
  }

  end = addr + size - 1;
  start_page = addr >> page_shift;
  end_page = end >> page_shift;

  /* first count total intersects */
  for(page=start_page;page<=end_page;page++) {
    num += count_intersects(page, addr, end);
  }

  if(num == 0) {
    *res_size = 0;
    return NULL;
  }

  /* alloc result */
  result = (label_entry_t **)malloc(sizeof(label_entry_t *) * num);
  if(result == NULL) {
    *res_size = 0;
    return NULL;
  }

  /* finally store intersects */
  for(page=start_page;page<=end_page;page++) {
    got += store_intersects(page, addr, end, &result[got]);
  }

  assert(num == got);

  *res_size = num;
  return result;
}
