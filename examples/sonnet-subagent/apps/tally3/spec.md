NAME: tally3
TITLE: TALLY
PURPOSE: A tally counter with three named counters that are saved to the card and restored on the next launch.
SCREENS:
- Main screen: header "TALLY" at top with the selected counter's number (e.g. "2/3") on the right. Body shows three rows, each 30px tall, between Widget.body_top() and Widget.body_bottom(). Each row has the counter name at left (x=8, theme_text) and the count right-aligned at x=232 in Widget.big_text (24px font). The selected row is filled with theme_box, framed with theme_selected, and its name is drawn in theme_selected. Footer shows hints "UP/DOWN pick  ENTER +1  BS -1  r name  q quit".
- Rename prompt: modal Widget.input(sprite, "Name", current_name) over the main screen. Enter accepts (trimmed, clipped to 10 chars, empty is ignored), ESC cancels.
- Reset confirm: modal Widget.confirm(sprite, "Reset counter?") for the selected counter only. Toast "saved" shown in the footer message after each change.
CONTROLS:
- UP / k: select the previous counter (wraps)
- DOWN / j: select the next counter (wraps)
- ENTER / SPACE / RIGHT / l: add 1 to the selected counter
- BS / LEFT / h: subtract 1 from the selected counter (stops at 0)
- 1 / 2 / 3: jump to that counter
- r: rename the selected counter via the text input
- z: reset the selected counter to 0 after confirmation
- q / ESC: save and quit
DATA: /home/ai/tally3/data.txt, created with Dir.mkdir if missing. Plain text, 3 lines of "name|count". Loaded at start (defaults "A", "B", "C" with 0 if the file is missing or malformed). Saved after every change (increment, decrement, rename, reset) and again on quit.
LIMITS: No slicing, so name clipping and line parsing use index loops and str.find/split. No clock, so there are no timestamps or daily counts, only running totals. Counts are capped at 99999 so the 24px text fits the row.
TEST: DOWN ENTER ENTER ENTER UP ENTER BS q
TEST: 3 ENTER r B O B ENTER ENTER z y UP ENTER q
