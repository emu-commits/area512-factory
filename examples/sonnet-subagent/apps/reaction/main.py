# Reaction test: 5 rounds, frame-based timing (1 frame = 30 ms).

TITLE = "REACTION TEST"
DIR_PATH = "/home/ai/reaction"
DATA_PATH = "/home/ai/reaction/best.txt"
FRAME_MS = 30
ROUNDS = 5
GREEN = 0x00C000
RED = 0xC00000

S_READY = 0
S_WAIT = 1
S_GO = 2
S_RESULT = 3
S_SUMMARY = 4


def center_x(text):
    x = (240 - len(text) * 12) // 2
    if x < 0:
        x = 0
    return x


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.state = S_READY
        self.best = 0
        self.times = []
        self.wait_left = 0
        self.frames = 0
        self.early = False
        self.last_ms = 0
        self.avg = 0
        self.fast = 0
        self.slow = 0
        self.new_best = False
        self.dirty = True

    def read_key(self):
        key = self.console.read_nonblock(1)
        return "" if key is None else key

    def load(self):
        if File.exist(DATA_PATH):
            text = SD.read(DATA_PATH).strip()
            if text.isdigit():
                self.best = int(text)

    def save(self):
        if not Dir.exist(DIR_PATH):
            Dir.mkdir(DIR_PATH)
        SD.write(DATA_PATH, str(self.best))

    def start_round(self):
        self.state = S_WAIT
        self.wait_left = RNG.random_int() % 80 + 40
        self.early = False
        self.dirty = True

    def finish_run(self):
        total = 0
        fast = self.times[0]
        slow = self.times[0]
        for t in self.times:
            total = total + t
            if t < fast:
                fast = t
            if t > slow:
                slow = t
        self.avg = total // len(self.times)
        self.fast = fast
        self.slow = slow
        self.new_best = False
        if self.best == 0 or self.avg < self.best:
            self.new_best = True
            self.best = self.avg
            try:
                self.save()
            except OSError:
                pass
        self.state = S_SUMMARY
        self.dirty = True

    def act(self):
        if self.state == S_READY:
            self.times = []
            self.start_round()
        elif self.state == S_WAIT:
            self.early = True
            self.state = S_RESULT
            self.dirty = True
        elif self.state == S_GO:
            self.last_ms = self.frames * FRAME_MS
            self.times.append(self.last_ms)
            self.early = False
            self.state = S_RESULT
            self.dirty = True
        elif self.state == S_RESULT:
            if self.early:
                self.start_round()
            elif len(self.times) >= ROUNDS:
                self.finish_run()
            else:
                self.start_round()
        elif self.state == S_SUMMARY:
            self.times = []
            self.start_round()

    def handle(self, key):
        if key == "":
            return
        if key == "q" or key == "\x1b":
            self.quit = True
        elif key == " " or key == "\r" or key == "\n":
            self.act()

    def step(self):
        if self.state == S_WAIT:
            self.wait_left = self.wait_left - 1
            if self.wait_left <= 0:
                self.state = S_GO
                self.frames = 0
                self.dirty = True
        elif self.state == S_GO:
            self.frames = self.frames + 1
            if self.frames >= 200:
                self.last_ms = self.frames * FRAME_MS
                self.times.append(self.last_ms)
                self.early = False
                self.state = S_RESULT
                self.dirty = True

    def rounds_text(self):
        s = ""
        i = 0
        for t in self.times:
            i = i + 1
            if i > 1:
                s = s + " "
            s = s + "{}:{}".format(i, t)
        return s

    def best_text(self):
        if self.best > 0:
            return "best {}".format(self.best)
        return "best --"

    def fill_body(self, color):
        top = Widget.body_top()
        h = Widget.body_bottom() - top + 1
        self.sprite.fill_rect(0, top, 240, h, color)

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        st = self.state
        if st == S_READY:
            Widget.header(sp, TITLE, self.best_text())
            Widget.text_center(sp, 50, "Press SPACE to start")
            if self.best > 0:
                Widget.text_center(sp, 72, "Best average: {} ms".format(self.best))
            else:
                Widget.text_center(sp, 72, "Best average: --")
            Widget.footer(sp, "SPACE start  q quit")
        elif st == S_WAIT:
            Widget.header(sp, TITLE, self.best_text())
            self.fill_body(Widget.theme_box())
            Widget.big_text(sp, center_x("WAIT..."), 55, "WAIT...")
            Widget.text_center(sp, 90, "Round {}/{}".format(len(self.times) + 1, ROUNDS))
            Widget.footer(sp, "press SPACE when green")
        elif st == S_GO:
            Widget.header(sp, TITLE, self.best_text())
            self.fill_body(GREEN)
            Widget.big_text(sp, center_x("GO!"), 55, "GO!", Widget.bg())
            Widget.footer(sp, "SPACE now!")
        elif st == S_RESULT:
            Widget.header(sp, TITLE, self.best_text())
            if self.early:
                msg = "Too early!"
                Widget.big_text(sp, center_x(msg), 35, msg, RED)
            else:
                msg = "Round {}: {} ms".format(len(self.times), self.last_ms)
                Widget.big_text(sp, center_x(msg), 35, msg)
            Widget.wrap_text(sp, 10, 75, 220, 40, self.rounds_text())
            Widget.footer(sp, "SPACE next  q quit")
        else:
            Widget.header(sp, TITLE, self.best_text())
            Widget.titled_panel(sp, 20, 25, 200, 90, "RESULTS")
            Widget.text_center(sp, 47, "Average: {} ms".format(self.avg))
            Widget.text_center(sp, 63, "Fastest: {} ms".format(self.fast))
            Widget.text_center(sp, 79, "Slowest: {} ms".format(self.slow))
            if self.new_best:
                Widget.badge(sp, 92, 96, "NEW BEST")
            Widget.footer(sp, "SPACE again  q quit")

    def draw(self):
        while self.sprite.draw():
            self.render()

    def run(self):
        Display.fill_screen(Widget.theme_background())
        self.sprite = BandedSprite(12)
        try:
            self.load()
            while not self.quit:
                self.handle(self.read_key())
                if self.quit:
                    break
                self.step()
                if self.dirty:
                    self.dirty = False
                    self.draw()
                sleep_ms(FRAME_MS)
        finally:
            self.sprite.delete()
            self.sprite = None
            Display.fill_screen(Widget.theme_background())


App().run()
