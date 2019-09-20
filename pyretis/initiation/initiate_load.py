# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Method for initiating paths by loading from previous simulation(s).

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

initiate_load (:py:func:`.initiate_load`)
    A method that will get the initial path from the output of
    a previous simulation.
"""
import collections
import errno
import logging
import os
import shutil
import mdtraj
from pyretis.inout.formats.xyz import read_xyz_file, convert_snapshot
from pyretis.core.pathensemble import generate_ensemble_name
from pyretis.inout import print_to_screen
from pyretis.inout.common import make_dirs
from pyretis.inout.formats.order import OrderPathFile, OrderFile
from pyretis.inout.formats.energy import EnergyPathFile
from pyretis.inout.formats.path import PathIntFile, PathExtFile
from pyretis.core.path import Path, paste_paths
from pyretis.tools.recalculate_order import recalculate_order
from pyretis.engines.cp2k import read_cp2k_box
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


__all__ = ['initiate_load']


def initiate_load(simulation, cycle, settings):
    """Initialise paths by loading already generated ones.

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
    folder = settings['initial-path'].get('load_folder', 'load')

    if not os.path.exists(folder):
        logger.critical('Load folder "%s" not found!', folder)
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                                folder)

    for path_ensemble in simulation.path_ensembles:
        name = path_ensemble.ensemble_name
        logger.info('Loading data for path path ensemble %s:', name)
        print_to_screen('Loading data for path path ensemble {}:'.format(name))
        simulation.engine.exe_dir = path_ensemble.directory['generate']
        path = Path(simulation.rgen, maxlen=maxlen)
        path.generated = ('re', 0, 0, 0)  # To be eventually replaced.
        edir = os.path.join(
            folder,
            generate_ensemble_name(path_ensemble.ensemble_number))

        if not os.path.exists(os.path.join(edir, 'traj.txt')):
            logger.info('Input Load missing')
            print_to_screen('No traj.txt file found in {}, attempt generate!'
                            .format(edir))
            # Make sure the files are where they are supposed to be:
            _do_the_dirty_load_job(folder, edir)
            # Generate a traj.txt file for the path ensemble:

            logger.warning('Input Load missing')
            print_to_screen('No traj.txt file found in {}, attempt generate!'
                            .format(edir))
            _generate_traj_txt_from_ext(edir, simulation.system,
                                        simulation.engine)
            path.set_move('ld')

        if simulation.engine.engine_type == 'internal':
            accept, status = read_path_files(
                path,
                path_ensemble,
                edir,
                simulation.system,
                simulation.order_function,
                simulation.engine
            )
        elif simulation.engine.engine_type == 'external':
            accept, status = read_path_files_ext(
                path,
                path_ensemble,
                edir,
                simulation.system,
                simulation.order_function,
                simulation.engine
            )
        else:
            raise ValueError('Unknown engine type!')

        # If a path is not acceptable, than here we try to rearrange it such
        # to satisfy each ensemble definition
        if not accept and path.get_move() == 'ld':  # Let's try to fix the path
            path, (accept, status) = reorderframes(path, path_ensemble)
            path.status = status
            if status != 'ACC':
                msg = 'Path stored in folder {} does not satisfy the relative'\
                      ' ensemble ({}) definition. ' \
                      'The given path has a min of {} and a max of {} while '\
                      'the relative interface are located at {}, {} and {}. '\
                      'NOTE: points withing state B are not used.'\
                      .format(edir, path_ensemble.ensemble_number,
                              path.ordermin[0], path.ordermax[0],
                              path_ensemble.interfaces[0],
                              path_ensemble.interfaces[1],
                              path_ensemble.interfaces[2])
                raise ValueError(msg)
        path_ensemble.add_path_data(path, status, cycle)
        path_ensemble.last_path = path
        yield accept, path, status, path_ensemble


