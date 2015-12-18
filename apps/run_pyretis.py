#! /usr/bin/python
# -*- coding: utf-8 -*-
"""pyretis

This script is a part of the pyretis library. It will parse input
settings and run a simulation based on those settings.
"""
# pylint: disable=C0103
from __future__ import print_function, absolute_import
import logging
import argparse
import os
from pyretis import __version__ as VERSION
from pyretis import __program_name__ as NAME
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import parse_settings_file
from pyretis.inout.settings import (create_system, create_force_field,
                                    create_simulation)
from pyretis.inout import create_output


class MultiLineFormatter(logging.Formatter):
    """Hardcoded formatter for pyretis log."""
    def format(self, record):
        out = logging.Formatter.format(self, record)
        shortname = record.name.split('.')[-1]
        out = out.replace(record.name, shortname)
        header, _ = out.split(record.message)
        out = out.replace('\n', '\n' + ' '*len(header))
        return out


class MultiLineFormatter2(logging.Formatter):
    """Hardcoded formatter for pyretis log."""
    def format(self, record):
        out = logging.Formatter.format(self, record)
        header, _ = out.split(record.message)
        out = out.replace('\n', '\n' + ' '*len(header))
        return out

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
#formatter_file = MultiLineFormatter2('%(name)s: [%(levelname)s]: %(message)s')
    console.setFormatter(formatter)
    fileh.setFormatter(formatter_file)
    logger.addHandler(fileh)
    logger.addHandler(console)
    settings = parse_settings_file(localfile)
    units = settings['units']
    settings['unit-system'] = units['system']
    create_conversion_factors(settings['unit-system'])
    system = create_system(settings)
    system.forcefield = create_force_field(settings)
    simulation = create_simulation(settings, system)
    output_tasks = [task for task in create_output(system, settings)]

    for result in simulation.run():
        #stepno = result['cycle']['stepno']
        #result['thermo']['stepno'] = stepno
        for task in output_tasks:
            task.output(result)
