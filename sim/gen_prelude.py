#!/usr/bin/env python3
"""Generate sim/prelude.py: MicroPython mocks of AREA512's hardware API.

Source of truth is AREA512's own stubs (components/area512/sig/micropython/*.pyi),
so a model that calls a method AREA512 does not have, passes the wrong number of
arguments, uses keyword arguments on a builtin, or hands a float to an int
parameter fails here the way it fails on the device.

The emitted file must itself run under AREA512's MINIMUM-level MicroPython:
no slicing, no % formatting, no f-strings, no min/max/enumerate/set.

Behaviour that a stub cannot express (key input, banded drawing, the in-memory
SD card, plausible screen metrics) lives in BEHAVIOUR below. Every value there
not read from AREA512's source is an ASSUMPTION and says so.
"""
import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SIG = HERE.parent / "vendor/area512/components/area512/sig/micropython"
STUBS = ["Sprite", "BandedSprite", "Widget", "WidgetList", "WidgetTextView",
         "Dot", "SD", "RNG", "GPIO", "ADC", "IO", "Console"]

# Method bodies that need behaviour, keyed "Class.method". `a` is the tuple of
# positional args (self excluded), already arity- and type-checked.
BEHAVIOUR = {
    # --- screen: 240x135 is the Cardputer panel (AREA512 README) ---
    "Display.width": "return 240",
    "Display.height": "return 135",
    "Sprite.__init__": "self._w = a[0]\nself._h = a[1]\n_sim_live.append(self)",
    "Sprite.width": "return self._w",
    "Sprite.height": "return self._h",
    "Sprite.delete": "_sim_live.remove(self) if self in _sim_live else None",
    "BandedSprite.__init__": "self._band = 0\n_sim_live.append(self)",
    "BandedSprite.width": "return 240",
    "BandedSprite.height": "return 135",
    "BandedSprite.delete": "_sim_live.remove(self) if self in _sim_live else None",
    # draw() returns True once per band, then False after the final transfer.
    # ASSUMPTION: 4 bands per frame.
    "BandedSprite.draw": "_sim_frame()\nself._band = self._band + 1\n"
                         "if self._band > 4:\n    self._band = 0\n    return False\nreturn True",
    "BandedSprite.region_top": "return (self._band - 1) * 34 if self._band > 0 else 0",
    "BandedSprite.region_bottom": "return self._band * 34 if self._band > 0 else 34",
    "Sprite.push": "_sim_frame()",
    # Text drawn during a frame is kept as a crude "screen dump" for reports.
    "Sprite.text": "_sim_txt(a[2])",
    "BandedSprite.text": "_sim_txt(a[2])",
    "Widget.header": "_sim_txt(a[1])\nif len(a) > 2:\n    _sim_txt(a[2])",
    "Widget.footer": "_sim_txt(a[1])",
    "Widget.splash": "_sim_txt(a[1])",
    "Widget.toast": "_sim_txt(a[1])",
    "Widget.big_text": "_sim_txt(a[3])",
    "Widget.text_center": "_sim_txt(a[2])",
    "Widget.text_right": "_sim_txt(a[3])",
    "Widget.cell": "_sim_txt(a[5])",
    "Widget.field": "_sim_txt(a[4] + ': ' + a[5])",
    "Widget.button": "_sim_txt('[' + a[4] + ']')",
    "Widget.badge": "_sim_txt(a[3])",
    "Widget.center_lines":
        "for x in a[1]:\n    _sim_txt(x if isinstance(x, str) else x[0])",
    "Widget.table_row": "_sim_txt(' | '.join(a[4]))",
    "Widget.hints": "_sim_txt(' '.join([h[0] + ':' + h[1] for h in a[1]]))",
    # --- Widget: colours are the documented fixed/default theme values ---
    "Widget.bg": "return 0x000000", "Widget.amber": "return 0xF5972D",
    "Widget.dim": "return 0xCFA45F", "Widget.gold": "return 0xFFD966",
    "Widget.dark": "return 0x241604",
    "Widget.theme_background": "return 0x000000", "Widget.theme_text": "return 0xCFA45F",
    "Widget.theme_emphasis": "return 0xF5972D", "Widget.theme_border": "return 0xF5972D",
    "Widget.theme_selected": "return 0xFFD966", "Widget.theme_box": "return 0x241604",
    # ASSUMPTION: metrics for the default font; only used for layout arithmetic.
    "Widget.char_width": "return 6", "Widget.row_height": "return 11",
    "Widget.header_height": "return 13", "Widget.body_top": "return 14",
    "Widget.body_bottom": "return 122", "Widget.body_height": "return 108",
    "Widget.text_width": "return 6 * len(a[1])",
    "Widget.clip": "return a[1]",
    "Widget.wrap_text": "return a[2] + 11",
    "Widget.marquee": "return a[5] + 1",
    "Widget.read_key": "return _sim_key_blocking(True)",
    # Modal widgets read keys themselves on the device; here they consume the
    # key script the same way (ENTER accepts, ESC cancels).
    "Widget.input": "return _sim_modal_text(a[2] if len(a) > 2 else '')",
    "Widget.input_number": "k = _sim_key_blocking(True)\nreturn None if k == 'ESC' else a[2]",
    "Widget.confirm": "k = _sim_key_blocking(True)\nreturn k == 'ENTER' or k == 'y'",
    "Widget.dialog": "k = _sim_key_blocking(True)\nreturn None if k == 'ESC' else 0",
    "Widget.menu": "k = _sim_key_blocking(True)\nreturn None if k == 'ESC' else (a[3] if len(a) > 3 else 0)",
    "Widget.alert": "_sim_key_blocking(True)",
    # --- WidgetList / WidgetTextView keep enough state to be navigable ---
    "WidgetList.__init__": "self._items = []\nself._i = 0\nself._marks = {}",
    "WidgetList.clear": "self._items = []\nself._i = 0\nself._marks = {}",
    "WidgetList.add": "self._items.append(a[0])",
    "WidgetList.count": "return len(self._items)",
    "WidgetList.index": "return self._i",
    "WidgetList.set_index": "self._i = a[0]",
    "WidgetList.mark": "self._marks[a[0]] = a[1]",
    "WidgetList.marked": "return self._marks.get(a[0], False)",
    "WidgetList.toggle_mark": "self._marks[self._i] = not self._marks.get(self._i, False)",
    "WidgetList.handle":
        "n = len(self._items)\n"
        "if a[0] == 'DOWN' and self._i < n - 1:\n    self._i = self._i + 1\n    return True\n"
        "if a[0] == 'UP' and self._i > 0:\n    self._i = self._i - 1\n    return True\n"
        "return False",
    "WidgetTextView.__init__": "self._s = 0",
    "WidgetTextView.scroll": "return self._s",
    "WidgetTextView.set_scroll": "self._s = a[0]",
    "WidgetTextView.handle": "return a[0] == 'UP' or a[0] == 'DOWN'",
    # --- storage: an in-memory SD card, empty at start ---
    # ASSUMPTION: reading a missing file returns '' (device behaviour unverified).
    "SD.mount": "return True",
    "SD.exist": "return a[0] in _sim_fs",
    "SD.mkdir": "_sim_fs[a[0]] = None\nreturn True",
    "SD.read": "v = _sim_fs.get(a[0], '')\nreturn '' if v is None else v",
    "SD.write": "_sim_fs[a[0]] = a[1]\nreturn len(a[1])",
    "File.__init__": "self._p = a[0]",
    "File.read": "v = _sim_fs.get(self._p, '')\nreturn '' if v is None else v",
    "File.exist": "return a[0] in _sim_fs",
    "File.file": "return _sim_fs.get(a[0], None) is not None",
    "File.directory": "return a[0] in _sim_fs and _sim_fs[a[0]] is None",
    "File.unlink": "_sim_fs.pop(a[0], None)\nreturn 0",
    "File.rename": "_sim_fs[a[1]] = _sim_fs.pop(a[0], '')\nreturn 0",
    "Dir.__init__": "self._n = 0",
    "Dir.exist": "return a[0] in _sim_fs and _sim_fs[a[0]] is None",
    "Dir.mkdir": "_sim_fs[a[0]] = None\nreturn 0",
    "Dot.load": "return Dot()",
    # --- misc ---
    "RNG.random_int": "return _sim_rand()",
    "RNG.random_string": "return b'x' * a[0]",
    "RNG.uuid": "return '00000000-0000-4000-8000-000000000000'",
    # --- console IO: IO() is a singleton on the device ---
    "IO.getch": "return _sim_io_char(_sim_key_blocking(True))",
    "IO.read_nonblock":
        "k = _sim_key_blocking(False)\nreturn None if k is None else _sim_io_char(k)",
}

