# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file contains functions used for initiation of paths.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

initiate_load (:py:func`.initiate_load`)
    Method that will get the initial path from the output from
    a previous simulation.
"""
import collections
import logging
import os
import shutil
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.core.common import get_path_class
from pyretis.inout.common import print_to_screen
from pyretis.inout.writers import prepare_load, get_writer
from pyretis.tools.recalculate_order import recalculate_order
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['initiate_load']


def initiate_load(simulation, cycle, settings):
    """Initiate paths by loading already generated ones.

    Parameters
    ----------
    simulation : object like :py:class:`.Simulation`
        The simulation we are setting up.
    cycle : integer
        The simulation cycles we are starting at.
    settings : dictionary
        A dictionary with settings for the initiation.
    """
    maxlen = settings['tis']['maxlength']
    klass = get_path_class(simulation.engine.engine_type)
    folder = settings['initial-path'].get('load_folder', 'load')
    for ensemble in simulation.path_ensembles:
        name = ensemble.ensemble_name
        logger.info('Loading data for path ensemble %s:', name)
        print_to_screen('Loading data for path ensemble {}:'.format(name))
        simulation.engine.exe_dir = ensemble.directory['generate']
        path = klass(simulation.rgen, maxlen=maxlen)
        edir = os.path.join(folder, PATH_DIR_FMT.format(ensemble.ensemble))
        if simulation.engine.engine_type == 'internal':
            accept, status = read_path_files(
                path,
                ensemble,
                edir,
                simulation.system,
                simulation.order_function,
                simulation.engine,
            )
        elif simulation.engine.engine_type == 'external':
            accept, status = read_path_files_ext(
                path,
                ensemble,
                edir,
                simulation.order_function,
                simulation.engine,
            )
        else:
            raise ValueError('Unknown engine type!')
        ensemble.add_path_data(path, status, cycle)
        yield accept, path, status


def _load_order_parameters(traj, dirname, system, order_function):
    """Load or recalculate the order parameters.

    Parameters
    ----------
    traj : dictionary
        The trajectory we have loaded. Used here if we are
        re-calculating the order parameter(s).
    dirname : string
        The path to the directory with the input files.
    system : object like :py:class:`.System`
        A system object we can use when calculating the order parameter(s).
    order_function : object like :py:class:`.OrderParameter`
        This can be used to re-calculate order parameters in case
        they are not given.

    Returns
    -------
    out : list
        The order parameters, each item in the list corresponds to a time
        frame.
    """
    order_file_name = os.path.join(dirname, 'order.txt')
    orderfile = prepare_load('pathorder', order_file_name, required=False)
    if orderfile is not None:
        print_to_screen('Loading order parameters')
        order = next(orderfile)
        return order['data'][:, 1:]
    orderdata = []
    print_to_screen('Recalculating order parameters for input path')
    logger.info('Recalculating order parameters for input path')
    for snapshot in traj['data']:
        system.particles.pos = snapshot['pos']
        system.particles.vel = snapshot['vel']
        orderdata.append(order_function.calculate_all(system))
    return orderdata


def _load_order_parameters_ext(traj, dirname, order_function):
    """Load or re-calculate the order parameters.

    For external trajectories, dumping of specific frames from a
    trajectory might be expensive and we here do slightly more work than
    just dumping the frames.

    Parameters
    ----------
    traj : dictionary
        The trajectory we have loaded. Used here if we are
        re-calculating the order parameter(s).
    dirname : string
        The path to the directory with the input files.
    order_function : object like :py:class:`.OrderParameter`
        This can be used to re-calculate order parameters in case
        they are not given.

    Returns
    -------
    out : list
        The order parameters, each item in the list corresponds to a time
        frame.
    """
    order_file_name = os.path.join(dirname, 'order.txt')
    orderfile = prepare_load('pathorder', order_file_name, required=False)
    if orderfile is not None:
        print_to_screen('Loading order parameters from file!')
        order = next(orderfile)
        return order['data'][:, 1:]
    orderdata = []
    print_to_screen('Recalculating order parameters for input path!')
    logger.info('Recalculating order parameters for input path')
    # First get unique files and indexes for them:
    files = collections.OrderedDict()
    for snapshot in traj['data']:
        filename = snapshot[1]
        if filename not in files:
            files[filename] = {'minidx': None, 'maxidx': None,
                               'reverse': snapshot[3]}
        if snapshot[2] is None:
            idx = 0
        else:
            idx = int(snapshot[2])
        minidx = files[filename]['minidx']
        if minidx is None or idx < minidx:
            files[filename]['minidx'] = idx
        maxidx = files[filename]['maxidx']
        if maxidx is None or idx > maxidx:
            files[filename]['maxidx'] = idx
    # ok now we have the files, calculate the order parameters:
    for filename, info in files.items():
        for new_order in recalculate_order(order_function, filename,
                                           reverse=info['reverse'],
                                           maxidx=info['maxidx'],
                                           minidx=info['minidx']):
            orderdata.append(new_order)
    # Store the re-calculated order parameters so we don't have
    # to re-calculate again later:
    write_order_parameters(order_file_name, orderdata)
    return orderdata


def write_order_parameters(order_file_name, orderdata):
    """Store re-calculated order parameters to a file."""
    writer = get_writer('order')
    with open(order_file_name, 'w') as outfile:
        outfile.write('# Cycle: Re-calculated\n')
        outfile.write('{}\n'.format(writer.header))
        for step, data in enumerate(orderdata):
            txt = writer.format_data(step, data)
            outfile.write('{}\n'.format(txt))


def _load_energies_for_path(path, dirname):
    """Load energy data for a path.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        The path we are to set up/fill.
    dirname : string
        The path to the directory with the input files.

    Returns
    -------
    None, but may add energies to the path.
    """
    # Get energies if any:
    energy_file_name = os.path.join(dirname, 'energy.txt')
    energyfile = prepare_load('pathenergy', energy_file_name, required=False)
    if energyfile is not None:
        energy = next(energyfile)
        logger.debug('Energies found')
        print_to_screen('Loading energies')
        path.vpot = [i for i in energy['data']['vpot']]
        path.ekin = [i for i in energy['data']['ekin']]


def _check_path(path, ensemble):
    """Run some checks for the path.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        The path we are to set up/fill.
    ensemble : object like :py:class:`.PathEnsemble`
        The ensemble the path could be added to.
    """
    start, end, _, cross = path.check_interfaces(ensemble.interfaces)
    start_condition = ensemble.start_condition
    accept = True
    status = 'ACC'

    if start != start_condition:
        logger.critical('Initial path for %s start at wrong interface!',
                        ensemble.ensemble_name)
        status = 'SWI'
        accept = False

    if not (end == 'R' or end == 'L'):
        logger.critical('Initial path for %s end at wrong interface!',
                        ensemble.ensemble_name)
        status = 'EWI'
        accept = False
        if ensemble.ensemble == 0 and end == 'L':
            logger.critical('Path for %s ends at LEFT interface!',
                            ensemble.ensemble_name)
    if not cross[1]:
        logger.critical('Initial path for %s did not cross middle interface!',
                        ensemble.ensemble_name)
        status = 'NCR'
        accept = False
    path.status = status
    return accept, status


def _load_trajectory(dirname):
    """Method to set-up and load a trajectory from a file.

    Parameters
    ----------
    dirname : string
        Directory where we can find the trajectory file(s).

    Returns
    -------
    traj : dict
        A dictionary containing the trajectory information. Here,
        the trajectory information is name of files with indices and
        information about velocity direction.
    """
    trajfile = prepare_load(
        'pathtrajint',
        os.path.join(dirname, 'traj.txt'),
        required=True
    )
    # Just get the first trajectory:
    traj = next(trajfile)
    return traj


def read_path_files(path, ensemble, dirname, system, order_function, engine):
    """Read data needed for a path from a directory.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        The path we are to set up/fill.
    ensemble : object like :py:class:`.PathEnsemble`
        The ensemble the path could be added to.
    dirname : string
        The path to the directory with the input files.
    system : object like :py:class:`.System`
        A system object we can use when calculating the order parameter(s).
    order_function : object like :py:class:`.OrderParameter`
        This can be used to re-calculate order parameters in case
        they are not given.
    engine : object like :py:class:`.EngineBase`
        The engine we use for the dynamics.
    """
    left, _, right = ensemble.interfaces
    traj = _load_trajectory(dirname)
    orderdata = _load_order_parameters(traj, dirname, system, order_function)

    # Add to path :-)
    print_to_screen('Creating path from files')
    logger.debug('Creating path from files')
    for snapshot, orderi in zip(traj['data'], orderdata):
        phase_point = {'order': orderi,
                       'pos': snapshot['pos'],
                       'vel': snapshot['vel'],
                       'vpot': None,
                       'ekin': None}
        engine.add_to_path(
            path,
            phase_point,
            left,
            right
        )
    _load_energies_for_path(path, dirname)
    path.generated = ('re', 0, 0, 0)
    return _check_path(path, ensemble)


def _load_external_trajectory(dirname, engine):
    """Method to set-up and load an external trajectory.

    Here, we also do some moving of files to set up for a path
    simulation.

    Parameters
    ----------
    dirname : string
        Directory where we can find the trajectory file(s).
    engine : object like :py:class:`.ExternalMDEngine`
        The engine we use, here it is used to access the directories
        for the new simulation.

    Returns
    -------
    traj : dict
        A dictionary containing the trajectory information. Here,
        the trajectory information is name of files with indices and
        information about velocity direction.
    """
    traj_file_name = os.path.join(dirname, 'traj.txt')
    trajfile = prepare_load('pathtrajext', traj_file_name, required=True)
    # Just get the first trajectory:
    traj = next(trajfile)
    # Hard-copy the files. Here we assume that they are stored
    # in an folder called accepted and that we can get the **correct**
    # names from the traj.txt file!
    files = set([])
    for snapshot in traj['data']:
        filename = os.path.join(os.path.abspath(dirname),
                                'accepted', snapshot[1])
        files.add(filename)
    print_to_screen('Copying trajectory files')
    for filename in files:
        logger.debug('Copying %s -> %s', filename, engine.exe_dir)
        shutil.copy(filename, engine.exe_dir)
    # update trajectory to use full path names:
    for i, snapshot in enumerate(traj['data']):
        config = os.path.join(engine.exe_dir, snapshot[1])
        traj['data'][i][1] = config
        reverse = (int(snapshot[3]) == -1)
        idx = int(snapshot[2])
        if idx < 0:
            idx = None
        traj['data'][i][2] = idx
        traj['data'][i][3] = reverse
    return traj


def read_path_files_ext(path, ensemble, dirname, order_function, engine):
    """Read data needed for a path from a directory.

    Parameters
    ----------
    path : object like :py:class:`.PathExt`
        The path we are to set up/fill.
    ensemble : object like :py:class:`.PathEnsembleExt`
        The ensemble the path could be added to.
    dirname : string
        The path to the directory with the input files.
    order_function : object like :py:class:`.OrderParameter`
        This can be used to re-calculate order parameters in case
        they are not given.
    engine : object like :py:class:`.ExternalMDEngine`
        The engine we use for the dynamics.
    """
    left, _, right = ensemble.interfaces
    traj = _load_external_trajectory(dirname, engine)
    orderdata = _load_order_parameters_ext(traj, dirname, order_function)
    # Add to path :-)
    print_to_screen('Creating path from files')
    logger.debug('Creating path from files')
    for snapshot, orderi in zip(traj['data'], orderdata):
        phase_point = {'order': orderi,
                       'pos': (snapshot[1], snapshot[2]),
                       'vel': snapshot[3],
                       'vpot': None,
                       'ekin': None}
        engine.add_to_path(
            path,
            phase_point,
            left,
            right
        )
    _load_energies_for_path(path, dirname)
    path.generated = ('re', 0, 0, 0)
    return _check_path(path, ensemble)
