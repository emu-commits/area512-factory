NAME: stopwatch
TITLE: STOPWATCH
PURPOSE: A stopwatch with lap times, counting frames since there is no clock, with the best lap saved.
SCREENS:
- Main screen: Widget.header "STOPWATCH" with right text RUN, STOP or READY. Elapsed time in Widget.big_text centered at about y=28, formatted MM:SS.cc. Below it (y=58 to 110) the lap list in 12px text, newest first, 4 rows visible, each "LAP n  MM:SS.cc  +split". The fastest lap is drawn in theme_selected and the others in theme_text. Widget.footer shows "SPACE start/stop  l lap  r reset  q quit".
- Lap history screen (key h): Widget.header "LAPS" with the lap count on the right. A WidgetList in the body shows all laps (max 99) as "n  MM:SS.cc" with the best marked "*". Footer: "UP/DOWN scroll  ESC back".
CONTROLS:
- SPACE: start or stop the timer
- l or ENTER: record a lap while running (ignored when stopped)
- r: reset the time and laps (only when stopped)
- h: open lap history
- j/k or DOWN/UP: scroll lap history
- s: save best lap time
- ESC: back from history; quits on the main screen
- q: quit
DATA: /home/ai/stopwatch/best.txt holds the best lap in centiseconds as an integer. It is written when s is pressed or on a new best lap, and loaded at start.
LIMITS: There is no clock, so the loop polls IO().read_nonblock(1) and calls sleep_ms(10) each frame. Each frame adds 1 centisecond (10 ms) to elapsed, so the time drifts slightly with draw time and is approximate. Every key is read non-blocking, and the screen redraws every frame with BandedSprite(12).
TEST: SPACE WAIT WAIT WAIT l WAIT WAIT l WAIT SPACE h DOWN ESC r q
TEST: SPACE WAIT l WAIT l WAIT l WAIT l WAIT l SPACE s h UP ESC q
