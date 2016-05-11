#! /usr/bin/python
# -*- coding: utf-8 -*-
"""pyretis

This script is a part of the pyretis library and can be used for
running simulations from an input script.

Usage is:

pyretisrun -i inputfile.txt
"""
# pylint: disable=C0103
from __future__ import print_function, absolute_import
import argparse
import datetime
import logging
import os
import sys
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


DATEFORMAT = '%H:%M:%S %d.%m.%Y'


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


def hello_world(infile, basedir, logfile):
    """Method to print out a standard greeting for pyretis.

    Parameters
    ----------
    infile : string
        String showing the location of the input file.
    basedir : string
        String showing the location we are running in.
    logfile : string
        The output log file
    """
    timestart = datetime.datetime.now().strftime(DATEFORMAT)
    msg = ['# Running {} version {}'.format(NAME, VERSION)]
    msg += ['# Start of execution: {}'.format(timestart)]
    msg += ['# Running in directory: {}'.format(basedir)]
    msg += ['# Input file: {}'.format(infile)]
    msg += ['# Log file: {}'.format(logfile)]
    for message in msg:
        msgtxt = message.replace('# ', '').strip()
        logger.info(msgtxt)
    if sys.version_info < (3, 0):
        pyversion = sys.version.split()[0]
        warntxt = ('You are running Python {}!'
                   '\nPlease upgrade to Python 3.'
                   '\nPython 2.X support will be dropped in the near future!')
        warntxt = warntxt.format(pyversion)
        logger.warning(warntxt)
        if sys.version_info < (2.7):
            msgtxt = ('Your version of Python is NOT supported by {}!'
                      '\nPlease upgrade!')
            msgtxt = msgtxt.format(NAME)
            raise ValueError(msgtxt)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis."""
    timeend = datetime.datetime.now().strftime(DATEFORMAT)
    msg = ['# End of {} execution: {}'.format(NAME, timeend)]
    references = ['{} references:'.format(NAME)]
    for line in CITE.split('\n'):
        if line:
            references.append(' {}'.format(line))
    reftxt = ['\n'.join(references)]
    msg += reftxt
    msg += ['# Visit us at: {}'.format(URL)]
    for message in msg:
        msgtxt = message.replace('# ', '')
        logger.info(msgtxt)


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
    basepath = os.path.dirname(inputfile)
    localfile = os.path.basename(inputfile)
    if os.path.isdir(basepath):
        os.chdir(basepath)
    else:
        basepath = os.getcwd()
    # set up for logging:
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    # log to console:
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
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
        hello_world(localfile, basepath, args_dict['log'])
        if not os.path.isfile(inputfile):
            errtxt = ('No simulation input:'
                      ' {} is not a file!'.format(inputfile))
            raise ValueError(errtxt)

        logger.info('Reading input settings.')
        settings = parse_settings_file(localfile)
        create_conversion_factors(settings['units'], **settings['units-base'])

        logger.info('Creating system from settings.')
        system = create_system(settings)
        system.forcefield = create_force_field(settings)

        logger.info('Creating simulation from settings.')
        simulation = create_simulation(settings, system)

        logger.info('Creating output tasks from settings.')
        output_tasks = [task for task in create_output(settings)]

        logger.info('Running simulation.')
        for result in simulation.run():
            #stepno = result['cycle']['stepno']
            #result['thermo']['stepno'] = stepno
            for task in output_tasks:
                task.output(result)
    except Exception as error:
        logger.error(error.args[0])
        logger.error('Execution failed! Will exit now.')
        raise
    finally:
        bye_bye_world()
