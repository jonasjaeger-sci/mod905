#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""pyretisanalyse - An application for analysing PyRETIS simulations.

This script is a part of the PyRETIS library and can be used for
analysing the result from simulations.

usage: pyretisanalyse.py [-h] -i INPUT [-V]

PyRETIS

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Location of PyRETIS input file
  -V, --version         show program's version number and exit
"""
# pylint: disable=invalid-name
import argparse
import logging
import os
import sys
import traceback
import colorama
from pyretis import __version__ as VERSION
from pyretis.info import PROGRAM_NAME, URL, CITE, LOGO
from pyretis.core.units import CONSTANTS
from pyretis.core.pathensemble import generate_ensemble_name
from pyretis.inout.analysisio.analysisio import run_analysis
from pyretis.inout.common import (
    check_python_version,
    make_dirs,
    name_file,
    create_backup,
)
from pyretis.inout.formats.formatter import (
    LOG_FMT,
    PyretisLogFormatter,
)
from pyretis.inout import print_to_screen
from pyretis.inout.report import generate_report
from pyretis.inout.settings import parse_settings_file
from pyretis.visualization.orderparam_density import PathDensity
from pyretis.visualization.common import hello_pyvisa
from pyretis.visualization import HAS_PYQT5
if HAS_PYQT5:
    from pyretis.visualization.visualize import visualize_main

logger = logging.getLogger('')
runpath = os.getcwd()

# Hard-coded patters for report outputs:
REPORTFILES = {
    'md-flux': 'md_flux_report',
    'retis': 'retis_report',
    'tis-multiple': 'tis-multiple_report',
    'tis': 'tis_report'
}


ERROR_FILE = 'error.txt'


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
        The path to the directory where the reports should be saved.

    Yields
    ------
    out : string
        The report files created.

    """
    if settings['simulation']['task'] == 'tis':
        task = 'tis'
        pfix = generate_ensemble_name(settings['simulation']['ensemble'])
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


def hello_world(infile, run_dir, report_dir):
    """Output a standard greeting for PyRETIS analysis.

    Parameters
    ----------
    infile : string
        String showing the location of the input file.
    run_dir : string
        The location where we are executing the analysis.
    report_dir : string
        String showing the location of where we write the output.

    """
    pyversion = sys.version.split()[0]
    msgtxt = [LOGO]
    msgtxt += ['                                                    Starting']
    msgtxt += ['analysis tool!']
    msgtxt += ['{} version: {}'.format(PROGRAM_NAME, VERSION)]
    msgtxt += ['Python version: {}'.format(pyversion)]
    msgtxt += ['Running in directory: {}'.format(run_dir)]
    msgtxt += ['Report directory: {}'.format(report_dir)]
    msgtxt += ['Input file: {}'.format(infile)]
    print_to_screen('\n'.join(msgtxt), level='message')
    logger.info('\n'.join(msgtxt))


def bye_bye_world():
    """Print out the goodbye message for PyRETIS."""
    msgtxt = 'End of {} analysis execution.'.format(PROGRAM_NAME)
    logger.info(msgtxt)
    print_to_screen('')
    print_to_screen(msgtxt, level='info')
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
    print_to_screen(urltxt, level='info')


def write_traceback(filename):
    """Write the error traceback to the given file."""
    msg = create_backup(filename)
    if msg:
        logger.warning(msg)
    with open(filename, 'w') as out:
        out.write(traceback.format_exc())


