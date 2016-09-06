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
import tqdm  # for a nice progress bar
# pyretis library imports:
from pyretis import __version__ as VERSION
from pyretis import __program_name__ as NAME
from pyretis import __url__ as URL
from pyretis import __cite__ as CITE
from pyretis.core.units import units_from_settings
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.inout import create_output
from pyretis.inout.common import (check_python_version,
                                  LOG_DEBUG_FMT,
                                  LOG_FMT,
                                  make_dirs,
                                  print_to_screen,
                                  PyretisLogFormatter,
                                  PyretisLogFormatterDebug)
from pyretis.inout.settings import (parse_settings_file,
                                    write_settings_file,
                                    create_system,
                                    create_force_field,
                                    create_orderparameter,
                                    create_simulation)


_DATE_FMT = '%d.%m.%Y %H:%M:%S'


def use_tqdm(progress):
    """Return a progress bar if we want one."""
    if progress:
        return tqdm.tqdm
    else:
        def empty_tqdm(*args, **kwargs):
            """Dummy function to replace tqdm when it's not used."""
            if args:
                return args[0]
            return kwargs.get('iterable', None)
        return empty_tqdm


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
    timestart = datetime.datetime.now().strftime(_DATE_FMT)
    pyversion = sys.version.split()[0]
    msg = ['{}'.format(timestart)]
    msg += ['{} version {} (Python version: {})'.format(NAME, VERSION,
                                                        pyversion)]
    msg += ['Running in directory: {}'.format(rundir)]
    msg += ['Input file: {}'.format(infile)]
    msg += ['Log file: {}'.format(logfile)]
    for message in msg:
        print_and_loginfo(message)


def print_and_loginfo(msg):
    """Print and log a message."""
    logger.info(msg)
    print_to_screen(msg)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis."""
    timeend = datetime.datetime.now().strftime(_DATE_FMT)
    msgtxt = 'End of {} execution: {}'.format(NAME, timeend)
    print_and_loginfo(msgtxt)
    # display some references:
    references = ['{} references:'.format(NAME)]
    references.append(('-')*len(references[0]))
    for line in CITE.split('\n'):
        if line:
            references.append(line)
    reftxt = '\n'.join(references)
    logger.info(reftxt)
    print_to_screen()
    print_to_screen(reftxt)
    urltxt = '{}'.format(URL)
    logger.info(urltxt)
    print_to_screen()
    print_to_screen(urltxt)


def get_tasks(sim_settings, progress=False):
    """Simple function to create tasks from settings.

    Parameters
    ----------
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar and we don't need
        to set up writing of results to the screen.

    Returns
    -------
    out : list of objects like `OutputTask`.
        Objects that can be used for creating output.
    """
    msgtxt = 'Creating output tasks from settings'
    print_to_screen(msgtxt)
    logger.info(msgtxt)
    output_tasks = []
    for task in create_output(sim_settings):
        if progress and task.target == 'screen':
            pass
        else:
            output_tasks.append(task)
    return output_tasks


def run_md_flux_simulation(sim, sim_settings, progress=False):
    """This will run a md-flux simulation.

    Note that we will try do do a small analysis after the
    simulation is done.

    Parameters
    ----------
    sim : object like `Simulation`.
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    output_tasks = get_tasks(sim_settings, progress=progress)
    print_and_loginfo('Starting MD-Flux simulation')
    tqd = use_tqdm(progress)
    for result in tqd(sim.run(), total=sim_settings['steps'],
                      desc='# MD-flux'):
        for task in output_tasks:
            task.output(result)


