#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""pyretisanalysis - An application for analysing pyretis simulations

This script is a part of the pyretis library and can be used for
analysing the result from simulations.

usage: pyretisanalyse.py [-h] -i INPUT [-V]

pyretis

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Location of pyretis input file
  -V, --version         show program's version number and exit
"""
# pylint: disable=C0103
import argparse
import logging
import os
import sys
# pyretis library imports:
from pyretis import __version__ as VERSION
from pyretis.info import PROGRAM_NAME, URL, CITE
from pyretis.core.units import CONSTANTS
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.inout.analysisio.analysisio import run_analysis
from pyretis.inout.common import (check_python_version,
                                  LOG_FMT,
                                  make_dirs,
                                  name_file,
                                  print_to_screen,
                                  PyretisLogFormatter)
from pyretis.inout.report import generate_report
from pyretis.inout.settings import parse_settings_file, is_single_tis


# Hard-coded patters for report outputs:
REPORTFILES = {'md-flux': 'md_flux_report',
               'retis': 'retis_report',
               'tis': 'tis_report',
               'tis-single': 'tis_single_report'}


def get_report_name(report_type, ext, prefix=None, path=None):
    """Generate file name for a report.

    Parameters
    ----------
    report_type : string
        Identifier for the report we are writing.
    ext : string
        Extension for the file to write.
    prefix : string, optional
        A prefix to add to the file name. Usually just used
        to mark reports with ensemble number for `report_type` equal
        to 'tis-single'
    path : string
        A directory to use for saving the report to.

    Returns
    -------
    out : string
        The name of the file written.
    """
    name = REPORTFILES[report_type]
    if prefix is not None:
        name = '{}_{}'.format(prefix, name)
    return name_file(name, ext, path=path)


def write_file(outname, report_txt):
    """Write a generated report to a given file.

    Parameters
    ----------
    outname : string
        The name of the file to write/create.
    report_txt : string
        This is the generated report as a string.

    Returns
    -------
    out : string
        The name of the file written.
    """
    with open(outname, 'wt') as report_fh:
        try:  # will work in python 3
            report_fh.write(report_txt)
        except UnicodeEncodeError:  # for python 2
            report_fh.write(report_txt.encode('utf-8'))
    return outname


def create_reports(settings, analysis_results, report_path):
    """Create some reports to display the output.

    Parameters
    ----------
    settings : dict
        Settings for analysis (and the simulation).
    analysis_results : dict
        Results from the analysis.
    report_path : string
        Path to the directory where the reports should be saved.

    Yields
    ------
    out : string
        The reprot files created
    """
    if is_single_tis(settings):
        task = 'tis-single'
        pfix = PATH_DIR_FMT.format(settings['simulation']['ensemble'])
    else:
        task = settings['simulation']['task']
        pfix = None
    for report_type in settings['analysis']['report']:
        report, ext = generate_report(task, analysis_results,
                                      output=report_type)
        if report is not None:
            reportfile = get_report_name(task, ext, prefix=pfix,
                                         path=report_path)
            write_file(reportfile, report)
            yield reportfile


def hello_world(infile, reportdir):
    """Method to output a standard greeting for pyretis analysis.

    Parameters
    ----------
    infile : string
        String showing the location of the input file.
    reportdir : string
        String showing the location of where we write the output.
    """
    pyversion = sys.version.split()[0]
    msg = ['{} analysis version {} (Python version: {})'.format(PROGRAM_NAME,
                                                                VERSION,
                                                                pyversion)]
    msg += ['Input file: {}'.format(infile)]
    msg += ['Report directory: {}'.format(reportdir)]
    for message in msg:
        logger.info(message)
        print_to_screen(message)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis."""
    msgtxt = 'End of {} analysis execution.'.format(PROGRAM_NAME)
    logger.info(msgtxt)
    print_to_screen('')
    print_to_screen(msgtxt)
    # display some references:
    references = ['{} references:'.format(PROGRAM_NAME)]
    references.append(('-')*len(references[0]))
    for line in CITE.split('\n'):
        if line:
            references.append(line)
    reftxt = '\n'.join(references)
    logger.info(reftxt)
    print_to_screen('')
    print_to_screen(reftxt)
    urltxt = '{}'.format(URL)
    logger.info(urltxt)
    print_to_screen('')
    print_to_screen(urltxt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=PROGRAM_NAME)
    parser.add_argument('-i', '--input',
                        help=('Location of {} input file'.format(PROGRAM_NAME)),
                        required=True)
    parser.add_argument('-V', '--version', action='version',
                        version='{} {}'.format(PROGRAM_NAME, VERSION))
    args_dict = vars(parser.parse_args())

    inputfile = args_dict['input']
    runpath = os.getcwd()
    basepath = os.path.dirname(inputfile)
    localfile = os.path.basename(inputfile)
    if not os.path.isdir(basepath):
        basepath = os.getcwd()
    report_dir = os.path.join(runpath, 'report')
    # set up for logging:
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    # Define a console logger. This will log to sys.stderr:
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(PyretisLogFormatter(LOG_FMT))
    logger.addHandler(console)

    check_python_version()

    try:
        hello_world(inputfile, report_dir)
        if not os.path.isfile(inputfile):
            errtxt = ('Could not open input'
                      ' "{}"'.format(inputfile))
            raise ValueError(errtxt)
        settings = parse_settings_file(inputfile)
        # override exe-path to the one we are executing in now:
        settings['simulation']['exe-path'] = runpath
        #print(settings['unit-system'])
        units = settings['system']['units']
        #create_conversion_factors(settings['system']['units'],
        #                          **settings['unit-system'])
        # set derived properties:
        settings['system']['beta'] = (settings['system']['temperature'] *
                                      CONSTANTS['kB'][units])**-1
        settings['analysis']['report-dir'] = report_dir
        msg_dir = make_dirs(report_dir)
        print_to_screen(msg_dir)
        task = settings['simulation']['task']
        print_to_screen('Will run analysis for task "{}"'.format(task))
        results = run_analysis(settings)
        print_to_screen('')
        for outfile in create_reports(settings, results, report_dir):
            relfile = os.path.relpath(outfile, start=runpath)
            print_to_screen('Report created: {}'.format(relfile))
    except Exception as error:  # Exceptions should subclass BaseException.
        errtxt = '{}: {}'.format(type(error).__name__, error.args)
        print_to_screen(errtxt)
        print_to_screen('Execution failed! Will exit now.')
        raise
    finally:
        bye_bye_world()
