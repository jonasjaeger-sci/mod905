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


def hello_word(version, infile, basedir):
    """Method to print out a standard greeting for pyretis.

    Parameters
    ----------
    version : string
        The version number of pyretis being used.
    inputfile : string
        String showing the location of the input file.
    basedir : string
        String showing the location we are running in.
    """
    timestart = datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')
    msg = ['This is pyretis version {}'.format(version)]
    msg += ['Start of pyretis execution: {}'.format(timestart)]
    msg += ['Input file: {}'.format(infile)]
    msg += ['Running in directory: {}'.format(basedir)]
    msg += ['Please cite: [1] A. A., B. B., C. C, Some Journal, 99, pp. 100']
    msgtxt = '\n'.join(msg)
    print(msgtxt)
    logger.info(msgtxt)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis.

    Parameters
    ----------
    version : string
        String with the version number of pyretis.
    """
    timeend = datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')
    msg = ['End of pyretis execution: {}'.format(timeend)]
    msg += ['http://www.pyretis.org']
    msgtxt = '\n'.join(msg)
    print(msgtxt)
    logger.info(msgtxt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pyretis')
    parser.add_argument('-i', '--input', help='pyretis input file)',
                        required=True)
    parser.add_argument('-v', '--version', action='version',
                        version='{} {}'.format(NAME, VERSION))
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
    fileh = logging.FileHandler('pyretis.log', mode='w')
    fileh.setLevel(logging.DEBUG)
    formatter = MultiLineFormatter('[%(levelname)s]: %(message)s')
    formatter_file = MultiLineFormatter('[%(levelname)s]: %(message)s')
    console.setFormatter(formatter)
    fileh.setFormatter(formatter_file)
    logger.addHandler(fileh)
    logger.addHandler(console)

    hello_word(VERSION, localfile, basepath)

    settings = parse_settings_file(localfile)
    create_conversion_factors(settings['units'], **settings['units-base'])

    system = create_system(settings)
    system.forcefield = create_force_field(settings)
    simulation = create_simulation(settings, system)
    output_tasks = [task for task in create_output(system, settings)]

    for result in simulation.run():
        #stepno = result['cycle']['stepno']
        #result['thermo']['stepno'] = stepno
        for task in output_tasks:
            task.output(result)
    bye_bye_world()
