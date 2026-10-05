NAME: spanish_cards
TITLE: SPANISH CARDS
PURPOSE: Flashcard quiz that shows a Spanish word, lets you reveal the English answer, and keeps score of what you knew.
SCREENS:
- Quiz (front): header "SPANISH CARDS" with right text "3/12" (card number / deck size). Body: the Spanish word centered in 24px Widget.big_text around y=50. Below it, a dim line "? press SPACE to reveal". Under that, Widget.text_right score line "Right 4  Miss 2". Footer: "SPACE reveal  q quit".
- Quiz (back): same header. Spanish word shown smaller via Widget.text_center near top, the English answer in Widget.big_text below it. Score line stays. Footer: "y knew it  n missed  q quit".
- Results: header "SPANISH CARDS" right "DONE". Widget.center_lines shows "Score: 9 / 12", a percent line like "75 percent", and a best-score line "Best: 10". Widget.gauge below the text shows the percentage. Footer: "r restart  q quit".
CONTROLS:
- SPACE or ENTER: reveal the answer (front); on the back, ENTER or RIGHT/l skips to the next card without scoring.
- y: mark "knew it" (+1 right) and go to the next card (back side only).
- n: mark "missed" (+1 miss) and go to the next card (back side only).
- LEFT/h: go back one card (resets that card's reveal state).
- r: reshuffle and restart (results screen, or any time).
- ESC: quit from the main screen.
- q: quit.
DATA: Saves the best score as one integer text file /home/ai/spanish_cards/best.txt when a round finishes with a higher score than before; it is loaded at start. The deck itself is a built-in list of 24 (spanish, english) tuples in main.py; each round deals 12 shuffled cards using RNG.random_int() (Fisher-Yates in a loop, no random module).
LIMITS: No network or clock, so the deck is built in rather than downloaded and there is no spaced-repetition timing; the next card is chosen by deck order after the shuffle. Text is ASCII only, so words appear without accents (for example "cafe", "nino", "adios"). The deck is kept small to fit the RAM budget.
TEST: SPACE y SPACE n SPACE y SPACE y SPACE n SPACE y SPACE n SPACE y SPACE y SPACE n SPACE y SPACE y r q
TEST: SPACE ENTER SPACE y LEFT SPACE n SPACE y WAIT DOWN SPACE n r SPACE y ESC
