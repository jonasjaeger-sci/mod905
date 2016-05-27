#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""pyretis -- analysis program

This script is a part of the pyretis library and can be used for
analysing the result from simulations.

Typical usage is:

pyretisanalyse.py -i inputfile.txt
"""
# pylint: disable=C0103
from __future__ import print_function, absolute_import
import argparse
import logging
import os
# pyretis library imports:
from pyretis import __version__ as VERSION
from pyretis import __program_name__ as NAME
from pyretis import __url__ as URL
from pyretis import __cite__ as CITE
from pyretis.core.units import create_conversion_factors, CONSTANTS
from pyretis.inout.settings import parse_settings_file
from pyretis.inout.analysisio import run_md_flux_analysis
from pyretis.inout.common import (check_python_version,
                                  LOG_FMT,
                                  make_dirs,
                                  print_to_screen,
                                  PyretisLogFormatter)


RAW_DATA = {'md-flux': {'files': {'cross': 'cross.dat',
                                  'energy': 'energy.dat',
                                  'order': 'order.dat'}}}
ANALYSIS = {'md-flux': run_md_flux_analysis}


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
        output_dir = os.path.join(runpath, 'report')
        msg_dir = make_dirs(output_dir)
        print_to_screen(msg_dir)
        task = settings['task']
        print_to_screen('Will run analysis for task "{}"'.format(task))
        analysis = ANALYSIS[task]
        analysis(settings, RAW_DATA[task])
    except Exception as error:  # Exceptions should subclass BaseException.
        errtxt = '{}: {}'.format(type(error).__name__, error.args)
        print_to_screen(errtxt)
        print_to_screen('Execution failed! Will exit now.')
        raise
    finally:
        print_to_screen(79*('-'))
        #bye_bye_world()