# Instances whose __init__ the stub does not declare (Dot has no constructor)
# are created internally with no arguments.
INTERNAL_CTOR = {"Dot"}

PRELUDE_HEAD = r'''# GENERATED by sim/gen_prelude.py from AREA512's .pyi stubs -- do not edit.
# MicroPython mocks of AREA512's builtin hardware API, for a512sim.

class _SimDone(BaseException):
    pass

_sim_live = []
_sim_fs = {}
_sim_seed = [12345]
_sim_frames = [0]
_sim_tokens = _sim_keys.split()
_sim_pos = [0]
_sim_idle = [0]
_SIM_IDLE_LIMIT = 300      # empty polls allowed after the key script ends
_SIM_FRAME_LIMIT = 20000   # frames without ever finishing -> stop, not a failure

_sim_cur = []
_sim_last = []

def _sim_txt(t):
    if len(_sim_cur) < 40:
        _sim_cur.append(t)

def _sim_frame():
    if len(_sim_cur):
        _sim_last.clear()
        _sim_last.extend(_sim_cur)
        _sim_cur.clear()
    _sim_frames[0] = _sim_frames[0] + 1
    if _sim_frames[0] > _SIM_FRAME_LIMIT:
        raise _SimDone("frame_limit")

def _sim_rand():
    _sim_seed[0] = (_sim_seed[0] * 1103515245 + 12345) & 0x3FFFFFFF
    return _sim_seed[0]

def _sim_key_blocking(block):
    # Next token of the key script. 'WAIT' is one empty poll. After the script
    # ends, non-blocking polls see nothing for a while, then the run stops.
    while _sim_pos[0] < len(_sim_tokens):
        t = _sim_tokens[_sim_pos[0]]
        _sim_pos[0] = _sim_pos[0] + 1
        if t == "WAIT":
            if block:
                continue
            return None
        if t == "SPACE":
            return " "
        return t
    if block:
        raise _SimDone("keys_exhausted")
    _sim_idle[0] = _sim_idle[0] + 1
    if _sim_idle[0] > _SIM_IDLE_LIMIT:
        raise _SimDone("keys_exhausted")
    return None

def _sim_io_char(k):
    if k == "ENTER":
        return "\r"
    if k == "ESC":
        return "\x1b"
    if k == "BS":
        return "\x7f"
    if k == "UP" or k == "DOWN" or k == "LEFT" or k == "RIGHT":
        return "\x1b"
    return k

def _sim_modal_text(initial):
    s = initial
    while True:
        k = _sim_key_blocking(True)
        if k == "ENTER":
            return s
        if k == "ESC":
            return None
        if len(k) == 1:
            s = s + k

#@@CHUNK
def _sim_type_name(v):
    return str(type(v))

def _sim_bad(where, i, want, v):
    raise TypeError("{}: argument {} must be {}, not {}".format(
        where, i + 1, want, _sim_type_name(v)))

def _sim_chk(where, a, lo, hi, codes):
    n = len(a)
    if n < lo or n > hi:
        if lo == hi:
            raise TypeError("{} takes {} positional arguments but {} were given".format(where, lo, n))
        raise TypeError("{} takes {} to {} positional arguments but {} were given".format(where, lo, hi, n))
    i = 0
    while i < n:
        c = codes[i]
        v = a[i]
        opt = len(c) > 1
        if v is None and opt:
            pass
        elif c[0] == "i":
            # mp_obj_get_int: int and bool convert, float does NOT.
            if not isinstance(v, int):
                _sim_bad(where, i, "int", v)
        elif c[0] == "f":
            if not (isinstance(v, int) or isinstance(v, float)):
                _sim_bad(where, i, "a number", v)
        elif c[0] == "s":
            if not isinstance(v, str):
                _sim_bad(where, i, "str", v)
        elif c[0] == "S":
            if not (isinstance(v, Sprite) or isinstance(v, BandedSprite)):
                _sim_bad(where, i, "Sprite or BandedSprite", v)
        elif c[0] == "D":
            if not isinstance(v, Dot):
                _sim_bad(where, i, "Dot", v)
        elif c[0] == "L":
            if not (isinstance(v, list) or isinstance(v, tuple)):
                _sim_bad(where, i, "list", v)
            for e in v:
                if not isinstance(e, int):
                    _sim_bad(where, i, "a list of int", e)
        elif c[0] == "l":
            if not (isinstance(v, list) or isinstance(v, tuple)):
                _sim_bad(where, i, "list", v)
        i = i + 1

def _sim_stats():
    _sim_frame()
    print("@@STATS frames={} keys_used={}/{}".format(
        _sim_frames[0], _sim_pos[0], len(_sim_tokens)))
    for t in _sim_last:
        print("@@SCREEN " + t)

def sleep(s):
    _sim_frame()

def sleep_ms(ms):
    _sim_frame()
'''

