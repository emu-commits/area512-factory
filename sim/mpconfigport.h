#pragma once

#include <port/mpconfigport_common.h>

#define MICROPY_CONFIG_ROM_LEVEL (MICROPY_CONFIG_ROM_LEVEL_MINIMUM)
#define MICROPY_ENABLE_COMPILER (1)
#define MICROPY_ENABLE_FINALISER (1)
#define MICROPY_ENABLE_GC (1)
#define MICROPY_GCREGS_SETJMP (1)
#define MICROPY_GC_SPLIT_HEAP (1)
#define MICROPY_GC_SPLIT_HEAP_AUTO (1)
#define MICROPY_HELPER_REPL (1)
#define MICROPY_NLR_SETJMP (1)
#define MICROPY_PY_GC (1)
#define MICROPY_PY_SYS (0)

#define MICROPY_PERSISTENT_CODE_LOAD (1)
#define MICROPY_PERSISTENT_CODE_SAVE (1)

// ADC.read_voltage() returns ADC_read_voltage()'s picorb_float_t, which
// MRBC_USE_FLOAT=2 makes double; complex would come along for free otherwise.
#define MICROPY_FLOAT_IMPL (MICROPY_FLOAT_IMPL_DOUBLE)
#define MICROPY_PY_BUILTINS_COMPLEX (0)

// AREA512's hardware builtins (Sprite, Widget, IO, ...) are replaced in the
// simulator by Python mocks generated from AREA512's .pyi stubs (prelude.py).
// Everything above this line is copied verbatim from AREA512.

// Simulator-only diagnostics. These change error MESSAGES, not behaviour:
// the device runs with terse errors and no line numbers, which is useless for
// deciding what went wrong in a generated app.
#define MICROPY_ENABLE_SOURCE_LINE (1)
#define MICROPY_ERROR_REPORTING (MICROPY_ERROR_REPORTING_DETAILED)
// The device has no stack check (deep recursion hard-faults it); here it is
// reported as a RuntimeError instead, so the run can say so.
#define MICROPY_STACK_CHECK (1)
#include <stdlib.h>  // for MP_PLAT_ALLOC_HEAP
