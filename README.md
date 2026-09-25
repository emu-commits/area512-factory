# AREA512 app factory — PC-side validation

Question being tested: **can a model one-shot a small AREA512 app** (request →
spec → all files, two API calls, no tools, no repair loop) well enough that it
runs on the device first time? If yes, a WiFi "partner" firmware booted via
M5Launcher could do the same calls on-device and drop the app on the SD card.

## Setup

    ./setup.sh                      # fetch pinned AREA512 + MicroPython, build sim, verify rules
    export OPENROUTER_API_KEY=...   # or put it in ~/.config/area512-factory/openrouter_key

## Use

    ./factory.py "a dice roller for D&D"
    ./factory.py --batch requests.txt --jobs 4           # -> out/<batch>/summary.md
    ./factory.py --batch requests.txt --model deepseek/deepseek-v4.1-flash
    ./factory.py --sim out/<batch>/<app>                  # re-test after a hand edit
    ./factory.py --show-prompts                           # see exactly what is sent

Each app lands in `out/<batch>/<app>/` (`main.py`, `README.md`, `spec.md`).
Copy that folder to the SD card as `/home/ai/<app>/`, open `main.py` in AREA512
(Enter compiles and runs it) — that is the real verdict.

## What "pass" means

`sim/a512sim` is AREA512's MicroPython (same v1.28.0 source, same
`mpconfigport.h`, MINIMUM feature level) with the hardware API replaced by
mocks generated from AREA512's own `.pyi` stubs. It catches, with line numbers:
syntax the device can't compile (slicing, f-strings…), missing builtins
(`min`, `enumerate`, `import`…), API methods that don't exist, wrong argument
counts, keyword args to builtins, floats passed as ints, and crashes along the
spec's TEST key scripts plus a 150-key random fuzz.

It does **not** see: how the screen looks, device-only memory pressure (the
sim gives the app 96 KB and no heap growth), timing, or mock behaviour that
differs from the real API (assumptions are marked in `sim/gen_prelude.py`).
So a sim pass is necessary, not sufficient; the device run is the ground truth.

`sim/probe_features.py` re-verifies every claim in `prompts/rules.md` (50 checks).

## Layout

    factory.py            the prompter (stdlib only — same HTTP calls the device would make)
    prompts/rules.md      platform rules given to the model (verified by probe_features.py)
    prompts/skeleton.py   sim-verified example app
    sim/                  a512sim (C, embed port) + mock generator + feature probe
    requests.txt          10 sample requests
