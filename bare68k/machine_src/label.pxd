# label.h
cdef extern from "glue/label.h":

  ctypedef unsigned int uint

  ctypedef struct label_entry_t:
    unsigned int      addr
    unsigned int      size
    unsigned int      end;
    void             *data
    void             *node

  ctypedef void (*label_cleanup_func_t)(label_entry_t *)

  int  label_init(uint num_pages, uint page_shift)
  void label_free()

  int  label_get_num_labels()
  int  label_get_num_page_labels(uint page)
  label_entry_t **label_get_all(uint *res_num)
  label_entry_t **label_get_for_page(uint page, uint *res_num)

  void label_set_cleanup_func(label_cleanup_func_t func)

  label_entry_t *label_add(uint addr, uint size, void *data)
  int label_remove(label_entry_t *label)
  int label_remove_inside(uint addr, uint size)

  label_entry_t *label_find(uint addr)
  label_entry_t **label_find_intersecting(uint addr, uint size, uint *res_offset)
