#! /usr/bin/env python3
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

More information about running pyretis can be found at: www.pyretis.org
"""
# pylint: disable=C0103
import argparse
import datetime
import logging
import os
import sys
# Other libraries:
import tqdm  # For a progress bar
# pyretis library imports:
from pyretis import __version__ as VERSION
from pyretis.info import PROGRAM_NAME, URL, CITE
from pyretis.core.units import units_from_settings
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.core.initiation import initiate_path_simulation
from pyretis.inout.settings import create_output_tasks
from pyretis.inout.common import (check_python_version,
                                  get_log_formatter,
                                  make_dirs,
                                  print_to_screen)
from pyretis.inout.settings import (parse_settings_file,
                                    write_settings_file,
                                    create_system,
                                    create_force_field,
                                    create_simulation,
                                    create_engine,
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
    for txt in msgtxt:
        print_to_screen(txt)
        if txt is not None:
            logger.info(txt)


def bye_bye_world():
    """Method to print out the goodbye message for pyretis."""
    timeend = datetime.datetime.now().strftime(_DATE_FMT)
    msgtxt = 'End of {} execution: {}'.format(PROGRAM_NAME, timeend)
    print_to_screen(msgtxt)
    logger.info(msgtxt)
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


def get_tasks(sim_settings, directory=None, engine=None, progress=False):
    """Simple function to create tasks from settings.

    Parameters
    ----------
    sim_settings : dict
        The simulation settings.
    directory : string
        The directory where output files should be written.
    engine : object like :py:class:`.EngineBase`
        The engine (if any) specified for the simulation.
    progress : boolean, optional
        If True, we will display a progress bar and we don't need
        to set up writing of results to the screen.

    Returns
    -------
    out : list of objects like :py:class:`.OutputTask`
        Objects that can be used for creating output.
    """
    msgtxt = 'Creating output tasks from settings'
    print_to_screen(msgtxt)
    logger.info(msgtxt)
    output_tasks = []
    for out_task in create_output_tasks(sim_settings,
                                        directory=directory,
                                        engine=engine):
        if progress and out_task.target == 'screen':
            msgtxt = ('Ignoring "{}" since progress '
                      'bar is ON'.format(out_task.name))
            logger.info(msgtxt)
            print_to_screen(msgtxt)
        else:
            output_tasks.append(out_task)
    return output_tasks


def run_md_flux_simulation(sim, sim_settings, progress=False):
    """This will run a md-flux simulation.

    Parameters
    ----------
    sim : object like :py:class:`.Simulation`
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    output_tasks = get_tasks(sim_settings, engine=sim.engine,
                             progress=progress)
    print_to_screen('Starting MD-Flux simulation')
    tqd = use_tqdm(progress)
    nsteps = sim.cycle['end'] - sim.cycle['step']
    for result in tqd(sim.run(), total=nsteps, desc='MD-flux'):
        for out_task in output_tasks:
            out_task.output(result)


