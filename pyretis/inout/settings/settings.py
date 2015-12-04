# -*- coding: utf-8 -*-
"""This module handles parsing of input settings.

This module define the file format for pyretis input files.
"""
import ast
import re
import logging
#from pyretis.core.simulation.common import check_settings

logging.getLogger(__name__).addHandler(logging.NullHandler())


__all__ = ['parse_settings_file', 'parse_setting',
           'look_for_keyword']


KNOWN_KEYWORDS = {'integrator': 'dict',
                  'task': 'string',
                  'units': 'dict',
                  'ensemble': 'string',
                  'interfaces': 'list',
                  'generate-vel': 'dict',
                  'output-dir': 'string',
                  'box': 'dict',
                  'particles': 'dict',
                  'initial-pos': 'dict',
                  'initial-vel': 'dict',
                  'dimensions': 'number',
                  'temperature': 'number',
                  'tis': 'dict',
                  'output': 'list',
                  'potential-parameters': 'list',
                  'potential-settings': 'list',
                  'potential-functions': 'list'}

#ALWAYS_REQUIRED = ['task', 'units', 'initial-pos']


def look_for_keyword(line):
    """Function to look for a keyword in a string.

    The keyword is assumed to be given as `keyword =` at the
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
    key = re.match(r'(.*?)=', line)
    if key:
        keyword = key.group(1)
        keywordl = keyword.strip().lower()
        return keyword, keywordl, keywordl in KNOWN_KEYWORDS
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
            msg = 'Could not understand {} = {}'.format(keyword, setting)
            ev_setting = str_setting
            raise ValueError(msg)
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
                    to_read = to_read.split('{}='.format(match))[1].strip()
                    settings[read_keyword] = []
                else:
                    msg = 'Unknown keyword "{}" found. Ignored!'.format(match)
                    logging.warning(msg)
                    reading = False
                    read_keyword = None
            if reading:
                settings[read_keyword].append(to_read)
                read_type = KNOWN_KEYWORDS[read_keyword]
                if read_type in ('string', 'number', 'boolean'):
                    reading = False  # just read the current line
                elif read_type == 'list':
                    # stop reading if we end by a ')' or ']'
                    # if this is a list of lists we end by ']]' if the
                    # input ends, otherwise we end by ','.
                    reading = not (to_read.endswith(']') or
                                   to_read.endswith(')'))
                elif read_type == 'dict':
                    reading = not to_read.endswith('}')
                else:
                    msg = 'Unknown read type "{}"'.format(read_type)
                    logging.warning(msg)
    for key in settings:
        settings[key] = parse_setting(settings[key], key)
    return settings
