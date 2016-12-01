#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
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
from pyretis.info import PROGRAM_NAME, URL, CITE
from pyretis.core.units import units_from_settings
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.inout.settings import create_output
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
                                    create_simulation,
                                    is_single_tis)


_DATE_FMT = '%d.%m.%Y %H:%M:%S'


def use_tqdm(progress):
    """Return a progress bar if we want one.

    Parameters
    ----------
    progress : boolean
        If True, we should use a progress bar, otherwise not."""
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
    if level < logging.DEBUG:
        # Note: This will not happen. This formatter is intended
        # for development and debugging. Change to
        # level <= logging.DEBUG to use it at set the loglevel to debug.
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
    msgtxt = ["Welcome to"]
    msgtxt += [r"                          _    _"]
    msgtxt += [r" _ __   _   _  _ __  ___ | |_ (_) ___"]
    msgtxt += [r"| '_ \ | | | || '__|/ _ \| __|| |/ __|"]
    msgtxt += [r"| |_) || |_| || |  |  __/| |_ | |\__ \ "]
    msgtxt += [r"| .__/  \__, ||_|   \___| \__||_||___/"]
    msgtxt += [r"|_|     |___/"]
    msgtxt += [None]
    msgtxt += ['Version: {}'.format(VERSION)]
    msgtxt += ['Start of execution: {}'.format(timestart)]
    msgtxt += ['Python version: {}'.format(pyversion)]
    msgtxt += ['Running in directory: {}'.format(rundir)]
    msgtxt += ['Input file: {}'.format(infile)]
    msgtxt += ['Log file: {}'.format(logfile)]
    msgtxt += [None]
    for message in msgtxt:
        print_and_loginfo(message)


def print_and_loginfo(msgtxt):
    """Print and log a message."""
    if msgtxt is not None:
        logger.info(msgtxt)
    print_to_screen(msgtxt)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis."""
    timeend = datetime.datetime.now().strftime(_DATE_FMT)
    msgtxt = 'End of {} execution: {}'.format(PROGRAM_NAME, timeend)
    print_and_loginfo(msgtxt)
    # display some references:
    references = ['{} references:'.format(PROGRAM_NAME)]
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
    for out_task in create_output(sim_settings):
        if progress and out_task.target == 'screen':
            pass
        else:
            output_tasks.append(out_task)
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
    nsteps = sim.cycle['end'] - sim.cycle['step']
    for result in tqd(sim.run(), total=nsteps, desc='MD-flux'):
        for out_task in output_tasks:
            out_task.output(result)


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
    nsteps = sim.cycle['end'] - sim.cycle['step']
    for result in tqd(sim.run(), total=nsteps, desc='MD step'):
        for out_task in output_tasks:
            out_task.output(result)


def run_tis_single_simulation(sim, sim_settings, progress=False):
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
    """
    # Ensure that we create an output directory
    msg_dir = make_dirs(sim_settings['output']['directory'])
    msgtxt = ('Creating output directory: '
              '{}'.format(msg_dir))
    print_and_loginfo(msgtxt)
    # Create output tasks:
    output_tasks = get_tasks(sim_settings, progress=progress)
    print_and_loginfo(None)
    print_and_loginfo('Starting TIS simulation!')
    print_and_loginfo('Generating initial path...')
    result = sim.step()
    path = result['trialpath']
    print_and_loginfo('Initiated path: {}'.format(path))
    print_and_loginfo(None)
    for out_task in output_tasks:
        out_task.output(result)
    # Start the full simulation:
    tqd = use_tqdm(progress)
    nsteps = (sim.cycle['end'] - sim.cycle['step']) - 1  # -1 for init
    desc = 'Ensemble {}'.format(sim_settings['simulation']['ensemble'])
    for result in tqd(sim.run(), total=nsteps, desc=desc):
        for out_task in output_tasks:
            out_task.output(result)


