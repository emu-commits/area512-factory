# Stopwatch with laps. Counts frames (1 frame = 1 centisecond), no clock.

DIR_PATH = "/home/ai/stopwatch"
DATA_PATH = "/home/ai/stopwatch/best.txt"
MAX_LAPS = 99

ST_READY = 0
ST_RUN = 1
ST_STOP = 2


def pad2(n):
    if n < 10:
        return "0" + str(n)
    return str(n)


def fmt(cs):
    mins = cs // 6000
    secs = (cs // 100) % 60
    c = cs % 100
    return pad2(mins) + ":" + pad2(secs) + "." + pad2(c)


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.state = ST_READY
        self.elapsed = 0
        self.last_total = 0
        self.totals = []
        self.splits = []
        self.best = 0
        self.screen = 0
        self.wl = None
        self.toast = ""
        self.toast_frames = 0

    def read_key(self):
        k = self.console.read_nonblock(1)
        if k is None:
            return ""
        if k == "\x1b":
            sleep_ms(3)
            k2 = self.console.read_nonblock(1)
            if k2 is None:
                return "ESC"
            if k2 == "[" or k2 == "O":
                k3 = self.console.read_nonblock(1)
                if k3 == "A":
                    return "UP"
                if k3 == "B":
                    return "DOWN"
            return ""
        return k

    def load(self):
        try:
            if File.exist(DATA_PATH):
                text = SD.read(DATA_PATH).strip()
                if text.isdigit():
                    self.best = int(text)
        except OSError:
            pass

    def save(self):
        try:
            if not Dir.exist(DIR_PATH):
                Dir.mkdir(DIR_PATH)
            SD.write(DATA_PATH, str(self.best))
            self.say("saved " + fmt(self.best))
        except OSError:
            self.say("save failed")

    def say(self, msg):
        self.toast = msg
        self.toast_frames = 80

    def fastest(self):
        idx = -1
        for i in range(len(self.splits)):
            if idx < 0 or self.splits[i] < self.splits[idx]:
                idx = i
        return idx

    def add_lap(self):
        if len(self.splits) >= MAX_LAPS:
            return
        split = self.elapsed - self.last_total
        self.last_total = self.elapsed
        self.totals.append(self.elapsed)
        self.splits.append(split)
        if self.best == 0 or split < self.best:
            self.best = split
            self.save()

    def reset(self):
        self.state = ST_READY
        self.elapsed = 0
        self.last_total = 0
        self.totals = []
        self.splits = []

    def open_history(self):
        self.wl = WidgetList()
        self.wl.set_empty_text("no laps yet")
        f = self.fastest()
        for i in range(len(self.splits)):
            text = "{}  {}".format(i + 1, fmt(self.splits[i]))
            if i == f:
                text = text + " *"
            self.wl.add(text)
        self.screen = 1

    def handle(self, key):
        if key == "":
            return
        if key == "q":
            self.quit = True
            return
        if self.screen == 1:
            if key == "ESC":
                self.screen = 0
            elif key == "UP" or key == "k":
                self.wl.handle("k")
            elif key == "DOWN" or key == "j":
                self.wl.handle("j")
            return
        if key == "ESC":
            self.quit = True
        elif key == " ":
            if self.state == ST_RUN:
                self.state = ST_STOP
            else:
                self.state = ST_RUN
        elif key == "l" or key == "\r" or key == "\n":
            if self.state == ST_RUN:
                self.add_lap()
        elif key == "r":
            if self.state != ST_RUN:
                self.reset()
        elif key == "h":
            self.open_history()
        elif key == "s":
            if self.best > 0:
                self.save()
            else:
                self.say("no best lap yet")

    def render_main(self):
        sp = self.sprite
        if self.state == ST_RUN:
            right = "RUN"
        elif self.state == ST_STOP:
            right = "STOP"
        else:
            right = "READY"
        Widget.header(sp, "STOPWATCH", right)
        Widget.big_text(sp, 72, 28, fmt(self.elapsed))
        n = len(self.splits)
        if n == 0:
            if self.best > 0:
                Widget.text_center(sp, 70, "best " + fmt(self.best))
            else:
                Widget.text_center(sp, 70, "no laps yet")
        else:
            f = self.fastest()
            rows = 4
            if n < 4:
                rows = n
            for r in range(rows):
                i = n - 1 - r
                line = "LAP {}  {}  +{}".format(i + 1, fmt(self.totals[i]), fmt(self.splits[i]))
                color = Widget.theme_text()
                if i == f:
                    color = Widget.theme_selected()
                sp.text(8, 58 + r * 12, line, color)
        Widget.footer(sp, "SPACE start/stop  l lap  r reset  q quit")

    def render_history(self):
        sp = self.sprite
        Widget.header(sp, "LAPS", "{}".format(len(self.splits)))
        self.wl.draw(sp)
        Widget.footer(sp, "UP/DOWN scroll  ESC back")

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        if self.screen == 1:
            self.render_history()
        else:
            self.render_main()
        if self.toast_frames > 0:
            Widget.toast(sp, self.toast)

    def draw(self):
        while self.sprite.draw():
            self.render()

    def run(self):
        Display.fill_screen(Widget.theme_background())
        self.sprite = BandedSprite(12)
        self.console.raw()
        try:
            self.load()
            while not self.quit:
                self.handle(self.read_key())
                if self.state == ST_RUN:
                    self.elapsed = self.elapsed + 1
                if self.toast_frames > 0:
                    self.toast_frames = self.toast_frames - 1
                self.draw()
                sleep_ms(10)
        finally:
            self.console._restore_termios()
            self.sprite.delete()
            self.sprite = None
            Display.fill_screen(Widget.theme_background())


App().run()