def run_md_simulation(sim, sim_settings, progress=False):
    """This will run a md simulation.

    Parameters
    ----------
    sim : object like `Simulation`.
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    # create output tasks:
    output_tasks = get_tasks(sim_settings, progress=progress)
    print_and_loginfo('Starting MD simulation')
    tqd = use_tqdm(progress)
    for result in tqd(sim.run(), total=sim_settings['simulation']['steps'],
                      desc='# MD step'):
        for task in output_tasks:
            task.output(result)


def run_tis_single_simulation(sim, sim_settings, progress=False,
                              position=0):
    """This will run a single TIS simulation.

    Parameters
    ----------
    sim : object like `Simulation`.
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    position : integer
        Used to control location of progress bars
    """
    # ensure that we create an output directory
    msg_dir = make_dirs(sim_settings['output-dir'])
    msgtxt = ('Creating output directory: '
              '{}'.format(msg_dir))
    print_and_loginfo(msgtxt)
    # create output tasks:
    output_tasks = get_tasks(sim_settings, progress=progress)
    print_and_loginfo('Running TIS ensemble simulation')
    tqd = use_tqdm(progress)
    for result in tqd(sim.run(), total=sim_settings['simulation']['steps'],
                      desc='# Ensemble {}'.format(sim_settings['ensemble']),
                      position=position):
        for task in output_tasks:
            task.output(result)

def run_retis_simulation(sim, sim_settings, progress=False,
                         position=0):
    """This will run a RETIS simulation.

    Parameters
    ----------
    sim : object like `Simulation`.
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    position : integer
        Used to control location of progress bars
    """
    output_tasks = []
    print_and_loginfo('Creating output directories:')
    for ensemble in sim.path_ensembles:
        dirname = ensemble.ensemble_name_simple
        msg_dir = make_dirs(dirname)
        msgtxt = 'Ensemble {}: {}'.format(ensemble.ensemble_name, msg_dir)
        print_and_loginfo(msgtxt)
        sim_settings['output-dir'] = dirname
        ensemble_task = get_tasks(sim_settings, progress=progress)
        output_tasks.extend(ensemble_task)
    print_to_screen('')
    print_and_loginfo('Running RETIS ensemble simulation')
    print_and_loginfo('Initializing the path ensembles...')
    # Here we explicitly do the initialization. This is just
    # because we want to print out some info!
    for task, ensemble in zip(output_tasks, sim.path_ensembles):
        print_and_loginfo('Initiating in {}'.format(ensemble.ensemble_name))
        path = sim.initiate_ensemble(ensemble)
        print_and_loginfo('Initial path: {}'.format(path))
        print_to_screen('')
        result = {'pathensemble': ensemble, 'cycle': sim.cycle}
        task.output(result)
    sim.first_step = False  # We have done the "first" step now.
    print_and_loginfo('Starting main RETIS simulation...')
    tqd = use_tqdm(progress)
    for result in tqd(sim.run(), total=sim_settings['steps'],
                      desc='RETIS',
                      position=position):
        for task, ensemble in zip(output_tasks, sim.path_ensembles):
            print('Ensemble path-length:', ensemble.ensemble_name, ensemble.last_path.length)
            result['pathensemble'] = ensemble
            task.output(result)
        print('\nStep:', result['cycle']['step']+1)


def run_tis_simulation(settings_all, settings_tis, progress=False):
    """This will run several TIS simulations.

    Here, we have the possibility of doing 2 things:

    1) Just write out input files for single TIS simulations and
       exit without running a simulation.

    2) Run the TIS simulations in series.

    pyretisrun will not run a parallel TIS simulation. This since
    the tasks can be run in parallel by using option 1.


    Parameters
    ----------
    settings_all : list of dicts.
        The settings for the single TIS simulations to run.
    settings_tis : dict
        The simulation settings for the TIS simulation.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    run_type = settings_tis.get('run_type', 'serial')
    if run_type == 'write':
        print_and_loginfo('Creation of input files requested.')
        for i, setting in enumerate(settings_all):
            ens = setting['ensemble']
            ensf = PATH_DIR_FMT.format(ens)
            msgtxt = 'Setting up TIS ensemble: {}'.format(ens)
            print_and_loginfo(msgtxt)
            infile = '{}-{}.rst'.format(setting['task'], ensf)
            print_and_loginfo('Create file: "{}"'.format(infile))
            write_settings_file(setting, infile, backup=False)
            print_and_loginfo('Command for executing:')
            print_and_loginfo('pyretisrun -i {} -p -f {}.log'.format(infile,
                                                                     ensf))
            print_to_screen()
    else:
        simulations = []
        for i, setting in enumerate(settings_all):
            ens = setting['ensemble']
            msgtxt = 'Creating TIS simulation, ensemble: {0}'.format(ens)
            print_and_loginfo(msgtxt)
            simulations.append(create_simulation(setting, system))
        print_to_screen()
        print_and_loginfo('Starting SERIAL TIS simulation')
        print_to_screen()
        nens = len(simulations)
        for i, (sim, setting) in enumerate(zip(simulations, settings_all)):
            print_and_loginfo('Running TIS ensemble: {}'.format(i + 1))
            run_tis_single_simulation(sim, setting, progress=progress)
            print_and_loginfo('Done with TIS ensemble: {}!'.format(i + 1))
            print_and_loginfo('{0} / {1} Completed!'.format(i + 1, nens))
            print_to_screen()