def run_md_simulation(sim, sim_settings, progress=False):
    """This will run a md simulation.

    Parameters
    ----------
    sim : object like :py:class:`.Simulation`
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    # create output tasks:
    output_tasks = get_tasks(sim_settings, engine=sim.engine,
                             progress=progress)
    print_to_screen('Starting MD simulation')
    tqd = use_tqdm(progress)
    nsteps = sim.cycle['end'] - sim.cycle['step']
    for result in tqd(sim.run(), total=nsteps, desc='MD step'):
        for out_task in output_tasks:
            out_task.output(result)


def create_pathensemble_directories(ensemble):
    """Create directories for a given path ensemble.

    Parameters
    ----------
    ensemble : object like :py:class:`.Pathensemble`
        The path ensemble to create for.
    """
    for ensemble_dir in ensemble.directories():
        msg_dir = make_dirs(ensemble_dir)
        msgtxt = 'Ensemble {}: {}'.format(ensemble.ensemble_name, msg_dir)
        print_to_screen(msgtxt)
        logger.info(msgtxt)


def run_tis_single_simulation(sim, sim_settings, progress=False):
    """This will run a single TIS simulation.

    Parameters
    ----------
    sim : object like :py:class:`.Simulation`
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    # Ensure that we create the output directory for the ensemble
    # we are simulating for:
    ensemble = sim.path_ensemble
    ensemble_name = ensemble.ensemble_name

    logtxt = 'TIS simulation: {}'.format(ensemble_name)
    print_to_screen(logtxt)
    logger.info(logtxt)

    logtxt = 'Creating output directories'
    print_to_screen(logtxt)
    logger.info(logtxt)
    create_pathensemble_directories(ensemble)

    # Create output tasks:
    output_tasks = get_tasks(
        sim_settings,
        directory=ensemble.ensemble_name_simple,
        engine=sim.engine,
        progress=progress
    )

    print_to_screen('')

    logtxt = 'Starting TIS simulation: {}'.format(ensemble_name)
    print_to_screen(logtxt)
    logger.info(logtxt)

    logtxt = 'Generating initial path'
    print_to_screen(logtxt)
    logger.info(logtxt)

    # We perform the initiation here. The initiation method expects
    # a iterable of path ensembles so we just give that to it:
    _help_with_initialization(sim, (output_tasks,))

    logtxt = 'Initialization done. Starting main TIS simulation'
    print_to_screen(logtxt)
    logger.info(logtxt)

    tqd = use_tqdm(progress)
    nsteps = (sim.cycle['end'] - sim.cycle['step'])
    desc = 'TIS Ensemble {}'.format(ensemble_name)
    for result in tqd(sim.run(), total=nsteps, desc=desc):
        for out_task in output_tasks:
            out_task.output(result)

def _help_with_initialization(sim, output_tasks):
    """Just a helper method do initialization and output results."""
    settings = sim.settings['tis']
    for i, result in enumerate(initiate_path_simulation(sim, settings)):
        path = result[1]
        logtxt = 'Initial path is:'
        print_to_screen(logtxt)
        logger.info(logtxt)
        logtxt = '{}'.format(path)
        print_to_screen(logtxt)
        logger.info(logtxt)
        print_to_screen('')
        ensemble_result = {
            'pathensemble': sim.path_ensembles[i],
            'cycle': sim.cycle,
            'path': path,
            'system': sim.system
        }
        for out_task in output_tasks[i]:
            out_task.output(ensemble_result)


