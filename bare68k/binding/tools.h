/* Tools
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#ifndef _TOOLS_H
#define _TOOLS_H

#include <stdint.h>

#define NO_POINT      -1

typedef void (*free_func_t)(void *data);

extern int tools_pc_trace_enabled;
extern int tools_breakpoints_enabled;

extern int tools_setup_pc_trace(int num);
extern int tools_get_pc_trace_size(void);
extern uint32_t *tools_get_pc_trace(int *size);
extern void tools_free_pc_trace(uint32_t *data);
extern void tools_update_pc_trace(uint32_t pc);

extern int tools_get_max_breakpoints(void);
extern int tools_get_num_breakpoints(void);
extern int tools_setup_breakpoints(int num, free_func_t free_func);
extern int tools_create_breakpoint(int id, uint32_t addr, int flags, void *data);
extern int tools_free_breakpoint(int id);
extern int tools_enable_breakpoint(int id);
extern int tools_disable_breakpoint(int id);
extern int tools_is_breakpoint_enabled(int id);
extern int tools_check_breakpoint(uint32_t addr, int flags);
extern void *tools_get_breakpoint_data(int id);

#endif