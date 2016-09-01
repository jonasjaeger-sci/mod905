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


SECTIONS = {'system', 'simulation',
            'units base',
            'tis settings',
            'box',
            'integrator',
            'path sampling',
            'particles',
            'force field',
            'potential',
            'order parameter',
            'output trajectory',
            'output pathensemble'}

KEYWORDS = {}
KEYWORDS['system'] = {'dimensions': 3,
                      'temperature': 1.0,
                      'units': 'lj'}
KEYWORDS['simulation'] = {'task': None,
                          'run_type': None,
                          'steps': 0,
                          'startcycle': 0,
                          'endcycle': 0,
                          'ensemble': None}
KEYWORDS['units base'] = {'name': None,
                          'length': None,
                          'mass': None,
                          'energy': None,
                          'charge': None}
KEYWORDS['box'] = {'size': None,
                   'periodic': None}
KEYWORDS['integrator'] = {'class': None,
                          'module': None,
                          'setting': None}
KEYWORDS['order parameter'] = {'class': None,
                              'module': None,
                              'setting': None}
KEYWORDS['potential'] = {'class': None,
                         'setting': None,
                         'parameter': None}
KEYWORDS['force field'] = {'description': None}
KEYWORDS['output trajectory'] = {'when': None}
KEYWORDS['output pathensemble'] = {'when': None}
KEYWORDS['particles'] = {'position': None,
                         'velocity': None,
                         'mass': None,
                         'name': None,
                         'type': None}
SPECIAL_KEY = set(('parameter', 'setting'))


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


def look_for_section(string):
    """Return True + section name if we find a section name."""
    if string is None:
        return False, None
    for key in SECTIONS:
        if string.lower().startswith(key):
            return True, key
    return False, None


def look_for_section_mark(string):
    """Return True if we find a headline marker like '-------'"""
    return string.startswith('--') or string.startswith('==')


def look_for_keyword(keywords, line):
    """Function to look for a keyword in a string.

    A string is assumed to define a keyword if the keyword appears as
    the first word in the string, ending with a `=`.

    Parameters
    ----------
    keywords : dict
        The keywords to search for.
    line : string
        A string to check for a keyword.

    Returns
    -------
    out[0] : string
        The matched keyword. It may contains spaces and it will also
        contain the matched `=` seperator.
    out[1] : string
        A lower-case, stripped version of `out[0]`.
    out[2] : boolean
        `True` if we found a possible keyword.
    """
    # match a word followed by a '='
    key = re.match(r'(.*?)=', line)
    if key:
        keyword = ''.join([key.group(1), '='])
        keyword_low = key.group(1).strip().lower()
        for i in SPECIAL_KEY:
            if keyword_low.startswith(i):
                return keyword, i, True
        return keyword, keyword_low, True
    else:
        return None, None, False


def _parse_sections(inputtxt):
    """Parse raw data in sections from the input file.

    Parameters
    ----------
    inputtxt : list of strings or iterable file object
        The raw data to parse

    Returns
    -------
    raw_data : dict
        A dictionary with keys corresponding to the sections found
        in the input file. `raw_data[key]` contains the raw data
        for the section corresponding to `key`.
    """
    potentials = 0
    raw_data = {}
    heading = None
    current_line = None
    previous_line = None
    add_section = None
    data = []
    for lines in inputtxt:
        current_line, _, _ = lines.strip().partition('#')
        if not current_line:
            continue
        else:
            data += [current_line]
        if look_for_section_mark(current_line):
            found, section_title = look_for_section(previous_line)
            if found:
                if section_title == 'potential':
                    section_title = 'potential{}'.format(potentials)
                    potentials += 1
                if section_title not in raw_data:
                    raw_data[section_title] = []
                if add_section is not None:
                    raw_data[add_section].extend(data[:-2])
                    data = []
                else:
                    # All data before first section is assumed
                    # to just be a heading.
                    heading = data[:-2]
                    data = []
                add_section = section_title
            else:
                # we found a section mark, let's just nuke it
                # from data:
                data.pop()
        previous_line = current_line
    if add_section is not None:
        raw_data[add_section].extend(data)
    return raw_data, heading


def _parse_raw_section(raw_section, section):
    """Parse the raw data from a section.

    Parameters
    ----------
    raw_section : list of strings
        The text data for a given section which will be parsed.
    section : string
        A text identifying the section we are parsing for. This is
        used to get a list over valid keywords for the section.

    Returns
    -------
    setting : dict
        A dict with keys corresponding to the settings.
    """
    setting = {}
    if section not in KEYWORDS:
        # unknown section, just ignore silently
        return None
    merged = []
    # first we merge text that is split across line.
    # this is done by assuming that keyword separate settings
    for line in raw_section:
        _, _, found_keyword = look_for_keyword(KEYWORDS[section], line)
        if found_keyword or len(merged) == 0:
            merged.append(line)
        else:
            merged[-1] = ''.join((merged[-1], line))

    for line in merged:
        match, keyword, found_keyword = look_for_keyword(KEYWORDS[section],
                                                         line)
        if found_keyword:
            raw = line[len(match):].strip()
            parsed, success = parse_primitive(raw)
            if success:
                if keyword in SPECIAL_KEY:
                    if not keyword in setting:
                        setting[keyword] = {}
                    var = line.split(keyword)[1].split()[0]
                    setting[keyword][var] = parsed
                else:
                    setting[keyword] = parsed
            else:
                msg = ['Could read keyword {}'.format(keyword)]
                msg += ['Keyword was skipped, please check your input!']
                msg += ['Input setting: {}'.format(raw)]
                msgtxt = '\n'.join(msg)
                logger.critical(msgtxt)
    return setting


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
    settings : dict
        A dictionary with settings for pyretis.
    """
    settings = {}
    with open(filename, 'r') as fileh:
        raw_sections, _ = _parse_sections(fileh)
    for key in raw_sections:
        if key.startswith('potential'):
            new_setting = _parse_raw_section(raw_sections[key], 'potential')
            if not 'potential' in settings:
                settings['potential'] = []
            settings['potential'].append(new_setting)
        else:
            new_setting = _parse_raw_section(raw_sections[key], key)
            if new_setting is None:
                continue
            settings[key] = {}
            for sub_key in new_setting:
                settings[key][sub_key] = new_setting[sub_key]
    if add_default:
        print('Time to add defaults!')
    return settings


def settings_to_text(settings, section):
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
    sec = '{}\n{}'.format(section.capitalize(), len(section)*('-'))
    data = []
    for key in settings:
        if settings[key] is None:
            continue
        leng = len(key) + 3
        pretty = pprint.pformat(settings[key], width=79-leng)
        pretty = pretty.replace('\n', '\n' + ' ' * leng)
        dump = '{} = {}\n'.format(key, pretty)
        data.append(dump)
    if len(data) > 0:
        string = '{}\n{}'.format(sec, ''.join(data))
    else:
        string = ''
    return string


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
    if settings is None:
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
            if key not in written and settings[key] is not None:
                to_write.append(setting_to_text(settings, key))
                written.add(key)
        if len(to_write) > 1:
            fileh.write('\n'.join(to_write))
