# TALLY: three named counters saved to the SD card.

TITLE = "TALLY"
DIR_PATH = "/home/ai/tally3"
DATA_PATH = "/home/ai/tally3/data.txt"
HINT = "UP/DOWN pick  ENTER +1  BS -1  r name  q quit"
ROW_H = 30
CAP = 99999


def clean_name(text):
    out = ""
    n = 0
    t = text.strip()
    for i in range(len(t)):
        if n >= 10:
            break
        c = t[i]
        if c == "|" or c == "\n" or c == "\r":
            c = " "
        out = out + c
        n = n + 1
    return out.strip()


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.names = ["A", "B", "C"]
        self.counts = [0, 0, 0]
        self.sel = 0
        self.message = HINT

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
            lines = SD.read(DATA_PATH).split("\n")
            names = []
            counts = []
            for line in lines:
                if len(names) >= 3:
                    break
                line = line.strip()
                if line == "":
                    continue
                p = line.find("|")
                if p < 0:
                    return
                name = ""
                for i in range(p):
                    name = name + line[i]
                num = ""
                for i in range(p + 1, len(line)):
                    num = num + line[i]
                num = num.strip()
                name = clean_name(name)
                if name == "" or not num.isdigit():
                    return
                v = int(num)
                if v > CAP:
                    v = CAP
                names.append(name)
                counts.append(v)
            if len(names) == 3:
                self.names = names
                self.counts = counts
        except Exception:
            self.names = ["A", "B", "C"]
            self.counts = [0, 0, 0]

    def save(self):
        try:
            if not Dir.exist(DIR_PATH):
                Dir.mkdir(DIR_PATH)
            text = ""
            for i in range(3):
                text = text + "{}|{}\n".format(self.names[i], self.counts[i])
            SD.write(DATA_PATH, text)
            self.message = "saved"
        except Exception:
            self.message = "save failed"

    def add(self, d):
        v = self.counts[self.sel] + d
        if v < 0:
            v = 0
        if v > CAP:
            v = CAP
        self.counts[self.sel] = v
        self.save()

    def rename(self):
        res = Widget.input(self.sprite, "Name", self.names[self.sel])
        if res is None:
            return
        name = clean_name(res)
        if name == "":
            return
        self.names[self.sel] = name
        self.save()

    def reset(self):
        if Widget.confirm(self.sprite, "Reset counter?"):
            self.counts[self.sel] = 0
            self.save()

    def handle(self, key):
        if key == "q" or key == "ESC":
            self.save()
            self.quit = True
        elif key == "UP" or key == "k":
            self.sel = (self.sel + 2) % 3
        elif key == "DOWN" or key == "j":
            self.sel = (self.sel + 1) % 3
        elif key == "ENTER" or key == " " or key == "RIGHT" or key == "l":
            self.add(1)
        elif key == "BS" or key == "LEFT" or key == "h":
            self.add(-1)
        elif key == "1":
            self.sel = 0
        elif key == "2":
            self.sel = 1
        elif key == "3":
            self.sel = 2
        elif key == "r":
            self.rename()
        elif key == "z":
            self.reset()

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        Widget.header(sp, TITLE, "{}/3".format(self.sel + 1))
        top = Widget.body_top()
        for i in range(3):
            y = top + i * ROW_H
            txt = "{}".format(self.counts[i])
            if i == self.sel:
                sp.fill_rect(2, y, 236, ROW_H - 2, Widget.theme_box())
                sp.rect(2, y, 236, ROW_H - 2, Widget.theme_selected())
                sp.text(8, y + 9, self.names[i], Widget.theme_selected())
            else:
                sp.text(8, y + 9, self.names[i], Widget.theme_text())
            Widget.big_text(sp, 232 - 12 * len(txt), y + 3, txt)
        Widget.footer(sp, self.message)

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
