NAME: reaction
TITLE: REACTION TEST
PURPOSE: Measure how fast you press a key after the screen turns green, over 5 rounds, and keep your best average.
SCREENS:
- Ready screen: header "REACTION TEST" with right text "best NNN" (or "best --"); body shows centered text "Press SPACE to start" and below it the best average in frames-based ms; footer "SPACE start  q quit".
- Wait screen: whole body filled with theme_box colour, big_text "WAIT..." centered at y about 55, small text "Round N/5" under it at y about 90; footer "press SPACE when green".
- Go screen: whole body filled with solid green (0x00C000, colour is the point), big_text "GO!" centered at y about 55; footer "SPACE now!". The frame counter runs, one frame = 30 ms.
- Result screen (after each round): body shows centered "Round N: NNN ms" (big_text); if pressed too early shows "Too early!" in red (0xC00000) instead; below it a row of the rounds so far as small text "1:245 2:230 ..." wrapped with Widget.wrap_text; footer "SPACE next  q quit".
- Summary screen (after round 5): Widget.titled_panel at x 20, y 25, w 200, h 90 titled "RESULTS" with lines "Average: NNN ms", "Fastest: NNN ms", "Slowest: NNN ms", and a Widget.badge "NEW BEST" if the average beats the saved best; footer "SPACE again  q quit".
CONTROLS:
- SPACE: start a round / react when green / advance past results / restart after summary
- ENTER: same as SPACE
- q: quit (from any screen)
- ESC: quit
DATA: /home/ai/reaction/best.txt holds the best average in ms as a plain integer; loaded at start, written only when a finished 5-round run beats it. Folder created with Dir.mkdir if missing.
LIMITS: There is no clock, so each frame is one sleep_ms(30) call and reaction time is frames * 30 ms (30 ms resolution). The random wait before GO is RNG.random_int() % 80 + 40 frames (about 1.2 to 3.6 s). Keys are polled with IO().read_nonblock(1) each frame; pressing SPACE during WAIT counts as too early and the round repeats without counting.
TEST: SPACE WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT WAIT SPACE q
TEST: SPACE SPACE SPACE q
