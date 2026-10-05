NAME: snake
TITLE: SNAKE
PURPOSE: Classic real-time snake game where you steer a growing snake to eat food on a grid without hitting walls or yourself.
SCREENS:
- Play: header "SNAKE" with right text "S:<score>" (Widget.header); body is a 20x10 grid of 10px cells (200x100 px) centered at x=20, y=Widget.body_top()+2, drawn with a theme_border rectangle frame; snake body cells as fill_rect in theme_text, head in theme_selected, food as a fill_circle in theme_emphasis; footer shows "arrows/hjkl move  p pause  q quit".
- Ready: same board with the snake shown still and Widget.text_center "PRESS ENTER" over the board; game starts on ENTER or any direction key.
- Game over: a Widget.panel centered (x=60,y=40,w=120,h=55) with "GAME OVER" (theme_emphasis), "Score N" and "Best N" lines; footer "ENTER again  q quit".
CONTROLS:
- UP / k / w: turn up (ignored if moving down)
- DOWN / j / s: turn down (ignored if moving up)
- LEFT / h / a: turn left (ignored if moving right)
- RIGHT / l / d: turn right (ignored if moving left)
- ENTER: start from Ready, restart from Game over
- p: pause / resume
- ESC: quit from Ready or Game over; pauses during play
- q: quit
DATA: Best score saved as text to /home/ai/snake/best.txt (folder created with Dir.mkdir if missing) when a game ends with a new high score; loaded at startup.
LIMITS: No clock, so speed is frame based: the loop polls IO().read_nonblock(1) and calls sleep_ms(30) per frame; the snake advances one cell every N frames (N starts at 6 and drops by 1 every 5 foods eaten, minimum 2). Food placement uses RNG.random_int() % cells, retrying until a free cell is found. No min/max, slicing or imports; the snake is a plain list of cell indexes (y*20+x), and arrow keys arriving as multi-byte escape sequences are also read through the nonblocking reader (ESC [ A/B/C/D) alongside hjkl/wasd.
TEST: ENTER WAIT WAIT WAIT WAIT WAIT WAIT RIGHT WAIT WAIT WAIT WAIT WAIT WAIT DOWN WAIT WAIT WAIT WAIT WAIT WAIT p WAIT p WAIT WAIT q
TEST: ENTER UP WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT ENTER WAIT q
