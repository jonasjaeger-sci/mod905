# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This module handles parsing of input settings.

This module defines the file format for PyRETIS input files.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

parse_settings_file (:py:func:`.parse_settings_file`)
    Method for parsing settings from a given input file.

write_settings_file (:py:func:`.write_settings_file`)
    Method for writing settings from a simulation to a given file.
"""
import ast
import logging
import pprint
import re
from pyretis.inout.common import create_backup, create_empty_ensembles
from pyretis.info import PROGRAM_NAME, URL
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())

__all__ = ['parse_settings_file', 'write_settings_file',
           '_fill_up_tis_and_retis_settings']


SECTIONS = dict()
TITLE = '{} input settings'.format(PROGRAM_NAME)
HEADING = '{}\n{}\nFor more info, please see: {}\nHave Fun!'
SECTIONS['heading'] = {'text': HEADING.format(TITLE, '=' * len(TITLE), URL)}

SECTIONS['simulation'] = {
    'endcycle': None,
    'exe_path': None,
    'interfaces': None,
    'restart': None,
    'rgen': None,
    'startcycle': None,
    'steps': None,
    'task': 'md',
    'zero_left': None
}

SECTIONS['system'] = {
    'dimensions': 3,
    'temperature': 1.0,
    'units': 'lj',
}

SECTIONS['unit-system'] = {
    'charge': None,
    'energy': None,
    'length': None,
    'mass': None,
    'name': None,
}

SECTIONS['engine'] = {
    'class': None,
    'module': None,
}

SECTIONS['box'] = {
    'cell': None,
    'high': None,
    'low': None,
    'periodic': None,
}

SECTIONS['particles'] = {
    'mass': None,
    'name': None,
    'npart': None,
    'position': None,
    'type': None,
    'velocity': None,
}

SECTIONS['forcefield'] = {
    'description': None
}

SECTIONS['potential'] = {
    'class': None,
    'parameter': None
}

SECTIONS['orderparameter'] = {
    'class': None,
    'module': None,
    'name': 'Order Parameter'
}

SECTIONS['collective-variable'] = {
    'class': None,
    'module': None,
    'name': None
}

SECTIONS['output'] = {
    'backup': 'overwrite',
    'cross-file': 1,
    'energy-file': 1,
    'pathensemble-file': 1,
    'prefix': None,
    'order-file': 1,
    'restart-file': 10,
    'screen': 10,
    'trajectory-file': 100,
}

SECTIONS['tis'] = {
    'allowmaxlength': False,
    'aimless': True,
    'ensemble_number': None,
    'detect': None,
    'freq': None,
    'maxlength': None,
    'n_jumps': None,
    'high_accept': False,
    'interface_sour': None,
    'rescale_energy': False,
    'rgen': None,
    'seed': 0,
    'shooting_move': 'sh',
    'shooting_moves': [],
    'sigma_v': -1,
    'zero_momentum': False,
}

SECTIONS['initial-path'] = {
    'method': None
}

SECTIONS['retis'] = {
    'nullmoves': None,
    'relative_shoots': None,
    'rgen': None,
    'seed': None,
    'swapfreq': None,
    'swapsimul': None,
}

SECTIONS['ensemble'] = {
    'interface': None
}

SECTIONS['ensemble'] = {
    'interface': None
}

SECTIONS['analysis'] = {
    'blockskip': 1,
    'bins': 100,
    'maxblock': 1000,
    'maxordermsd': -1,
    'ngrid': 1001,
    'plot': {'plotter': 'mpl', 'output': 'png',
             'style': 'pyretis'},
    'report': ['latex', 'rst', 'html'],
    'report-dir': None,
    'skipcross': 1000,
    'txt-output': 'txt.gz',
}


SPECIAL_KEY = {'parameter'}

# This dictionary contains sections where the keywords
# can not be defined before we parse the input. The reason
# for this is that we support user-defined external modules
# and that the user should have the freedom to define keywords
# for these modules:
ALLOW_MULTIPLE = {
    'collective-variable',
    'engine',
    'ensemble',
    'initial-path',
    'orderparameter',
    'potential',
}

# This dictionary contains sections that can be defined
# multiple times. When parsing, these sections will be
# prefixed with a number to distinguish them.
SPECIAL_MULTIPLE = {
    'collective-variable',
    'ensemble',
    'potential',
}


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
        A dictionary with settings for PyRETIS.

    """
    with open(filename, 'r') as fileh:
        raw_sections = _parse_sections(fileh)
    settings = _parse_all_raw_sections(raw_sections)
    if add_default:
        logger.debug('Adding default settings')
        add_default_settings(settings)
    if settings['simulation']['task'] in {'retis'}:
        _fill_up_tis_and_retis_settings(settings)
    return _clean_settings(settings)


