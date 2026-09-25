#!/usr/bin/env python3
"""AREA512 app factory — PC-side prompter for validating the one-shot idea.

Two model calls per app, no repair loop, no tools:
  1. request -> build spec          (the partner firmware would show this for approval)
  2. spec    -> every file, one message
Then the files are written to out/ in AREA512's SD layout and run through
a512sim (AREA512's exact MicroPython config + mocks of its API) to measure
whether the first attempt would have worked on the device.

stdlib only, on purpose: the device will do one plain HTTPS POST per step,
and this script should make exactly the requests the device would.

  ./factory.py "a dice roller for D&D"          one app
  ./factory.py --batch requests.txt --jobs 4    a batch + summary.md
  ./factory.py --sim out/<batch>/<app>          re-run the simulator only
  ./factory.py --show-prompts                   print the prompts, no API call

Key: $OPENROUTER_API_KEY, or ~/.config/area512-factory/openrouter_key
"""
import argparse
import ast
import concurrent.futures
import datetime
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
SIG = HERE / "vendor/area512/components/area512/sig/micropython"
LANDER = HERE / "vendor/area512/storage/home/game/space_lander"
SIM = HERE / "sim/a512sim"
PRELUDE = HERE / "sim/prelude.py"
OUT = HERE / "out"
DEFAULT_MODEL = "anthropic/claude-sonnet-5"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_STUBS = ["Sprite", "BandedSprite", "Widget", "WidgetList", "WidgetTextView",
             "Dot", "SD", "RNG", "IO", "Console", "GPIO", "ADC"]
SIM_HEAP_KB = 96        # app heap budget in the simulator (device: dynamic, up to 192 KB)
SIM_TIMEOUT_S = 20
FUZZ_TOKENS = ["UP", "DOWN", "LEFT", "RIGHT", "ENTER", "SPACE", "BS", "WAIT", "WAIT",
               "j", "k", "h", "l", "a", "s", "d", "w", "x", "1", "2", "3"]


# ---------------------------------------------------------------- prompts

def api_reference():
    """Compact API reference generated from AREA512's own .pyi stubs."""
    out = []
    for stub in API_STUBS:
        tree = ast.parse((SIG / (stub + ".pyi")).read_text())
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            out.append("class {}:".format(node.name))
            for m in node.body:
                if isinstance(m, ast.AnnAssign):
                    out.append("    {}: {}".format(ast.unparse(m.target), ast.unparse(m.annotation)))
                if not isinstance(m, ast.FunctionDef):
                    continue
                static = any(getattr(d, "id", "") == "staticmethod" for d in m.decorator_list)
                args = ast.unparse(m.args).replace("self, ", "").replace("self", "")
                args = re.sub(r",?\s*/\s*$", "", args).replace(", /,", ",")
                ret = ast.unparse(m.returns) if m.returns else "None"
                doc = ast.get_docstring(m) or ""
                doc = " ".join(doc.split())
                line = "    {}{}({}) -> {}".format("static " if static else "", m.name, args, ret)
                out.append(line + ("   # " + doc if doc else ""))
            out.append("")
    out.append("sleep(seconds: float) -> None    # builtin function")
    out.append("sleep_ms(milliseconds: int) -> None    # builtin function")
    out.append("STDIN: IO    # the same instance IO() returns")
    return "\n".join(out)


def lander_example():
    parts = []
    for name in ("main.py", "input.py", "hud.py"):
        parts.append("# ---- space_lander/{} ----\n{}".format(name, (LANDER / name).read_text()))
    return "\n".join(parts)


def platform_block():
    return "\n\n".join([
        (HERE / "prompts/rules.md").read_text(),
        "# API reference (every builtin; generated from AREA512's stubs)\n\n```python\n"
        + api_reference() + "\n```",
        "# Skeleton app (runs on AREA512)\n\n```python\n"
        + (HERE / "prompts/skeleton.py").read_text() + "```",
        "# Real shipped AREA512 app: Space Lander (real-time loop; excerpt: 3 of its 9 files)\n\n"
        "```python\n" + lander_example() + "```",
    ])


