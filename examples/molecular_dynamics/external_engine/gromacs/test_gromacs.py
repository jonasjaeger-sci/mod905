# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""
Example test for an interface for PyRETIS and an external MD package.

Here we test the following:

1. That we can run plain MD forward in time.

2. That we after performing 1, can reverse the velocities
   and end up back at the starting point.
"""
import os
import subprocess
import numpy as np
from pyretis.core import Box
from pyretis.core.path import PathExt
from pyretis.engines.gromacs import read_gromos96_file
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import (create_system, create_engine,
                                    create_orderparameter)
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
    box : object like :py:class:`.box`
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
                legend = lines.split('legend')[-1].strip()
                legends.append(legend.replace('"', ''))
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


def make_msd_plot(mse_x, mse_v):
    """Just plot the results."""
    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    ax1.set_xlabel('Step')
    ax1.set_ylabel('MSE position')
    ax2.set_xlabel('Step')
    ax2.set_ylabel('MSE velocity')
    ax1.plot(mse_x)
    ax2.plot(mse_v)


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
        files1 = files1[::-1]
    all_mse_x = []
    all_mse_v = []
    for file1, file2 in zip(files1, files2):
        mse_x, mse_v = compare_g96_files(file1, file2, box, negvel=reverse)
        all_mse_x.append(mse_x)
        all_mse_v.append(mse_v)
    print('Average MSE positions: {}'.format(np.average(all_mse_x)))
    print('Average MSE velocity: {}'.format(np.average(all_mse_v)))
    make_msd_plot(all_mse_x, all_mse_v)

def compare_results(path1, path2, out_files, patho, reverse):
    """Compare gromacs results from simulations in two paths.

    Parameters
    ----------
    path1 : string
        Path to folder with frames for first trajectory.
    path2 : string
        Path to folder with frames for second trajectory.
    out_files : dict
        A dict with files from the ouput when running the
        gromacs simulation with PyRETIS.
    path0 : object like :py:class:`.PathExt`.
        The path object.
    reverse : boolean
        If True, we are comparing time reversed results.
    """
    cmd = ['gmx_5.1.4', 'trjconv', '-f', out_files['trr'],
           '-s', out_files['tpr'], '-o', 'frame.g96', '-sep',
           '-nzero', '5']
    exe = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           shell=False,
                           cwd=path1)
    _ = exe.communicate(input=b'0')

    compare_frames(path1, os.path.join(path2, 'frames'),
                   reverse=reverse)

    xvg2 = os.path.join(path2, 'energy.xvg')
    energy2 = read_xvg_file(xvg2)
    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    if reverse:
        ekin = patho.ekin[::-1]
        vpot = patho.vpot[::-1]
    else:
        ekin = patho.ekin
        vpot = patho.vpot
    ax1.plot(ekin, lw=3, alpha=0.8, label='GromacsExternal')
    ax1.plot(energy2['Kinetic En.'], lw=2, alpha=0.8, label='Plain GROMACS')
    ax1.set_ylabel('Kinetic En.')
    ax1.legend()
    ax2.plot(vpot, lw=3, alpha=0.8)
    ax2.plot(energy2['Potential'], lw=2, alpha=0.8)
    ax2.set_ylabel('Potential')
    plt.show()


def run_forward(gro, system, order_function):
    """Test implementation of gromacs integrator.

    This test will run a gromacs simulation with starting and stopping
    forward in time and compare the output with the results from a
    pure gromacs simulation with the same output frequency and other
    settings.

    Parameters
    ----------
    gro : object like :py:class:`.GromacsExt`
        The object which handles gromacs integration.
    system : object like :py:class:`.System`
        The system we are studying.

    Returns
    -------
    out[0] : dict
        Some files created by this method.
    out[1] : object like :py:class:`.PathExt`.
        The trajectory created.
    """
    exe_path = os.path.join(os.getcwd(), 'trajf')
    make_dirs(exe_path)
    gro.exe_dir = exe_path
    plain_path = os.path.join(os.getcwd(), 'plain-md')
    # Test 1:
    # We have performed a plain MD simulation with gromacs, starting from
    # initial.g96 for 1000 steps. We now do the same with start and
    # stopping:
    length = 1000 // gro.subcycles + 1
    path = PathExt(None, maxlen=length)
    interfaces = [-float('inf'), None, float('inf')]
    gro.propagate(path, system, order_function,
                  interfaces, reverse=False)
    out_files = {'tpr': gro.input_files['tpr'],
                 'trr': 'trajF.trr'}
    compare_results(exe_path, plain_path, out_files, path, False)
    return out_files, path


def run_reverse(gro, system, forward_path, order_function):
    """Test implementation of gromacs integrator.

    This test will run a gromacs simulation with starting and stopping
    backward in time and compare the output with the results from a
    gromacs simulation with the same output frequency and other settings.

    Parameters
    ----------
    gro : object like :py:class:`.GromacsExt`
        The object which handles gromacs integration.
    system : object like :py:class:`.System`
        The system we are studying.
    forward_path : object like :py:class:`.PathExt`
        The forward path generated. Used here to pick the initial point.

    Returns
    -------
    out[0] : dict
        Some files created by this method.
    out[1] : object like :py:class:`.PathExt`.
        The trajectory created.
    """
    exe_path = os.path.join(os.getcwd(), 'trajb')
    make_dirs(exe_path)
    gro.exe_dir = exe_path
    plain_path = os.path.join(os.getcwd(), 'plain-md')

    length = 1000 // gro.subcycles + 1
    path = PathExt(None, maxlen=length)

    phasepoint = forward_path.phasepoint(-1)
    system.particles.set_particle_state(phasepoint)

    interfaces = [-float('inf'), None, float('inf')]
    gro.propagate(path, system, order_function,
                  interfaces, reverse=True)
    out_files = {'tpr': gro.input_files['tpr'],
                 'trr': 'trajB.trr'}
    compare_results(exe_path, plain_path, out_files, path, True)
    return out_files, path


def do_setup():
    """Do initial setup needed for running the test.

    Returns
    -------
    system : object like :py:class`.System`
        A system which we are integrating. It contains information
        about the order parameter and how to calculate it.
    gro : object like :py:class:`.GromacsExt`
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
    settings['engine'] = {'class': 'gromacs',
                          'gmx': 'gmx_5.1.4',
                          'mdrun': 'gmx_5.1.4 mdrun',
                          'input_path': 'ext_input',
                          'input_files': {'configuration': 'initial.g96',
                                          'input': 'grompp.mdp',
                                          'topology': 'topol.top'},
                          'timestep': 0.002, 'subcycles': 5}

    create_conversion_factors(settings['system']['units'])
    gro = create_engine(settings)
    system = create_system(settings, engine=gro)
    order_function = create_orderparameter(settings)
    return system, order_function, gro


if __name__ == '__main__':
    sys, order_fun, grom = do_setup()
    print('Running forward...')
    _, pathf = run_forward(grom, sys, order_fun)
    print('Running backward...')
    _, _ = run_reverse(grom, sys, pathf, order_fun)
