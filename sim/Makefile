# a512sim: AREA512's MicroPython (same version, same mpconfigport.h) on the PC.
EMBED = micropython_embed
CFLAGS = -std=c99 -O1 -g -I. -I$(EMBED) -Wall -Wno-unused-function
SRC = main.c $(wildcard $(EMBED)/py/*.c) $(EMBED)/port/embed_util.c \
      $(EMBED)/port/mphalport.c $(EMBED)/shared/runtime/gchelper_generic.c

a512sim: $(SRC) mpconfigport.h
	$(CC) $(CFLAGS) -o $@ $(SRC) -lm

$(EMBED): mpconfigport.h
	rm -rf $(EMBED) build-embed
	$(MAKE) -f embed.mk

# Everything the factory needs: the embed package, the binary, the mocks.
setup: $(EMBED) prelude.py
	$(MAKE) a512sim

prelude.py: gen_prelude.py
	python3 gen_prelude.py

clean:
	rm -rf a512sim prelude.py $(EMBED) build-embed
