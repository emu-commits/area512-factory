# Examples

## `sonnet-subagent/` — 10/10 apps that run on real AREA512 firmware

Ten requests from [`requests.txt`](../requests.txt), each answered one-shot
(spec call + code call, no tools, no repair loop) by a Claude Sonnet subagent
via `factory.py --export-prompts` / `--replies`. All ten passed the simulator
and were then launched with `R` on the official AREA512 firmware in the
emucard-adv emulator (`emu/fwbatch.py`), drove their spec's TEST 1 keys and
returned cleanly to Filer.

- `apps/<name>/main.mpy` — what the device runs (built by `mpyc/a512c`, header `4d 06 00 1f`)
- `apps/<name>/main.py` — source, for reading
- `apps/<name>/spec.md` — the spec the code was written from (call 1's output)
- `apps/<name>/README.md` — the app's own help text
- `firmware/<name>-{start,test,end}.png` — screenshots from the real firmware;
  `ends.png` stacks every app's final Filer status line ("Returned: <app>")
- `summary.md`, `results.json` — the harness verdicts

### Running one on a Cardputer ADV (or the emulator)

Copy an app folder to the SD card as `/Area512_data/home/ai/<name>/`
(at least `main.mpy`), then in Filer open `ai/`, select the folder and press `R`.
Filer's `R` runs `main.manifest`, `main.mrb` or `main.mpy` — never `main.py` —
which is why every app ships a precompiled `main.mpy`.

### Same requests, other models (for comparison)

| model | answered | simulator pass | clean on firmware |
|---|---|---|---|
| Claude Sonnet subagent (this folder) | 10/10 | 10/10 | 10/10 |
| qwen/qwen3.8-27b:free | 8/10 (2× HTTP 429) | 7/8 | 7/7 |
| openrouter/free | 10/10 | 3/10 | — |
| nvidia/nemotron-3-ultra-550b-a55b:free | 7/10 (503 overloaded) | 3/7 | 2/7 |

The dominant failure across the free models is syntax the device's MicroPython
can't compile — mainly slicing (`board[:]`, `line[:pos]`).
