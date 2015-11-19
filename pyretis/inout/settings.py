# -*- coding: utf-8 -*-
"""This module handles parsing of input settings.

This module define the file format for pyretis input files.
"""
import ast
import re
import warnings

KNOWN_KEYWORDS = {'integrator': 'dict',
                  'ensemble': 'string',
                  'interfaces': 'list',
                  'generate-vel': 'dict',
                  'output-dir': 'string',
                  'periodic_boundary': 'list',
                  'temperature': 'number',
                  'tis': 'dict',
                  'units': 'string',
                  'output': 'list'}


def look_for_keyword(line):
    """Function to look for a keyword in a string.

    The keyword is assumed to be given as `:keyword:` at the
    beginning of the string.

    Parameters
    ----------
    line : string
        The string for which we look for the keyword

    Returns
    -------
    out[0] : string
        The matched keyword, note that this can be any case.
    out[1] : string
        A lower-case version of `out[0]`.
    out[2] : boolean
        `True` if the keyword is one of the known keywords.
    """
    key = re.match(r':(.*?):', line)
    if key:
        keyword = key.group(1).lower()
        return key.group(1), keyword, keyword in KNOWN_KEYWORDS
    else:
        return None, None, False


def parse_setting(setting, keyword):
    """Parse one setting to python usable stuff.

    This will parse settings using the `ast` module. The output will
    be usable as input to pyretis.

    Parameters
    ----------
    settings : list
        The setting to parse.
    keyword : string
        The keyword for which we are parsing a setting.

    Returns
    -------
    out : string, number, tuple, list, dict, boolea or None
        The parsed setting.
    """
    str_setting = ''.join(setting)
    if KNOWN_KEYWORDS[keyword] == 'string':
        return str_setting
    else:
        try:
            ev_setting = ast.literal_eval(str_setting)
        except SyntaxError:
            ev_setting = str_setting
        return ev_setting


def parse_settings_file(filename):
    """Parse settings from a file name.

    Parameters
    ----------
    filename : string
        The file to parse.

    Returns
    -------
    out : dict
        A dictionary with settings for pyretis.
    """
    settings = {}
    reading = False
    read_keyword = None
    with open(filename, 'r') as fileh:
        for lines in fileh:
            to_read = lines.strip()
            if not to_read:
                continue
            if to_read.startswith('#'):
                continue
            match, keyword, known = look_for_keyword(to_read)
            if keyword:  # found a new keyword!
                if known:
                    reading = True
                    read_keyword = keyword
                    to_read = to_read.split(':{}:'.format(match))[1].strip()
                    settings[read_keyword] = []
                else:
                    msg = 'Unknown keyword "{}" found. Ignoring.'
                    warnings.warn(msg.format(match))
                    reading = False
                    read_keyword = None
            if reading:
                settings[read_keyword].append(to_read)
                read_type = KNOWN_KEYWORDS[read_keyword]
                if read_type in ('string', 'number', 'boolean'):
                    reading = False  # just read the current line
                elif read_type == 'list':
                    reading = not (to_read.endswith(']') or
                                   to_read.endswith(')'))
                elif read_type == 'dict':
                    reading = not to_read.endswith('}')
                else:
                    warnings.warn('{}'.format(read_type))
    for key in settings:
        settings[key] = parse_setting(settings[key], key)
    return settings
