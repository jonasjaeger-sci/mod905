# -*- coding: utf-8 -*-
"""This file contains common methods and functions for the input/output.

It contains some functions that is used when generating reports, typically
to format tables and numbers.

Important functions defined here:

- create_backup: A method to handle the creation of backups of old files.

- apply_format: Apply a format string to a given value.

- remove_extensions: Remove extensions for a list of files.
"""
from __future__ import absolute_import
import os


__all__ = ['create_backup', 'apply_format', 'remove_extensions']


# hard-coded patters for energy analysis output files:
_ENERFILES = {'energies': os.extsep.join(['energies', '{}']),
              'run_energies': os.extsep.join(['runenergies', '{}']),
              'temperature': os.extsep.join(['temperature', '{}']),
              'run_temp': os.extsep.join(['runtemperature', '{}']),
              'block': os.extsep.join(['{}block', '{}']),
              'dist': os.extsep.join(['{}dist', '{}'])}
# hard-coded information for the energy terms:
_ENERTITLE = {'vpot': 'Potential energy',
              'ekin': 'Kinetic energy',
              'etot': 'Total energy',
              'ham': 'Hamilt. energy',
              'temp': 'Temperature',
              'elec': 'Energy (externally computed)'}
# hard-coded patters for flux analysis output files:
_FLUXFILES = {'runflux': os.extsep.join(['runflux_{}', '{}']),
              'block': os.extsep.join(['errflux_{}', '{}'])}
# order files:
_ORDERFILES = {'order': os.extsep.join(['orderp', '{}']),
               'ordervel': os.extsep.join(['orderpv', '{}']),
               'run_order': os.extsep.join(['runorderp', '{}']),
               'dist': os.extsep.join(['orderdist', '{}']),
               'block': os.extsep.join(['ordererror', '{}']),
               'msd': os.extsep.join(['ordermsd', '{}'])}
# hard-coded patters for path analysis output files:
_PATHFILES = {'pcross': os.extsep.join(['{}_pcross', '{}']),
              'prun': os.extsep.join(['{}_prun', '{}']),
              'perror': os.extsep.join(['{}_perror', '{}']),
              'pathlength': os.extsep.join(['{}_lpath', '{}']),
              'shoots': os.extsep.join(['{}_shoots', '{}']),
              'shoots-scaled': os.extsep.join(['{}_shoots_scale', '{}'])}
# hard-coded patterns for matched files:
_PATH_MATCH = {'total': os.extsep.join(['total-probability', '{}']),
               'match': os.extsep.join(['matched-probability', '{}'])}
# hard-coded patters for report outputs:
_REPORTFILES = {'mdflux': os.extsep.join(['md_flux_report', '{}']),
                'tis': os.extsep.join(['tis_report', '{}'])}


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
