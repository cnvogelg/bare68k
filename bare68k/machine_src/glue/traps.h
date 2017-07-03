/* a dispatcher for a-line opcodes to be used as traps in vamos
 *
 * written by Christian Vogelgsang <chris@vogelgsang.org>
 * under the GNU Public License V2
 */

#ifndef _TRAPS_H
#define _TRAPS_H

#include "m68k.h"
#include <stdint.h>

#define TRAP_DEFAULT    0
#define TRAP_ONE_SHOT   1
#define TRAP_AUTO_RTS   2
#define TRAP_SETUP      4
#define TRAP_ENABLE     8

#define TRAP_INVALID    0xffff

/* ------ Types ----- */
#ifndef UINT_TYPE
#define UINT_TYPE
typedef unsigned int uint;
#endif

/* ----- API ----- */
extern void traps_init(void);
extern int traps_shutdown(void);

extern int traps_get_num_free(void);

extern uint16_t trap_setup(int flags, void *data);
extern uint16_t trap_setup_abs(uint16_t trap_num, int flags, void *data);
extern void *trap_free(uint16_t opcode);

extern void trap_enable(uint16_t opcode);
extern void trap_disable(uint16_t opcode);

extern void traps_global_enable(void);
extern void traps_global_disable(void);

#endif