def reorderframes(path, path_ensemble):
    """Re-order the phase points in the input path.

    This function assumes that the path needs to be fixed.
    It checks for the validity of the path and keeps only the frames
    that are useful for the region to explore e.g. [0^-].

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        The path we try to fix.
    path_ensemble : object like :py:class:`.PathEnsembleExt`
        The path ensemble the path could be added to.

    """
    slave_path = path.copy()
    left, _, right = path_ensemble.interfaces
    # If the path is from L to R, we order the phase points according
    # to the order parameter.
    # If the path is from R to L (e.g. for the [0^-] ensemble),
    # a reversed path is generated.
    # If the path goes from L and stops, it is doubled to create a
    # L to L path.
    # If the path goes from R and stops, it is doubled to create a
    # R to R path.
    if path_ensemble.start_condition == 'R':
        path.sorting('order', reverse=False)
        slave_path.sorting('order', reverse=False)
        path = paste_paths(path, slave_path)

    if path_ensemble.start_condition == 'L':
        path.sorting('order', reverse=False)

        if path.get_end_point(left, right) not in {'L', 'R'}:
            slave_path = path.copy()
            path.sorting('order', reverse=True)
            slave_path.sorting('order', reverse=True)
            path = paste_paths(path, slave_path)
    path.set_move('ld')

    clean_path(path, path_ensemble)

    return path, _check_path(path, path_ensemble)


def clean_path(path, path_ensemble):
    """Remove useless frames from a path.

    This function remove phasepoints from a path that are
    not needed (e.g. the one in stable states)

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        The path we try to fix.
    path_ensemble : object like :py:class:`.PathEnsembleExt`
        The path ensemble the path could be added to.

    """
    left, _, right = path_ensemble.interfaces
    # Set up initial guest for the crossing point search.
    # 0,1,2,3,4 is a safe initial guess to eventually avoid empty paths out.
    # Such cases shall be intercepted by _check_path and not give an error
    # here.

    # Initialize
    ph_min = path.phasepoints[0].copy()
    ph_max = path.phasepoints[0].copy()
    dist_right = float('inf')
    dist_left = float('inf')

    # First, find the two nearest crossing points to the 0 interface.
    for i, phasepoint in enumerate(path.phasepoints):
        # From left:
        if phasepoint.order[0] < left:
            if left - phasepoint.order[0] <= dist_left:
                dist_left = left - phasepoint.order[0]
                ph_min = phasepoint.copy()
        # From right:
        if phasepoint.order[0] >= right:
            if phasepoint.order[0] - right < dist_right:
                dist_right = phasepoint.order[0] - right
                ph_max = phasepoint.copy()

    # Delete unnecessary frames.
    erase_list = []
    for i, phasepoint in enumerate(path.phasepoints):
        if not left <= phasepoint.order[0] < right:
            erase_list.append(i)

    # Erase the largest elements first to avoid counting problems.
    erase_list.reverse()

    # Happy Ending.
    for i in erase_list:
        path.delete(i)

    # The path has to cope with the ensemble requirements.
    if path_ensemble.start_condition == 'R':
        path.phasepoints.insert(0, ph_max.copy())
        path.phasepoints.append(ph_max.copy())
    if path_ensemble.start_condition == 'L':
        path.phasepoints.insert(0, ph_min.copy())
        path.phasepoints.append(ph_min.copy())


def _do_the_dirty_load_job(mainfolder, edir):
    """Copy the files to a place where PyRETIS expects them to be.

    Parameters
    ----------
    mainfolder : string
        The path of the main load directory with frame/trajectory
        files.
    edir : string
        The path of the path ensemble load directory with
        frame/trajectory files.

    """
    formats = ['.xyz', '.gro', '.xtc', '.trr', '.txt']

    listoffiles = [i.name for i in os.scandir(mainfolder) if i.is_file()]
    traj_files = [i for i in listoffiles if i[-4:] in formats]

    if not os.path.exists(edir):
        if not traj_files:
            logger.critical('No files to load in %s', mainfolder)
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                                    mainfolder)
        else:
            make_dirs(os.path.join(edir, 'accepted'))
            for filei in traj_files:
                shutil.copy(
                    os.path.join(mainfolder, filei),
                    os.path.join(edir, 'accepted', filei)
                )
    elif not os.path.exists(os.path.join(edir, 'accepted')):
        listoffiles = [i.name for i in os.scandir(edir) if i.is_file()]
        traj_files_ens = [i for i in listoffiles if i[-4:] in formats]
        if not traj_files_ens and not traj_files:
            logger.critical('No files to load in %s', edir)
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                                    edir)
        else:
            make_dirs(os.path.join(edir, 'accepted'))
            if not traj_files_ens:
                for filei in traj_files:
                    shutil.copy(
                        os.path.join(mainfolder, filei),
                        os.path.join(edir, 'accepted', filei)
                    )
            else:
                for filei in traj_files_ens:
                    os.rename(
                        os.path.join(edir, filei),
                        os.path.join(edir, 'accepted', filei)
                    )


