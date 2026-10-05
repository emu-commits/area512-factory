NAME: pomodoro
TITLE: POMODORO
PURPOSE: A 25-minute focus / 5-minute break timer that counts completed focus sessions and saves the count.
SCREENS:
- Timer screen: header "POMODORO" with right text "#N" (sessions done today so far). Body: mode label "FOCUS" or "BREAK" via Widget.text_center near y=30; big countdown "MM:SS" via Widget.big_text centered around y=55; Widget.gauge across x=20..220 at y=90 showing elapsed progress of the current phase; a line "Sessions: N" at y=108. Footer: key hints "SPACE start/pause  n skip  r reset  q quit". When paused, the mode label reads "FOCUS (paused)" or "BREAK (paused)".
- Phase-change flash: when a phase ends, Widget.toast "Focus done! Break time" or "Break over! Focus" is shown for about 60 frames and the next phase starts paused.
CONTROLS:
- SPACE: start or pause the countdown
- n: skip to the next phase (skipping a FOCUS phase does not count a session)
- r: reset the current phase to its full length and pause
- c: clear the session count (asks Widget.confirm first)
- q: quit (ESC also quits)
DATA: /home/ai/pomodoro/count.txt holds the session count as a plain integer; it is written each time a focus phase completes and when the count is cleared, and loaded at startup.
LIMITS: There is no clock, so the app is real-time-polled: each frame is IO().read_nonblock(1) plus sleep_ms(50), and 20 frames count as one second (1500 s focus = 30000 frames, 300 s break = 6000 frames). Time is therefore approximate and drifts with drawing time; the count is a total across runs, not per calendar day, since the date is unknown.
TEST: SPACE WAIT WAIT WAIT SPACE r q
TEST: SPACE n n n c y q
