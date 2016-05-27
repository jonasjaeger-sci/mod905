# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This module handles parsing of input settings.

This module define the file format for pyretis input files.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

parse_settings_file
    Method for parsing settings from a given input file.

write_settings_file
    Method for writing settings from a simulation to a given file.
"""
import ast
import logging
import pprint
import re
from pyretis.inout.common import create_backup
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['parse_settings_file', 'write_settings_file']


KEYWORDS = {'integrator': {'default': None},
            'orderparameter': {'default': None},
            'steps': {'default': 0},
            'startcycle': {'default': 0},
            'endcycle': {'default': None},
            'task': {'default': None},
            'units': {'default': 'lj'},
            'units-base': {'default': {}},
            'ensemble': {'default': None},
            'interfaces': {'default': None},
            'output-dir': {'default': None},
            'exe-path': {'defualt': None},
            'box': {'default': None},
            'particles-position': {'default': None},
            'particles-velocity': {'default': None},
            'particles-mass': {'default': None},
            'particles-type': {'default': None},
            'particles-name': {'default': None},
            'dimensions': {'default': 3},
            'temperature': {'default': None},
            'tis': {'default': None},
            'output-add': {'default': None},
            'output-modify': {'default': None},
            'potentials': {'default': None},
            'potential-parameters': {'default': None},
            'forcefield': {'default': None},
            # Next are analysis-specific:
            'skipcross': {'default': 1001},
            'maxblock': {'default': 1000},
            'blockskip': {'default': 1},
            'bins': {'default': 1000},
            'ngrid': {'default': 1001},
            'maxordermsd': {'default': 100},
            'plot': {'default': {'plotter': 'mpl', 'output': 'png',
                                 'style': 'pyretis', 'backup': False}},
            'txt-output': {'default': {'fmt': 'txt.gz', 'backup': False}},
            'report': {'default': ['latex', 'rst', 'html']},
            'npart': {'default': None}}


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


def parse_settings_file(filename, add_default=True):
    """Parse settings from a file name.

    Here, we read the file line-by-line and check if the current line
    contains a keyword, if so, we parse that keyword.

    Parameters
    ----------
    filename : string
        The file to parse.
    add_default : boolean
        If True, we will add default settings as well for keywords
        not found in the input.

    Returns
    -------
    out : dict
        A dictionary with settings for pyretis.
    """
    with open(filename, 'r') as fileh:
        settings = parse_settings(fileh, add_default=add_default)
    return settings


def parse_settings(input_text, add_default=True):
    """Parse settings from a list of strings.

    Here, we read the file line-by-line and check if the current line
    contains a keyword, if so, we parse that keyword.

    Parameters
    ----------
    input_text : iterable (e.g. list of strings)
        The input to parse.
    add_default : boolean
        If True, we will add default settings as well for keywords
        not found in the input.

    Returns
    -------
    out : dict
        A dictionary with settings for pyretis.
    """
    settings = {}
    current_keyword = None
    to_parse = []
    for lines in input_text:
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
    if add_default:
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


def settings_to_text(settings):
    """Turn the given settings into text usable for an output file.

    Parameters
    ----------
    settings : dict
        The dictionary to write

    Yields
    ------
    out : strings
        The strings representing the settings.
    """
    for key in settings:
        if settings[key] is None:
            continue
        leng = len(key) + 3
        pretty = pprint.pformat(settings[key], width=79-leng)
        pretty = pretty.replace('\n', '\n' + ' ' * leng)
        dump = '{} = {}\n'.format(key, pretty)
        yield dump


def setting_to_text(settings, key):
    """Turn a given setting into text usable for an output file.

    Parameters
    ----------
    settings : dict
        The dictionary to write
    key : string
        The setting to format

    Returns
    ------
    out : string
        The string representing the settings.
    """
    if settings[key] is None:
        return ''
    else:
        leng = len(key) + 3
        pretty = pprint.pformat(settings[key], width=79-leng)
        pretty = pretty.replace('\n', '\n' + ' ' * leng)
        return '{} = {}'.format(key, pretty)


def write_settings_file(settings, outfile, backup=True):
    """Write simulation settings to an output file.

    This will write a dictionary to a output file in the pyretis input
    file format.

    Parameters
    ----------
    settings : dict
        The dictionary to write
    outfile : string
        The file to create
    backup : boolean, optional
        If True, we will backup existing files with the same file
        name as the provided file name.

    Note
    ----
    This will currently fail if objects have made it into the supplied
    ``settings``.
    """
    # define a ordering of sections to write to the file:
    group = [{'header': 'pyretis simulation\n==================\n',
              'keys': ('units', 'task', 'steps', 'startcycle', 'interfaces',
                       'integrator')},
             {'header': '\n\nSystem settings\n---------------\n',
              'keys': ('dimensions', 'temperature')},
             {'header': '\n\nParticles\n---------\n',
              'keys': ('particles-position', 'particles-velocity',
                       'particles-mass', 'particles-name', 'particles-type')},
             {'header': '\n\nForce field settings\n--------------------\n',
              'keys': ('forcefield', 'potentials', 'potential-parameters')},
             {'header': '\n\nOrder parameter\n---------------\n',
              'keys': ('orderparameter',)},
             {'header': '\n\nOutput settings\n---------------\n',
              'keys': ('output-modify', 'output-add')},
             {'header': '\n\nAnalysis settings\n-----------------\n',
              'keys': ('endcycle', 'skipcross', 'maxblock', 'blockskip',
                       'bins', 'ngrid', 'maxordermsd', 'plot', 'txt-output',
                       'report', 'npart')}]

    if backup:
        msg = create_backup(outfile)
        if msg:
            logger.warning(msg)

    written = set()  # make sure we don't write the same thing in many places
    with open(outfile, 'w') as fileh:
        for i, section in enumerate(group):
            to_write = [section['header']]
            for key in section['keys']:
                if key in settings and key not in written:
                    to_write.append(setting_to_text(settings, key))
                    written.add(key)
            if len(to_write) > 1 or i == 0:
                fileh.write('\n'.join(to_write))
        # Also write remaining if anything
        to_write = ['\n\nOther settings\n--------------\n']
        for key in sorted(settings):
            if not key in written and settings[key] is not None:
                to_write.append(setting_to_text(settings, key))
                written.add(key)
        if len(to_write) > 1:
            fileh.write('\n'.join(to_write))


def add_default_settings(settings):
    """Method that will add default values to the settings.

    Parameters
    ----------
    settings : dict
        The current settings.

    Returns
    -------
    None, but will update `settings` with default values.

    Note
    ----
    For many cases the default values can depend on what we want do
    to. For instance if we are reading particles from an input file,
    then the default particle type is not used but read from the
    file and assigned automatically. When generating on a lattice,
    we do not have information on the particles types and in this case,
    the default is used. This means that we can't set a uniform default
    in this case. That is why we ignore all defaults here when the
    default is `None`
    """
    for key in KEYWORDS:
        if key not in settings:
            default = KEYWORDS[key].get('default', None)
            if default is not None:
                settings[key] = default
