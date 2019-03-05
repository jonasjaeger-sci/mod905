# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Module defining the base classes for the PyRETIS output.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ScreenOutput (:py:class:`.FileIO`)
    A generic class for handling output to the screen.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

print_to_screen (:py:func:`.print_to_screen`)
    A method used for printing messages to screen.

"""
import logging
import colorama
from pyretis.inout.common import OutputBase


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


# Colors for printing:
_PRINT_COLORS = {
    'error': colorama.Fore.RED,
    'info': colorama.Fore.BLUE,
    'warning': colorama.Fore.YELLOW,
    'message': colorama.Fore.CYAN,
    'success': colorama.Fore.GREEN
}


__all__ = ['ScreenOutput', 'print_to_screen']


class ScreenOutput(OutputBase):
    """A class for handling output to the screen."""

    target = 'screen'

    def write(self, towrite, end=None):
        """Write a string to the file.

        Parameters
        ----------
        towrite : string
            The string to output to the file.
        end : string, optional
            Override how the print statements ends.

        Returns
        -------
        status : boolean
            True if we managed to write, False otherwise.

        """
        if towrite is None:
            return False
        if end is not None:
            print(towrite, end=end)
            return True
        print(towrite)
        return True


def print_to_screen(txt=None, level=None):  # pragma: no cover
    """Print output to standard out.

    This method is included to ensure that output from PyRETIS to the
    screen is written out in a uniform way across the library and
    application(s).

    Parameters
    ----------
    txt : string, optional
        The text to write to the screen.
    level : string, optional
        The level can be used to color the output.

    """
    if txt is None:
        print()
    else:
        out = '{}'.format(txt)
        color = _PRINT_COLORS.get(level, None)
        if color is None:
            print(out)
        else:
            print(color + out)
