#! /usr/bin/python
# -*- coding: utf-8 -*-
"""pyretis

This script is a part of the pyretis library and can be used for
running simulations from an input script.

Usage is:

run_pyretis -i inputfile.txt
"""
# pylint: disable=C0103
from __future__ import print_function, absolute_import
import argparse
import datetime
import logging
import os
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
    timestart = datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')
    msg = ['# Running {} version {}'.format(NAME, VERSION)]
    msg += ['# Start of execution: {}'.format(timestart)]
    msg += ['# Running in directory: {}'.format(basedir)]
    msg += ['# Input file: {}'.format(infile)]
    msg += ['# Log file: {}'.format(logfile)]
    printtxt = '\n'.join(msg)
    print(printtxt)
    logtxt = printtxt.replace('# ', '').strip()
    logger.info(logtxt)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis."""
    timeend = datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')
    msg = ['# End of {} execution: {}'.format(NAME, timeend)]
    txt = '# Please cite: {}'
    indent = len(txt) - 5
    for line in CITE.split('\n'):
        if line:
            txt = txt.format(line)
            msg.append(txt)
            txt = '# ' + ' ' * indent + ' {}'
    msg += ['# Visit us at: {}'.format(URL)]
    printtxt = '\n'.join(msg)
    print(printtxt)
    logtxt = printtxt.replace('# ', '').strip()
    logger.info(logtxt)


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
    if not os.path.isfile(inputfile):
        raise ValueError('{} is not a file'.format(inputfile))
    basepath = os.path.dirname(inputfile)
    localfile = os.path.basename(inputfile)
    os.chdir(basepath)

    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    fileh = logging.FileHandler(args_dict['log'], mode='w')
    fileh.setLevel(logging.DEBUG)
    formatter = MultiLineFormatter('[%(levelname)s]: %(message)s')
    formatter_file = MultiLineFormatter('[%(levelname)s]: %(message)s')
    console.setFormatter(formatter)
    fileh.setFormatter(formatter_file)
    logger.addHandler(fileh)
    logger.addHandler(console)

    hello_world(localfile, basepath, args_dict['log'])

    print('# Reading input settings.')
    settings = parse_settings_file(localfile)
    create_conversion_factors(settings['units'], **settings['units-base'])

    print('# Creating systems from settings.')
    system = create_system(settings)
    system.forcefield = create_force_field(settings)
    print('# Creating simulation from settings.')
    simulation = create_simulation(settings, system)
    print('# Creating output tasks from settings.')
    output_tasks = [task for task in create_output(settings)]

    print('# Running simulation.')
    logger.info('Running simulation')
    for result in simulation.run():
        #stepno = result['cycle']['stepno']
        #result['thermo']['stepno'] = stepno
        for task in output_tasks:
            task.output(result)
    bye_bye_world()
