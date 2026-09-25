// a512sim: runs an AREA512 MicroPython app on a PC, under the same MicroPython
// version and ROM level as the device. AREA512's hardware API is mocked in
// Python (prelude.py, generated from AREA512's .pyi stubs).
//
// usage: a512sim <prelude.py> <keys-file> <heap-kb> <file.py>...
//   Files are compiled first (all of them), then executed in order into one
//   shared globals dict -- the same as AREA512's main.manifest loader.
//
// Output protocol (stdout, one line each, parsed by factory.py):
//   @@COMPILE_ERROR <file>     followed by the exception text
//   @@RUNTIME_ERROR <file>     followed by the exception text
//   @@HEAP ...                 heap sizing, informational
//   @@STATS / @@SCREEN         frames run, keys used, last frame's text
//   @@EXIT <reason>            ok | keys_exhausted | error
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "port/micropython_embed.h"
#include "py/compile.h"
#include "py/gc.h"
#include "py/lexer.h"
#include "py/runtime.h"
#include "py/stackctrl.h"

static char *read_file(const char *path) {
  FILE *f = fopen(path, "rb");
  if (!f) return NULL;
  fseek(f, 0, SEEK_END);
  long n = ftell(f);
  fseek(f, 0, SEEK_SET);
  char *buf = malloc((size_t)n + 1);
  if (fread(buf, 1, (size_t)n, f) != (size_t)n) { fclose(f); free(buf); return NULL; }
  buf[n] = '\0';
  fclose(f);
  return buf;
}

// Compile one source file into a callable module function. MP_OBJ_NULL on error.
static mp_obj_t compile_file(const char *path, const char *src) {
  nlr_buf_t nlr;
  if (nlr_push(&nlr) == 0) {
    qstr name = qstr_from_str(path);
    mp_lexer_t *lex = mp_lexer_new_from_str_len(name, src, strlen(src), 0);
    mp_parse_tree_t tree = mp_parse(lex, MP_PARSE_FILE_INPUT);
    mp_obj_t fun = mp_compile(&tree, name, false);
    nlr_pop();
    return fun;
  }
  printf("@@COMPILE_ERROR %s\n", path);
  mp_obj_print_exception(&mp_plat_print, (mp_obj_t)nlr.ret_val);
  return MP_OBJ_NULL;
}

// Returns 0 ok, 1 the prelude's _SimDone ended the run, -1 error.
static int run(const char *path, mp_obj_t fun) {
  nlr_buf_t nlr;
  if (nlr_push(&nlr) == 0) {
    mp_call_function_0(fun);
    nlr_pop();
    return 0;
  }
  mp_obj_t exc = (mp_obj_t)nlr.ret_val;
  // Looked up without raising: we are outside any nlr handler here.
  mp_map_elem_t *done = mp_map_lookup(&mp_globals_get()->map,
                                      MP_OBJ_NEW_QSTR(qstr_from_str("_SimDone")),
                                      MP_MAP_LOOKUP);
  if (done && mp_obj_is_subclass_fast(MP_OBJ_FROM_PTR(mp_obj_get_type(exc)), done->value))
    return 1;
  printf("@@RUNTIME_ERROR %s\n", path);
  mp_obj_print_exception(&mp_plat_print, exc);
  return -1;
}

// Run the prelude in chunks (split at "#@@CHUNK" lines) so compiling it never
// needs more than a small transient heap. Returns 0 on success.
static int run_prelude(const char *path, char *text) {
  char *p = text;
  while (p && *p) {
    char *next = strstr(p, "#@@CHUNK");
    if (next) *next = '\0';
    mp_obj_t fun = compile_file(path, p);
    if (fun == MP_OBJ_NULL || run(path, fun) != 0) return -1;
    if (next) { *next = '#'; p = next + 8; } else p = NULL;
    gc_collect();
  }
  return 0;
}

static void set_keys(const char *keys) {
  mp_store_global(qstr_from_str("_sim_keys"),
                  mp_obj_new_str(keys ? keys : "", keys ? strlen(keys) : 0));
}

int main(int argc, char **argv) {
  if (argc < 5) {
    fprintf(stderr, "usage: a512sim <prelude.py> <keys-file> <heap-kb> <file.py>...\n");
    return 2;
  }
  char *prelude = read_file(argv[1]);
  if (!prelude) { fprintf(stderr, "cannot read %s\n", argv[1]); return 2; }
  char *keys = read_file(argv[2]);
  int stack_top;

  // Pass 1: measure what the mocks occupy once loaded, so the app's heap
  // budget (argv[3]) is not eaten by the simulator's own objects.
  size_t probe_size = 1024 * 1024;
  void *probe = malloc(probe_size);
  mp_embed_init(probe, probe_size, &stack_top);
  mp_stack_set_limit(24 * 1024);
  set_keys("");
  if (run_prelude(argv[1], prelude) != 0) { fprintf(stderr, "prelude failed\n"); return 2; }
  gc_collect();
  gc_info_t info;
  gc_info(&info);
  size_t prelude_resident = info.used;
  mp_embed_deinit();
  free(probe);

  size_t app_heap = (size_t)atoi(argv[3]) * 1024;
  size_t heap_size = prelude_resident + app_heap;
  void *heap = malloc(heap_size);
  mp_embed_init(heap, heap_size, &stack_top);
  mp_stack_set_limit(24 * 1024);
  set_keys(keys);
  free(keys);
  if (run_prelude(argv[1], prelude) != 0) { fprintf(stderr, "prelude failed\n"); return 2; }
  gc_collect();
  printf("@@HEAP app_kb=%d prelude_bytes=%u\n", atoi(argv[3]), (unsigned)prelude_resident);

  int nfiles = argc - 4;
  mp_obj_t *funs = calloc((size_t)nfiles, sizeof(mp_obj_t));
  int compile_failed = 0;
  for (int i = 0; i < nfiles; i++) {
    char *src = read_file(argv[4 + i]);
    if (!src) { printf("@@COMPILE_ERROR %s\ncannot read file\n", argv[4 + i]); compile_failed = 1; continue; }
    funs[i] = compile_file(argv[4 + i], src);
    free(src);
    if (funs[i] == MP_OBJ_NULL) compile_failed = 1;
  }
  if (compile_failed) return 1;

  const char *exit_reason = "ok";
  int rc = 0;
  for (int i = 0; i < nfiles; i++) {
    int r = run(argv[4 + i], funs[i]);
    if (r < 0) { exit_reason = "error"; rc = 1; break; }
    if (r > 0) { exit_reason = "keys_exhausted"; break; }
  }
  mp_embed_exec_str("_sim_stats()");
  printf("@@EXIT %s\n", exit_reason);
  if (rc) return rc;
  gc_sweep_all();
  mp_embed_deinit();
  return 0;
}

// GC_SPLIT_HEAP_AUTO: the device grows the heap from whatever system RAM is
// left. The simulator does not grow at all, so a run that fits here fits in
// the initial heap -- a conservative (pessimistic) memory check.
size_t gc_get_max_new_split(void) {
  return 0;
}
