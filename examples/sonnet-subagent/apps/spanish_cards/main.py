# Spanish flashcards: reveal the answer, mark what you knew, keep a best score.

TITLE = "SPANISH CARDS"
DIR_PATH = "/home/ai/spanish_cards"
BEST_PATH = "/home/ai/spanish_cards/best.txt"
ROUND = 12

DECK = [
    ("hola", "hello"),
    ("adios", "goodbye"),
    ("gracias", "thank you"),
    ("por favor", "please"),
    ("agua", "water"),
    ("casa", "house"),
    ("perro", "dog"),
    ("gato", "cat"),
    ("libro", "book"),
    ("cafe", "coffee"),
    ("nino", "child"),
    ("amigo", "friend"),
    ("comida", "food"),
    ("noche", "night"),
    ("dia", "day"),
    ("sol", "sun"),
    ("luna", "moon"),
    ("rojo", "red"),
    ("azul", "blue"),
    ("grande", "big"),
    ("pequeno", "small"),
    ("feliz", "happy"),
    ("tiempo", "time"),
    ("ciudad", "city"),
]


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.order = []
        self.marks = []
        self.pos = 0
        self.revealed = False
        self.done = False
        self.best = 0
        self.right = 0
        self.miss = 0

    def read_key(self):
        self.console.raw()
        try:
            return Widget.read_key()
        finally:
            self.console._restore_termios()

    def load(self):
        if File.exist(BEST_PATH):
            text = SD.read(BEST_PATH).strip()
            if text.isdigit():
                self.best = int(text)

    def save(self):
        if not Dir.exist(DIR_PATH):
            Dir.mkdir(DIR_PATH)
        SD.write(BEST_PATH, str(self.best))

    def deal(self):
        idx = []
        for i in range(len(DECK)):
            idx.append(i)
        i = len(idx) - 1
        while i > 0:
            j = RNG.random_int() % (i + 1)
            t = idx[i]
            idx[i] = idx[j]
            idx[j] = t
            i = i - 1
        self.order = []
        self.marks = []
        for i in range(ROUND):
            self.order.append(idx[i])
            self.marks.append(0)
        self.pos = 0
        self.revealed = False
        self.done = False
        self.right = 0
        self.miss = 0

    def tally(self):
        r = 0
        m = 0
        for v in self.marks:
            if v == 1:
                r = r + 1
            elif v == 2:
                m = m + 1
        self.right = r
        self.miss = m

    def next_card(self):
        self.pos = self.pos + 1
        self.revealed = False
        if self.pos >= ROUND:
            self.pos = ROUND - 1
            self.tally()
            self.done = True
            if self.right > self.best:
                self.best = self.right
                self.save()

    def prev_card(self):
        if self.pos > 0:
            self.pos = self.pos - 1
            self.marks[self.pos] = 0
            self.revealed = False
            self.tally()

    def mark(self, value):
        self.marks[self.pos] = value
        self.tally()
        self.next_card()

    def handle(self, key):
        if key == "q":
            self.quit = True
            return
        if key == "ESC":
            self.quit = True
            return
        if key == "r":
            self.deal()
            return
        if self.done:
            return
        if not self.revealed:
            if key == " " or key == "ENTER":
                self.revealed = True
            elif key == "LEFT" or key == "h":
                self.prev_card()
        else:
            if key == "y":
                self.mark(1)
            elif key == "n":
                self.mark(2)
            elif key == "ENTER" or key == "RIGHT" or key == "l":
                self.next_card()
            elif key == "LEFT" or key == "h":
                self.prev_card()

    def big_x(self, text):
        x = (Display.width() - 12 * len(text)) // 2
        if x < 0:
            x = 0
        return x

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        if self.done:
            self.render_results(sp)
            return
        card = DECK[self.order[self.pos]]
        Widget.header(sp, TITLE, "{}/{}".format(self.pos + 1, ROUND))
        score = "Right {}  Miss {}".format(self.right, self.miss)
        if not self.revealed:
            Widget.big_text(sp, self.big_x(card[0]), 40, card[0])
            Widget.text_center(sp, 76, "? press SPACE to reveal", Widget.theme_text())
            Widget.text_right(sp, 236, 98, score)
            Widget.footer(sp, "SPACE reveal  q quit")
        else:
            Widget.text_center(sp, Widget.body_top() + 4, card[0], Widget.theme_text())
            Widget.big_text(sp, self.big_x(card[1]), 55, card[1])
            Widget.text_right(sp, 236, 98, score)
            Widget.footer(sp, "y knew it  n missed  q quit")

    def render_results(self, sp):
        Widget.header(sp, TITLE, "DONE")
        pct = self.right * 100 // ROUND
        Widget.center_lines(sp, [
            "Score: {} / {}".format(self.right, ROUND),
            "{} percent".format(pct),
            "Best: {}".format(self.best),
        ])
        Widget.gauge(sp, 20, 98, 200, pct, 100)
        Widget.footer(sp, "r restart  q quit")

    def draw(self):
        while self.sprite.draw():
            self.render()

    def run(self):
        Display.fill_screen(Widget.theme_background())
        self.sprite = BandedSprite(12)
        try:
            self.load()
            self.deal()
            while not self.quit:
                self.draw()
                self.handle(self.read_key())
        finally:
            self.sprite.delete()
            self.sprite = None
            Display.fill_screen(Widget.theme_background())


App().run()
