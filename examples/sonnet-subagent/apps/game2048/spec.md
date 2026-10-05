NAME: game2048
TITLE: 2048
PURPOSE: Classic 2048 sliding-tile puzzle on a 4x4 grid where equal tiles merge toward a 2048 tile, with a saved best score.
SCREENS:
- Game screen: header "2048" with the current score right-aligned (e.g. "S 1240"). Body shows a 4x4 grid on the left, each cell 26x26 px with 2 px gaps (about 110x110 px, starting at x=8, y=Widget.body_top()+2). Each cell is a Widget.cell() showing the tile value centered ("" for empty); cells holding tiles of 128 or more use a highlighted (selected=True) frame so big tiles stand out. To the right of the grid (x=130 to 232): "SCORE" with the value, "BEST" with the best value, and "MOVES" with the move count, drawn with sprite.text. Below them a Widget.toast-style message line for "NEW GAME", "NO MOVES LEFT" or "YOU WIN". Footer: "arrows/hjkl move  n new  q quit".
- Win overlay: when the first 2048 tile appears, Widget.dialog(sp, "You made 2048!", ["Keep going", "New game"]) is shown. Keep going continues play and never shows the dialog again that game.
- Game over overlay: when no move is possible, Widget.dialog(sp, "No moves left. Score {}".format(score), ["New game", "Quit"]) is shown. Index 0 or ESC starts a new game, index 1 quits.
CONTROLS:
- UP / k: slide all tiles up
- DOWN / j: slide all tiles down
- LEFT / h: slide all tiles left
- RIGHT / l: slide all tiles right
- n: start a new game, with a Widget.confirm if the current score is above 0
- ESC / q: quit (saves best score first)
DATA: /home/ai/game2048/best.txt holds the best score as a decimal string. It is written with SD.write whenever the score exceeds the best (checked after each move) and on quit. The folder is created with Dir.mkdir if missing. It is read at start; if the file is missing or not all digits, best is 0.
LIMITS: No keyword args, no slicing, no min/max, no import. Tile values are stored as plain ints in a 16-item list and row/column lines are extracted and written back with index loops, so there is one slide-left routine reused for all four directions by mapping indices. The new-tile position and value (2 with 90 percent chance, 4 otherwise) use RNG.random_int() % n. There is no clock, so there is no timer or animation; the screen redraws only after a keypress via the blocking Widget.read_key() loop.
TEST: LEFT UP RIGHT DOWN LEFT UP RIGHT DOWN h j k l LEFT LEFT UP UP
TEST: LEFT DOWN n ENTER LEFT UP RIGHT DOWN ESC q
