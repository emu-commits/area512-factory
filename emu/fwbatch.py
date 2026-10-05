#!/usr/bin/env python3
"""Run every app of a factory batch on the REAL AREA512 firmware (emu/fwrun.mjs).
For each app: fresh card with only that app in /home/ai/, Filer -> ai/ -> app -> R,
then the spec's first TEST script, then q. Screenshots: start / test / end
(end = back in Filer: its status line says "Returned: <app>" or "Error: <app>").

  emu/fwbatch.py out/<batch> [-j 4]      -> out/<batch>/firmware/<app>-{start,test,end}.png
"""
import argparse, concurrent.futures, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent.parent

def script_for(app):
    spec = (app / "spec.md").read_text() if (app / "spec.md").exists() else ""
    tests = re.findall(r"^TEST:\s*(.+)$", spec, re.M)
    keys = []
    for tok in (tests[0].split() if tests else []):
        if tok == "q":
            break                    # quit is done below, after the screenshot
        keys += [tok, "WAIT"]
    return " ".join(["j", "ENTER", "j", "R"] + ["WAIT"] * 6 + ["SHOT:start"] + keys +
                    ["WAIT"] * 4 + ["SHOT:test", "q"] + ["WAIT"] * 6 + ["SHOT:end"])

def run(app, out):
    r = subprocess.run(["node", str(HERE / "emu/fwrun.mjs"), str(app), "--out", str(out),
                        "--keys", script_for(app)], capture_output=True, text=True, timeout=900)
    return app.name, r.returncode, (r.stderr.strip().splitlines() or [""])[-1]

ap = argparse.ArgumentParser()
ap.add_argument("batch")
ap.add_argument("-j", type=int, default=4)
a = ap.parse_args()
batch = pathlib.Path(a.batch)
out = batch / "firmware"
apps = sorted(p for p in batch.iterdir() if (p / "main.mpy").exists())
with concurrent.futures.ThreadPoolExecutor(a.j) as pool:
    for name, rc, err in pool.map(lambda p: run(p, out), apps):
        print(name, "ok" if rc == 0 else "runner failed: " + err, flush=True)