SPEC_TASK = """You write build specs for tiny apps on AREA512 (a Cardputer OS).
The user typed a short request on the device's keyboard. Turn it into a spec a
programmer can implement in ONE main.py of at most ~400 lines, using only the
platform and API documented below. If the request needs something the platform
lacks (network, sound, real-time clock, images from the internet...), keep the
spirit and design around it; say how in one line under LIMITS.

There is NO clock: time only advances by counting sleep_ms() calls, and the
date/time of day is unknown. Design timers around that.

Reply with the spec only, in exactly this format:

NAME: <folder name: lowercase a-z, 0-9, _ ; at most 16 chars>
TITLE: <header title, at most 16 chars, uppercase>
PURPOSE: <one sentence>
SCREENS:
- <each screen/mode: what is drawn where on the 240x135 screen>
CONTROLS:
- <key>: <action>     (keys: letters, digits, SPACE, ENTER, ESC, BS, UP DOWN LEFT RIGHT; q quits)
DATA: <what is saved under /home/ai/<NAME>/ and when, or "none">
LIMITS: <platform workarounds, or "none">
TEST: <key script exercising the main flow>
TEST: <key script exercising a second flow, ending with q>

A key script is space-separated tokens: single characters, SPACE, ENTER, ESC,
BS, UP, DOWN, LEFT, RIGHT, and WAIT (one idle frame for real-time apps).
"""

CODE_TASK = """You write complete apps for AREA512 (a Cardputer OS), in one reply,
with no chance to run or fix them afterwards: the files you send are copied to
the device's SD card as-is. Follow the platform rules exactly — they are the
difference between an app that runs and one that crashes on launch. Before
writing each line, check it against the "not available" table.

Implement the spec the user sends. Reply with ONLY these blocks, nothing before
or after, no Markdown fences:

=== FILE: main.py ===
<the complete program>
=== FILE: README.md ===
<title, one-line description, controls list — like AREA512's app READMEs>
=== END ===
"""


def spec_messages(request, platform):
    return [
        {"role": "system", "content": [
            {"type": "text", "text": SPEC_TASK + "\n\n" + platform,
             "cache_control": {"type": "ephemeral"}}]},
        {"role": "user", "content": request},
    ]


def code_messages(spec, platform):
    return [
        {"role": "system", "content": [
            {"type": "text", "text": CODE_TASK + "\n\n" + platform,
             "cache_control": {"type": "ephemeral"}}]},
        {"role": "user", "content": spec},
    ]


# ---------------------------------------------------------------- API

def api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    path = pathlib.Path.home() / ".config/area512-factory/openrouter_key"
    if not key and path.exists():
        key = path.read_text().strip()
    if not key:
        sys.exit("no API key: set OPENROUTER_API_KEY or write it to " + str(path))
    return key


def chat(messages, model, effort):
    body = {"model": model, "messages": messages, "max_tokens": 32000,
            "usage": {"include": True}}
    if effort != "none":
        # Reasoning happens server-side; exclude it so the reply carries only
        # the answer (this is what keeps the device's download small).
        body["reasoning"] = {"effort": effort, "exclude": True}
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": "Bearer " + api_key(),
                 "Content-Type": "application/json",
                 "X-Title": "AREA512 app factory"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP {}: {}".format(e.code, e.read().decode(errors="replace")[:500]))
    data = json.loads(raw)
    if "error" in data:
        raise RuntimeError("API error: {}".format(data["error"]))
    usage = data.get("usage") or {}
    return {
        "text": data["choices"][0]["message"].get("content") or "",
        "finish": data["choices"][0].get("finish_reason"),
        "seconds": round(time.time() - t0, 1),
        "response_bytes": len(raw),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
        "cost": usage.get("cost"),
        "model": data.get("model"),
    }


# ---------------------------------------------------------------- parsing

def parse_spec(text):
    name = re.search(r"^NAME:\s*([a-z0-9_]+)", text, re.M)
    tests = [t.strip() for t in re.findall(r"^TEST:\s*(.+)$", text, re.M)]
    return (name.group(1)[:16] if name else None), tests


