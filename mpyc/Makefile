# a512c: compiles .py to .mpy exactly as AREA512 does on the device (Enter on a
# .py, or Filer's `c`): same MicroPython source, same mpconfigport.h, same
# mp_compile_to_raw_code + mp_raw_code_save call. Folder apps launched with `R`
# only look for main.mpy / main.manifest, so this is what the factory ships.
EMBED = micropython_embed
DEVICE_CONFIG = ../vendor/area512/components/area512_micropython/mpconfigport.h
CFLAGS = -std=c99 -D_POSIX_C_SOURCE=200809L -O1 -I. -I$(EMBED) -Wall -Wno-unused-function
SRC = main.c $(wildcard $(EMBED)/py/*.c) $(EMBED)/port/embed_util.c \
      $(EMBED)/port/mphalport.c $(EMBED)/shared/runtime/gchelper_generic.c

a512c: $(EMBED) main.c
	$(CC) $(CFLAGS) -o $@ $(SRC) -lm

# The device's config verbatim, minus the hardware builtins table (names only
# resolved at run time, so they cannot change the bytecode).
mpconfigport.h: $(DEVICE_CONFIG)
	sed '/^\/\/ Declared incomplete/,$$d' $< > $@
	echo '// a512c only: emit for the ESP32-S3 (31-bit small ints, bytecode only)' >> $@
	echo '// like mpy-cross; a 64-bit host would otherwise write 63 into the header.' >> $@
	echo '#define MICROPY_DYNAMIC_COMPILER (1)' >> $@
	echo '#include <stdlib.h>  // embed port: MP_PLAT_ALLOC_HEAP' >> $@

$(EMBED): mpconfigport.h
	rm -rf $(EMBED) build-embed
	$(MAKE) -f embed.mk

clean:
	rm -rf a512c mpconfigport.h $(EMBED) build-embed
