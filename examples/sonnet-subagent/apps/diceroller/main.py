# DICE ROLLER: pick a die (d4..d20) and a count, roll, see each die and the total.
# Everything here is a builtin: no imports.

TITLE = "DICE ROLLER"
DATA_DIR = "/home/ai/diceroller"
DATA_PATH = "/home/ai/diceroller/data.txt"
SIDES = [4, 6, 8, 10, 12, 20]
MAIN_HINT = "L/R die  U/D count  ENTER roll  h hist  q quit"


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.die = 1
        self.count = 1
        self.rolled = False
        self.results = []
        self.total = 0
        self.last_label = ""
        self.history = []
        self.show_history = False
        self.hist_list = WidgetList()

    def read_key(self):
        self.console.raw()
        try:
            return Widget.read_key()
        finally:
            self.console._restore_termios()

    def load(self):
        try:
            if File.exist(DATA_PATH):
                parts = SD.read(DATA_PATH).strip().split(" ")
                if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                    d = int(parts[0])
                    c = int(parts[1])
                    if d >= 0 and d < len(SIDES):
                        self.die = d
                    if c >= 1 and c <= 10:
                        self.count = c
        except Exception:
            pass

    def save(self):
        try:
            if not Dir.exist(DATA_DIR):
                Dir.mkdir(DATA_DIR)
            SD.write(DATA_PATH, "{} {}".format(self.die, self.count))
        except Exception:
            pass

    def roll(self):
        sides = SIDES[self.die]
        res = []
        total = 0
        for i in range(self.count):
            v = RNG.random_int() % sides + 1
            res.append(v)
            total = total + v
        self.results = res
        self.total = total
        self.rolled = True
        self.last_label = "{}d{}".format(self.count, sides)
        self.history.insert(0, "{} = {}".format(self.last_label, total))
        if len(self.history) > 8:
            self.history.pop()

    def open_history(self):
        self.hist_list.clear()
        self.hist_list.set_empty_text("No rolls yet")
        for h in self.history:
            self.hist_list.add(h)
        self.show_history = True

    def do_quit(self):
        self.save()
        self.quit = True

    def handle(self, key):
        if self.show_history:
            if key == "ESC" or key == "i" or key == "H":
                self.show_history = False
            elif key == "q":
                self.do_quit()
            else:
                self.hist_list.handle(key)
            return
        if key == "q" or key == "ESC":
            self.do_quit()
        elif key == "LEFT" or key == "h":
            self.die = (self.die + len(SIDES) - 1) % len(SIDES)
        elif key == "RIGHT" or key == "l":
            self.die = (self.die + 1) % len(SIDES)
        elif key == "UP" or key == "k":
            if self.count < 10:
                self.count = self.count + 1
        elif key == "DOWN" or key == "j":
            if self.count > 1:
                self.count = self.count - 1
        elif key == "0":
            self.count = 10
        elif len(key) == 1 and key >= "1" and key <= "9":
            self.count = int(key)
        elif key == "ENTER" or key == " " or key == "r":
            self.roll()
        elif key == "s":
            self.save()
        elif key == "i" or key == "H":
            self.open_history()

    def render_history(self, sp):
        Widget.header(sp, "HISTORY", "")
        self.hist_list.draw(sp)
        Widget.footer(sp, "ESC back")

    def render_main(self, sp):
        right = ""
        if self.rolled:
            right = "{}".format(self.total)
        Widget.header(sp, TITLE, right)
        top = Widget.body_top() + 4
        for i in range(len(SIDES)):
            x = 8 + i * 37
            label = "d{}".format(SIDES[i])
            if i == self.die:
                Widget.badge(sp, x, top, label)
            else:
                sp.text(x + 2, top, label, Widget.theme_text())
        Widget.spinner(sp, 60, 48, 120, "{} dice".format(self.count), True)
        line = "{}d{}".format(self.count, SIDES[self.die])
        Widget.big_text(sp, 12, 68, line)
        if self.rolled:
            sp.text(130, 76, "TOTAL: {}".format(self.total), Widget.theme_emphasis())
            txt = ""
            for v in self.results:
                if txt == "":
                    txt = str(v)
                else:
                    txt = txt + " " + str(v)
            Widget.wrap_text(sp, 8, 96, 224, 20, txt, Widget.theme_text())
        else:
            Widget.wrap_text(sp, 8, 96, 224, 20, "ENTER to roll", Widget.theme_text())
        Widget.footer(sp, MAIN_HINT)

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        if self.show_history:
            self.render_history(sp)
        else:
            self.render_main(sp)

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
