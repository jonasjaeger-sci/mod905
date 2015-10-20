# -*- coding: utf-8 -*-
"""This file contains common methods and functions for the input/output."""
from __future__ import absolute_import
import os


__all__ = ('create_backup')


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
_REPORTFILES = {'md-flux': os.extsep.join(['md_flux_report', '{}']),
                'tis': os.extsep.join(['tis_report', '{}'])}


def create_backup(outputfile):
    """
    Check if a file exist and create backup if requested.

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
    No warning is issued here. This is just in case the msg returned here
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
