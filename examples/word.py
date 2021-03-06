#  words.py
#
#  An example of using the word_by_word method from text boxes.

import curses

from visualdialog import DialogBox


# Definition of curses key constants.
# 10 and 32 correspond to enter and space keys.
ENTER_KEY = 10
SPACE_KEY = 32

def main(stdscr):
    instructions = (
        "Instead of the char_by_char method, word_by_word displays the "
        "given text word by word.",
        "It can be useful to make robots talk for example."
    )

    # Makes the cursor invisible.
    curses.curs_set(False)

    textbox = DialogBox(1, 1,  # Position 1;1 in stdscr.
                        40, 6,  # Length and width of textbox (in character).
                        title="Robot")  # Title of textbox.

    # Definition of accepted key codes to pass a dialog.
    textbox.confirm_dialog_key = (ENTER_KEY, SPACE_KEY)

    # Iterate on each sentence contained in replys.
    for instruction in instructions:
        textbox.word_by_word(stdscr,
                             instruction,
                             delay=0.2)  # Set delay between writting each words to 0.1 seconde.


# Execution of main function.
curses.wrapper(main)
