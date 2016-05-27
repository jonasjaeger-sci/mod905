#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""pyretisrun - An application for running pyretis simulations

This script is a part of the pyretis library and can be used for
running simulations from an input script.

usage: pyretisrun.py [-h] -i INPUT [-V] [-f LOG_FILE] [-l LOG_LEVEL] [-p]

pyretis

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Location of pyretis input file
  -V, --version         show program's version number and exit
  -f LOG_FILE, --log_file LOG_FILE
                        Specify log file to write
  -l LOG_LEVEL, --log_level LOG_LEVEL
                        Specify log level for log file
  -p, --progress        Display a progress meter instead of text output for
                        the simulation
"""
# pylint: disable=C0103
from __future__ import print_function, absolute_import
import argparse
import datetime
import logging
import os
import sys
# Other libraries:
from tqdm import tqdm  # for a nice progress bar
# pyretis library imports:
from pyretis import __version__ as VERSION
from pyretis import __program_name__ as NAME
from pyretis import __url__ as URL
from pyretis import __cite__ as CITE
from pyretis.core.units import create_conversion_factors
from pyretis.inout import create_output
from pyretis.inout.common import (check_python_version,
                                  LOG_DEBUG_FMT,
                                  LOG_FMT,
                                  print_to_screen,
                                  PyretisLogFormatter,
                                  PyretisLogFormatterDebug)
from pyretis.inout.settings import (parse_settings_file,
                                    write_settings_file,
                                    create_system,
                                    create_force_field,
                                    create_simulation)


DATE_FMT = '%d.%m.%Y %H:%M:%S'


def get_formatter(level):
    """Helper function to select a log format.

    Parameters
    ----------
    level : integer
        This integer defines the log level.

    Returns
    -------
    out : object like ``logging.Formatter``
        An object that can be used as a formatter for a logger.
    """
    if level <= logging.DEBUG:
        return PyretisLogFormatterDebug(LOG_DEBUG_FMT)
    else:
        return PyretisLogFormatter(LOG_FMT)


def hello_world(infile, rundir, logfile):
    """Method to print out a standard greeting for pyretis.

    Parameters
    ----------
    infile : string
        String showing the location of the input file.
    rundir : string
        String showing the location we are running in.
    logfile : string
        The output log file
    """
    timestart = datetime.datetime.now().strftime(DATE_FMT)
    pyversion = sys.version.split()[0]
    msg = ['{}'.format(timestart)]
    msg += ['{} version {} (Python version: {})'.format(NAME, VERSION,
                                                        pyversion)]
    msg += ['Running in directory: {}'.format(rundir)]
    msg += ['Input file: {}'.format(infile)]
    msg += ['Log file: {}'.format(logfile)]
    for message in msg:
        logger.info(message)
        print_to_screen(message)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis."""
    timeend = datetime.datetime.now().strftime(DATE_FMT)
    msgtxt = 'End of {} execution: {}'.format(NAME, timeend)
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
                        help='Location of {} input file'.format(NAME),
                        required=True)
    parser.add_argument('-V', '--version', action='version',
                        version='{} {}'.format(NAME, VERSION))
    parser.add_argument('-f', '--log_file',
                        help='Specify log file to write',
                        required=False,
                        default='{}.log'.format(NAME.lower()))
    parser.add_argument('-l', '--log_level',
                        help='Specify log level for log file',
                        required=False,
                        default='INFO')
    parser.add_argument('-p', '--progress', action='store_true',
                        help=('Display a progress meter instead of text '
                              'output for the simulation'))
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
    # Define a file logger:
    fileh = logging.FileHandler(args_dict['log_file'], mode='w')
    log_level = getattr(logging, args_dict['log_level'].upper(),
                        logging.INFO)
    fileh.setLevel(log_level)
    fileh.setFormatter(get_formatter(log_level))
    logger.addHandler(fileh)

    check_python_version()

    simulation = None
    system = None

    try:
        hello_world(inputfile, basepath, args_dict['log_file'])
        if not os.path.isfile(inputfile):
            errtxt = ('No simulation input:'
                      ' {} is not a file!'.format(inputfile))
            raise ValueError(errtxt)
        logger.info('Reading input settings.')
        print_to_screen('Reading input settings.')
        settings = parse_settings_file(inputfile)
        # Add to exe-path:
        settings['exe-path'] = runpath
        create_conversion_factors(settings['units'], **settings['units-base'])

        print_to_screen('Creating system from settings.')
        system = create_system(settings)
        system.forcefield = create_force_field(settings)

        print_to_screen('Creating simulation from settings.')
        simulation = create_simulation(settings, system)

        print_to_screen('Creating output tasks from settings.')
        output_tasks = [task for task in create_output(settings)]

        logger.info('Running simulation.')
        print_to_screen('Running simulation!')
        print_to_screen(79*('-'))
        if args_dict['progress']:
            for result in tqdm(simulation.run(), total=settings['steps']):
                for task in output_tasks:
                    if task.target != 'screen':
                        task.output(result)
        else:
            for result in simulation.run():
                for task in output_tasks:
                    task.output(result)
    except Exception as error:  # Exceptions should subclass BaseException.
        logger.error(error)
        logger.error('Execution failed! Will exit now.')
        print_to_screen(error)
        print_to_screen('Execution failed! Will exit now.')
        raise
    finally:
        # write out the simulation settings and add some extra ones:
        if simulation is not None:
            cycle = getattr(simulation, 'cycle', {'step': None})
            settings['endcycle'] = cycle['step']
        if system is not None:
            settings['npart'] = system.particles.npart
        settings_out = os.path.join(basepath, 'settings_out.rst')
        logger.info('Writing simulation settings.')
        write_settings_file(settings, settings_out, backup=False)
        print_to_screen(79*('-'))
        bye_bye_world()