def run_retis_simulation(sim, sim_settings, progress=False):
    """This will run a RETIS simulation.

    Parameters
    ----------
    sim : object like :py:class:`.Simulation`
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    path_ensembles = sim.path_ensembles
    output_tasks = []

    logtxt = 'Creating output directories'
    print_to_screen(logtxt)
    logger.info(logtxt)

    for ensemble in path_ensembles:
        create_pathensemble_directories(ensemble)
        ensemble_task = get_tasks(
            sim_settings,
            directory=ensemble.ensemble_name_simple,
            engine=sim.engine,
            progress=progress
        )
        output_tasks.append(ensemble_task)
    print_to_screen('')
    logtxt = 'Starting RETIS simulation'
    print_to_screen(logtxt)
    logger.info(logtxt)
    logtxt = 'Initializing path ensembles'
    print_to_screen(logtxt)
    logger.info(logtxt)
    # Here we do the initialization:
    _help_with_initialization(sim, output_tasks)

    logtxt = 'Starting main RETIS simulation.'
    print_to_screen(logtxt)
    logger.info(logtxt)

    tqd = use_tqdm(progress)
    nsteps = sim.cycle['end'] - sim.cycle['step']
    for result in tqd(sim.run(), total=nsteps, desc='RETIS'):
        # Do output for each ensemble:
        for i, ensemble in enumerate(path_ensembles):
            ensemble_result = {'pathensemble': ensemble,
                               'cycle': result['cycle'],
                               'path': result['retis'][i][2],
                               'system': result['system']}
            for out_task in output_tasks[i]:
                out_task.output(ensemble_result)
        if not progress:
            logtxt = '\nStep: {}'.format(result['cycle']['step'])
            print_to_screen(logtxt)
            for res, ensemble in zip(result['retis'], sim.path_ensembles):
                logtxt = '{:>10s}: {:>8s} {:>5s}'.format(ensemble.ensemble_name,
                                                         res[0], res[1])
                print_to_screen(logtxt)
            print_to_screen()


def run_tis_simulation(settings_sim, settings_tis, progress=False):
    """This will run TIS simulations.

    Here, we have the possibility of doing 2 things:

    1) Just write out input files for single TIS simulations and
       exit without running a simulation.

    2) Run a single TIS simulation.

    Parameters
    ----------
    settings_sim : list of dicts or Simulation objects
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
        print_to_screen()
        logtxt = 'Input settings requests: TIS for multiple path ensembles.'
        print_to_screen(logtxt)
        logger.info(logtxt)
        logtxt = 'Will create input files for the TIS simulations and exit'
        print_to_screen(logtxt)
        logger.info(logtxt)

        print_to_screen()
        for setting in settings_sim:
            ens = setting['simulation']['ensemble']
            ensf = PATH_DIR_FMT.format(ens)
            logtxt = 'Setting up TIS ensemble: {}'.format(ens)
            print_to_screen(logtxt)
            logger.info(logtxt)
            infile = '{}-{}.rst'.format(setting['simulation']['task'], ensf)
            logtxt = 'Create file: "{}"'.format(infile)
            print_to_screen()
            logger.info(logtxt)
            write_settings_file(setting, infile, backup=False)
            logtxt = 'Command for executing:'
            print_to_screen(logtxt)
            logger.info(logtxt)
            logtxt = 'pyretisrun -i {} -p -f {}.log'.format(infile, ensf)
            print_to_screen(logtxt)
            logger.info(logtxt)
            print_to_screen()


def run_generic_simulation(sim, sim_settings, progress=False):
    """Run a pyretis single simulation.

    These are simulations that are just going to complete a given
    number of steps. Other simulation may consist of several
    simulations tied together and these are NOT handled here.

    Parameters
    ----------
    sim : object like :py:class:`.Simulation`
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise we print
        results to the screen.
    """
    # create output tasks:
    output_tasks = get_tasks(sim_settings,
                             engine=getattr(sim, 'engine', None),
                             progress=progress)
    logtxt = 'Running simulation'
    print_to_screen(logtxt)
    logger.info(logtxt)
    tqd = use_tqdm(progress)
    for result in tqd(sim.run(), desc='Step'):
        for out_task in output_tasks:
            out_task.output(result)


_RUNNERS = {'md-flux': run_md_flux_simulation,
            'md-nve': run_md_simulation,
            'tis': run_tis_simulation,
            'retis': run_retis_simulation}