def _generate_traj_txt_from_ext(dirname, system, engine):
    """Generate a traj.txt file in the path ensemble folder.

    Parameters
    ----------
    dirname : string
        The path of the path ensemble directory with
        trajectory files.
    system : object like :py:class:`.System`
        A system object we can use when calculating the order
        parameter(s).
    engine : object like :py:class:`.Engine`
        The engine used for the simulation. It is used here to
        reference a topology, if needed, for mdtraj.

    """
    trajexts = ['.xyz', '.gro', '.trr', '.xtc', '.txt']
    load_file = os.path.join(dirname, 'traj.txt')

    traj_files = sorted([i for i in
                         os.listdir(os.path.join(dirname, 'accepted'))
                         if i[-4:] in trajexts])

    path = Path()
    # Load Sparse works also from multiple initial trajectories
    # both internally and externally
    if system.particles.particle_type == 'internal':
        for filei in traj_files:
            if filei[-4:] == '.xyz':
                for snap in read_xyz_file(os.path.join(dirname,
                                                       'accepted', filei)):
                    _, pos, vel, _ = convert_snapshot(snap)
                    snapshot = {'pos': pos, 'vel': vel}
                    phase_point = system_from_snapshot(system, snapshot)
                    path.append(phase_point)
            if filei[-4:] == '.txt':
                traj = _load_trajectory(os.path.join(dirname, 'accepted'),
                                        filei)
                for snapshot in traj['data']:
                    snapshot = {'pos': snapshot['pos'],
                                'vel': snapshot['vel']}
                    phase_point = system_from_snapshot(system, snapshot)
                    path.append(phase_point)

        with PathIntFile(load_file, 'w', backup=True) as trajfile:
            trajfile.output(0, (path, 'ACC'))
    else:
        for tfile in traj_files:
            if tfile[-4:] == '.txt':
                continue
            all_tfile = os.path.join(dirname, 'accepted', tfile)
            if tfile[-4:] == '.xyz':
                for i, snap in enumerate(read_xyz_file(all_tfile)):
                    snapshot = {'pos': (tfile, i), 'vel': False}
                    phase_point = system_from_snapshot(system, snapshot)
                    path.append(phase_point)
            else:
                if tfile[-4:] == '.gro':
                    md_file = mdtraj.load(all_tfile)
                else:
                    md_file = mdtraj.load(all_tfile, top=system.particles.top)

                for i in range(0, md_file.n_frames):
                    snapshot = {'pos': (tfile, i), 'vel': False}
                    phase_point = system_from_snapshot(system, snapshot)
                    path.append(phase_point)
        with PathExtFile(load_file, 'w', backup=True) as pathfile:
            pathfile.output(0, (path, 'ACC'))


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
        A system object we can use when calculating the order
        parameter(s).
    order_function : object like :py:class:`.OrderParameter`
        This can be used to re-calculate order parameters in case
        they are not given.

    Returns
    -------
    out : list
        The order parameters, each item in the list corresponds to a
        time frame.

    """
    order_file_name = os.path.join(dirname, 'order.txt')
    try:
        with OrderPathFile(order_file_name, 'r') as orderfile:
            print_to_screen('Loading order parameters.')
            order = next(orderfile.load())
            return order['data'][:, 1:]
    except FileNotFoundError:
        print_to_screen('Could not read file: {}'.format(order_file_name))
    orderdata = []
    print_to_screen('Recalculating order parameters for input path.')
    logger.info('Recalculating order parameters for input path.')
    for snapshot in traj['data']:
        system.particles.pos = snapshot['pos']
        system.particles.vel = snapshot['vel']
        orderdata.append(order_function.calculate(system))
    return orderdata


def _load_order_parameters_ext(traj, dirname, order_function, system, engine):
    """Load or re-calculate the order parameters.

    For external trajectories, dumping of specific frames from a
    trajectory might be expensive and we here do slightly more work
    than just dumping the frames.

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
    system : object like :py:class:`.System`
        A system object we can use when calculating the order
        parameter(s).

    Returns
    -------
    out : list
        The order parameters, each item in the list corresponds to
        a time frame.

    """
    order_file_main_name = os.path.join(dirname, '../', 'order.txt')
    order_file_name = os.path.join(dirname, 'order.txt')
    if os.path.isfile(order_file_name):
        with OrderPathFile(order_file_name, 'r') as orderfile:
            print_to_screen('Loading order parameters.')
            order = next(orderfile.load())
            return order['data'][:, 1:]
    elif os.path.isfile(order_file_main_name):
        with OrderPathFile(order_file_main_name, 'r') as orderfile:
            print_to_screen('Loading order parameters from main directory.')
            order = next(orderfile.load())
            # Store the re-calculated order parameters so we don't have
            # to re-calculate again later:
            write_order_parameters(order_file_name, order['data'][:, 1:])
            return order['data'][:, 1:]
    else:
        print_to_screen('Could not read file: {}'.format(order_file_name))

    orderdata = []
    print_to_screen('Recalculating order parameters for input path.')
    logger.info('Recalculating order parameters for input path.')
    # First get unique files and indices for them:
    files = collections.OrderedDict()
    for snapshot in traj['data']:
        filename = snapshot[1]
        if filename not in files:
            files[filename] = {'minidx': None, 'maxidx': None,
                               'reverse': snapshot[3]}
        idx = int(snapshot[2])
        minidx = files[filename]['minidx']
        if minidx is None or idx < minidx:
            files[filename]['minidx'] = idx
        maxidx = files[filename]['maxidx']
        if maxidx is None or idx > maxidx:
            files[filename]['maxidx'] = idx
    # Ok, now we have the files, calculate the order parameters:
    for filename, info in files.items():
        if hasattr(system.particles, 'top'):  # mdtraj specific.
            info['top'] = system.particles.top
        if filename[-4:] == '.xyz':           # CP2K specific NVE.
            info['box'], _ = read_cp2k_box(engine.input_files['template'])
        for new_order in recalculate_order(order_function, filename, info):
            orderdata.append(new_order)

    # Store the re-calculated order parameters so we don't have
    # to re-calculate again later:
    write_order_parameters(order_file_name, orderdata)
    # Make a copy in the main load folder
    write_order_parameters(order_file_main_name, orderdata)
    return orderdata


def write_order_parameters(order_file_name, orderdata):
    """Store re-calculated order parameters to a file."""
    with OrderFile(order_file_name, 'w') as orderfile:
        orderfile.write('# Re-calculated order parameters.')
        for step, data in enumerate(orderdata):
            orderfile.output(step, data)


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
    try:
        with EnergyPathFile(energy_file_name, 'r') as energyfile:
            print_to_screen('Loading energy data.')
            energy = next(energyfile.load())
            path.update_energies(
                [i for i in energy['data']['ekin']],
                [i for i in energy['data']['vpot']]
            )
    except FileNotFoundError:
        print_to_screen('Could not read file: {}'.format(energy_file_name))
        print_to_screen('Energies are not set.')


def _check_path(path, path_ensemble):
    """Run some checks for the path.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        The path we are to set up/fill.
    path_ensemble : object like :py:class:`.PathEnsemble`
        The path ensemble the path could be added to.

    """
    start, end, _, cross = path.check_interfaces(path_ensemble.interfaces)
    start_condition = path_ensemble.start_condition
    accept = True
    status = 'ACC'

    if start != start_condition:
        logger.critical('Initial path for %s start at wrong interface!',
                        path_ensemble.ensemble_name)
        status = 'SWI'
        accept = False

    if end not in ('R', 'L'):
        logger.critical('Initial path for %s end at wrong interface!',
                        path_ensemble.ensemble_name)
        status = 'EWI'
        accept = False
    if not cross[1]:
        logger.critical('Initial path for %s did not cross middle interface!',
                        path_ensemble.ensemble_name)
        status = 'NCR'
        accept = False
    path.status = status
    return accept, status


def _load_trajectory(dirname, filename='traj.txt'):
    """Set-up and load a trajectory from a file.

    Parameters
    ----------
    dirname : string
        The directory where we can find the trajectory file(s).
    filename : string
        The name of the trajectory file.

    Returns
    -------
    traj : dict
        A dictionary containing the trajectory information.
        That is, position and velocity for each frame.

    """
    with PathIntFile(os.path.join(dirname, filename), 'r') as trajfile:
        # Just get the first trajectory:
        traj = next(trajfile.load())
    return traj


def read_path_files(path, path_ensemble, dirname, system, order_function,
                    engine):
    """Read data needed for a path from a directory.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        The path we are to set up/fill.
    path_ensemble : object like :py:class:`.PathEnsemble`
        The path ensemble the path could be added to.
    dirname : string
        The path to the directory with the input files.
    system : object like :py:class:`.System`
        A system object we can use when calculating the order
        parameter(s).
    order_function : object like :py:class:`.OrderParameter`
        This can be used to re-calculate order parameters in case
        they are not given.
    engine : object like :py:class:`.EngineBase`
        The engine we use for the dynamics.

    """
    left, _, right = path_ensemble.interfaces
    traj = _load_trajectory(dirname)
    orderdata = _load_order_parameters(traj, dirname, system, order_function)

    # Add to path:
    print_to_screen('Creating path from files.')
    logger.debug('Creating path from files.')
    for snapshot, orderi in zip(traj['data'], orderdata):
        snapshot = {'order': orderi, 'pos': snapshot['pos'],
                    'vel': snapshot['vel']}
        phase_point = system_from_snapshot(system, snapshot)
        engine.add_to_path(
            path,
            phase_point,
            left,
            right
        )
    _load_energies_for_path(path, dirname)
    return _check_path(path, path_ensemble)


def _load_external_trajectory(dirname, engine):
    """Set-up and load an external trajectory.

    Here, we also do some moving of files to set up for a path
    simulation.

    Parameters
    ----------
    dirname : string
        The directory where we can find the trajectory file(s).
    engine : object like :py:class:`.ExternalMDEngine`
        The engine we use, here it is used to access the directories
        for the new simulation.

    Returns
    -------
    traj : dict
        A dictionary containing the trajectory information. Here,
        the trajectory information is a list of files with indices and
        information about velocity direction.

    """
    traj_file_name = os.path.join(dirname, 'traj.txt')
    with PathExtFile(traj_file_name, 'r') as trajfile:
        # Just get the first trajectory:
        traj = next(trajfile.load())
        # Hard-copy the files. Here we assume that they are stored
        # in an folder called "accepted" and that we can get the
        # **correct** names from the traj.txt file!
        files = set([])
        for snapshot in traj['data']:
            filename = os.path.join(os.path.abspath(dirname),
                                    'accepted', snapshot[1])
            files.add(filename)
        print_to_screen('Copying trajectory files.')
        for filename in files:
            logger.debug('Copying %s -> %s', filename, engine.exe_dir)
            shutil.copy(filename, engine.exe_dir)
        # Update trajectory to use full path names:
        for i, snapshot in enumerate(traj['data']):
            config = os.path.join(engine.exe_dir, snapshot[1])
            traj['data'][i][1] = config
            reverse = (int(snapshot[3]) == -1)
            idx = int(snapshot[2])
            traj['data'][i][2] = idx
            traj['data'][i][3] = reverse
        return traj


def read_path_files_ext(path, path_ensemble, dirname, system, order_function,
                        engine):
    """Read data needed for a path from a directory.

    Parameters
    ----------
    path : object like :py:class:`.Path`
        The path we are to set up/fill.
    path_ensemble : object like :py:class:`.PathEnsembleExt`
        The path ensemble the path could be added to.
    dirname : string
        The path to the directory with the input files.
    system : object like :py:class:`.System`
        A system object we can use when calculating the order parameter(s).
    order_function : object like :py:class:`.OrderParameter`
        This can be used to re-calculate order parameters in case
        they are not given.
    engine : object like :py:class:`.ExternalMDEngine`
        The engine we use for the dynamics.

    """
    left, _, right = path_ensemble.interfaces
    traj = _load_external_trajectory(dirname, engine)
    orderdata = _load_order_parameters_ext(traj, dirname,
                                           order_function, system, engine)
    # Add to path:
    print_to_screen('Creating path from files.')
    logger.debug('Creating path from files.')
    for snapshot, order in zip(traj['data'], orderdata):
        snapshot = {'order': order,
                    'pos': (snapshot[1], snapshot[2]),
                    'vel': snapshot[3],
                    'vpot': None,
                    'ekin': None}
        phase_point = system_from_snapshot(system, snapshot)
        engine.add_to_path(
            path,
            phase_point,
            left,
            right
        )
    _load_energies_for_path(path, dirname)
    return _check_path(path, path_ensemble)


def system_from_snapshot(system, snapshot):
    """Create a system from a given snapshot."""
    system_copy = system.copy()
    system_copy.particles.ekin = snapshot.get('ekin', None)
    system_copy.particles.vpot = snapshot.get('vpot', None)
    system_copy.order = snapshot.get('order', None)
    system_copy.particles.set_pos(snapshot.get('pos', None))
    system_copy.particles.set_vel(snapshot.get('vel', None))
    return system_copy
