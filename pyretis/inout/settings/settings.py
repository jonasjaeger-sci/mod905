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
from collections import OrderedDict
import logging
import pprint
import re
from pyretis.inout.common import create_backup
from pyretis import __program_name__ as NAME
from pyretis import __url__ as URL
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['parse_settings_file', 'write_settings_file']


MAX_POT = 99  # For practical reasons, just limit this.
SECTIONS = OrderedDict()
TITLE = '{} input settings'.format(NAME)
HEADING = '{}\n{}\nFor more info, please see: {}\nHave Fun!'
SECTIONS['heading'] = {'text': HEADING.format(TITLE, ('=')*len(TITLE), URL)}
SECTIONS['simulation'] = {'task': None,
                          'steps': None,
                          'startcycle': None,
                          'endcycle': None,
                          'ensemble': None}
SECTIONS['system'] = {'dimensions': 3,
                      'temperature': 1.0,
                      'units': 'lj'}
SECTIONS['unit-system'] = {'name': None,
                           'length': None,
                           'mass': None,
                           'energy': None,
                           'charge': None}
SECTIONS['integrator'] = {'class': None,
                          'module': None}
SECTIONS['box'] = {'size': None,
                   'periodic': None}
SECTIONS['particles'] = {'position': None,
                         'velocity': None,
                         'mass': None,
                         'name': None,
                         'type': None,
                         'npart': None}
SECTIONS['forcefield'] = {'description': None}
SECTIONS['potential'] = {'class': None,
                         'parameter': None}
SECTIONS['orderparameter'] = {'class': None,
                              'module': None}
SECTIONS['output'] = {'backup': False,
                      'directory': None,
                      'prefix': None,
                      'energy-file': 10,
                      'cross-file': 1,
                      'order-file': 10,
                      'pathensemble-file': 1,
                      'trajectory-file': 100,
                      'energy-screen': 10,
                      'write_vel': False}
SECTIONS['analysis'] = {'skipcross': 1000,
                        'maxblock': 1000,
                        'blockskip': 1,
                        'bins': 100,
                        'ngrid': 1001,
                        'maxordermsd': 100,
                        'plot': {'plotter': 'mpl', 'output': 'png',
                                 'style': 'pyretis'},
                        'txt-output': 'txt.gz',
                        'report': ['latex', 'rst', 'html'],
                        'report-dir': None}


SPECIAL_KEY = set(('parameter', ))
ALLOW_MULTIPLE = set(('potential', 'orderparameter', 'integrator'))


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


