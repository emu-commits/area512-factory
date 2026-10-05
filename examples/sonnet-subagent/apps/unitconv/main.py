# Unit converter: length, weight, temperature.
TITLE = "UNIT CONVERTER"
DIR_PATH = "/home/ai/unitconv"
DATA_PATH = "/home/ai/unitconv/state.txt"

CATS = ["LENGTH", "WEIGHT", "TEMP"]
UNITS = [
    ["mm", "cm", "m", "km", "in", "ft", "yd", "mi"],
    ["mg", "g", "kg", "oz", "lb"],
    ["C", "F", "K"],
]
FACTORS = [
    [0.001, 0.01, 1.0, 1000.0, 0.0254, 0.3048, 0.9144, 1609.344],
    [0.001, 1.0, 1000.0, 28.349523, 453.59237],
    [1.0, 1.0, 1.0],
]


def parse(text):
    has_digit = False
    for ch in text:
        if ch.isdigit():
            has_digit = True
    if not has_digit:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def to_celsius(unit, v):
    if unit == 1:
        return (v - 32.0) * 5.0 / 9.0
    if unit == 2:
        return v - 273.15
    return v


def from_celsius(unit, c):
    if unit == 1:
        return c * 9.0 / 5.0 + 32.0
    if unit == 2:
        return c + 273.15
    return c


def convert(cat, fi, ti, v):
    if cat == 2:
        return from_celsius(ti, to_celsius(fi, v))
    base = v * FACTORS[cat][fi]
    return base / FACTORS[cat][ti]


def fmt(x):
    s = "{:.4f}".format(x)
    s = s.rstrip("0")
    s = s.rstrip(".")
    if s == "" or s == "-0" or s == "-":
        s = "0"
    return s


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.cat = 0
        self.fi = 0
        self.ti = 1
        self.entry = ""
        self.saved = 0

    def read_key(self):
        self.console.raw()
        try:
            return Widget.read_key()
        finally:
            self.console._restore_termios()

    def load(self):
        try:
            if not File.exist(DATA_PATH):
                return
            text = SD.read(DATA_PATH).strip()
        except OSError:
            return
        parts = text.split(" ")
        if len(parts) < 3:
            return
        if not (parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit()):
            return
        cat = int(parts[0])
        fi = int(parts[1])
        ti = int(parts[2])
        if cat >= len(CATS):
            return
        if fi >= len(UNITS[cat]) or ti >= len(UNITS[cat]):
            return
        self.cat = cat
        self.fi = fi
        self.ti = ti
        if len(parts) > 3:
            self.entry = parts[3]

    def save(self):
        try:
            if not Dir.exist(DIR_PATH):
                Dir.mkdir(DIR_PATH)
            SD.write(
                DATA_PATH,
                "{} {} {} {}".format(self.cat, self.fi, self.ti, self.entry),
            )
            self.saved = 20
        except OSError:
            self.saved = 0

    def set_cat(self, cat):
        self.cat = cat
        self.fi = 0
        self.ti = 1
        if cat == 2:
            self.fi = 0
            self.ti = 1

    def drop_last(self):
        out = ""
        n = len(self.entry) - 1
        for i in range(n):
            out = out + self.entry[i]
        self.entry = out

    def toggle_minus(self):
        if self.entry != "" and self.entry[0] == "-":
            out = ""
            for i in range(1, len(self.entry)):
                out = out + self.entry[i]
            self.entry = out
        elif len(self.entry) < 10:
            self.entry = "-" + self.entry

    def handle(self, key):
        n = len(UNITS[self.cat])
        if key == "q" or key == "ESC":
            self.quit = True
        elif len(key) == 1 and key.isdigit():
            if len(self.entry) < 10:
                self.entry = self.entry + key
        elif key == ".":
            if self.entry.find(".") < 0 and len(self.entry) < 10:
                self.entry = self.entry + "."
        elif key == "-":
            self.toggle_minus()
        elif key == "BS":
            self.drop_last()
        elif key == "c":
            self.entry = ""
        elif key == "LEFT" or key == "h":
            self.set_cat((self.cat + 2) % 3)
        elif key == "RIGHT" or key == "l":
            self.set_cat((self.cat + 1) % 3)
        elif key == "UP" or key == "k":
            self.fi = (self.fi + n - 1) % n
        elif key == "DOWN" or key == "j":
            self.fi = (self.fi + 1) % n
        elif key == "s":
            self.ti = (self.ti + 1) % n
        elif key == "x":
            t = self.fi
            self.fi = self.ti
            self.ti = t
        elif key == "ENTER":
            self.save()
            return
        if self.saved > 0:
            self.saved = self.saved - 1

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        Widget.header(sp, TITLE, CATS[self.cat])
        top = Widget.body_top()
        Widget.tabs(sp, top, CATS, self.cat)
        units = UNITS[self.cat]
        v = parse(self.entry)
        res = fmt(convert(self.cat, self.fi, self.ti, v))
        Widget.field(sp, 6, top + 26, 228, "From  " + units[self.fi], self.entry + "_", True)
        Widget.field(sp, 6, top + 46, 228, "To    " + units[self.ti], res, False)
        Widget.text_center(
            sp,
            top + 70,
            "{} -> {}".format(units[self.fi], units[self.ti]),
            Widget.theme_text(),
        )
        if self.saved > 0:
            Widget.toast(sp, "saved")
        Widget.footer(sp, "0-9 . - BS  UD from s to x swap c clr")

    def draw(self):
        while self.sprite.draw():
            self.render()

    def run(self):
        Display.fill_screen(Widget.theme_background())
        self.sprite = BandedSprite(12)
        try:
            self.load()
            while not self.quit:
                self.draw()
                self.handle(self.read_key())
        finally:
            self.sprite.delete()
            self.sprite = None
            Display.fill_screen(Widget.theme_background())


App().run()
