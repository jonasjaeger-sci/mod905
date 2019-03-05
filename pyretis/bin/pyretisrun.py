#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""pyretisrun - An application for running PyRETIS simulations.

This script is a part of the PyRETIS library and can be used for
running simulations from an input script.

usage: pyretisrun.py [-h] -i INPUT [-V] [-f LOG_FILE] [-l LOG_LEVEL] [-p]

PyRETIS

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Location of PyRETIS input file
  -V, --version         show program's version number and exit
  -f LOG_FILE, --log_file LOG_FILE
                        Specify log file to write
  -l LOG_LEVEL, --log_level LOG_LEVEL
                        Specify log level for log file
  -p, --progress        Display a progress meter instead of text output for
                        the simulation

More information about running PyRETIS can be found at: www.pyretis.org
"""
# pylint: disable=invalid-name
import argparse
import datetime
import logging
import os
import signal
import sys
import traceback
# Other libraries:
import tqdm  # For a progress bar
import colorama  # For coloring text
# PyRETIS library imports:
from pyretis import __version__ as VERSION
from pyretis.info import PROGRAM_NAME, URL, CITE, LOGO
from pyretis.core.units import units_from_settings
from pyretis.core.pathensemble import generate_ensemble_name
from pyretis.inout.setup import (
    create_system,
    create_force_field,
    create_simulation,
    create_engine
)
from pyretis.inout.common import (
    check_python_version,
    create_backup,
)
from pyretis.inout import print_to_screen
from pyretis.inout.formats.formatter import get_log_formatter
from pyretis.inout.settings import (
    parse_settings_file,
    write_settings_file
)
from pyretis.inout.restart import (
    read_restart_file,
)


_DATE_FMT = '%d.%m.%Y %H:%M:%S'
# Set up for logging:
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
# Define a console logger. This will log to sys.stderr:
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
console.setFormatter(get_log_formatter(logging.WARNING))
logger.addHandler(console)


def use_tqdm(progress):
    """Return a progress bar if we want one.

    Parameters
    ----------
    progress : boolean
        If True, we should use a progress bar, otherwise not.

    Returns
    -------
    out : object like :py:class:`tqdm.tqdm`
        The progress bar, if requested. Otherwise, just a dummy
        iterator.

    """
    if progress:
        pbar = tqdm.tqdm
    else:
        def empty_tqdm(*args, **kwargs):
            """Return an iterator to replace tqdm."""
            if args:
                return args[0]
            return kwargs.get('iterable', None)
        pbar = empty_tqdm
    return pbar


def hello_world(infile, rundir, logfile):
    """Print out a standard greeting for PyRETIS.

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
    print_to_screen('\n'.join([LOGO]), level='message')
    logger.info('\n'.join([LOGO]))

    print_to_screen('{} version: {}'.format(PROGRAM_NAME, VERSION),
                    level='message')
    logger.info('%s version: %s', PROGRAM_NAME, VERSION)

    print_to_screen('Start of execution: {}'.format(timestart),
                    level='message')
    logger.info('Start of execution: %s', timestart)
    print_to_screen('Python version: {}'.format(pyversion), level='message')
    logger.info('Python version: %s', pyversion)

    print_to_screen('\nRunning in directory: {}'.format(rundir))
    logger.info('Running in directory: %s', rundir)
    print_to_screen('Input file: {}'.format(infile))
    logger.info('Input file: %s', infile)
    print_to_screen('Log file: {}'.format(logfile))
    logger.info('Log file: %s', logfile)


def bye_bye_world():
    """Print out the goodbye message for PyRETIS."""
    timeend = datetime.datetime.now().strftime(_DATE_FMT)
    msgtxt = 'End of {} execution: {}'.format(PROGRAM_NAME, timeend)
    print_to_screen(msgtxt, level='info')
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
    print_to_screen(urltxt, level='info')


