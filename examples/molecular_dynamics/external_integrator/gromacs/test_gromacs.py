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
import numpy as np
import os
from pyretis.core import Box
from pyretis.integrators import GromacsExt, ExternalScript
from pyretis.integrators.gromacs import read_gromos96_file
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import create_system
from pyretis.inout.settings import create_orderparameter
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
    return np.array(data), legends
        

def test1(gro, external, md_settings):


    steps = md_settings['steps'] * md_settings['subcycles']

    # Test 1:
    # We have first performed a plain MD simulation, starting from
    # initial.g96 for 500 steps. We now do the same with start and
    # stopping:

    initial = os.path.join(os.getcwd(), 'initial.g96')

    out_files, order = gro.execute_until(initial, system,
                                         md_settings, reverse=False)

    cmd = ['gmx_5.1.4', 'trjconv', '-f', out_files['trr'],
           '-s', out_files['tpr'], '-o', 'frame.g96', '-sep',
           '-nzero', '5']
    external.execute_command(cmd, inputs=b'0', cwd=exe_path)
    cmd = ['gmx_5.1.4', 'energy', '-f', out_files['edr']]
    external.execute_command(cmd, inputs=b'5 6 7 8', cwd=exe_path)

    # compare frames:
    box = Box([2.384999990, 2.384999990, 2.384999990])
    plain_path = 'plain-md'
    plain_path_frame = os.path.join(plain_path, 'frames')
    all_mse_x = []
    all_mse_v = []
    for files in os.listdir(exe_path):
        if files.endswith('.g96') and files.startswith('frame'):
            file1 = os.path.join(exe_path, files)
            file2 = os.path.join(plain_path_frame, files)
            mse_x, mse_v = compare_g96_files(file1, file2, box)
            all_mse_x.append(mse_x)
            all_mse_v.append(mse_v)
    print('Average MSE positions: {}'.format(np.average(all_mse_x)))
    print('Average MSE velocity: {}'.format(np.average(all_mse_v)))

    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    ax1.plot(all_mse_x)
    ax1.set_xlabel('Step')
    ax1.set_ylabel('MSE position')
    ax2.plot(all_mse_v)
    ax2.set_xlabel('Step')
    ax2.set_ylabel('MSE velocity')

    energy1, leg1 = read_xvg_file(os.path.join(plain_path, 'energy.xvg'))
    energy2, leg2 = read_xvg_file(os.path.join(exe_path, 'energy.xvg'))
    print(leg1, leg2)
    fig2 = plt.figure()
    ax3 = fig2.add_subplot(111)
    nrow1, ncol1 = energy1.shape 
    nrow2, ncol2 = energy2.shape
    row = min(nrow1, nrow2)
    assert ncol1 == ncol2
    delta = energy1[:row, :] - energy2[:row, :]
    for i in range(1, ncol1):
        ax3.plot(delta[:, i], label=leg2[i-1])
    ax3.set_xlabel('Step')
    ax3.set_ylabel('Energy difference')
    ax3.legend()
    plt.show()
    return out_files


if __name__ == '__main__':
    # Run a test:
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
    system.order_function = create_orderparameter(settings)

    input_dir = 'ext_input'

    input_files = {'configuration': 'conf.g96',
                   'input': 'grompp.mdp',
                   'topology': 'topol.top'}
    
    exe_path = 'trajf'

    md_settings = {'steps': 100, 'subcycles': 5, 'timestep': 0.002}

    gro = GromacsExt('gmx_5.1.4', input_dir, input_files,
                     md_settings['timestep'], md_settings['subcycles'])
    
    external = ExternalScript('For executing commands', None, None, None)
    #out_files = test1(gro, md_settings, external)    

    out_files = {'trr': 'trajF_new.trr', 'tpr': 'trajF_new.tpr'}

    exe_path = 'trajf'
    trr = os.path.join(exe_path, out_files['trr'])
    tpr = os.path.join(exe_path, out_files['tpr'])

    md_settings = {'steps': 100, 'subcycles': 5, 'timestep': 0.002}

    exe_path = os.path.join(os.getcwd(), 'trajb')
    
    initial = os.path.join(exe_path, 'lastf.g96')

    gro.get_trr_frame(trr, tpr, md_settings['steps'], initial)

    out_files, order = gro.execute_until(initial, system,
                                         md_settings, reverse=True,
                                         exe_dir=exe_path)
    cmd = ['gmx_5.1.4', 'trjconv', '-f', out_files['trr'],
           '-s', out_files['tpr'], '-o', 'frame.g96', '-sep',
           '-nzero', '5']
    external.execute_command(cmd, inputs=b'0', cwd=exe_path)
    cmd = ['gmx_5.1.4', 'energy', '-f', out_files['edr']]
    external.execute_command(cmd, inputs=b'5 6 7 8', cwd=exe_path)
    
    # compare frames:
    box = Box([2.384999990, 2.384999990, 2.384999990])
    forward = 'trajf'
    all_mse_x = []
    all_mse_v = []
    file_forward = []
    file_backward = []
    for files in os.listdir(exe_path):
        if files.endswith('.g96') and files.startswith('frame'):
            file1 = os.path.join(exe_path, files)
            file2 = os.path.join(forward, files)
            file_forward.append(file2)
            file_backward.append(file1)
    file_forward = sorted(file_forward)
    file_backward = sorted(file_backward)
    for file1, file2 in zip(file_backward, file_forward[::-1]):
        mse_x, mse_v = compare_g96_files(file1, file2, box, negvel=True)
        all_mse_x.append(mse_x)
        all_mse_v.append(mse_v)
    print('Average MSE positions: {}'.format(np.average(all_mse_x)))
    print('Average MSE velocity: {}'.format(np.average(all_mse_v)))