def parse_primitive(text):
    """Parse text to Python using the ast module.

    Parameters
    ----------
    text : string
        The text to parse.

    Returns
    -------
    out[0] : string, dict, list, boolean, or other type
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
    """Search for a keyword in the given string.

    A string is assumed to define a keyword if the keyword appears as
    the first word in the string, ending with a `=`.

    Parameters
    ----------
    line : string
        A string to check for a keyword.

    Returns
    -------
    out[0] : string
        The matched keyword. It may contain spaces and it will also
        contain the matched `=` separator.
    out[1] : string
        A lower-case, stripped version of `out[0]`.
    out[2] : boolean
        `True` if we found a possible keyword.

    """
    # Match a word followed by a '=':
    key = re.match(r'(.*?)=', line)
    if key:
        keyword = ''.join([key.group(1), '='])
        keyword_low = key.group(1).strip().lower()
        for i in SPECIAL_KEY:
            if keyword_low.startswith(i):
                return keyword, i, True

        # Here we assume that keys with len One or Two are Atoms names
        if len(keyword_low) <= 2:
            keyword_low = key.group(1).strip()

        return keyword, keyword_low, True
    return None, None, False


def _parse_sections(inputtxt):
    """Find sections in the input file with raw data.

    This method will find sections in the input file and
    collect the corresponding raw data.

    Parameters
    ----------
    inputtxt : list of strings or iterable file object
        The raw data to parse.

    Returns
    -------
    raw_data : dict
        A dictionary with keys corresponding to the sections found
        in the input file. `raw_data[key]` contains the raw data
        for the section corresponding to `key`.

    """
    multiple = {key: 0 for key in SPECIAL_MULTIPLE}
    raw_data = {'heading': []}
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
            if section_title in SPECIAL_MULTIPLE:
                new_section_title = '{}{}'.format(
                    section_title,
                    multiple[section_title]
                )
                multiple[section_title] += 1
                section_title = new_section_title
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


def _parse_section_heading(raw_section):
    """Parse the heading section.

    Parameters
    ----------
    raw_section : list of strings
        The text data for a given section which will be parsed.

    Returns
    -------
    setting : dict
        A dict with keys corresponding to the settings.

    """
    if not raw_section:
        return None
    return {'text': '\n'.join(raw_section)}


def _merge_section_text(raw_section):
    """Merge text for settings that are split across lines.

    This method supports keyword settings that are split across several
    lines. Here we merge these lines by assuming that keywords separate
    different settings.

    Parameters
    ----------
    raw_section : string
        The text we will merge.

    """
    merged = []
    for line in raw_section:
        _, _, found_keyword = look_for_keyword(line)
        if found_keyword or not merged:
            merged.append(line)
        else:
            merged[-1] = ''.join((merged[-1], line))
    return merged


def _parse_section_default(raw_section):
    """Parse a raw section.

    This is the default parser for sections.

    Parameters
    ----------
    raw_section : list of strings
        The text data for a given section which will be parsed.

    Returns
    -------
    setting : dict
        A dict with keys corresponding to the settings.

    """
    merged = _merge_section_text(raw_section)
    setting = {}
    for line in merged:
        match, keyword, found_keyword = look_for_keyword(line)
        if found_keyword:
            raw = line[len(match):].strip()
            parsed, success = parse_primitive(raw)
            if success:
                special = None
                for skey in SPECIAL_MULTIPLE:
                    # To avoid a false True for ensemble_number
                    if keyword.startswith(skey) and keyword[len(skey)] != '_':
                        special = skey

                if special is not None:
                    var = [''.join(line.split(keyword.split()[0])[1])]
                    new_setting = _parse_section_default(var)
                    var = line.split(special)[1].split()[0]
                    num = 0 if not var.isdigit() else int(var)

                    if special not in setting:
                        setting[special] = [{}]
                    while num >= len(setting[special]):
                        setting[special].append({})
                    setting[special][num].update(new_setting)

                elif keyword in SPECIAL_KEY:
                    if keyword not in setting:
                        setting[keyword] = {}
                    var = line.split(keyword)[1].split()[0]
                    # Yes, in some cases we really want an integer.
                    # Note: This will only work for positive numbers
                    # (which we are assuming here).
                    if var.isdigit():
                        setting[keyword][int(var)] = parsed
                    else:
                        setting[keyword][var] = parsed

                elif len(keyword.split()) > 1:
                    key_0 = match.split()[0]
                    var = [' '.join(line.split()[1:])]
                    new_setting = _parse_section_default(var)
                    if key_0 not in setting:
                        setting[key_0] = {}
                    for key in new_setting:
                        if key in setting[key_0]:
                            setting[key_0][key].update(new_setting[key])
                        else:
                            setting[key_0][key] = new_setting[key]

                else:
                    setting[keyword] = parsed

            else:  # pragma: no cover
                msg = ['Could read keyword {}'.format(keyword)]
                msg += ['Keyword was skipped, please check your input!']
                msg += ['Input setting: {}'.format(raw)]
                msgtxt = '\n'.join(msg)
                logger.critical(msgtxt)
    return setting


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
    out : dict
        A dict with keys corresponding to the settings.

    """
    if section not in SECTIONS:
        # Unknown section, just ignore it and give a warning.
        msgtxt = 'Ignoring unknown input section "{}"'.format(section)
        logger.warning(msgtxt)
        return None
    if section == 'heading':
        return _parse_section_heading(raw_section)
    return _parse_section_default(raw_section)


