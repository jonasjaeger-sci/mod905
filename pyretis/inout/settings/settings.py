# -*- coding: utf-8 -*-
"""This module handles parsing of input settings.

This module define the file format for pyretis input files.
"""
import ast
import logging
import os
import pprint
#from pyretis.core.simulation.common import check_settings

logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())



__all__ = ['parse_settings_file', 'parse_setting',
           'look_for_keyword', 'write_settings_file']


KNOWN_KEYWORDS = {'integrator': {'type': 'dict'},
                  'orderparameter': {'type': 'dict'},
                  'endcycle': {'type': 'number'},
                  'task': {'type': 'string'},
                  'units': {'type': 'dict'},
                  'ensemble': 'string',
                  'interfaces': {'type': 'list'},
                  'output-dir': {'type': 'string'},
                  'box': {'type': 'dict'},
                  'particle-position': {'type': 'dict'},
                  'particle-velocity': {'type': 'dict'},
                  'particle-mass': {'type': 'dict'},
                  'dimensions': {'type': 'number'},
                  'temperature': {'type': 'number'},
                  'tis': {'type': 'dict'},
                  'particles-position': {'type': 'dict'},
                  'particles-velocity': {'type': 'dict'},
                  #a'output': 'many',
                  'potential-function': {'type': 'dict', 'append': True},
                  'potential-parameters': {'type': 'dict', 'append': True},
                  'forcefield': {'type': 'string'}}


def look_for_keyword(line):
    """Function to look for a keyword in a string.

    A string is assumed to define a keyword if the keyword appears as
    the first word in the string.

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
    try:
        key = line.split()[0].strip()
    except IndexError:
        return None, None, False
    keyword = key.lower()
    if keyword in KNOWN_KEYWORDS:
        return key, keyword, True
    else:
        return None, None, False


def parse_setting(setting, keyword):
    """Parse one setting to python usable stuff.

    The setting for keywords are on the form:

    keyword setting, optional1 10, optional2, 100, optional3 1000

    Parameters
    ----------
    setting : string
        The setting to parse.
    keyword : string
        The keyword for which we are parsing a setting.

    Returns
    -------
    out[0] : string, dict, list, boolean, etc.
        The parsed setting.
    out[1] : boolean
        True if we managed to parse the setting, False otherwise.
    """
    parsed = None
    success = False

    try:
        str_setting = setting.split(' ', 1)[1].strip()
    except IndexError:
        return None, False

    key_type = KNOWN_KEYWORDS[keyword].get('type', '')

    if key_type == 'string':
        parsed = str_setting
        success = True
    elif key_type == 'number':
        try:
            parsed = ast.literal_eval(str_setting)
            success = True
        except SyntaxError:
            success = False
    elif key_type == 'dict':
        parsed = {}
        for opti in str_setting.split(','):
            key, _, val = opti.strip().partition(' ')
            key = key.strip().lower()
            if len(key) < 1:
                continue
            val = val.strip()
            if len(val) < 1:
                msg = 'Ignoring empty value: {} = {}'.format(key, val)
                logger.warning(msg)
            try:
                parsed[key] = ast.literal_eval(val)
            except SyntaxError:
                parsed[key] = val
            except ValueError:
                parsed[key] = val
        success = True
    elif key_type == 'list':
        try:
            parsed = ast.literal_eval('[{}]'.format(str_setting))
            success = True
        except SyntaxError:
            success = False
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
    keyword_split = False
    to_parse = []
    with open(filename, 'r') as fileh:
        for lines in fileh:
            to_read = lines.strip()
            if to_read.startswith('#') or not to_read:
                if current_keyword is not None:
                    parse_and_add(' '.join(to_parse), current_keyword,
                                  settings)
                    current_keyword = None
                    keyword_split = False
                    to_parse = []
                continue
            _, keyword, found_keyword = look_for_keyword(to_read)
            if found_keyword:
                if current_keyword is not None:
                    parse_and_add(' '.join(to_parse), current_keyword,
                                  settings)
                keyword_split = to_read.endswith(',')
                to_parse = []
                if not keyword_split:
                    # just parse this line
                    parse_and_add(to_read, keyword, settings)
                    current_keyword = None
                else:
                    current_keyword = keyword
            if keyword_split:
                to_parse.append(to_read)
                keyword_split = to_read.endswith(',')
                if not keyword_split:
                    # parse things
                    parse_and_add(' '.join(to_parse), current_keyword,
                                  settings)
                    current_keyword = None
                    to_parse = []
    if current_keyword is not None:
        parse_and_add(' '.join(to_parse), current_keyword, settings)
    return settings


def parse_and_add(text, keyword, settings):
    """Method that will parse a string and try to add the settings.

    Parameters
    ----------
    text : string
       The text to parse.
    keyword : string
        The keyword we are trying to parse data for.
    settings : dict
        Where to store the text.

    Returns
    -------
    N/A but updates the input dictionary `settings`.
    """
    parsed, success = parse_setting(text, keyword)
    if success:
        append = KNOWN_KEYWORDS[keyword].get('append', False)
        if append:  # maybe to be removed?
            try:
                settings[keyword].append(parsed)
            except KeyError:
                settings[keyword] = [parsed]
        else:
            if keyword in settings:
                msg = 'Updating already defined setting {}: {}'
                msgtxt = msg.format(keyword, settings[keyword])
                logger.warning(msgtxt)
            settings[keyword] = parsed
    else:
        msg = 'Could not understand setting "{}"'
        msgtxt = msg.format(text)
        logger.warning(msgtxt)
    return settings


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
            leng = len(key) + 3
            pretty = pprint.pformat(settings[key], width=79-leng)
            pretty = pretty.replace('\n', '\n' + ' ' * leng)
            dump = '{} = {}\n'.format(key, pretty)
            fileh.write(dump)