def run_md_flux_simulation(sim, sim_settings, progress=False):
    """Run a MD-FLUX simulation.

    Parameters
    ----------
    sim : object like :py:class:`.Simulation`
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise, we print
        results to the screen.

    """
    print_to_screen('Starting MD-Flux simulation', level='info')
    tqd = use_tqdm(progress)
    nsteps = sim.cycle['end'] - sim.cycle['step']
    sim.engine.exe_dir = sim_settings['simulation']['exe-path']
    sim.set_up_output(sim_settings, progress=progress)
    for _ in tqd(sim.run(), total=nsteps, desc='MD-flux'):
        pass
    # Write final restart file:
    sim.write_restart(now=True)


def run_md_simulation(sim, sim_settings, progress=False):
    """Run a MD simulation.

    Parameters
    ----------
    sim : object like :py:class:`.Simulation`
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise, we print
        results to the screen.

    """
    print_to_screen('Starting MD simulation', level='info')
    tqd = use_tqdm(progress)
    nsteps = sim.cycle['end'] - sim.cycle['step']
    sim.engine.exe_dir = sim_settings['simulation']['exe-path']
    sim.set_up_output(sim_settings, progress=progress)
    for _ in tqd(sim.run(), total=nsteps, desc='MD step'):
        pass
    # Write final restart file:
    sim.write_restart(now=True)


def run_tis_single_simulation(sim, sim_settings, progress=False):
    """Run a single TIS simulation with PyRETIS.

    Parameters
    ----------
    sim : object like :py:class:`.Simulation`
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise, we print
        results to the screen.

    """
    # Ensure that we create the output directory for the ensemble
    # we are simulating for:
    ensemble = sim.path_ensemble
    ensemble_name = ensemble.ensemble_name

    logtxt = 'TIS simulation, ensemble: {}'.format(ensemble_name)
    print_to_screen(logtxt, level='info')
    logger.info(logtxt)

    sim.set_up_output(
        sim_settings,
        progress=progress
    )

    print_to_screen('')

    logtxt = 'Starting TIS simulation: {}'.format(ensemble_name)
    print_to_screen(logtxt)
    logger.info(logtxt)

    logtxt = 'Generating initial path'
    print_to_screen(logtxt)
    logger.info(logtxt)
    if not sim.initiate(sim_settings):
        print_to_screen('Initiation stopped, will exit now.')
        logger.info('Initiation stopped, will exit now.')
        return False
    sim.write_restart(now=True)

    logtxt = 'Initialisation done. Starting main TIS simulation'
    print_to_screen(logtxt, level='info')
    logger.info(logtxt)

    tqd = use_tqdm(progress)
    nsteps = (sim.cycle['end'] - sim.cycle['step'])
    desc = 'TIS Ensemble {}'.format(ensemble_name)
    for _ in tqd(sim.run(), total=nsteps, desc=desc):
        pass
    # Write final restart file:
    sim.write_restart(now=True)
    return True


def run_retis_simulation(sim, sim_settings, progress=False):
    """Run a RETIS simulation with PyRETIS.

    Parameters
    ----------
    sim : object like :py:class:`.Simulation`
        This is the simulation to run.
    sim_settings : dict
        The simulation settings.
    progress : boolean, optional
        If True, we will display a progress bar, otherwise, we print
        results to the screen.

    """
    sim.set_up_output(
        sim_settings,
        progress=progress
    )

    logtxt = 'Initialising RETIS simulation'
    print_to_screen('\n{}'.format(logtxt), level='info')
    logger.info(logtxt)

    logtxt = 'Initialising path ensembles:'
    print_to_screen('\n{}'.format(logtxt))
    logger.info(logtxt)

    # Here we do the initialisation:
    if not sim.initiate(sim_settings):
        print_to_screen('Initiation stopped, will exit now.')
        logger.info('Initiation stopped, will exit now.')
        return False
    sim.write_restart(now=True)

    logtxt = 'Initiation done. Starting main RETIS simulation.'
    print_to_screen('\n{}'.format(logtxt), level='success')
    logger.info(logtxt)

    tqd = use_tqdm(progress)
    nsteps = sim.cycle['end'] - sim.cycle['step']
    for _ in tqd(sim.run(), total=nsteps, desc='RETIS'):
        pass
    # Write final restart files:
    sim.write_restart(now=True)
    return True


