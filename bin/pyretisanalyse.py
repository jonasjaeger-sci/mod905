#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
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
from __future__ import print_function, absolute_import
import argparse
import logging
import os
import sys
# pyretis library imports:
from pyretis import __version__ as VERSION
from pyretis import __program_name__ as NAME
from pyretis import __url__ as URL
from pyretis import __cite__ as CITE
from pyretis.core.units import create_conversion_factors, CONSTANTS
from pyretis.inout.settings import parse_settings_file
from pyretis.inout.analysisio import run_analysis_files, report_results
from pyretis.inout.common import (check_python_version,
                                  LOG_FMT,
                                  make_dirs,
                                  print_to_screen,
                                  PyretisLogFormatter)


FILES = {'md-flux': {'cross': 'cross.dat',
                     'energy': 'energy.dat',
                     'order': 'order.dat'},
         'md-nve': {'energy': 'energy.dat'},
         'tis-single': {'pathensemble': 'pathensemble.dat'}}


def get_raw_files(sim_settings):
    """Return a list of files we can analyse."""
    raw_data = {}
    sim_task = sim_settings['task']
    ensemble_sim = sim_task in set(('tis-single', 'retis'))
    for file_type in FILES[sim_task]:
        filename = FILES[sim_task][file_type]
        if ensemble_sim:
            filename = os.path.join(sim_settings['output-dir'], filename)
        if os.path.isfile(filename):
            raw_data[file_type] = filename
    return raw_data


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
    msg = ['{} analysis version {} (Python version: {})'.format(NAME,
                                                                VERSION,
                                                                pyversion)]
    msg += ['Input file: {}'.format(infile)]
    msg += ['Report directory: {}'.format(reportdir)]
    for message in msg:
        logger.info(message)
        print_to_screen(message)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis."""
    msgtxt = 'End of {} analysis execution.'.format(NAME)
    logger.info(msgtxt)
    print_to_screen(msgtxt)
    # display some references:
    references = ['{} references:'.format(NAME)]
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
    parser = argparse.ArgumentParser(description=NAME)
    parser.add_argument('-i', '--input',
                        help=('Location of {} input file'.format(NAME)),
                        required=True)
    parser.add_argument('-V', '--version', action='version',
                        version='{} {}'.format(NAME, VERSION))
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
            errtxt = ('No simulation input file!'
                      ' "{}" is not a file!'.format(inputfile))
            raise ValueError(errtxt)
        print_to_screen('Reading input settings for analysis.')
        settings = parse_settings_file(inputfile)
        # override exe-path to the one we are executing in now:
        settings['exe-path'] = runpath
        create_conversion_factors(settings['units'], **settings['units-base'])
        # set derived properties:
        settings['beta'] = 1.0 / (settings['temperature'] *
                                  CONSTANTS['kB'][settings['units']])
        settings['report-dir'] = report_dir
        msg_dir = make_dirs(report_dir)
        print_to_screen(msg_dir)
        task = settings['task']
        print_to_screen('Will run analysis for task "{}"'.format(task))
        results = run_analysis_files(settings, get_raw_files(settings))
        for report in report_results(settings, results):
            print_to_screen('Created report: {}'.format(report))
        print_to_screen('Analysis done. Output created:')
        # Just write info about what we created:
        for files in results['txtfile']:
            print_to_screen('- {}'.format(os.path.basename(files)))
    except Exception as error:  # Exceptions should subclass BaseException.
        errtxt = '{}: {}'.format(type(error).__name__, error.args)
        print_to_screen(errtxt)
        print_to_screen('Execution failed! Will exit now.')
        raise
    finally:
        bye_bye_world()