def look_for_keyword(line):
    """Function to look for a keyword in a string.

    A string is assumed to define a keyword if the keyword appears as
    the first word in the string, ending with a `=`.

    Parameters
    ----------
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
    raw_data = {'heading': []}
    current_line = None
    previous_line = None
    add_section = 'heading'
    data = []
    for lines in inputtxt:
        current_line, _, _ = lines.strip().partition('#')
        if not current_line:
            continue
        if current_line.startswith('---'):
            if previous_line is None:
                continue
            section_title = previous_line.split()[0].lower()
            if section_title == 'potential':
                if potentials < MAX_POT:
                    section_title = 'potential{:02d}'.format(potentials)
                    potentials += 1
                else:
                    logger.critical('If you are having potential-function'
                                    'problems if feel bad for you son. \n'
                                    "I got 99 problems but a pot ain't one")
            if section_title not in raw_data:
                raw_data[section_title] = []
            raw_data[add_section].extend(data[:-1])
            data = []
            add_section = section_title
        else:
            data += [current_line]
        previous_line = current_line
    if add_section is not None:
        raw_data[add_section].extend(data)
    return raw_data


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
    if section not in SECTIONS:
        msgtxt = 'Ignoring unknown input section "{}"'.format(section)
        logger.warning(msgtxt)
        # unknown section, just ignore silently
        return None
    if section == 'heading':
        if len(raw_section) == 0:
            return None
        else:
            return {'text': '\n'.join(raw_section)}
    merged = []
    # first we merge text that is split across line.
    # this is done by assuming that keyword separate settings
    for line in raw_section:
        _, _, found_keyword = look_for_keyword(line)
        if found_keyword or len(merged) == 0:
            merged.append(line)
        else:
            merged[-1] = ''.join((merged[-1], line))
    for line in merged:
        match, keyword, found_keyword = look_for_keyword(line)
        if found_keyword:
            raw = line[len(match):].strip()
            parsed, success = parse_primitive(raw)
            if success:
                if keyword in SPECIAL_KEY:
                    if keyword not in setting:
                        setting[keyword] = {}
                    var = line.split(keyword)[1].split()[0]
                    # yes, in some cases we really want an int
                    # this only work for positive numbers.
                    if var.isdigit():
                        setting[keyword][int(var)] = parsed
                    else:
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


def _parse_all_raw_sections(raw_sections):
    """Helper method to parse all raw sections.

    This method is helpfull for running tests etc.

    Parameters
    ----------
    raw_sections : dict
        The dictionary with the raw data in sections.

    Returns
    -------
    settings : dict
        The parsed settings, with one key for each section parsed.
    """
    settings = {}
    for key in sorted(raw_sections.keys()):
        if key.startswith('potential'):
            new_setting = _parse_raw_section(raw_sections[key], 'potential')
            if 'potential' not in settings:
                settings['potential'] = []
            settings['potential'].append(new_setting)
        else:
            new_setting = _parse_raw_section(raw_sections[key], key)
            if new_setting is None:
                continue
            settings[key] = {}
            for sub_key in new_setting:
                settings[key][sub_key] = new_setting[sub_key]
    return settings


def _add_default_settings(settings):
    """Add default settings.

    Paramters
    ---------
    settings : dict
        The current input settings.

    Returns
    -------
    None, but this method might add data to the input settings.
    """
    for sec in SECTIONS:
        if sec not in settings:
            settings[sec] = {}
        for key in SECTIONS[sec]:
            if SECTIONS[sec][key] is not None and key not in settings[sec]:
                settings[sec][key] = SECTIONS[sec][key]
    to_remove = [key for key in settings if len(settings[key]) == 0]
    for key in to_remove:
        settings.pop(key, None)


def _clean_settings(settings):
    """Clean up input settings.

    Here, we attempt to remove unwanted stuff from the input settings.

    Parameters
    ----------
    settings : dict
        The current input settings.

    Returns
    -------
    settingsc : dict
        The cleaned input settings.
    """
    settingc = {}
    # Add other sections
    for sec in settings:
        if sec not in SECTIONS:  # Well, ignore unknown ones
            msgtxt = 'Ignoring unknown section "{}"'.format(sec)
            logger.warning(msgtxt)
            continue
        if sec == 'potential':
            settingc[sec] = [i for i in settings[sec]]
        else:
            settingc[sec] = {}
            if sec in ALLOW_MULTIPLE:  # Here, just add them all
                for key in settings[sec]:
                    settingc[sec][key] = settings[sec][key]
            else:
                for key in settings[sec]:
                    if key not in SECTIONS[sec]:  # Ignore junk
                        msgtxt = 'Ignoring unknown "{}" in "{}"'.format(key,
                                                                        sec)
                        logger.warning(msgtxt)
                    else:
                        settingc[sec][key] = settings[sec][key]
    to_remove = [key for key in settingc if len(settingc[key]) == 0]
    for key in to_remove:
        settingc.pop(key, None)
    return settingc


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
    with open(filename, 'r') as fileh:
        raw_sections = _parse_sections(fileh)
    settings = _parse_all_raw_sections(raw_sections)
    if add_default:
        logger.debug('Adding default settings')
        _add_default_settings(settings)
    return _clean_settings(settings)


def settings_to_text(settings):
    """Turn settings into text usable for an output file.

    Parameters
    ----------
    settings : dict
        The dictionary to write

    Returns
    ------
    out : string
        Text represeting the settings.
    """
    txt = []
    for section in SECTIONS:
        if section not in settings:
            continue
        if section == 'potential':
            for pot in settings[section]:
                title = section.capitalize()
                line = ('-') * len(title)
                raw_data = section_to_text(pot)
                txt.append('{}\n{}\n{}\n\n'.format(title, line, raw_data))
        elif section == 'heading':
            txt.append('{}\n\n'.format(settings[section]['text']))
        else:
            title = '{} settings'.format(section.capitalize())
            line = ('-') * len(title)
            raw_data = section_to_text(settings[section])
            txt.append('{}\n{}\n{}\n\n'.format(title, line, raw_data))
    return ''.join(txt)


def section_to_text(settings, prefix=None):
    """Turn settings for a section into text for output.

    Parameters
    ----------
    settings : dict
        A dictionary with settings to transform.

    Returns
    -------
    out : string
        Formatted text representing the settings.
    """
    data = []
    for key in settings:
        if key == 'parameter':
            txt = section_to_text(settings[key], prefix='parameter')
        else:
            if prefix is not None:
                leng = len(str(key)) + 3 + len(prefix) + 1
            else:
                leng = len(str(key)) + 3
            pretty = pprint.pformat(settings[key], width=79-leng)
            pretty = pretty.replace('\n', '\n' + ' ' * leng)
            if prefix is not None:
                txt = '{} {} = {}'.format(prefix, key, pretty)
            else:
                txt = '{} = {}'.format(key, pretty)
        if len(txt) >= 5:  # Shortest is a = 1
            data.append(txt)
    return '\n'.join(data)


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
    if backup:
        msg = create_backup(outfile)
        if msg:
            logger.warning(msg)
    with open(outfile, 'w') as fileh:
        txt = settings_to_text(settings)
        fileh.write(txt)
