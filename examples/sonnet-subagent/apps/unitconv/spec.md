NAME: unitconv
TITLE: UNIT CONVERTER
PURPOSE: Convert a typed number between units of length, weight and temperature.
SCREENS:
- Main screen: header "UNIT CONVERTER" with the category name on the right. Widget.tabs at the top of the body shows LENGTH / WEIGHT / TEMP with the active category highlighted. Below it, a "From" row (Widget.field) shows the from-unit and the typed value. A "To" row shows the to-unit and the converted result with up to 4 decimals, trailing zeros trimmed. Footer shows key hints.
- Units: LENGTH = mm, cm, m, km, in, ft, yd, mi. WEIGHT = mg, g, kg, oz, lb. TEMP = C, F, K.
- Entry: the value is typed on the main screen (digits, "." and "-"). A small cursor mark "_" follows the typed text. An empty entry counts as 0.
- Saved flag: after ENTER, the toast "saved" is shown for about 20 frames.
CONTROLS:
- 0-9: append a digit to the value (max 10 chars)
- . : append a decimal point (only one allowed)
- -: toggle a leading minus sign
- BS: delete the last character
- LEFT/RIGHT (h/l): switch category (length, weight, temp)
- UP/DOWN (k/j): change the from-unit
- TAB is not available, so s: cycle the to-unit
- x: swap the from-unit and the to-unit
- c: clear the value
- ENTER: save the current category, units and value as the default
- q or ESC: quit
DATA: /home/ai/unitconv/state.txt holds category, from-unit index, to-unit index and value on one line separated by spaces. Written on ENTER, loaded at start if present.
LIMITS: No math module and no float formatting beyond "{:.4f}".format. Conversions use a table of factors to a base unit (m, g) and temperature goes through Celsius, all in plain arithmetic. The value is parsed with float() on the entry string, with an empty string or a lone "-" or "." treated as 0. Letter keys h, j, k, l double as navigation, so unit selection uses the arrows and the entry only takes digits, "." and "-".
TEST: 1 2 DOWN s ENTER q
TEST: RIGHT RIGHT 1 0 0 x UP LEFT BS BS c 5 . 5 q