def run_generic_simulation(sim, sim_settings, progress=False):
    """Run a pyretis single simulation.

    These are simulations that are just going to complete a given
    number of steps. Other simulation may consist of several
    simulations tied together and these are NOT handled here.

    Parameters
    ----------
    sim : object like `Simulation`.
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    # create output tasks:
    output_tasks = get_tasks(sim_settings, progress=progress)
    print_and_loginfo('Running simulation')
    tqd = use_tqdm(progress)
    for result in tqd(sim.run(), desc='# Step'):
        for task in output_tasks:
            task.output(result)


_RUNNERS = {'md-flux': run_md_flux_simulation,
            'md-nve': run_md_simulation,
            'tis-single': run_tis_single_simulation,
            'tis': run_tis_simulation,
            'retis': run_retis_simulation}


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
    settings = {}

    try:
        hello_world(inputfile, basepath, args_dict['log_file'])
        if not os.path.isfile(inputfile):
            errtxt = ('No simulation input:'
                      ' {} is not a file!'.format(inputfile))
            logger.error(errtxt)
            raise ValueError(errtxt)
        print_and_loginfo('Reading input settings')
        settings = parse_settings_file(inputfile)
        settings['exe-path'] = runpath
        print_and_loginfo('Initiaizing unit system.')
        units_from_settings(settings)
        print_and_loginfo('Creating system from settings.')
        system = create_system(settings)
        print_and_loginfo('Creating force field')
        system.forcefield = create_force_field(settings)
        print_and_loginfo('Creating order parameter')
        system.order_function = create_orderparameter(settings)
        if system.order_function is None:
            print_and_loginfo('-> No order parameter was created!')
        system.extra_setup()
        print_and_loginfo('Creating simulation from settings.')
        simulation = create_simulation(settings, system)
        task = settings['simulation']['task'].lower()
        print_and_loginfo('Will run simulation: "{}"'.format(task))
        runner = _RUNNERS.get(task, run_generic_simulation)
        runner(simulation, settings, progress=args_dict['progress'])
    except Exception as error:  # Exceptions should subclass BaseException.
        errtxt = '{}: {}'.format(type(error).__name__, error.args)
        logger.error(errtxt)
        print_to_screen('Error encountered, execution stopped.')
        print_to_screen('Please see the LOG for more info.')
        raise
    finally:
        # write out the simulation settings and add some extra ones:
        if simulation is not None:
            end = getattr(simulation, 'cycle', {'step': None})['step']
            if end is not None:
                settings['simulation']['endcycle'] = end
                print_and_loginfo('Execution ended at step {}'.format(end))
        if system is not None:
            settings['particles']['npart'] = system.particles.npart
        outfile = '_out-{}'.format(inputfile)
        outpath = os.path.join(basepath, outfile)
        print_and_loginfo('Saving simulation settings: "{}"'.format(outfile))
        write_settings_file(settings, outpath,
                            backup=settings['output']['backup'])
        bye_bye_world()
