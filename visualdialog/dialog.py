#  dialog.py
#
#  2020 Timéo Arnouts <tim.arnouts@protonmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

__all__ = ["DialogBox"]

import curses
from numbers import Number
import random
import textwrap
import time
from typing import Callable, Dict, List, Optional, Tuple, Union

from .box import BaseTextBox
from .utils import (CursesTextAttributesConstant,
                    CursesTextAttributesConstants,
                    CursesWindow,
                    TextAttributes,
                    _make_chunk)


class DialogBox(BaseTextBox):
    """This class provides methods and attributs to manage a dialog box.

    :param end_dialog_indicator: Character that will be displayed in the
        lower right corner the character once all the characters have
        been completed. String with a length of more than one character
        can lead to an overflow of the dialog box frame. This defaults
        to ``"►"``.

    :key kwargs: Keyword arguments correspond to the instance attributes
        of ``TextBox``.

    .. NOTE::
        This class inherits from ``BaseTextBox``.

    .. NOTE::
        This class is a context manager.

    .. WARNING::
        Parameters ``downtime_chars`` and ``downtime_chars_delay`` do
        not affect ``word_by_word`` method.
    """

    def __init__(
        self,
        pos_x: int,
        pos_y: int,
        height: int,
        width: int,
        title: str = "",
        title_colors_pair_nb: int = 0,
        title_text_attr: Union[CursesTextAttributesConstant,
                            CursesTextAttributesConstants] = curses.A_BOLD,
        downtime_chars: Union[Tuple[str],
                            List[str]] = (",", ".", ":", ";", "!", "?"),
        downtime_chars_delay: Number = .6,
        end_indicator: str = "►"):
        BaseTextBox.__init__(self,
                             pos_x, pos_y,
                             height, width,
                             title,
                             title_colors_pair_nb, title_text_attr,
                             downtime_chars, downtime_chars_delay)

        self.end_indicator_char = end_indicator
        self.end_indicator_pos_x = self.pos_x + self.height - 2

        if self.title:
            self.end_indicator_pos_y = self.pos_y + self.width + 1
        else:
            self.end_indicator_pos_y = self.pos_y + self.width - 1

        self.text_wrapper = textwrap.TextWrapper(width=self.nb_char_max_line)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        ...

    def _display_end_indicator(
        self,
        win: CursesWindow,
        text_attr: CursesTextAttributesConstants = (curses.A_BOLD,
                                                    curses.A_BLINK)):
        """Displays an end indicator in the lower right corner of
        textbox.

        :param win: ``curses`` window object on which the method
            will have effect.

        :param text_attr: Text attributes of
            ``end_indicator`` method. This defaults to
            ``(curses.A_BOLD, curses.A_BLINK)``.
        """
        if self.end_indicator_char:
            with TextAttributes(win, *text_attr):
                win.addch(self.end_indicator_pos_y,
                          self.end_indicator_pos_x,
                          self.end_indicator_char)

    def char_by_char(
        self,
        win: CursesWindow,
        text: str,
        colors_pair_nb: int = 0,
        text_attr: Union[CursesTextAttributesConstant,
                         CursesTextAttributesConstants] = (),
        words_attr: Union[Dict[Tuple[str], CursesTextAttributesConstant],
                          Dict[Tuple[str], CursesTextAttributesConstants]] = {},
        flash_screen: bool = False,
        delay: Number = .04,
        random_delay: Union[Tuple[Number], List[Number]] = (0, 0),
        callback: Callable = lambda: None,
        cargs: Union[Tuple, List] = ()):
        """Writes the given text character by character in the current
        dialog box.

        :param win: ``curses`` window object on which the method will
            have effect.

        :param text: Text that will be displayed character by character
            in the dialog box. This text can be wrapped to fit the
            proportions of the dialog box.

        :param colors_pair_nb: Number of the curses color pair that
            will be used to color the text. The number zero
            corresponding to the pair of white color on black
            background initialized by ``curses``). This defaults to
            ``0``.

        :param text_attr: Dialog box curses text attributes. It should
            be a single curses text attribute or a tuple of curses text
            attribute. This defaults an empty tuple.

        :param words_attr: Dictionary composed of string as a key and a
            single curses text attribute or tuple as a value. Each key
            is colored with its associated values This defaults to an
            empty dictionary.

        :param flash_screen: Allows or not to flash screen with a short
            light effect done before writing the first character by
            ``flash`` function from ``curses`` module. This defaults to
            ``False``.

        :param delay: Waiting time between the writing of each character
            of text in second. This defaults to ``0.04``.

        :param random_delay: Waiting time between the writing of each
            character in seconds where time waited is a random number
            generated in ``random_delay`` interval. This defaults to
            ``(0, 0)``.

        :param callback: Callable called after writing a character and
            the delay time has elapsed. This defaults to a lambda which
            do nothing.

        :param cargs: All the arguments that will be passed to callback.
            This defaults to an empty tuple.

        .. NOTE::
            Method flow:
                - Calling ``framing_box`` method.
                - Flash screen depending ``flash_screen`` parameter.
                - Cutting text into line to stay within the dialog box
                  frame.
                - Writing paragraph by paragraph.
                - Writing each line of the current paragraph, character
                  by character.
                - Waits until a key contained in the class attribute
                  ``confirm_dialog_key`` was pressed before writing the
                  following paragraph.
                - Complete cleaning ``win``.

        .. WARNING::
            If the volume of text displayed is too large to be contained
            in a dialog box, text will be automatically cut into
            paragraphs using ``textwrap.wrap`` function. See
            `textwrap module documentation
            <https://docs.python.org/fr/3.8/library/textwrap.html#textwrap.wrap>`_.
            for more information of the behavior of text wrap.

        .. WARNING::
            ``win`` will be completely cleaned when writing each
            paragraph by ``window.clear()`` method of ``curses``
            module.
        """
        self.framing_box(win)

        if flash_screen:
            curses.flash()

        wrapped_text = self.text_wrapper.wrap(text)
        wrapped_text = _make_chunk(wrapped_text, self.nb_lines_max)

        for paragraph in wrapped_text:
            win.clear()
            self.framing_box(win)

            for y, line in enumerate(paragraph):
                offsetting_x = 0
                for word in line.split():
                    if word in words_attr.keys():
                        attr = words_attr[word]

                        # Test if only one argument is passed instead of a tuple.
                        if isinstance(attr, int):
                            attr = (attr, )
                    else:
                        if isinstance(text_attr, int):
                            text_attr = (text_attr, )

                        attr = (curses.color_pair(colors_pair_nb), *text_attr)

                    with TextAttributes(win, *attr):
                        for x, char in enumerate(word):
                            win.addstr(self.text_pos_y + y,
                                       self.text_pos_x + x + offsetting_x,
                                       char)
                            win.refresh()

                            if char in self.downtime_chars:
                                time.sleep(self.downtime_chars_delay +
                                           random.uniform(*random_delay))
                            else:
                                time.sleep(delay +
                                           random.uniform(*random_delay))

                            callback(*cargs)

                        # Waiting for space character.
                        time.sleep(delay)

                    # Compensates for the space between words.
                    offsetting_x += len(word) + 1

            self._display_end_indicator(win)
            self.getkey(win)

    def word_by_word(
        self,
        win: CursesWindow,
        text: str,
        colors_pair_nb: int = 0,
        cut_char: str = " ",
        text_attr: Union[CursesTextAttributesConstant,
                         CursesTextAttributesConstants] = (),
        words_attr: Union[Dict[Tuple[str], CursesTextAttributesConstant],
                          Dict[Tuple[str], CursesTextAttributesConstants]] = {},
        flash_screen: bool = False,
        delay: Number = .15,
        random_delay: Union[Tuple[Number], List[Number]] = (0, 0),
        callback: Callable = lambda: None,
        cargs: Union[Tuple, List] = ()):
        """Writes the given text word by word at position in the current
        dialog box.

        :param win: ``curses`` window object on which the method will
            have effect.

        :param text: Text that will be displayed word by word in the
            dialog box. This text can be wrapped to fit the proportions
            of the dialog box.

        :param colors_pair_nb:
            Number of the curses color pair that will be used to color
            the text. The number zero corresponding to the pair of
            white color on black background initialized by ``curses``).
            This defaults to ``0``.

        :param text_attr: Dialog box curses text attributes. It should
            be a single curses text attribute or a tuple of curses text
            attribute. This defaults an empty tuple.

        :param words_attr: Dictionary composed of string as a key and a
            single curses text attribute or tuple as a value. Each key
            is colored with its associated values This defaults to an
            empty dictionary.

        :param cut_char: The delimiter according which to split the text
            in word. This defaults to ``" "``.

        :param flash_screen: Allows or not to flash screen with a short
            light effect done before writing the first character by
            ``flash`` function from ``curses`` module. This defaults to
            ``False``.

        :param delay: Waiting time between the writing of each word of
            ``text`` in second. This defaults to ``0.15``.

        :param random_delay: Waiting time between the writing of each
            word in seconds where time waited is a random number
            generated in ``random_delay`` interval. This defaults to
            ``(0, 0)``.

        :param callback: Callable called after writing a word and the
            delay time has elapsed. This defaults to a lambda which do
            nothing.

        :param cargs: All the arguments that will be passed to callback.
            This defaults to an empty tuple.

        .. NOTE::
            Method flow:
                - Calling ``framing_box`` method.
                - Flash screen depending ``flash_screen`` parameter.
                - Cutting text into line to stay within the dialog box
                  frame.
                - Writing paragraph by paragraph.
                - Writing each line of the current paragraph, word by
                  word.
                - Waits until a key contained in the class attribute
                  ``confirm_dialog_key`` was pressed before writing the
                  following paragraph.
                - Complete cleaning ``win``.

        .. WARNING::
            If the volume of text displayed is too large to be contained
            in a dialog box, text will be automatically cut into
            paragraphs using ``textwrap.wrap`` function. See
            `textwrap module documentation
            <https://docs.python.org/fr/3.8/library/textwrap.html#textwrap.wrap>`_
            for more information of the behavior of text wrap.

        .. WARNING::
            ``win`` will be completely cleaned when writing each
            paragraph by ``window.clear()`` method of ``curses``
            module.
        """
        self.framing_box(win)

        if flash_screen:
            curses.flash()

        attr = (curses.color_pair(colors_pair_nb), *text_attr)

        wrapped_text = self.text_wrapper.wrap(text)
        wrapped_text = _make_chunk(wrapped_text, self.nb_lines_max)

        for paragraph in wrapped_text:
            win.clear()
            self.framing_box(win)
            for y, line in enumerate(paragraph):
                offsetting_x = 0
                for word in line.split(cut_char):
                    if word in words_attr.keys():
                        attr = words_attr[word]

                        # Test if only one argument is passed instead of a tuple.
                        if isinstance(text_attr, int):
                            text_attr = (text_attr, )
                    else:
                        if isinstance(text_attr, int):
                            text_attr = (text_attr, )

                        attr = (curses.color_pair(colors_pair_nb), *text_attr)

                    with TextAttributes(win, *attr):
                        win.addstr(self.text_pos_y + y,
                                   self.text_pos_x + offsetting_x, word)
                        win.refresh()

                    # Compensates for the space between words.
                    offsetting_x += len(word) + 1

                    time.sleep(delay + random.uniform(*random_delay))

                callback(*cargs)

            self._display_end_indicator(win)
            self.getkey(win)