def _parse_all_raw_sections(raw_sections):
    """Parse all raw sections.

    This method is helpful for running tests etc.

    Parameters
    ----------
    raw_sections : dict
        The dictionary with the raw data in sections.

    Returns
    -------
    settings : dict
        The parsed settings, with one key for each section parsed.

    """
    settings = dict()
    for key, val in raw_sections.items():
        special = None
        for i in SPECIAL_MULTIPLE:
            if key.startswith(i):
                special = i
        if special is not None:
            new_setting = _parse_raw_section(val, special)
            if special not in settings:
                settings[special] = []
            settings[special].append(new_setting)
        else:
            new_setting = _parse_raw_section(val, key)
            if new_setting is None:
                continue
            if key not in settings:
                settings[key] = {}
            for sub_key in new_setting:
                settings[key][sub_key] = new_setting[sub_key]
    return settings


def _check_for_bullshitt(settings):
    """Do what is stated.

    Just for the input settings.

    Parameters
    ----------
    settings : dict
        The current input settings.

    """
    msg = [' ']
    success = True

    if (settings['simulation']['task'] in {'retis', 'tis'} and
            len(settings['simulation']['interfaces']) < 3):
        msg += ['Insufficient number of interfaces for {}'
                .format(settings['simulation']['task'])]
        success = False

    if settings['simulation']['task'] in {'tis', 'retis'}:
        if not is_sorted(settings['simulation']['interfaces']):
            msg += ['Interface lambda positions in the simulation '
                    'entry are NOT sorted (small to large)']
            success = False

        if 'ensemble' in settings:
            savelambda = []
            for i_ens, ens in enumerate(settings['ensemble']):
                if 'ensemble_number' not in ens and \
                        'interface' not in ens:
                    msg += ['An ensemble has been introduced without '
                            'references (interface in ensemble settings)']
                    success = False
                else:
                    savelambda.append(settings['simulation']['interfaces']
                                      [i_ens])
                    if 'interface' in ens and ens['interface'] \
                            not in settings['simulation']['interfaces']:
                        msg += ['An ensemble with declared interface '
                                'is not present in the simulation interface '
                                'list']
                        success = False

            # todo: finish this once the tis and retis
            # interface re-numbering is completed.
            # for i_ens, ens in enumerate(settings['ensemble']):
            #    if {'interface', 'ensemble_number'} <= set(ens):
            #        msg += ['interface and ensemble_number for ']
            #        msg += ['ensemble {}'.format(i_ens)]
            #        msg += ['are inconsistent']
            #        success = False

    if not success:
        msgtxt = '\n'.join(msg)
        logger.critical(msgtxt)
        raise ValueError(msgtxt)


