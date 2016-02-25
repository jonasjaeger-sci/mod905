# -*- coding: utf-8 -*-
"""This module handles parsing of input settings.

This module define the file format for pyretis input files.
"""
import ast
import logging
import os
import pprint
import re
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['parse_settings_file', 'write_settings_file']


KEYWORDS = {'integrator': {'default': None},
            'orderparameter': {'default': None},
            'endcycle': {'default': None},
            'task': {'default': None},
            'units': {'default': 'lj'},
            'units-base': {'default': None},
            'ensemble': {'default': None},
            'interfaces': {'default': None},
            'output-dir': {'default': None},
            'box': {'default': None},
            'particles-position': {'default': None},
            'particles-velocity': {'default': None},
            'particles-mass': {'default': None},
            'particles-type': {'default': None},
            'dimensions': {'default': 3},
            'temperature': {'default': None},
            'tis': {'default': None},
            'output-add': {'default': None},
            'output-modify': {'default': None},
            'potentials': {'default': None},
            'potential-parameters': {'default': None},
            'forcefield': {'default': None}}


def look_for_keyword(line):
    """Function to look for a keyword in a string.

    A string is assumed to define a keyword if the keyword appears as
    the first word in the string, ending with a '='.

    Parameters
    ----------
    line : string
        The string for which we look for the keyword

    Returns
    -------
    out[0] : string
        The matched keyword, note that this can be any case. And it
        may also contain spaces. It contains the '=' seperator also.
    out[1] : string
        A lower-case version of `out[0]`.
    out[2] : boolean
        `True` if the keyword is one of the known keywords.
    """

    key = re.match(r'(.*?)=', line)
    if key:
        keyword = ''.join([key.group(1), '='])
        keywordl = key.group(1).strip().lower()
        return keyword, keywordl, keywordl in KEYWORDS
    else:
        return None, None, False


def parse_primitive(text):
    """Parse text to python using the ast module

    Parameters
    ----------
    text : string
        The text to parse.

    Returns
    -------
    out[0] : string, dict, list, boolean, etc.
        The parsed text.
    out[1] : boolean
        True if we managed to parse the text, False otherwise.
    """
    parsed = None
    success = False
    try:
        parsed = ast.literal_eval(text.strip())
        success = True
    except SyntaxError:
        parsed = text.strip()
        success = True
    except ValueError:
        parsed = text.strip()
        success = True
    return parsed, success


def parse_settings_file(filename):
    """Parse settings from a file name.

    Here, we read the file line-by-line and check if the current line
    contains a keyword, if so, we parse that keyword.

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
    current_keyword = None
    to_parse = []
    with open(filename, 'r') as fileh:
        for lines in fileh:
            to_read, _, _ = lines.strip().partition('#')
            if not to_read:
                if current_keyword is not None:
                    # empty line or comment or something else -> parse!
                    parse_setting(''.join(to_parse), current_keyword,
                                  settings)
                    current_keyword = None
                    to_parse = []
                continue
            match, keyword, found_keyword = look_for_keyword(to_read)
            if found_keyword:
                if current_keyword is not None:
                    # found new keyword, parse for the previous one!
                    parse_setting(''.join(to_parse), current_keyword,
                                  settings)
                current_keyword = keyword
                to_parse = [to_read[len(match):]]
            else:
                if current_keyword is not None:
                    to_parse.append(to_read)
    if current_keyword is not None:
        # reached end of file, parse for the last setting!
        parse_setting(''.join(to_parse), current_keyword, settings)
    add_default_settings(settings)
    return settings


def parse_setting(text, keyword, settings):
    """Method that will parse a string and try to add the settings.

    Parameters
    ----------
    text : string
       The text to parse.
    keyword : string
        The keyword we are trying to read settings for.
    settings : dict
        The dict to store settings in.

    Returns
    -------
    out : boolean
        True if we managed to parse the setting, False otherwise.
    """
    parsed, success = parse_primitive(text.strip())
    if success:
        settings[keyword] = parsed
    else:
        msg = ['Could not parse setting for keyword {}'.format(keyword)]
        msg += ['Input setting: {}'.format(text.strip())]
        msgtxt = '\n'.join(msg)
        logger.critical(msgtxt)
    return success


def write_settings_file(settings, outfile, path=None):
    """Write simulation settings to an output file.

    This will write a dictionary to a output file in the pyretis input
    file format.

    Parameters
    ----------
    settings : dict
        The dictionary to write
    outfile : string
        The file to create
    path : string, optional
        A path which determines where the file should be written.

    Note
    ----
    This will currently fail for objects.
    """
    if path is not None:
        filename = os.path.join(path, outfile)
    else:
        filename = outfile
    with open(filename, 'w') as fileh:
        for key in settings:
            if settings[key] is None:
                continue
            leng = len(key) + 3
            pretty = pprint.pformat(settings[key], width=79-leng)
            pretty = pretty.replace('\n', '\n' + ' ' * leng)
            dump = '{} = {}\n'.format(key, pretty)
            fileh.write(dump)


def add_default_settings(settings):
    """Method that will add default values to the settings.

    Parameters
    ----------
    settings : dict
        The current settings.

    Returns
    -------
    None, but will update `settings` with default values.
    """
    for key in KEYWORDS:
        if 'default' in KEYWORDS[key] and key not in settings:
            settings[key] = KEYWORDS[key]['default']
