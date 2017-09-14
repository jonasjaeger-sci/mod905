# -*- coding: utf-8 -*-
"""
pyretis style for pygments
~~~~~~~~~~~~~~~~~~~~~~~~~~

This style is based on `Xcode` from the Pygments.
For the original style:

    :copyright: Copyright 2006-2015 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.

See: http://pygments.org/
"""

from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, \
     Number, Operator, Literal, Generic

def setup(app):
    pass

class PyretisStyle(Style):
    """
    Style similar to the Xcode default colouring theme.
    """

    default_style = ''

    styles = {
        Comment:                '#177500',
        Comment.Preproc:        '#633820',

        String:                 '#C41A16',
        String.Char:            '#2300CE',

        Operator:               '#000000',

        Keyword:                '#A90D91',

        Name:                   '#000000',
        Name.Attribute:         '#836C28',
        Name.Class:             '#3F6E75',
        Name.Function:          '#000000',
        Name.Builtin:           '#A90D91',
        # In Obj-C code this token is used to colour Cocoa types
        Name.Builtin.Pseudo:    '#5B269A',
        Name.Variable:          '#000000',
        Name.Tag:               '#000000',
        Name.Decorator:         '#000000',
        # Workaround for a BUG here: lexer treats multi-line method signatres as labels
        Name.Label:             '#000000',

        Literal:                '#1C01CE',
        Number:                 '#1C01CE',
        Error:                  '#000000',

        Generic.Heading:           "bold #000080",
        Generic.Subheading:        "bold #800080",
        Generic.Deleted:           "#A00000",
        Generic.Inserted:          "#00A000",
        Generic.Error:             "#FF0000",
        Generic.Emph:              "italic",
        Generic.Strong:            "bold",
        Generic.Prompt:            "bold #000080",
        Generic.Output:            "#888",
        Generic.Traceback:         "#04D",

    }