def _fill_up_tis_and_retis_settings(settings):
    """Make the life of sloppy users easier.

    The full input set-up will be here completed.

    Parameters
    ----------
    settings : dict
        The current input settings.

    Returns
    -------
    None, but this method might add data to the input settings.

    """
    create_empty_ensembles(settings)
    ensemble_save = settings['ensemble'].copy()

    # The previously constructed dictionary is inserted in the settings.
    # This is done such that the specific input given per ensemble
    # OVERWRITES the general input.
    for i_ens, ens in enumerate(ensemble_save):
        for key in settings:
            if key in ensemble_save[i_ens]:
                if key not in SPECIAL_MULTIPLE:
                    ensemble_save[i_ens][key] =\
                        {**settings[key].copy(),
                         **ensemble_save[i_ens][key].copy()}
                else:
                    for i_sub, sub in enumerate(settings[key]):
                        while len(ensemble_save[i_ens][key])\
                                < len(settings[key]):
                            ensemble_save[i_ens][key].append({})
                        ensemble_save[i_ens][key][i_sub] = {
                            **sub.copy(),
                            **ensemble_save[i_ens][key][i_sub].copy()
                            }

        ensemble_save[i_ens] = {**copy_settings(settings),
                                **ensemble_save[i_ens].copy()}
        del ensemble_save[i_ens]['ensemble']

    for i_ens, ens in enumerate(ensemble_save):
        settings['ensemble'][i_ens] = ensemble_save[i_ens].copy()