def set_up_simulation(inputfile, runpath):
    """This will run all the needed generic set-up.

    Parameters
    ----------
    inputfile : string
        The input file which defines the simulation.
    runpath : string
        The base path we are running the simulation from.

    Returns
    -------
    runner : method
        A method which can be used to execute the simulation.
    sim : object like :py:class:`.Simulation`
        The simulation defined by the input file.
    syst : object like :py:class:`.System`
        The system created.
    sim_settings : dict
        The input settings read from the input file.
    """

    if not os.path.isfile(inputfile):
        msg = 'No simulation input "{}" found!'.format(inputfile)
        logger.error(msg)
        raise ValueError(msg)

    logtxt = 'Reading input settings from: {}'.format(inputfile)
    print_to_screen(logtxt)
    logger.info(logtxt)

    sim_settings = parse_settings_file(inputfile)
    sim_settings['simulation']['exe-path'] = runpath

    print_to_screen()

    logtxt = 'Initiaizing unit system.'
    print_to_screen(logtxt)
    logger.info(logtxt)

    logtxt = units_from_settings(sim_settings)
    print_to_screen(logtxt)
    logger.info(logtxt)

    engine = create_engine(sim_settings)
    if engine is not None:
        logtxt = 'Created engine "{}" from settings'.format(engine)
        print_to_screen(logtxt)
        logger.info(logtxt)
    else:
        logtxt = 'No engine created'
        print_to_screen(logtxt)
        logger.info(logtxt)

    logtxt = 'Creating system from settings.'
    print_to_screen(logtxt)
    logger.info(logtxt)
    syst = create_system(sim_settings, engine=engine)

    logtxt = 'Creating force field'
    print_to_screen(logtxt)
    logger.info(logtxt)
    syst.forcefield = create_force_field(sim_settings)
    syst.extra_setup()

    logtxt = 'Creating simulation from settings.'
    print_to_screen(logtxt)
    logger.info(logtxt)
    keyargs = {'system': syst, 'engine': engine}
    sim = create_simulation(sim_settings, keyargs)

    task = sim_settings['simulation']['task'].lower()
    logtxt = 'Will run simulation: "{}"'.format(task)
    print_to_screen(logtxt)
    logger.info(logtxt)
    runner = _RUNNERS.get(task, run_generic_simulation)
    return runner, sim, syst, sim_settings


def main(infile, indir, exe_dir, progress):
    """The main method for executing pyretis.

    Parameters
    ----------
    infile : string
        The input file to open with settings for pyretis.
    indir : string
        The folder containing the settings file.
    run_path : string
        The directory we are working from.
    progress : boolean
        Determines if we should use a progress bar or not."""
    simulation = None
    system = None
    settings = {}

    try:
        run, simulation, system, settings = set_up_simulation(infile,
                                                              exe_dir)
        # Run the simulation:
        run(simulation, settings, progress=progress)
    except Exception as error:  # Exceptions should subclass BaseException.
        errtxt = '{}: {}'.format(type(error).__name__, error.args)
        logger.error(errtxt)
        print_to_screen('Error encountered, execution stopped.')
        print_to_screen('Please see the LOG for more info.')
        raise
    finally:
        # Write out the simulation settings as they were parsed and
        # add some additional info:
        if simulation is not None:
            end = getattr(simulation, 'cycle', {'step': None})['step']
            if end is not None:
                settings['simulation']['endcycle'] = end
                logtxt = 'Execution ended at step {}'.format(end)
                print_to_screen(logtxt)
                logger.info(logtxt)
        if system is not None:
            if 'particles' not in settings:
                settings['particles'] = {}
            settings['particles']['npart'] = system.particles.npart
        if len(settings) != 0:
            out_file = os.path.join(indir, 'out.rst')
            logtxt = 'Writing simulation settings: {}'.format(out_file)
            print_to_screen(logtxt)
            logger.info(logtxt)
            write_settings_file(settings, out_file,
                                backup=settings['output']['backup'])

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

    input_file = args_dict['input']
    # Store directories:
    cwd_dir = os.getcwd()
    input_dir = os.path.dirname(input_file)
    if not os.path.isdir(input_dir):
        input_dir = os.getcwd()

    # Set up for logging:
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    # Define a console logger. This will log to sys.stderr:
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(get_log_formatter(logging.WARNING))
    logger.addHandler(console)
    # Define a file logger:
    fileh = logging.FileHandler(args_dict['log_file'], mode='w')
    log_level = getattr(logging, args_dict['log_level'].upper(),
                        logging.INFO)
    fileh.setLevel(log_level)
    fileh.setFormatter(get_log_formatter(log_level))
    logger.addHandler(fileh)

    # Here, we just check the python version. pyretis should anyway
    # fail before this for python2.
    check_python_version()

    hello_world(input_file, cwd_dir, args_dict['log_file'])

    main(input_file, input_dir, cwd_dir, args_dict['progress'])

    bye_bye_world()