def run_tis_simulation(settings_sim, settings_tis, progress=False):
    """Run TIS simulations with PyRETIS.

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
        If True, we will display a progress bar, otherwise, we print
        results to the screen.

    """
    if settings_tis['simulation']['task'] == 'tis':
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
        for i, setting in enumerate(settings_sim):
            ens = i + 1
            ensf = generate_ensemble_name(ens)
            logtxt = 'Creating input for TIS ensemble: {}'.format(ens)
            print_to_screen(logtxt)
            logger.info(logtxt)
            infile = '{}-{}.rst'.format('tis', ensf)
            logtxt = 'Create file: "{}"'.format(infile)
            logger.info(logtxt)
            write_settings_file(setting, infile, backup=False)
            logtxt = 'Command for executing:'
            print_to_screen(logtxt)
            logger.info(logtxt)
            logtxt = 'pyretisrun -i {} -p -f {}.log'.format(infile, ensf)
            print_to_screen(logtxt, level='message')
            logger.info(logtxt)
            print_to_screen()


def run_generic_simulation(sim, sim_settings, progress=False):
    """Run a generic PyRETIS simulation.

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
        If True, we will display a progress bar, otherwise, we print
        results to the screen.

    """
    logtxt = 'Running simulation'
    print_to_screen(logtxt, level='info')
    logger.info(logtxt)

    tqd = use_tqdm(progress)
    sim.engine.exe_dir = sim_settings['simulation']['exe-path']
    sim.set_up_output(sim_settings, progress=progress)
    for _ in tqd(sim.run(), desc='Step'):
        pass
    # Write final restart file:
    sim.write_restart(now=True)
    return True


_RUNNERS = {'md-flux': run_md_flux_simulation,
            'md-nve': run_md_simulation,
            'md': run_md_simulation,
            'tis': run_tis_simulation,
            'tis-multiple': run_tis_simulation,
            'retis': run_retis_simulation}


