NAME: todo
TITLE: TODO
PURPOSE: A checklist where you add, check off and delete items, saved to the SD card.
SCREENS:
- List screen: header "TODO" with "done/total" (e.g. "2/5") right-aligned. Body from Widget.body_top() to Widget.body_bottom() is a WidgetList of items; each row's tag is "[x]" for done or "[ ]" for open, followed by the item text (clipped to the width). Cursor row is highlighted by WidgetList. An empty list shows the empty text "No items. Press a to add". Footer: "a add  SPACE check  d del  q quit".
- Add screen: Widget.input(sprite, "New item", "") modal over the list. ENTER with non-empty text adds the item, ESC cancels.
- Delete confirm: Widget.confirm(sprite, "Delete item?") modal over the list.
- Toast: after save/add/delete, the footer message briefly reads "saved", "added" or "deleted" (shown until the next key).
CONTROLS:
- UP / k: move cursor up
- DOWN / j: move cursor down
- a: open the add-item input
- SPACE: toggle done/not done on the cursor item
- ENTER: toggle done/not done on the cursor item
- d: delete the cursor item after confirm (y = yes)
- BS: delete the cursor item after confirm
- c: clear all done items after confirm
- ESC: quit from the list (ESC inside a modal cancels it)
- q: quit
DATA: /home/ai/todo/items.txt, one item per line as "0|text" (open) or "1|text" (done). Loaded at start if the file exists; rewritten with SD.write after every add, toggle, delete or clear, so nothing is lost on quit. Folder /home/ai/todo is created with Dir.mkdir if missing. Max 100 items (WidgetList holds 128 rows); item text max 40 chars and "|" and newlines are replaced by spaces on add.
LIMITS: No clock, so items carry no dates or due times. No slicing or imports: parse each line by checking line[0] and building the text with a loop from index 2. The list is rebuilt from a Python list of [done, text] pairs into the WidgetList after each change, and the cursor is restored with set_index.
TEST: a h i SPACE ENTER a m i l k ENTER SPACE DOWN SPACE UP d y q
TEST: a a ENTER a b ENTER a c ENTER DOWN SPACE j d y k a ESC c y q
