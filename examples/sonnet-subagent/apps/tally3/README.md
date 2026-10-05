# TALLY

A tally counter with three named counters, saved to the card and restored on the next launch.

Data is stored in /home/ai/tally3/data.txt as three "name|count" lines. Counts are capped at 99999.

## Controls

- UP / k: select previous counter (wraps)
- DOWN / j: select next counter (wraps)
- ENTER / SPACE / RIGHT / l: add 1
- BS / LEFT / h: subtract 1 (stops at 0)
- 1 / 2 / 3: jump to that counter
- r: rename the selected counter (max 10 chars)
- z: reset the selected counter to 0 (asks first)
- q / ESC: save and quit
