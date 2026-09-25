# AREA512 MicroPython — platform rules

AREA512 is an OS for the M5Stack Cardputer (ESP32-S3, 240x135 screen, small
QWERTY keyboard, NO PSRAM). Apps are MicroPython 1.28 built at the MINIMUM
feature level. That makes this a much smaller language than normal Python.
Every rule below was verified against the device's interpreter configuration.
Breaking one is a SyntaxError, NameError or TypeError on the device.

## The language is restricted

NOT available (use the replacement):

| Not available                     | Use instead                                              |
|-----------------------------------|----------------------------------------------------------|
| `import` of ANY module            | nothing to import: the API below is builtin              |
| slicing: `s[1:]`, `a[:3]`, `[::-1]` | loops and indexing: `s[i]`, build a new list/str in a loop |
| f-strings `f"{x}"`                | `"{}".format(x)`, `"{:>5}".format(x)`, `"{:.1f}".format(x)` |
| `%` formatting `"%d" % x`         | `"{}".format(x)`                                         |
| `min()`, `max()`                  | write `a if a < b else b`, or a small helper function    |
| `enumerate()`                     | `i = 0` ... `i = i + 1`, or `for i in range(len(a))`     |
| `reversed()`, `filter()`          | index loops / list comprehensions                        |
| sets `{1, 2}`, `set()`            | a dict with `True` values, or a list                     |
| walrus `:=`, `async`/`await`      | plain statements                                         |
| `@property`                       | plain methods                                            |
| `str.center/partition/splitlines/count/title/zfill/ljust/rjust` | `"{:^10}".format(s)`, `split("\n")`, loops |
| `bytearray`, `struct`, `math`, `time`, `random`, `json`, `os`, `sys` | builtins below (`RNG`, `sleep_ms`), manual code |
| unicode: strings are bytes; `len("é") == 2` | keep all text ASCII                          |

Available: classes, functions, closures, `*args`/`**kwargs` in YOUR functions,
list/dict comprehensions, generators, try/except/finally, int (big ints ok),
float, str (`split strip lstrip rstrip startswith endswith find index replace
join lower upper isdigit isalpha isspace format`), list (`append extend pop
insert remove index count sort reverse copy`), dict (`get items keys values pop
setdefault update clear`), `range len abs round divmod sorted sum any all zip
map int float str bool list tuple dict isinstance chr ord hex repr`.
`del l[i]` works; `l.pop(i)` works. Floats: `//` for integer division.

## Builtin API calls are strict

- **Positional arguments only.** Keyword arguments to ANY builtin API call are a TypeError.
- **int parameters reject floats.** `sprite.rect(x / 2, ...)` fails: use `x // 2` or `int(...)`.
- **Exact arity.** Call only methods listed in the API reference, with its argument count.
- `File` has no `write`: write files with `SD.write(path, text)`; read with `SD.read(path)`.

## App structure and UI conventions

- One file: `main.py`. It runs top to bottom; end it with `App().run()` (or similar).
- Screen is 240x135. Draw with `BandedSprite(12)`: `while sprite.draw(): render()`
  where `render()` repaints the WHOLE screen (it runs once per band).
  Avoid a full-screen `Sprite(240, 135)`: it needs a 64 KB buffer on a device
  with no spare RAM.
- UI style (AREA512 Gallery): `Widget.header(sp, "TITLE", right)` on top,
  `Widget.footer(sp, hint)` at the bottom with the key hints, body between
  `Widget.body_top()` and `Widget.body_bottom()`. Use the theme colours
  (`Widget.theme_text()`, `theme_emphasis()`, `theme_selected()`,
  `theme_border()`, `theme_box()`, `theme_background()`), never hard-coded RGB,
  unless a colour is the point of the app.
- Keys: `Widget.read_key()` returns "UP" "DOWN" "LEFT" "RIGHT" "ENTER" "ESC" "BS"
  or a one-character string. Wrap it in raw mode exactly as the skeleton does.
  Also accept vim keys: j/k = down/up, h/l = left/right.
- `q` (and `ESC` on the main screen) quits. Always clean up in `finally`:
  `sprite.delete()` then `Display.fill_screen(Widget.theme_background())`.
- Real-time apps (games, animation): poll with `IO().read_nonblock(1)` (returns
  a char or None) and `sleep_ms(30)` per frame, like Space Lander.
- Persistent data: store it under the app's own folder `/home/ai/<app-name>/`
  with `SD.write`/`SD.read`; create the folder with `Dir.mkdir` if missing.
- Random numbers: `RNG.random_int()` (non-negative int); use `%` to bound it.
- Keep it small: under ~400 lines, few objects, no big lists of strings in
  loops. RAM is roughly 100 KB for the whole app.