def parse_files(text):
    """Split '=== FILE: name ===' blocks. Tolerates stray Markdown fences."""
    files = {}
    parts = re.split(r"^=== FILE: (\S+) ===[ \t]*$", text, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        body = re.split(r"^=== END ===", parts[i + 1], flags=re.M)[0]
        lines = body.strip("\n").split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        files[parts[i]] = "\n".join(lines) + "\n"
    return files


# ---------------------------------------------------------------- simulator

def fuzz_script(seed):
    rng = random.Random(seed)
    return " ".join(["ENTER"] + [rng.choice(FUZZ_TOKENS) for _ in range(150)] + ["ESC", "q", "ESC", "q"])


def sim_run(app_dir, keys):
    keys_file = app_dir / ".simkeys"
    keys_file.write_text(keys)
    try:
        r = subprocess.run([str(SIM), str(PRELUDE), str(keys_file), str(SIM_HEAP_KB), "main.py"],
                           cwd=app_dir, capture_output=True, text=True, timeout=SIM_TIMEOUT_S)
        out = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return {"keys": keys, "result": "hang", "detail": "no exit within {}s (busy loop that never reads keys or sleeps?)".format(SIM_TIMEOUT_S)}
    finally:
        keys_file.unlink(missing_ok=True)
    screen = [l[len("@@SCREEN "):] for l in out.splitlines() if l.startswith("@@SCREEN ")]
    stats = next((l for l in out.splitlines() if l.startswith("@@STATS")), "")
    if "@@COMPILE_ERROR" in out:
        result = "compile_error"
    elif "@@RUNTIME_ERROR" in out:
        result = "runtime_error"
    elif "@@EXIT" in out:
        result = "ok"
    else:
        result = "crash"
    detail = ""
    if result != "ok":
        detail = "\n".join(l for l in out.splitlines()
                           if not l.startswith(("@@HEAP", "@@SCREEN", "@@STATS", "@@EXIT"))
                           and "sim/prelude.py" not in l).strip()
    return {"keys": keys, "result": result, "detail": detail,
            "stats": stats.replace("@@STATS ", ""), "screen": screen}


def simulate(app_dir, tests):
    runs = [sim_run(app_dir, t) for t in tests]
    runs.append(sim_run(app_dir, fuzz_script(app_dir.name)))
    runs[-1]["fuzz"] = True
    verdict = "pass"
    for r in runs:
        if r["result"] != "ok":
            verdict = r["result"]
            break
    return verdict, runs


def static_notes(src):
    notes = []
    if re.search(r"Sprite\(\s*240\s*,\s*135", src):
        notes.append("allocates a full-screen Sprite (64 KB buffer) - may not fit on device")
    return notes


# ---------------------------------------------------------------- pipeline

def build(request, model, effort, batch_dir, platform):
    rec = {"request": request, "model": model, "effort": effort, "calls": {}}
    try:
        spec_reply = chat(spec_messages(request, platform), model, effort)
        rec["calls"]["spec"] = {k: v for k, v in spec_reply.items() if k != "text"}
        spec = spec_reply["text"].strip()
        name, tests = parse_spec(spec)
        if not name:
            name = re.sub(r"[^a-z0-9]+", "_", request.lower()).strip("_")[:16] or "app"
        app_dir = batch_dir / name
        n = 2
        while app_dir.exists():
            app_dir = batch_dir / "{}_{}".format(name, n)
            n += 1
        app_dir.mkdir(parents=True)
        rec["app"] = app_dir.name
        (app_dir / "spec.md").write_text(spec + "\n")

        code_reply = chat(code_messages(spec, platform), model, effort)
        rec["calls"]["code"] = {k: v for k, v in code_reply.items() if k != "text"}
        (app_dir / ".raw_code_reply.txt").write_text(code_reply["text"])
        files = parse_files(code_reply["text"])
        if "main.py" not in files:
            rec["verdict"] = "no_main_py"
            return rec
        for fname, body in files.items():
            if fname in ("main.py", "README.md"):
                (app_dir / fname).write_text(body)
        src = files["main.py"]
        rec["lines"] = src.count("\n")
        rec["bytes"] = len(src.encode())
        rec["notes"] = static_notes(src)
        rec["tests"] = tests
        rec["verdict"], rec["runs"] = simulate(app_dir, tests)
    except Exception as e:  # noqa: BLE001 - one failed app must not stop a batch
        rec["verdict"] = "api_error"
        rec["error"] = str(e)
    return rec


def cost(rec):
    return sum((c.get("cost") or 0) for c in rec.get("calls", {}).values())


def write_report(batch_dir, recs):
    (batch_dir / "results.json").write_text(json.dumps(recs, indent=2))
    lines = ["# Batch {}\n".format(batch_dir.name),
             "| app | request | verdict | lines | reply KB | secs | cost |",
             "|---|---|---|---|---|---|---|"]
    for r in recs:
        calls = r.get("calls", {})
        secs = sum((c.get("seconds") or 0) for c in calls.values())
        kb = (calls.get("code", {}).get("response_bytes") or 0) / 1024
        lines.append("| {} | {} | **{}** | {} | {:.1f} | {:.0f} | ${:.3f} |".format(
            r.get("app", "-"), r["request"][:50], r.get("verdict"), r.get("lines", "-"),
            kb, secs, cost(r)))
    passed = sum(1 for r in recs if r.get("verdict") == "pass")
    lines.append("\n**{}/{} passed first try** — total ${:.2f}\n".format(
        passed, len(recs), sum(cost(r) for r in recs)))
    for r in recs:
        if r.get("verdict") != "pass":
            lines.append("## {} — {}\n".format(r.get("app", r["request"][:30]), r.get("verdict")))
            if r.get("error"):
                lines.append("```\n{}\n```".format(r["error"]))
            for run in r.get("runs", []):
                if run["result"] != "ok":
                    lines.append("keys: `{}`\n```\n{}\n```".format(run["keys"][:120], run["detail"][:1500]))
                    break
    (batch_dir / "summary.md").write_text("\n".join(lines) + "\n")
    return "\n".join(lines)


def print_rec(r):
    print("[{}] {} -> {} (${:.3f})".format(r.get("verdict"), r["request"][:60], r.get("app", "-"), cost(r)),
          flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("request", nargs="?", help="the app request, as typed on the device")
    ap.add_argument("--batch", help="file with one request per line")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default="medium", choices=["none", "low", "medium", "high"],
                    help="server-side reasoning effort (default medium)")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--sim", help="re-run the simulator on an existing app folder")
    ap.add_argument("--show-prompts", action="store_true")
    a = ap.parse_args()

    if not SIM.exists() or not PRELUDE.exists():
        sys.exit("build the simulator first: make -C sim setup")

    if a.show_prompts:
        p = platform_block()
        print(SPEC_TASK + "\n\n" + p + "\n\n======== CODE TASK ========\n" + CODE_TASK)
        print("\n[platform block: {} chars ~{}k tokens]".format(len(p), len(p) // 4000), file=sys.stderr)
        return

    if a.sim:
        app_dir = pathlib.Path(a.sim).resolve()
        spec = (app_dir / "spec.md").read_text() if (app_dir / "spec.md").exists() else ""
        verdict, runs = simulate(app_dir, parse_spec(spec)[1])
        for r in runs:
            print("{:14} {}  keys: {}".format(r["result"], r.get("stats", ""), r["keys"][:70]))
            if r["detail"]:
                print("   " + r["detail"].replace("\n", "\n   "))
            if r.get("screen"):
                print("   screen: " + " | ".join(r["screen"]))
        print("verdict:", verdict)
        return

    if a.batch:
        requests = [l.strip() for l in pathlib.Path(a.batch).read_text().splitlines()
                    if l.strip() and not l.startswith("#")]
    elif a.request:
        requests = [a.request]
    else:
        ap.error("give a request, --batch FILE, --sim DIR or --show-prompts")

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    batch_dir = OUT / "{}-{}".format(stamp, a.model.split("/")[-1])
    batch_dir.mkdir(parents=True)
    platform = platform_block()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futs = [pool.submit(build, r, a.model, a.effort, batch_dir, platform) for r in requests]
        for f in concurrent.futures.as_completed(futs):
            print_rec(f.result())
    recs = [f.result() for f in futs]
    print()
    print(write_report(batch_dir, recs))
    print("\nfiles: {}\ncopy an app to the SD card as /home/ai/<app>/ (main.py + README.md)".format(batch_dir))


if __name__ == "__main__":
    main()
