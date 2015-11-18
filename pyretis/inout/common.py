# -*- coding: utf-8 -*-
"""This file contains common methods and functions for the input/output.

It contains some functions that is used when generating reports, typically
to format tables and numbers.

Important functions defined here:

- create_backup: A method to handle the creation of backups of old files.

- apply_format: Apply a format string to a given value.

- remove_extensions: Remove extensions for a list of files.

- make_dirs: Create directories (for path simulation).
"""
from __future__ import absolute_import
import errno
import os
import re
import warnings

__all__ = ['create_backup', 'apply_format', 'remove_extensions',
           'make_dirs']


# Hard-coded patters for energy analysis output files.
# These are just used to make it simpler to change these default
# names in the future.
_ENERFILES = {'energies': 'energies',
              'run_energies': 'runenergies',
              'temperature': 'temperature',
              'run_temp': 'runtemperature',
              'block': '{}block',
              'dist': '{}dist'}
# hard-coded information for the energy terms:
_ENERTITLE = {'vpot': 'Potential energy',
              'ekin': 'Kinetic energy',
              'etot': 'Total energy',
              'ham': 'Hamilt. energy',
              'temp': 'Temperature',
              'elec': 'Energy (externally computed)'}
# hard-coded patters for flux analysis output files:
_FLUXFILES = {'runflux': 'runflux_{}',
              'block': 'errflux_{}'}
# order files:
_ORDERFILES = {'order': 'orderp',
               'ordervel': 'orderpv',
               'run_order': 'runorderp',
               'dist': 'orderdist',
               'block': 'ordererror',
               'msd': 'ordermsd'}
# hard-coded patters for path analysis output files:
_PATHFILES = {'pcross': '{}_pcross',
              'prun': '{}_prun',
              'perror': '{}_perror',
              'pathlength': '{}_lpath',
              'shoots': '{}_shoots',
              'shoots-scaled': '{}_shoots_scale'}
# hard-coded patterns for matched files:
_PATH_MATCH = {'total': 'total-probability',
               'match': 'matched-probability'}
# hard-coded patters for report outputs:
_REPORTFILES = {'mdflux': os.extsep.join(['md_flux_report', '{}']),
                'tis': os.extsep.join(['tis_report', '{}']),
                'tis_path': os.extsep.join(['tis_path_report', '{}'])}


def create_backup(outputfile):
    """Check if a file exist and create backup if requested.

    This method will check if the given filename exist and if it
    does, it will move that file to a new filename such that the given
    one can be used without overwriting.

    Parameters
    ----------
    outputfile : string
        This is the name of the file we wish to create.

    Returns
    -------
    out : string
        This string is None if no backup is made, otherwise it will just
        say what file was moved (and to where).

    Note
    ----
    No warning is issued here. This is just in case the `msg` returned here
    will be part of some more elaborate message.
    """
    filename = '{}'.format(outputfile)
    fileid = 0
    msg = None
    while os.path.isfile(filename) or os.path.isdir(filename):
        filename = '{}_{}'.format(outputfile, fileid)
        fileid += 1
    if fileid > 0:
        msg = 'Backup existing file {} to {}'.format(outputfile, filename)
        os.rename(outputfile, filename)
    return msg


def apply_format(value, fmt):
    """Apply a format string to a given value.

    Here we check the formatting of a float. We are *forcing* a
    *maximum length* on the resulting string. This is to avoid problems
    like: '{:7.2f}'.format(12345.7) which returns '12345.70' with a length
    8 > 7. The indended use of this method is to avoid shuch problems when we
    are formatting numbers for tables. Here it is done by switching to an
    exponential notation. But note however that this will have implications
    for how many decimal places we can show.

    Parameters
    ----------
    value : float
        The float to format.
    fmt : string
        The format to use.

    Note
    ----
    This method converts numbers to have a fixed length. In some cases this
    may reduce the number of significant digits. Remember to also output your
    numbers without this format in case a specific number of significant
    digits is important!
    """
    maxlen = fmt.split(':')[1].split('.')[0]
    align = ''
    if not maxlen[0].isalnum():
        align = maxlen[0]
        maxlen = maxlen[1:]
    maxlen = int(maxlen)
    str_fmt = fmt.format(value)
    if len(str_fmt) > maxlen:  # switch to exponential:
        if value < 0:
            deci = maxlen - 7
        else:
            deci = maxlen - 6
        new_fmt = '{{:{0}{1}.{2}e}}'.format(align, maxlen, deci)
        return new_fmt.format(value)
    else:
        return str_fmt


