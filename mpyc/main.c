// a512c: AREA512's on-device .py -> .mpy compile, on the PC.
//
// usage: a512c <in.py> <out.mpy> [source-name]
//   Mirrors compile_python_source_to_bytecode() in AREA512's
//   components/area512_micropython/area512_micropython_python_file.c: same
//   lexer/parse/compile calls, arch_flags 0, mp_raw_code_save. The output loads
//   on the device (header M/6/0/31) and is what Filer's `R` runs as main.mpy.
//   source-name (default: in.py's basename) is stored in the .mpy for
//   tracebacks; the device stores the path it compiled from.
//   Exit 0 ok, 1 compile error (exception text on stderr), 2 I/O.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "port/micropython_embed.h"
#include "py/compile.h"
#include "py/persistentcode.h"
#include "py/runtime.h"
#include "py/stackctrl.h"

static char heap[256 * 1024];

static void write_bytes(void *env, const char *str, size_t len) {
  if (fwrite(str, 1, len, (FILE *)env) != len) exit(2);
}

static void print_stderr(void *env, const char *str, size_t len) {
  (void)env;
  fwrite(str, 1, len, stderr);
}

int main(int argc, char **argv) {
  if (argc != 3 && argc != 4) { fprintf(stderr, "usage: a512c <in.py> <out.mpy> [source-name]\n"); return 2; }
  const char *src_name = argc == 4 ? argv[3] : strrchr(argv[1], '/') ? strrchr(argv[1], '/') + 1 : argv[1];
  FILE *f = fopen(argv[1], "rb");
  if (!f) { fprintf(stderr, "cannot read %s\n", argv[1]); return 2; }
  fseek(f, 0, SEEK_END);
  long n = ftell(f);
  fseek(f, 0, SEEK_SET);
  char *src = malloc((size_t)n + 1);
  if (fread(src, 1, (size_t)n, f) != (size_t)n) return 2;
  src[n] = '\0';
  fclose(f);

  int stack_top;
  mp_embed_init(heap, sizeof(heap), &stack_top);
  mp_dynamic_compiler.small_int_bits = 31;  // ESP32-S3: 32-bit mp_int_t
  mp_dynamic_compiler.native_arch = MP_NATIVE_ARCH_NONE;

  // Written to memory first so a compile error never leaves a partial .mpy.
  char *buf = NULL;
  size_t buf_len = 0;
  FILE *mem = open_memstream(&buf, &buf_len);
  mp_print_t out = {mem, write_bytes};
  mp_print_t err = {NULL, print_stderr};

  nlr_buf_t nlr;
  if (nlr_push(&nlr) != 0) {
    mp_obj_print_exception(&err, (mp_obj_t)nlr.ret_val);
    return 1;
  }
  qstr name = qstr_from_str(src_name);
  mp_lexer_t *lex = mp_lexer_new_from_str_len(name, src, (size_t)n, 0);
  mp_parse_tree_t tree = mp_parse(lex, MP_PARSE_FILE_INPUT);
  mp_compiled_module_t cm;
  cm.context = m_new_obj(mp_module_context_t);
  cm.arch_flags = 0;
  mp_compile_to_raw_code(&tree, name, false, &cm);
  mp_raw_code_save(&cm, &out);
  nlr_pop();
  fclose(mem);

  FILE *o = fopen(argv[2], "wb");
  if (!o || fwrite(buf, 1, buf_len, o) != buf_len || fclose(o) != 0) {
    fprintf(stderr, "cannot write %s\n", argv[2]);
    return 2;
  }
  mp_embed_deinit();
  return 0;
}

size_t gc_get_max_new_split(void) {
  return 0;
}
