# Minimal AREA512 widget app: header / body / footer, blocking key loop.
# Everything here is a builtin: no imports.

TITLE = "COUNTER"
DATA_PATH = "/home/ai/counter/data.txt"


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.count = 0
        self.message = "j/k change  s save  q quit"

    def read_key(self):
        # Widget.read_key() returns "UP" "DOWN" "LEFT" "RIGHT" "ENTER" "ESC"
        # "BS" or a one-character string. Wrap it in raw mode like this.
        self.console.raw()
        try:
            return Widget.read_key()
        finally:
            self.console._restore_termios()

    def load(self):
        if File.exist(DATA_PATH):
            text = SD.read(DATA_PATH).strip()
            if text.isdigit():
                self.count = int(text)

    def save(self):
        if not Dir.exist("/home/ai/counter"):
            Dir.mkdir("/home/ai/counter")
        SD.write(DATA_PATH, str(self.count))
        self.message = "saved"

    def handle(self, key):
        if key == "q" or key == "ESC":
            self.quit = True
        elif key == "k" or key == "UP":
            self.count = self.count + 1
        elif key == "j" or key == "DOWN":
            self.count = self.count - 1
        elif key == "s":
            self.save()

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        Widget.header(sp, TITLE, "v1")
        Widget.big_text(sp, 20, 50, "{}".format(self.count))
        Widget.gauge(sp, 20, 90, 200, self.count % 11, 10)
        Widget.footer(sp, self.message)

    def draw(self):
        # BandedSprite renders the screen band by band: render() must redraw
        # the WHOLE screen every time draw() returns True.
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
