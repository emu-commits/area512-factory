# 2048: sliding tile puzzle with a saved best score.

TITLE = "2048"
DIR_PATH = "/home/ai/game2048"
DATA_PATH = "/home/ai/game2048/best.txt"


def slide_line(line):
    # Slide one line of 4 values toward index 0.
    # Returns (new_line, points_gained).
    vals = []
    for v in line:
        if v != 0:
            vals.append(v)
    out = []
    gained = 0
    k = 0
    n = len(vals)
    while k < n:
        if k + 1 < n and vals[k] == vals[k + 1]:
            m = vals[k] * 2
            out.append(m)
            gained = gained + m
            k = k + 2
        else:
            out.append(vals[k])
            k = k + 1
    while len(out) < 4:
        out.append(0)
    return (out, gained)


def line_index(direction, i, j):
    # Board index of the j-th cell (from the leading edge) of line i.
    # direction: 0 left, 1 right, 2 up, 3 down
    if direction == 0:
        return i * 4 + j
    if direction == 1:
        return i * 4 + 3 - j
    if direction == 2:
        return j * 4 + i
    return (3 - j) * 4 + i


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.board = [0] * 16
        self.score = 0
        self.best = 0
        self.moves = 0
        self.won = False
        self.message = ""

    def read_key(self):
        self.console.raw()
        try:
            return Widget.read_key()
        finally:
            self.console._restore_termios()

    def load(self):
        self.best = 0
        try:
            if File.exist(DATA_PATH):
                text = SD.read(DATA_PATH).strip()
                if text.isdigit():
                    self.best = int(text)
        except OSError:
            self.best = 0

    def save(self):
        try:
            if not Dir.exist(DIR_PATH):
                Dir.mkdir(DIR_PATH)
            SD.write(DATA_PATH, str(self.best))
        except OSError:
            pass

    def add_tile(self):
        empties = []
        for i in range(16):
            if self.board[i] == 0:
                empties.append(i)
        if len(empties) == 0:
            return
        pos = empties[RNG.random_int() % len(empties)]
        if RNG.random_int() % 10 == 0:
            self.board[pos] = 4
        else:
            self.board[pos] = 2

    def new_game(self):
        self.board = [0] * 16
        self.score = 0
        self.moves = 0
        self.won = False
        self.add_tile()
        self.add_tile()
        self.message = "NEW GAME"

    def move(self, direction):
        changed = False
        gained = 0
        for i in range(4):
            line = []
            for j in range(4):
                line.append(self.board[line_index(direction, i, j)])
            res = slide_line(line)
            new_line = res[0]
            gained = gained + res[1]
            for j in range(4):
                idx = line_index(direction, i, j)
                if self.board[idx] != new_line[j]:
                    changed = True
                    self.board[idx] = new_line[j]
        if changed:
            self.score = self.score + gained
            self.moves = self.moves + 1
        return changed

    def can_move(self):
        for i in range(16):
            if self.board[i] == 0:
                return True
        for r in range(4):
            for c in range(4):
                v = self.board[r * 4 + c]
                if c < 3 and self.board[r * 4 + c + 1] == v:
                    return True
                if r < 3 and self.board[(r + 1) * 4 + c] == v:
                    return True
        return False

    def has_2048(self):
        for i in range(16):
            if self.board[i] >= 2048:
                return True
        return False

    def after_move(self):
        if self.score > self.best:
            self.best = self.score
            self.save()
        self.message = "YOU WIN" if self.won else ""
        if not self.won and self.has_2048():
            self.won = True
            self.message = "YOU WIN"
            self.draw()
            choice = Widget.dialog(
                self.sprite, "You made 2048!", ["Keep going", "New game"]
            )
            if choice == 1:
                self.new_game()
            return
        if not self.can_move():
            self.message = "NO MOVES LEFT"
            self.draw()
            choice = Widget.dialog(
                self.sprite,
                "No moves left. Score {}".format(self.score),
                ["New game", "Quit"],
            )
            if choice == 1:
                self.quit = True
            else:
                self.new_game()

    def do_move(self, direction):
        if self.move(direction):
            self.add_tile()
            self.after_move()

    def handle(self, key):
        if key == "q" or key == "ESC":
            self.quit = True
        elif key == "UP" or key == "k":
            self.do_move(2)
        elif key == "DOWN" or key == "j":
            self.do_move(3)
        elif key == "LEFT" or key == "h":
            self.do_move(0)
        elif key == "RIGHT" or key == "l":
            self.do_move(1)
        elif key == "n":
            if self.score > 0:
                self.draw()
                if Widget.confirm(self.sprite, "Start a new game?"):
                    self.new_game()
            else:
                self.new_game()

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        Widget.header(sp, TITLE, "S {}".format(self.score))
        top = Widget.body_top() + 2
        for r in range(4):
            for c in range(4):
                v = self.board[r * 4 + c]
                text = "" if v == 0 else str(v)
                Widget.cell(
                    sp, 8 + c * 28, top + r * 28, 26, 26, text, v >= 128
                )
        tx = Widget.theme_text()
        em = Widget.theme_emphasis()
        sp.text(130, top, "SCORE", tx)
        sp.text(130, top + 13, str(self.score), em)
        sp.text(130, top + 31, "BEST", tx)
        sp.text(130, top + 44, str(self.best), em)
        sp.text(130, top + 62, "MOVES", tx)
        sp.text(130, top + 75, str(self.moves), em)
        if self.message != "":
            sp.text(130, top + 93, self.message, Widget.theme_selected())
        Widget.footer(sp, "arrows/hjkl move  n new  q quit")

    def draw(self):
        while self.sprite.draw():
            self.render()

    def run(self):
        Display.fill_screen(Widget.theme_background())
        self.sprite = BandedSprite(12)
        try:
            self.load()
            self.new_game()
            while not self.quit:
                self.draw()
                self.handle(self.read_key())
            if self.score > self.best:
                self.best = self.score
            self.save()
        finally:
            self.sprite.delete()
            self.sprite = None
            Display.fill_screen(Widget.theme_background())


App().run()
