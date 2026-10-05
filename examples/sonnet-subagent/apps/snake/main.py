# SNAKE: real-time snake game. No imports; everything is builtin.

TITLE = "SNAKE"
DIR_PATH = "/home/ai/snake"
BEST_PATH = "/home/ai/snake/best.txt"
COLS = 20
ROWS = 10
CELL = 10
BOARD_X = 20
READY = 0
PLAY = 1
OVER = 2


def dir_of(key):
    if key == "UP" or key == "k" or key == "w":
        return (0, -1)
    if key == "DOWN" or key == "j" or key == "s":
        return (0, 1)
    if key == "LEFT" or key == "h" or key == "a":
        return (-1, 0)
    if key == "RIGHT" or key == "l" or key == "d":
        return (1, 0)
    return None


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.state = READY
        self.paused = False
        self.best = 0
        self.score = 0
        self.snake = []
        self.dx = 1
        self.dy = 0
        self.ndx = 1
        self.ndy = 0
        self.food = 0
        self.tick = 0
        self.board_y = Widget.body_top() + 2

    def load(self):
        try:
            if File.exist(BEST_PATH):
                text = SD.read(BEST_PATH).strip()
                if text.isdigit():
                    self.best = int(text)
        except OSError:
            pass

    def save(self):
        try:
            if not Dir.exist(DIR_PATH):
                Dir.mkdir(DIR_PATH)
            SD.write(BEST_PATH, str(self.best))
        except OSError:
            pass

    def reset(self):
        c = (ROWS // 2) * COLS + COLS // 2
        self.snake = [c, c - 1, c - 2]
        self.dx = 1
        self.dy = 0
        self.ndx = 1
        self.ndy = 0
        self.score = 0
        self.tick = 0
        self.paused = False
        self.place_food()

    def place_food(self):
        total = COLS * ROWS
        if len(self.snake) >= total:
            return
        f = RNG.random_int() % total
        while f in self.snake:
            f = RNG.random_int() % total
        self.food = f

    def speed(self):
        n = 6 - self.score // 5
        if n < 2:
            n = 2
        return n

    def end_game(self):
        self.state = OVER
        if self.score > self.best:
            self.best = self.score
            self.save()

    def step(self):
        self.dx = self.ndx
        self.dy = self.ndy
        head = self.snake[0]
        x = head % COLS + self.dx
        y = head // COLS + self.dy
        if x < 0 or x >= COLS or y < 0 or y >= ROWS:
            self.end_game()
            return
        cell = y * COLS + x
        if cell in self.snake:
            self.end_game()
            return
        self.snake.insert(0, cell)
        if cell == self.food:
            self.score = self.score + 1
            if len(self.snake) >= COLS * ROWS:
                self.end_game()
                return
            self.place_food()
        else:
            self.snake.pop()

    def turn(self, d):
        # ignore a reversal of the direction the snake last moved in
        if d[0] == -self.dx and d[1] == -self.dy:
            return
        self.ndx = d[0]
        self.ndy = d[1]

    def poll(self):
        # drain buffered input (1 byte at a time), up to 8 bytes
        s = ""
        n = 0
        while n < 8:
            c = self.console.read_nonblock(1)
            if c is None or c == "":
                break
            s = s + c
            n = n + 1
        keys = []
        i = 0
        L = len(s)
        while i < L:
            c = s[i]
            if c == "\x1b":
                if i + 2 < L and s[i + 1] == "[":
                    k = s[i + 2]
                    if k == "A":
                        keys.append("UP")
                    elif k == "B":
                        keys.append("DOWN")
                    elif k == "C":
                        keys.append("RIGHT")
                    elif k == "D":
                        keys.append("LEFT")
                    i = i + 3
                else:
                    keys.append("ESC")
                    i = i + 1
            else:
                keys.append(c)
                i = i + 1
        return keys

    def handle(self, key):
        if key == "q":
            self.quit = True
            return
        d = dir_of(key)
        enter = key == "\r" or key == "\n" or key == "ENTER"
        if self.state == READY:
            if key == "ESC":
                self.quit = True
            elif enter:
                self.state = PLAY
            elif d is not None:
                self.turn(d)
                self.state = PLAY
        elif self.state == PLAY:
            if key == "p" or key == "ESC":
                self.paused = not self.paused
            elif d is not None and not self.paused:
                self.turn(d)
        else:
            if key == "ESC":
                self.quit = True
            elif enter:
                self.reset()
                self.state = PLAY

    def cell_xy(self, idx):
        return (BOARD_X + (idx % COLS) * CELL, self.board_y + (idx // COLS) * CELL)

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        Widget.header(sp, TITLE, "S:{}".format(self.score))
        by = self.board_y
        sp.rect(BOARD_X - 1, by - 1, COLS * CELL + 2, ROWS * CELL + 2, Widget.theme_border())
        i = 0
        n = len(self.snake)
        while i < n:
            p = self.cell_xy(self.snake[i])
            if i == 0:
                col = Widget.theme_selected()
            else:
                col = Widget.theme_text()
            sp.fill_rect(p[0], p[1], CELL - 1, CELL - 1, col)
            i = i + 1
        f = self.cell_xy(self.food)
        sp.fill_circle(f[0] + 4, f[1] + 4, 4, Widget.theme_emphasis())
        if self.state == READY:
            Widget.text_center(sp, by + 44, "PRESS ENTER", Widget.theme_selected())
            Widget.footer(sp, "ENTER start  q quit")
        elif self.state == PLAY:
            if self.paused:
                Widget.text_center(sp, by + 44, "PAUSED", Widget.theme_selected())
            Widget.footer(sp, "arrows/hjkl move  p pause  q quit")
        else:
            Widget.panel(sp, 60, 40, 120, 55)
            Widget.text_center(sp, 46, "GAME OVER", Widget.theme_emphasis())
            Widget.text_center(sp, 62, "Score {}".format(self.score))
            Widget.text_center(sp, 76, "Best {}".format(self.best))
            Widget.footer(sp, "ENTER again  q quit")

    def draw(self):
        while self.sprite.draw():
            self.render()

    def run(self):
        Display.fill_screen(Widget.theme_background())
        self.sprite = BandedSprite(12)
        try:
            self.load()
            self.reset()
            while not self.quit:
                keys = self.poll()
                for k in keys:
                    self.handle(k)
                if self.state == PLAY and not self.paused and not self.quit:
                    self.tick = self.tick + 1
                    if self.tick >= self.speed():
                        self.tick = 0
                        self.step()
                self.draw()
                sleep_ms(30)
        finally:
            self.sprite.delete()
            self.sprite = None
            Display.fill_screen(Widget.theme_background())


App().run()
