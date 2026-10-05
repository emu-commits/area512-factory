NAME: diceroller
TITLE: DICE ROLLER
PURPOSE: Pick a die type (d4 to d20) and a count, roll them, and see each die plus the total.
SCREENS:
- Main screen: header "DICE ROLLER" with the last total on the right. Body top row (y=body_top+4) shows 6 die chips in a row (d4 d6 d8 d10 d12 d20), the chosen one drawn with Widget.badge/selected colour, others in theme text. Below it a Widget.spinner "< N dice >" (N from 1 to 10) centered at about y=48. Under that the roll line "NdS" (e.g. "3d8") in Widget.big_text at y=68. Below that the individual results as text, up to 10 numbers separated by spaces, wrapped with Widget.wrap_text in a box x=8,y=96,w=224,h=20. Right of the big text, "TOTAL: 17" in theme_emphasis. Before the first roll the results area says "ENTER to roll".
- History screen (H key): header "HISTORY", a WidgetList of the last 8 rolls, each row "3d8 = 17", newest first, empty text "No rolls yet". Footer shows "ESC back".
- Footer on main: "L/R die  U/D count  ENTER roll  h hist  q quit".
CONTROLS:
- LEFT / h: previous die type
- RIGHT / l: next die type
- UP / k: more dice (max 10)
- DOWN / j: fewer dice (min 1)
- 1-9: set the dice count directly to that digit
- 0: set the dice count to 10
- ENTER or SPACE: roll the chosen dice
- r: re-roll (same as ENTER)
- H (key "H" or "i"): open or close the history screen. Use "i" for history since h is left.
- s: save the current die type and count
- ESC: close history; on the main screen quit
- q: quit
DATA: /home/ai/diceroller/data.txt holds "<die index> <count>" (e.g. "5 3"). Saved when s is pressed and on quit; loaded at start if the file exists. History is kept in memory only (last 8 rolls).
LIMITS: No clock, so roll randomness comes only from RNG.random_int() % sides + 1; no animation timing needed, a roll is shown instantly. No imports, so die sizes live in a plain list [4,6,8,10,12,20].
TEST: RIGHT RIGHT UP UP ENTER ENTER i ESC q
TEST: LEFT DOWN 5 RIGHT SPACE s i ESC 0 ENTER q
