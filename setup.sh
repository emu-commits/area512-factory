#!/bin/sh
# Fetch the pinned AREA512 + MicroPython sources and build the simulator.
# Pins: AREA512 5d0fef9 (2026-09-23), whose components/micropython submodule is
# micropython e0e9fbb (v1.28.0). Bump both together, then re-run
# sim/probe_features.py: prompts/rules.md is only true for this pair.
set -e
cd "$(dirname "$0")"
AREA512_REV=5d0fef9
MICROPYTHON_REV=e0e9fbb17ed6fd06bb76e266ae554784c9c80804
mkdir -p vendor
if [ ! -d vendor/area512 ]; then
  git clone -q https://github.com/engneer-hamachan/area512 vendor/area512
  git -C vendor/area512 checkout -q "$AREA512_REV"
fi
if [ ! -d vendor/micropython ]; then
  git init -q vendor/micropython
  git -C vendor/micropython remote add origin https://github.com/micropython/micropython
  git -C vendor/micropython fetch -q --depth 1 origin "$MICROPYTHON_REV"
  git -C vendor/micropython checkout -q FETCH_HEAD
fi
if [ ! -d vendor/emucard-adv ]; then
  git clone -q https://github.com/emu-commits/emucard-adv vendor/emucard-adv
fi
make -C sim setup
make -C mpyc
python3 sim/probe_features.py