def set_up_simulation(inputfile, runpath):
    """Run all the needed generic set-up.

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
        raise ValueError('Input file "{}" NOT found!'.format(inputfile))

    print_to_screen('\nReading input settings from: {}'.format(inputfile),
                    level='info')
    logger.info('Reading input settings from: %s', inputfile)

    print_to_screen('\nSetting up simulation', level='success')

    sim_settings = parse_settings_file(inputfile)
    sim_settings['simulation']['exe-path'] = runpath

    restart = sim_settings['simulation'].get('restart', None)
    restart_info = None
    if restart is not None:
        print_to_screen('Reading restart file: "{}"'.format(restart),
                        level='warning')
        logger.info('Reading restart file: "%s"', restart)
        restart_info = read_restart_file(restart)
        sim_settings['output']['backup'] = 'append'
        logger.info('Setting output setting "backup" to "append"')

    logtxt = units_from_settings(sim_settings)
    print_to_screen('* {}'.format(logtxt))
    logger.info(logtxt)

    engine = create_engine(sim_settings)
    if engine is not None:
        logtxt = 'Created engine: "{}".'.format(engine)
        print_to_screen('* {}'.format(logtxt))
        logger.info(logtxt)
    else:
        logtxt = 'No engine created.'
        print_to_screen('* {}'.format(logtxt), level='warning')
        logger.info(logtxt)

    logtxt = 'Set up and create system.'
    print_to_screen('* {}'.format(logtxt))
    logger.info(logtxt)
    syst = create_system(sim_settings, engine=engine, restart=restart_info)

    logtxt = 'Set up and create force field.'
    print_to_screen('* {}'.format(logtxt))
    logger.info(logtxt)
    syst.forcefield = create_force_field(sim_settings)
    syst.extra_setup()

    logtxt = 'Set up and create simulation.'
    print_to_screen('* {}'.format(logtxt))
    logger.info(logtxt)
    keyargs = {'system': syst, 'engine': engine}
    sim = create_simulation(sim_settings, keyargs)
    if restart_info is not None:
        sim.load_restart_info(restart_info['simulation'])

    task = sim_settings['simulation']['task'].lower()
    print_to_screen('Will run simulation "{}".'.format(task),
                    level='success')
    logger.info('Setup for simulation "%s" is done.', task)
    runner = _RUNNERS.get(task, run_generic_simulation)
    return runner, sim, syst, sim_settings


def store_simulation_settings(settings, indir, backup):
    """Store the parsed input settings.

    Parameters
    ----------
    settings : dict
        The simulation settings.
    indir : string
        The directory which contains the input script.
    backup : boolean
        If True, an existing settings file will be backed up.

    """
    out_file = os.path.join(indir, 'out.rst')
    rel_file = os.path.relpath(out_file)
    print_to_screen(
        '\nFull settings used for simulation written to: {}'.format(rel_file),
    )
    logger.info('Full simulation settings written to: %s', out_file)
    write_settings_file(settings, out_file, backup=backup)


def soft_exit_ignore(turn_keyboard_interruption_off=True):
    """Manage the KeyboardInterrupt exception.

    Parameters
    ----------
    turn_keyboard_interruption_off : boolean
        If True, instead of regular exiting from the program,
        the file 'EXIT' is created to stop the PyRETIS.

    """
    def soft_exit_handler(signum, frame):  # pylint: disable=unused-argument
        """Handle with a keyboard interruption signal."""
        print_to_screen('Attempting soft exit - terminating soon...')
        open('EXIT', 'w').close()
    if turn_keyboard_interruption_off:
        return signal.signal(signal.SIGINT, soft_exit_handler)
    return signal.signal(signal.SIGINT, signal.default_int_handler)


def main(infile, indir, exe_dir, progress, log_level):
    """Execute PyRETIS.

    Parameters
    ----------
    infile : string
        The input file to open with settings for PyRETIS.
    indir : string
        The folder containing the settings file.
    exe_dir : string
        The directory we are working from.
    progress : boolean
        Determines if we should use a progress bar or not.
    log_level : integer
        Determines if we should display the error traceback or not.

    """
    simulation = None
    system = None
    settings = {}

    try:
        run, simulation, system, settings = set_up_simulation(infile,
                                                              exe_dir)
        store_simulation_settings(settings, indir, True)
        # Run the simulation:
        soft_exit_ignore()
        run(simulation, settings, progress=progress)
        soft_exit_ignore(turn_keyboard_interruption_off=False)
    except Exception as error:  # Exceptions should subclass BaseException.
        logger.error('"%s: %s".', error.__class__.__name__, error.args)
        print_to_screen('ERROR - execution stopped.', level='error')
        print_to_screen(
            'Please see the LOG for the error message and traceback.',
            level='error',
        )
        # Print the traceback to the log-file, but not to the screen.
        screen = logger.handlers[0]
        lvl = screen.level
        screen.setLevel(logging.CRITICAL + 1)
        logger.error(traceback.format_exc())
        screen.setLevel(lvl)
        if log_level <= logging.DEBUG:
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
        store_simulation_settings(settings, indir, False)
        bye_bye_world()


def entry_point():
    """entry_point - The entry point for the pip install of pyretisrun."""
    colorama.init(autoreset=True)
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

    # Define a file logger:
    create_backup(args_dict['log_file'])
    fileh = logging.FileHandler(args_dict['log_file'], mode='a')
    log_levl = getattr(logging, args_dict['log_level'].upper(),
                       logging.INFO)
    fileh.setLevel(log_levl)
    fileh.setFormatter(get_log_formatter(log_levl))
    logger.addHandler(fileh)
    # Here, we just check the python version. PyRETIS should anyway
    # fail before this for python2.
    check_python_version()

    hello_world(input_file, cwd_dir, args_dict['log_file'])
    main(input_file, input_dir, cwd_dir, args_dict['progress'], log_levl)


if __name__ == '__main__':
    entry_point()
