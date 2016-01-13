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


KNOWN_KEYWORDS = {'integrator': 'dict',
                  #'orderparameter': 'many',
                  'endcycle': 'number',
                  'task': 'string',
                  'units': 'dict',
                  #'ensemble': 'string',
                  #'interfaces': ('many'),
                  #'generate-vel': 'many',
                  'output-dir': 'string',
                  'box': 'dict',
                  'particle-position': 'dict',
                  'particle-velocity': 'dict',
                  'dimensions': 'number',
                  'temperature': 'number',
                  'tis': 'dict'}
                  #a'output': 'many',
                  #'potentials': 'many',
                  #'potential-parameters': 'many',
                  #'forcefield': 'many'}

INTEGRATOR_SETTINGS = {}

INTEGRATOR_SETTINGS['verlet'] = {'timestep', 'number'}
INTEGRATOR_SETTINGS['velocityverlet'] = {'timestep', 'number'}
INTEGRATOR_SETTINGS['langevin'] = {'timestep': 'number', 'gamma': 'number',
                                   'high-friction': 'boolean'}

KEYWORD_SETTINGS = {'integrator': INTEGRATOR_SETTINGS}


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

    if keyword not in KNOWN_KEYWORDS:
        return None, False

    try:
        str_setting = setting.split(' ', 1)[1].strip()
    except IndexError:
        return None, False

    if KNOWN_KEYWORDS[keyword] == 'string':
        parsed = str_setting
        success = True
    elif KNOWN_KEYWORDS[keyword] == 'number':
        try:
            parsed = ast.literal_eval(str_setting)
            success = True
        except ValueError:
            success = False
    elif KNOWN_KEYWORDS[keyword] == 'dict':
        parsed = {}
        par, _, opt = str_setting.partition(',')
        parsed['name'] = par.strip()
        opt = opt.strip()
        if len(opt) > 0:
            for opti in opt.split(','):
                key, _, val = opti.strip().partition(' ')
                parsed[key.strip().lower()] = val
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
    with open(filename, 'r') as fileh:
        for lines in fileh:
            to_read = lines.strip()
            if not to_read:
                continue
            if to_read.startswith('#'):
                continue
            _, keyword, known = look_for_keyword(to_read)
            if known:
                parsed, success = parse_setting(to_read, keyword)
                if success:
                    if keyword in settings:
                        msg = 'Updating already defined setting {}: {}'
                        msgtxt = msg.format(keyword, settings[keyword])
                        logger.warning(msgtxt)
                    settings[keyword] = parsed
                else:
                    msg = 'Could not understand setting "{}"'
                    msgtxt = msg.format(to_read)
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
