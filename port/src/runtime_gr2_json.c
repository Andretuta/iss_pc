/* Gravity Rush 2: libSceJson2 (sce::Json value/parser API).
 */
#define _GNU_SOURCE
#include "runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const RuntimeExport exports[]={
    {"__gr2_placeholder",NULL}, /* keeps the table non-empty until the first export */
};
uintptr_t runtime_gr2_json_resolve(const char *name) {
    return RUNTIME_LOOKUP(exports,name);
}
