# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""
Example test for an interface for pyretis and a external MD package.

Here we test the following:

1. That we can run plain MD forward in time.

2. That we after performing 1, can reverse the velocities
   and end up back at the starting point.

3. That we can generate several trajectories.
"""
import os
import numpy as np
from pyretis.core import Box
from pyretis.core.particles import ParticlesExt
from pyretis.integrators import GromacsExt, ExternalScript
from pyretis.integrators.gromacs import read_gromos96_file
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import create_system
from pyretis.inout.settings import create_orderparameter
from pyretis.inout.common import make_dirs
from matplotlib import pyplot as plt


def compare_g96_files(file1, file2, box, negvel=False):
    """Compare two g96 files.

    Parameters
    ----------
    file1 : string
        First file to open.
    file2 : string
        Second file to open.
    box : object like pyretis.core.box
        This is used to handle the periodic boundaries.
    negvel : boolean
        If True, we flip the velocities in file1.

    Returns
    -------
    mse_x : float
        Mean square error for positions.
    mse_v : float
        Mean square error for velocities.
    """
    _, xyz1, vel1 = read_gromos96_file(file1)
    _, xyz2, vel2 = read_gromos96_file(file2)
    delta = xyz2 - xyz1
    delta = box.pbc_dist_matrix(delta)
    rsq = np.einsum('ij, ij->i', delta, delta)
    mse_x = rsq.mean()
    if negvel:
        delta_v = vel2 + vel1
    else:
        delta_v = vel2 - vel1
    rsq_v = np.einsum('ij, ij->i', delta_v, delta_v)
    mse_v = rsq_v.mean()
    print('MSE positions between {} and {}: {}'.format(file1, file2, mse_x))
    print('MSE velocity between {} and {}: {}'.format(file1, file2, mse_v))
    return mse_x, mse_v


def read_xvg_file(filename):
    """Return data in xvg file as numpy array."""
    data = []
    legends = []
    with open(filename, 'r') as fileh:
        for lines in fileh:
            if lines.startswith('@ s'):
                legend = lines.split()[-1]
                legend.replace('"', '')
                legends.append(legend)
            else:
                if lines.startswith('#') or lines.startswith('@'):
                    pass
                else:
                    data.append([float(i) for i in lines.split()])
    data = np.array(data)
    data_dict = {'step': data[:, 0]}
    for i, key in enumerate(legends):
        data_dict[key] = data[:, i+1]
    return data_dict


def compare_energies(xvg1, xvg2, reverse=False):
    """Compare the energy output in two xvg-files.

    Parameters
    ----------
    xvg1 : string
        The first file to open.
    xvg2 : string
        The second file to open.
    reverse : boolean
        If True, we are comparing time reversed results.
    """
    print('Reading {}'.format(xvg1))
    energy1 = read_xvg_file(xvg1)
    if reverse:
        for key, val in energy1.items():
            energy1[key] = val[::-1]
    print('Data found: {}'.format(energy1.keys()))
    print('Reading {}'.format(xvg2))
    energy2 = read_xvg_file(xvg2)
    print('Data found: {}'.format(energy2.keys()))
    delta = {}
    for key in energy1:
        data1 = energy1[key]
        if key == 'step':
            continue
        if key in energy2:
            data2 = energy2[key]
            row = min(len(data1), len(data2))
            delta[key] = data1[:row] - data2[:row]
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    for key, val in delta.items():
        ax1.plot(val, label=key)
    ax1.set_xlabel('Step')
    ax1.legend()
    ax1.set_ylabel('Energy difference')


def compare_frames(path1, path2, reverse=False):
    """Compare frames in two directories.

    Parameters
    ----------
    path1 : string
        Path to folder with frames for first trajectory.
    path2 : string
        Path to folder with frames for second trajectory.
    reverse : boolean
        If True, we are comparing time reversed results.
    """
    box = Box([2.384999990, 2.384999990, 2.384999990])
    files1 = []
    files2 = []
    for files in os.listdir(path1):
        if files.endswith('.g96') and files.startswith('frame'):
            files1.append(os.path.join(path1, files))
            files2.append(os.path.join(path2, files))
    files1 = sorted(files1)
    files2 = sorted(files2)
    if reverse:
        files1 = reversed(files1)
    all_mse_x = []
    all_mse_v = []
    for file1, file2 in zip(files1, files2):
        mse_x, mse_v = compare_g96_files(file1, file2, box, negvel=reverse)
        all_mse_x.append(mse_x)
        all_mse_v.append(mse_v)
    print('Average MSE positions: {}'.format(np.average(all_mse_x)))
    print('Average MSE velocity: {}'.format(np.average(all_mse_v)))
    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    ax1.set_xlabel('Step')
    ax1.set_ylabel('MSE position')
    ax2.set_xlabel('Step')
    ax2.set_ylabel('MSE velocity')
    ax1.plot(all_mse_x)
    ax2.plot(all_mse_v)

def compare_results(path1, path2, out_files, reverse):
    """Compare gromacs results from simulations in two paths.

    Parameters
    ----------
    path1 : string
        Path to folder with frames for first trajectory.
    path2 : string
        Path to folder with frames for second trajectory.
    out_files : dict
        A dict with files from the ouput when running the
        gromacs simulation with pyretis.
    reverse : boolean
        If True, we are comparing time reversed results.
    """
    external = ExternalScript('For executing commands', None, None, None)

    cmd = ['gmx_5.1.4', 'trjconv', '-f', out_files['trr'],
           '-s', out_files['tpr'], '-o', 'frame.g96', '-sep',
           '-nzero', '5']
    external.execute_command(cmd, inputs=b'0', cwd=path1)

    cmd = ['gmx_5.1.4', 'energy', '-f', out_files['edr']]
    external.execute_command(cmd, inputs=b'1 2 3 4 5 6 7 8', cwd=path1)

    compare_frames(path1, os.path.join(path2, 'frames'),
                   reverse=reverse)

    compare_energies(os.path.join(path1, 'energy.xvg'),
                     os.path.join(path2, 'energy.xvg'),
                     reverse=reverse)
    plt.show()



def run_forward(gro, system, order_function):
    """Test implementation of gromacs integrator.

    This test will run a gromacs simulation with starting and stopping
    forward in time and compare the output with the results from a
    pure gromacs simulation with the same output frequency and other
    settings.

    Parameters
    ----------
    gro : object like :py:class:`pyretis.integrators.gromacs.GromacsExt`
        The object which handles gromacs integration.
    system : object like :py:class:`pyretis.core.system.System`
        The system we are studying.
    """
    exe_path = os.path.join(os.getcwd(), 'trajf')
    make_dirs(exe_path)
    plain_path = os.path.join(os.getcwd(), 'plain-md')
    # Test 1:
    # We have performed a plain MD simulation with gromacs, starting from
    # initial.g96 for 1000 steps. We now do the same with start and
    # stopping:
    initial = os.path.join(os.getcwd(), 'initial.g96')

    local_settings = {'steps': 1000 // gro.subcycles}
    system.particles.set_pos((initial, 0))
    system.particles.set_vel((initial, 0))
    out_files, order = gro.execute_until(system, order_function,
                                         local_settings,
                                         reverse=False,
                                         exe_dir=exe_path)

    compare_results(exe_path, plain_path, out_files, False)
    return out_files, order


def run_reverse(gro, system, order_function):
    """Test implementation of gromacs integrator.

    This test will run a gromacs simulation with starting and stopping
    backward in time and compare the output with the results from a
    gromacs simulation with the same output frequency and other settings.

    Parameters
    ----------
    gro : object like :py:class:`pyretis.integrators.gromacs.GromacsExt`
        The object which handles gromacs integration.
    system : object like :py:class:`pyretis.core.system.System`
        The system we are studying.
    """
    exe_path = os.path.join(os.getcwd(), 'trajb')
    make_dirs(exe_path)
    plain_path = os.path.join(os.getcwd(), 'plain-md')
    local_settings = {'steps': 1000 // gro.subcycles}
    # Extract last frame from the plain-md trr as a starting point:
    initial = os.path.join(exe_path, 'initial.g96')
    gro.get_trr_frame(os.path.join(plain_path, 'traj.trr'),
                      os.path.join(plain_path, 'topol.tpr'),
                      local_settings['steps'], initial)
    # Run backwards from this frame:
    system.particles.set_pos((initial, 0))
    system.particles.set_vel((initial, 0))
    out_files, order = gro.execute_until(system, order_function,
                                         local_settings,
                                         reverse=True,
                                         exe_dir=exe_path)
    compare_results(exe_path, plain_path, out_files, True)
    return out_files, order



def do_setup(md_settings):
    """Do initial setup needed for running the test.

    Parameters
    ----------
    md_settings : dict
        A dict containing settings for the gromacs integrator.

    Returns
    -------
    system : object like :py:class`pyretis.core.system.System`
        A system which we are integrating. It contains information
        about the order parameter and how to calculate it.
    gro : object like :py:class:`pyretis.integrators.gromacs.GromacsExt`
        The object used for interfacing gromacs.
    """
    settings = {}

    settings['system'] = {'units': 'gromacs',
                          'temperature': 200,
                          'dimensions': 3}

    settings['particles'] = {'position': {'file': 'ext_input/conf.gro'}}

    settings['orderparameter'] = {'class': 'Position',
                                  'index': 1472,
                                  'name': 'Gromacs distance',
                                  'periodic': True,
                                  'dim': 'z'}
    create_conversion_factors(settings['system']['units'])

    system = create_system(settings)
    # Transition to new particle class
    particles = ParticlesExt(dim=system.get_dim())
    for p in system.particles:
        particles.add_particle(p['pos'], p['vel'], p['force'],
                               mass=p['mass'], name=p['name'], ptype=p['type'])
    system.particles = particles
    # Transition done!
    order_function = create_orderparameter(settings)

    input_dir = os.path.join(os.getcwd(), 'ext_input')

    input_files = {'configuration': 'conf.g96',
                   'input': 'grompp.mdp',
                   'topology': 'topol.top'}
    gro = GromacsExt('gmx_5.1.4', input_dir, input_files,
                     md_settings['timestep'], md_settings['subcycles'])
    return system, order_function, gro


if __name__ == '__main__':
    md_settings = {'subcycles': 5, 'timestep': 0.002}
    sys, order_fun, grom = do_setup(md_settings)
    out, orderp = run_forward(grom, sys, order_fun)
    out, orderp = run_reverse(grom, sys, order_fun)