def run_retis_simulation(sim, sim_settings, progress=False):
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
    """
    output_tasks = []
    print_and_loginfo('Creating output directories:')
    for ensemble in sim.path_ensembles:
        dirname = ensemble.ensemble_name_simple
        msg_dir = make_dirs(dirname)
        msgtxt = 'Ensemble {}: {}'.format(ensemble.ensemble_name, msg_dir)
        print_and_loginfo(msgtxt)
        sim_settings['output']['directory'] = dirname
        sim_settings['simulation']['ensemble'] = ensemble.ensemble_name
        ensemble_task = get_tasks(sim_settings, progress=progress)
        #output_tasks.extend(ensemble_task)
        output_tasks.append(ensemble_task)
    print_to_screen('')
    print_and_loginfo('Running RETIS simulation!')
    print_and_loginfo('Initializing path ensembles...')
    # Here we explicitly do the initialization. This is just
    # because we want to print out some info!
    for tasks, ensemble in zip(output_tasks, sim.path_ensembles):
        print_and_loginfo('Initiating in {}:'.format(ensemble.ensemble_name))
        path = sim.initiate_ensemble(ensemble)
        print_and_loginfo('{}'.format(path))
        print_to_screen('')
        result = {'pathensemble': ensemble, 'cycle': sim.cycle}
        for out_task in tasks:
            out_task.output(result)
    sim.first_step = False  # We have done the "first" step now.
    print_and_loginfo('Starting main RETIS simulation!')
    tqd = use_tqdm(progress)
    nsteps = sim.cycle['end'] - sim.cycle['step']
    for result in tqd(sim.run(), total=nsteps, desc='RETIS'):
        for tasks, ensemble in zip(output_tasks, sim.path_ensembles):
            result['pathensemble'] = ensemble
            for out_task in tasks:
                out_task.output(result)
        if not progress:
            print('\nStep:', result['cycle']['step']+1)
            for res, ensemble in zip(result['retis'], sim.path_ensembles):
                print(ensemble.ensemble_name, res[0], res[1])
            print()


def run_tis_simulation(settings_sim, settings_tis, progress=False):
    """This will run TIS simulations.

    Here, we have the possibility of doing 2 things:

    1) Just write out input files for single TIS simulations and
       exit without running a simulation.

    2) Run a single TIS simulation.

    Parameters
    ----------
    settings_sim : list of dicts or Simulation object.
        The settings for the simulations or the actual simulation
        to run.
    settings_tis : dict
        The simulation settings for the TIS simulation.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    if is_single_tis(settings_tis):
        run_tis_single_simulation(settings_sim, settings_tis,
                                  progress=progress)
    else:
        print_and_loginfo(None)
        print_and_loginfo('Noted several path ensembles.')
        print_and_loginfo('Will just create input files...')
        print_and_loginfo(None)
        for setting in settings_sim:
            ens = setting['simulation']['ensemble']
            ensf = PATH_DIR_FMT.format(ens)
            msgtxt = 'Setting up TIS ensemble: {}'.format(ens)
            print_and_loginfo(msgtxt)
            infile = '{}-{}.rst'.format(setting['simulation']['task'], ensf)
            print_and_loginfo('Create file: "{}"'.format(infile))
            write_settings_file(setting, infile, backup=False)
            print_and_loginfo('Command for executing:')
            print_and_loginfo('pyretisrun -i {} -p -f {}.log'.format(infile,
                                                                     ensf))
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
    for result in tqd(sim.run(), desc='Step'):
        for out_task in output_tasks:
            out_task.output(result)


_RUNNERS = {'md-flux': run_md_flux_simulation,
            'md-nve': run_md_simulation,
            'tis': run_tis_simulation,
            'retis': run_retis_simulation}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=PROGRAM_NAME)
    parser.add_argument('-i', '--input',
                        help='Location of {} input file'.format(PROGRAM_NAME),
                        required=True)
    parser.add_argument('-V', '--version', action='version',
                        version='{} {}'.format(PROGRAM_NAME, VERSION))
    parser.add_argument('-f', '--log_file',
                        help='Specify log file to write',
                        required=False,
                        default='{}.log'.format(PROGRAM_NAME.lower()))
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
        print_and_loginfo('Reading input settings.')
        settings = parse_settings_file(inputfile)
        settings['simulation']['exe-path'] = runpath
        print_and_loginfo(None)
        print_and_loginfo('Initiaizing unit system.')
        msg = units_from_settings(settings)
        print_and_loginfo(msg)
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
        outfile = 'out.{}'.format(inputfile)
        outpath = os.path.join(basepath, outfile)
        print_and_loginfo('Saving simulation settings: "{}"'.format(outfile))
        write_settings_file(settings, outpath,
                            backup=settings['output']['backup'])
        bye_bye_world()
