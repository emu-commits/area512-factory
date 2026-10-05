# POMODORO: 25 min focus / 5 min break timer, polled in frames (20 frames = 1 s).

TITLE = "POMODORO"
DIR_PATH = "/home/ai/pomodoro"
DATA_PATH = "/home/ai/pomodoro/count.txt"
FOCUS_FRAMES = 30000
BREAK_FRAMES = 6000
FRAME_MS = 50
TOAST_FRAMES = 60


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.focus = True
        self.running = False
        self.elapsed = 0
        self.count = 0
        self.toast = ""
        self.toast_left = 0

    def total(self):
        if self.focus:
            return FOCUS_FRAMES
        return BREAK_FRAMES

    def load(self):
        try:
            if File.exist(DATA_PATH):
                text = SD.read(DATA_PATH).strip()
                if text.isdigit():
                    self.count = int(text)
        except OSError:
            pass

    def save(self):
        try:
            if not Dir.exist(DIR_PATH):
                Dir.mkdir(DIR_PATH)
            SD.write(DATA_PATH, str(self.count))
        except OSError:
            pass

    def next_phase(self):
        self.focus = not self.focus
        self.elapsed = 0
        self.running = False

    def phase_done(self):
        if self.focus:
            self.count = self.count + 1
            self.save()
            self.toast = "Focus done! Break time"
        else:
            self.toast = "Break over! Focus"
        self.toast_left = TOAST_FRAMES
        self.next_phase()

    def ask_clear(self):
        self.console.raw()
        try:
            ok = Widget.confirm(self.sprite, "Clear session count?")
        finally:
            self.console._restore_termios()
        if ok:
            self.count = 0
            self.save()

    def handle(self, key):
        if key == "q" or key == "\x1b":
            self.quit = True
        elif key == " ":
            self.running = not self.running
        elif key == "n":
            self.next_phase()
        elif key == "r":
            self.elapsed = 0
            self.running = False
        elif key == "c":
            self.ask_clear()

    def step(self):
        if self.toast_left > 0:
            self.toast_left = self.toast_left - 1
        if self.running:
            self.elapsed = self.elapsed + 1
            if self.elapsed >= self.total():
                self.phase_done()

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        Widget.header(sp, TITLE, "#{}".format(self.count))
        label = "FOCUS" if self.focus else "BREAK"
        if not self.running:
            label = label + " (paused)"
        Widget.text_center(sp, 30, label)
        total = self.total()
        remain = total - self.elapsed
        secs = (remain + 19) // 20
        text = "{:02d}:{:02d}".format(secs // 60, secs % 60)
        Widget.big_text(sp, 86, 48, text)
        Widget.gauge(sp, 20, 90, 200, self.elapsed * 100 // total, 100)
        Widget.text_center(sp, 108, "Sessions: {}".format(self.count))
        Widget.footer(sp, "SPACE start/pause  n skip  r reset  q quit")
        if self.toast_left > 0:
            Widget.toast(sp, self.toast)

    def draw(self):
        while self.sprite.draw():
            self.render()

    def read_key(self):
        key = self.console.read_nonblock(1)
        return "" if key is None else key

    def run(self):
        Display.fill_screen(Widget.theme_background())
        self.sprite = BandedSprite(12)
        try:
            self.load()
            while not self.quit:
                self.draw()
                self.handle(self.read_key())
                self.step()
                sleep_ms(FRAME_MS)
        finally:
            self.sprite.delete()
            self.sprite = None
            Display.fill_screen(Widget.theme_background())


App().run()