def _remove_extension(filename):
    """Remove the extension of a given filename.

    Parameters
    ----------
    filename : string
        The filename to check.

    Returns
    -------
    out : string
        The filename with the extension removed.
    """
    try:
        return os.path.splitext(filename)[0]
    except IndexError:
        return filename


def remove_extensions(list_of_files):
    """Remove extensions for a list of files.

    This will strip out extensions for all the files in a given iterable.
    Here, the iterable might be a simple list which contains dictionaries or
    it can be a dictionary. How we to the loop will depend on this.

    Parameters
    ----------
    list_of_files : list or dict, iterable
        This is the list for which we will try to remove extensions.

    Returns
    -------
    newlist : list or dict
        A copy of list_of_files, where the extensions has been removed.

    Note
    ----
    If, for some reason, list_of_files is a list and the items are just
    integers, the TypeError will not be raised. This is pretty unlikely and
    we therefor do not check for this.
    """
    # we assume that list_of_files is a simple dict
    try:
        newlist = {}
        for key in list_of_files:
            newlist[key] = _remove_extension(list_of_files[key])
        return newlist
    except TypeError:
        newlist = []
        for fig in list_of_files:
            newfig = {key: _remove_extension(fig[key]) for key in fig}
            newlist.append(newfig)
        return newlist


def make_dirs(dirname):
    """Create directories for path simulations.

    This method will create a folder using a specified path.
    If the path already exist and if it's a directory, we will do nothing.
    If the path exist and is a file we will raise an `OSError` exception here.

    Parameters
    ----------
    dirname : string
        This is the directory to create.

    Returns
    -------
    out : string
        A string with some info on what this method did. Intended for output.
    """
    try:
        os.makedirs(dirname)
        msg = 'Created directory: "{}"'.format(dirname)
        return msg
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise err
        if os.path.isfile(dirname):
            msg = '"{}" is a file. Will abort!'
            raise OSError(errno.EEXIST, msg, dirname)
        if os.path.isdir(dirname):
            msg = 'Directory "{}" exist. Will re-use it!'.format(dirname)
            return msg


def simplify_ensemble_name(ensemble, fmt='{:03d}'):
    """A method to simplify path names for file/directory names.

    Here, we are basically translating ensemble names to more friendly names
    for directories and files that is:

    - ``[0^-]`` returns ``000``,
    - ``[0^+]`` returns ``001``,
    - ``[1^+]`` returns ``002``, etc.

    Parameters
    ----------
    ensemble : string
        This is the string to translate
    fmt : string. optional
        This is a format to use for the directories.
    """
    match_ensemble = re.search(r'(?<=\[)(\d+)(?=\^)', ensemble)
    if match_ensemble:
        ens = int(match_ensemble.group())
    else:
        match_ensemble = re.search(r'(?<=\[)(\d+)(?=\])', ensemble)
        if match_ensemble:
            ens = int(match_ensemble.group())
        else:
            return ensemble  # assume that the ensemble is ok as it is.
    match_dir = re.search(r'(?<=\^)(.)(?=\])', ensemble)
    if match_dir:
        dire = match_dir.group()
        if dire == '-':
            ens = ens
        else:
            ens = ens + 1
    else:
        msg = ('Could not get direction for ensemble {}.'.format(ensemble),
               'We assume +, note that this might overwrite files')
        warnings.warn('\n'.join(msg))
        ens = ens + 1
    return fmt.format(ens)
