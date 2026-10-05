# TODO: checklist saved to the SD card.

TITLE = "TODO"
FOLDER = "/home/ai/todo"
DATA_PATH = "/home/ai/todo/items.txt"
HINT = "a add  SPACE check  d del  q quit"
MAX_ITEMS = 100
MAX_TEXT = 40


class App:
    def __init__(self):
        self.console = IO()
        self.sprite = None
        self.quit = False
        self.items = []
        self.lst = WidgetList()
        self.message = ""

    def read_key(self):
        self.console.raw()
        try:
            return Widget.read_key()
        finally:
            self.console._restore_termios()

    def load(self):
        if not File.exist(DATA_PATH):
            return
        try:
            text = SD.read(DATA_PATH)
        except OSError:
            return
        for line in text.split("\n"):
            line = line.rstrip()
            if len(line) < 3:
                continue
            if line[0] != "0" and line[0] != "1":
                continue
            body = ""
            i = 2
            while i < len(line):
                body = body + line[i]
                i = i + 1
            if len(self.items) < MAX_ITEMS:
                self.items.append([line[0] == "1", body])

    def save(self):
        try:
            if not Dir.exist(FOLDER):
                Dir.mkdir(FOLDER)
            lines = []
            for it in self.items:
                lines.append(("1|" if it[0] else "0|") + it[1])
            SD.write(DATA_PATH, "\n".join(lines))
        except OSError:
            self.message = "save failed"
            return False
        return True

    def done_count(self):
        n = 0
        for it in self.items:
            if it[0]:
                n = n + 1
        return n

    def rebuild(self, index):
        self.lst.clear()
        for it in self.items:
            tag = "[x]" if it[0] else "[ ]"
            self.lst.add(Widget.clip(self.sprite, it[1], 170), tag)
        if index >= len(self.items):
            index = len(self.items) - 1
        if index < 0:
            index = 0
        self.lst.set_index(index)

    def clean(self, text):
        out = ""
        for ch in text:
            if len(out) >= MAX_TEXT:
                break
            if ch == "|" or ch == "\n" or ch == "\r":
                ch = " "
            out = out + ch
        return out.strip()

    def add_item(self):
        if len(self.items) >= MAX_ITEMS:
            self.message = "list full"
            return
        text = Widget.input(self.sprite, "New item", "")
        if text is None:
            return
        text = self.clean(text)
        if text == "":
            return
        self.items.append([False, text])
        self.save()
        self.rebuild(len(self.items) - 1)
        self.message = "added"

    def toggle(self):
        if len(self.items) == 0:
            return
        i = self.lst.index()
        self.items[i][0] = not self.items[i][0]
        self.save()
        self.rebuild(i)
        self.message = "saved"

    def delete(self):
        if len(self.items) == 0:
            return
        if not Widget.confirm(self.sprite, "Delete item?"):
            return
        i = self.lst.index()
        del self.items[i]
        self.save()
        self.rebuild(i)
        self.message = "deleted"

    def clear_done(self):
        if self.done_count() == 0:
            return
        if not Widget.confirm(self.sprite, "Clear done items?"):
            return
        keep = []
        for it in self.items:
            if not it[0]:
                keep.append(it)
        self.items = keep
        self.save()
        self.rebuild(self.lst.index())
        self.message = "deleted"

    def handle(self, key):
        self.message = ""
        if key == "q" or key == "ESC":
            self.quit = True
        elif self.lst.handle(key):
            pass
        elif key == "a":
            self.add_item()
        elif key == " " or key == "ENTER":
            self.toggle()
        elif key == "d" or key == "BS":
            self.delete()
        elif key == "c":
            self.clear_done()

    def render(self):
        sp = self.sprite
        sp.fill(Widget.theme_background())
        Widget.header(sp, TITLE, "{}/{}".format(self.done_count(), len(self.items)))
        self.lst.draw(sp)
        Widget.footer(sp, self.message if self.message != "" else HINT)

    def draw(self):
        while self.sprite.draw():
            self.render()

    def run(self):
        Display.fill_screen(Widget.theme_background())
        self.sprite = BandedSprite(12)
        try:
            self.lst.set_empty_text("No items. Press a to add")
            self.load()
            self.rebuild(0)
            while not self.quit:
                self.draw()
                self.handle(self.read_key())
        finally:
            self.sprite.delete()
            self.sprite = None
            Display.fill_screen(Widget.theme_background())


App().run()