def main(input_file, run_path, report_dir, pyvisa_dict=None):
    """Run the analysis.

    Parameters
    ----------
    input_file : string
        The input file with settings for the analysis.
    run_path : string
        The location from which we are running the analysis.
    report_dir : string
        The location where we will write the report.
    pyvisa_dict : dictionary, optional
        It determines the section of pyvisa to use, it contains:
         * `pyvisa`, boolean
           If true, the compressor followed by the GUI will be executed
           if an .rst file will be provided as an input (-i option),
           while only the GUI will be executed if a pickle file will
           be providedd as a input.
         * `pyvisa-cmp`, boolean
           If true, only the compressor tool will be executed. A compressed
           file will be produced.

    """
    try:
        if pyvisa_dict.get('pyvisa_compressor', False):
            hello_pyvisa()
            only_ops = pyvisa_dict['only_order']
            p_data = PathDensity(iofile=input_file)
            p_data.walk_dirs(only_ops=only_ops)
            if pyvisa_dict['pickle']:
                p_data.pickle_data()
            else:
                p_data.deepdish_data()

        elif pyvisa_dict.get('pyvisa_all', False):
            if not HAS_PYQT5:
                msg = ('PyQt5 is not installed. You can still generate the '
                       'pickle by using the -pyvisa-cmp flag instead')
                raise ImportError(msg)
            runpath = os.path.dirname(os.path.realpath(input_file))
            hello_pyvisa()
            if not any(('pickle' in input_file,
                        'hdf5' in input_file)):
                p_data = PathDensity(iofile=input_file)
                p_data.walk_dirs()
                if pyvisa_dict['pickle']:
                    p_data.pickle_data()
                else:
                    p_data.deepdish_data()
                visualize_main(runpath, p_data.pfile)
            else:
                visualize_main(runpath, input_file)
        else:
            print_to_screen('Reading input file "{}"'.format(input_file))
            settings = parse_settings_file(input_file)
            # override exe-path to the one we are executing in now:
            settings['simulation']['exe-path'] = run_path
            units = settings['system']['units']
            # set derived properties:
            settings['system']['beta'] = (settings['system']['temperature'] *
                                          CONSTANTS['kB'][units])**-1
            settings['analysis']['report-dir'] = report_dir
            msg_dir = make_dirs(report_dir)
            print_to_screen(msg_dir)
            task = settings['simulation']['task']
            print_to_screen('Simulation task was: "{}"'.format(task))
            print_to_screen()

            results = run_analysis(settings)
            print_to_screen()
            for outfile in create_reports(settings, results, report_dir):
                relfile = os.path.relpath(outfile, start=run_path)
                print_to_screen('Report created: {}'.format(relfile),
                                level='info')

    except FileNotFoundError as error:
        errtxt = '{}: {}'.format(error.strerror, error.filename)
        print_to_screen(errtxt, level='error')
        print_to_screen('Execution failed!', level='error')
    except Exception as error:  # Exceptions should subclass BaseException.
        errtxt = '{}: {}'.format(type(error).__name__, error.args)
        print_to_screen(errtxt, level='error')
        print_to_screen('Execution failed!', level='error')
        print_to_screen('Error traceback is written to: {}'.format(ERROR_FILE),
                        level='error')
        write_traceback(ERROR_FILE)
    finally:
        bye_bye_world()


def entry_point():
    """entry_point - The entry point for the pip install of pyretisanalyse."""
    colorama.init(autoreset=True)
    parser = argparse.ArgumentParser(description=PROGRAM_NAME)
    parser.add_argument(
        '-i',
        '--input',
        help=('Location of {} input file'.format(PROGRAM_NAME)),
        required=False,
        default='retis.rst'
    )
    parser.add_argument('-V', '--version', action='version',
                        version='{} {}'.format(PROGRAM_NAME, VERSION))
    parser.add_argument('-pyvisa', '--pyvisa-all', action='store_true',
                        help='Run PyVisA',
                        default=False)
    parser.add_argument('-pyvisa-cmp', '--pyvisa-compressor',
                        action='store_true',
                        help='Run PyVisA compressor tool',
                        default=False)
    parser.add_argument('-oo', '--only_order', action='store_true',
                        help=('PyVisA: Use only data from order.txt files'),
                        default=False)
    parser.add_argument('-p', '--pickle', action='store_true',
                        help=('PyVisA: Output pickle file, default is hdf5.'),
                        default=False)

    args_dict = vars(parser.parse_args())

    # set up for logging:
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    # Define a console logger. This will log to sys.stderr:
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(PyretisLogFormatter(LOG_FMT))
    logger.addHandler(console)

    check_python_version()

    inputfile = args_dict['input']
    # runpath = os.getcwd()
    basepath = os.path.dirname(inputfile)
    if not os.path.isdir(basepath):
        basepath = os.getcwd()
    reportdir = os.path.join(runpath, 'report')

    hello_world(inputfile, runpath, reportdir)
    main(inputfile, runpath, reportdir, args_dict)


if __name__ == '__main__':
    entry_point()