PRELUDE_TAIL = r'''
STDIN = IO()
'''


def type_code(ann):
    """Map a stub annotation to a _sim_chk code ('*' = unchecked)."""
    if ann is None:
        return "*"
    s = ast.unparse(ann).replace(" ", "")
    opt = ""
    if s.endswith("|None"):
        s, opt = s[: -len("|None")], "?"
    code = {"int": "i", "float": "f", "str": "s", "Sprite|BandedSprite": "S",
            "Dot": "D", "list[int]": "L"}.get(s)
    if code is None and s.startswith("list["):
        code = "l"
    return (code or "*") + opt


def default_return(ann, classes):
    if ann is None:
        return "None"
    s = ast.unparse(ann).replace(" ", "")
    if s.endswith("|None") or s == "None":
        return "None"
    if s in classes and s in INTERNAL_CTOR:
        return s + "()"
    return {"int": "0", "float": "0.0", "str": "''", "bool": "False",
            "bytes": "b''"}.get(s, "None")


def emit_method(cls, fn, is_static, classes, out):
    args = fn.args
    params = list(args.posonlyargs) + list(args.args)
    if not is_static and params and params[0].arg == "self":
        params = params[1:]
    n_default = len(args.defaults)
    hi = len(params)
    lo = hi - n_default
    codes = tuple(type_code(p.annotation) for p in params)
    where = "{}.{}".format(cls, fn.name)
    key = where
    body = BEHAVIOUR.get(key)
    if body is None:
        body = "return " + default_return(fn.returns, classes)
    if fn.name == "__init__" and cls in INTERNAL_CTOR:
        return
    if is_static:
        out.append("    @staticmethod")
        out.append("    def {}(*a):".format(fn.name))
    else:
        out.append("    def {}(self, *a):".format(fn.name))
    out.append("        _sim_chk({!r}, a, {}, {}, {!r})".format(where, lo, hi, codes))
    for line in body.split("\n"):
        out.append("        " + line)


def main():
    classes = {}
    for stub in STUBS:
        tree = ast.parse((SIG / (stub + ".pyi")).read_text())
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes[node.name] = node
    out = [PRELUDE_HEAD]
    for name, node in classes.items():
        out.append("#@@CHUNK")
        out.append("class {}:".format(name))
        emitted = 0
        for m in node.body:
            if isinstance(m, ast.AnnAssign) and isinstance(m.target, ast.Name):
                out.append("    {} = {}".format(m.target.id, emitted))
                emitted += 1
            elif isinstance(m, ast.FunctionDef):
                is_static = any(getattr(d, "id", "") == "staticmethod" for d in m.decorator_list)
                emit_method(name, m, is_static, classes, out)
                emitted += 1
        if name in INTERNAL_CTOR:
            out.append("    def __init__(self):")
            out.append("        pass")
            emitted += 1
        if not emitted:
            out.append("    pass")
        out.append("")
    out.append("#@@CHUNK")
    out.append(PRELUDE_TAIL)
    (HERE / "prelude.py").write_text("\n".join(out))
    print("wrote prelude.py: {} classes".format(len(classes)), file=sys.stderr)


if __name__ == "__main__":
    main()