def add_default_settings(settings):
    """Add default settings.

    Parameters
    ----------
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
    # Add other sections:
    for sec in settings:
        if sec not in SECTIONS:  # Well, ignore unknown ones:
            msgtxt = 'Ignoring unknown section "{}"'.format(sec)
            logger.warning(msgtxt)
            continue
        if sec in SPECIAL_MULTIPLE:
            settingc[sec] = [i for i in settings[sec]]
        else:
            settingc[sec] = {}
            if sec in ALLOW_MULTIPLE:  # Here, just add multiple sections:
                for key in settings[sec]:
                    settingc[sec][key] = settings[sec][key]
            else:
                for key in settings[sec]:
                    if key not in SECTIONS[sec]:  # Ignore junk:
                        msgtxt = 'Ignoring unknown "{}" in "{}"'.format(key,
                                                                        sec)
                        logger.warning(msgtxt)
                    else:
                        settingc[sec][key] = settings[sec][key]
    to_remove = [key for key in settingc if len(settingc[key]) == 0]
    for key in to_remove:
        settingc.pop(key, None)
    return settingc


def settings_to_text(settings):
    """Turn settings into text usable for an output file.

    Parameters
    ----------
    settings : dict
        The dictionary to write

    Returns
    ------
    out : string
        Text representing the settings.

    """
    txt = []
    for section in SECTIONS:
        if section not in settings:
            continue
        if section in SPECIAL_MULTIPLE:
            for sec in settings[section]:
                title = section.capitalize()
                line = '-' * len(title)
                if section == 'ensemble':
                    _, raw_data = multiple_section_to_text(sec,
                                                           prefix=None,
                                                           pure=True)
                else:
                    raw_data = section_to_text(sec)
                txt.append('{}\n{}\n{}\n\n'.format(title, line, raw_data))
        elif section == 'heading':
            txt.append('{}\n\n'.format(settings[section]['text']))
        else:
            if section in ('tis', 'retis'):
                title = '{} settings'.format(section.upper())
            else:
                title = '{} settings'.format(section.capitalize())
            line = '-' * len(title)
            raw_data = section_to_text(settings[section])
            txt.append('{}\n{}\n{}\n\n'.format(title, line, raw_data))
    return ''.join(txt)


def double_section_to_text(settings):
    """Just here to not break 2.0 API, will be removed in Pyretis3."""
    return(multiple_section_to_text(settings)[1])


def multiple_section_to_text(settings, prefix=None, pure=False):
    """Turn settings for the ensemble into text for output.

    Parameters
    ----------
    settings : dict
        A dictionary with settings to transform.
    prefix : string, optional
        If this string is given, it will be prepended to
        the setting we are writing.
    pure: boolean, optional
        The flag is used to track if subroutine works on a
        main section (True) or in a sub section (False).
        In the first case, prefix has to be re-set.

    Returns
    -------
    out[0] : string
        Formatted text representing the prefix to use in
        a recursive key-word search.
    out[1] : string
        Formatted text representing the settings.

    """
    data = []
    for key in settings:
        prefix = None if pure else prefix
        if key in SPECIAL_MULTIPLE:
            for i, entry in enumerate(settings[key]):
                temp_prefix = '{}{:d}'.format(key, i)
                _, txt = multiple_section_to_text(entry,
                                                  prefix=temp_prefix)
                data.append(txt)

        elif key == 'interface':
            pretty = pprint.pformat(settings[key], width=67)
            pretty = pretty.replace('\n', '\n' + ' ' * 67)
            txt = '{} = {}'.format(key, pretty)
            data.append(txt)

        elif key == 'heading':
            txt = '{} = {}'.format(key, settings[key])
            data.append(txt)

        elif isinstance(settings[key], dict):
            base = prefix
            if prefix is None:
                prefix = key
            else:
                base = prefix
                prefix += ' ' + key
            _, txt = multiple_section_to_text(settings[key], prefix=prefix)
            prefix = base
            data.append(txt)

        else:
            txt = '{} {} = {}'.format(prefix, key, settings[key])
            data.append(txt)

    return prefix, '\n'.join(data)


def section_to_text(settings, prefix=None):
    """Turn settings for a section into text for output.

    Parameters
    ----------
    settings : dict
        A dictionary with settings to transform.
    prefix : string, optional
        If this string is given, it will be prepended to
        the setting we are writing.

    Returns
    -------
    out : string
        Formatted text representing the settings.

    """
    data = []
    for key in settings:
        if key == 'parameter':
            if prefix is not None:
                txt = section_to_text(settings[key], prefix=prefix+' '+key)
            else:
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
        if len(txt) >= 5:  # Shortest text, e.g: "a = 1".
            data.append(txt)
    return '\n'.join(data)


def write_settings_file(settings, outfile, backup=True):
    """Write simulation settings to an output file.

    This will write a dictionary to an output file in the PyRETIS input
    file format.

    Parameters
    ----------
    settings : dict
        The dictionary to write.
    outfile : string
        The file to create.
    backup : boolean, optional
        If True, we will backup existing files with the same file
        name as the provided file name.

    Note
    ----
    This will currently fail if objects have made it into the supplied
    ``settings``.

    """
    if backup:
        msg = create_backup(outfile)
        if msg:
            logger.info(msg)
    with open(outfile, 'w') as fileh:
        txt = settings_to_text(settings)
        fileh.write(txt.strip())


def copy_settings(settings):
    """Return a copy of the given settings.

    Parameters
    ----------
    settings : dict of dicts
        A dictionary which we will return a copy of.

    Returns
    -------
    lsetting : dict of dicts
        A copy of the settings.

    """
    lsetting = {}
    for sec in settings:  # this is common for all simulations:
        lsetting[sec] = {}
        if sec in SPECIAL_MULTIPLE:
            lsetting[sec] = [j for j in settings[sec]]
        else:
            for key in settings[sec]:
                lsetting[sec][key] = settings[sec][key]
    return lsetting


def is_sorted(lll):
    """Check if a list is sorted."""
    return all(aaa <= bbb for aaa, bbb in zip(lll[:-1], lll[1:]))
