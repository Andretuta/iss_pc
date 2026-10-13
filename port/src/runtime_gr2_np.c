/* Gravity Rush 2: PSN and network (NpToolkit, NpManager, Http, Ssl, Net) as an offline console.
 */
#define _GNU_SOURCE
#include "runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const RuntimeExport exports[]={
    {"__gr2_placeholder",NULL}, /* keeps the table non-empty until the first export */
};
uintptr_t runtime_gr2_np_resolve(const char *name) {
    return RUNTIME_LOOKUP(exports,name);
}
