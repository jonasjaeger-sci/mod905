#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""pyretis

This script is a part of the pyretis library and can be used for
running simulations from an input script.

Typical usage is:

pyretisrun -i inputfile.txt
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
from pyretis.inout.settings import parse_settings_file
from pyretis.inout.settings import (create_system, create_force_field,
                                    create_simulation)
from pyretis.inout import create_output


DATEFORMAT = '%d.%m.%Y %H:%M:%S'
USE_TQDM = True


def print_to_screen(txt):
    """Method to print output to standard out.

    This method is included to mirror the `MultiLineFormatter` used
    for the logging. The reason for not using just the console output
    is since we just want the console output to report on errors and
    possible problems (warnings etc.)

    Parameters
    ----------
    txt : string
        The text to write to the screen
    """
    out = '# {}'.format(txt)
    out = out.replace('\n', '\n# ')
    print(out)


class MultiLineFormatter(logging.Formatter):
    """Hardcoded formatter for pyretis log file."""
    def format(self, record):
        out = logging.Formatter.format(self, record)
        shortname = record.name.split('.')[-1]
        out = out.replace(record.name, shortname)
        header, _ = out.split(record.message)
        out = out.replace('\n', '\n' + ' ' * len(header))
        return out


class MultiLineFormatterDebug(logging.Formatter):
    """Hardcoded formatter for pyretis log.

    This formatter is intended for usage when more debugging
    information is needed with a format for logging as:

    `'%(name)s: [%(levelname)s]: %(message)s'`

    so that information about modules will be printed out as well.
    """
    def format(self, record):
        out = logging.Formatter.format(self, record)
        header, _ = out.split(record.message)
        out = out.replace('\n', '\n' + ' ' * len(header))
        return out


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
    timestart = datetime.datetime.now().strftime(DATEFORMAT)
    pyversion = sys.version.split()[0]
    msg = ['{}'.format(timestart)]
    msg += ['{} version {} (Python version: {})'.format(NAME, VERSION,
                                                        pyversion)]
    for message in msg:
        logger.info(message)
        print_to_screen(message)
    if sys.version_info < (3, 0):
        warntxt = ('Please upgrade to Python 3.'
                   '\nPython 2.X support will be dropped in the near future!')
        warntxt = warntxt.format(pyversion)
        logger.warning(warntxt)
        if sys.version_info < (2.7):
            msgtxt = ('Your version of Python is NOT supported by {}!'
                      '\nPlease upgrade!')
            msgtxt = msgtxt.format(NAME)
            raise ValueError(msgtxt)
    msg = ['Running in directory: {}'.format(rundir)]
    msg += ['Input file: {}'.format(infile)]
    msg += ['Log file: {}'.format(logfile)]
    for message in msg:
        logger.info(message)
        print_to_screen(message)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis."""
    timeend = datetime.datetime.now().strftime(DATEFORMAT)
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
    parser.add_argument('-l', '--log',
                        help='Specify log to write',
                        required=False,
                        default='{}.log'.format(NAME.lower()))
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
    # log to screen:
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    formatter = MultiLineFormatter('[%(levelname)s]: %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)
    # log to a file:
    fileh = logging.FileHandler(args_dict['log'], mode='w')
    fileh.setLevel(logging.DEBUG)
    formatter_file = MultiLineFormatter('[%(levelname)s]: %(message)s')
    fileh.setFormatter(formatter_file)
    logger.addHandler(fileh)

    try:
        hello_world(inputfile, basepath, args_dict['log'])
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
        if USE_TQDM:
            for result in tqdm(simulation.run(), total=settings['steps']):
                #for result in simulation.run():
                    #stepno = result['cycle']['stepno']
                    #result['thermo']['stepno'] = stepno
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
        print_to_screen(79*('-'))
        bye_bye_world()
