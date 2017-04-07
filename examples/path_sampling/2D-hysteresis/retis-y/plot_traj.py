# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Plot raw data from a simulation."""
# pylint: disable=C0103
import os
import sys
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.cm import get_cmap
from pyretis.core import Box, System, Particles
from pyretis.inout.setup import create_force_field
from pyretis.inout.settings import parse_settings_file
from pyretis.inout.writers import prepare_load


def plot_potential(settings, axi):
    """Just plot the potential in the given axis"""
    forcefield = create_force_field(settings)
    box = Box(periodic=[False, False])
    fakesys = System(units='reduced', box=box)
    fakesys.particles = Particles(dim=2)
    fakesys.add_particle(name='B', pos=np.zeros(2), ptype=1)
    xval = np.linspace(-0.5, 0.5, 100)
    yval = np.linspace(-1.0, 1.0, 100)
    xpos, ypos = np.meshgrid(xval, yval, indexing='ij')
    pot = np.zeros_like(xpos)
    for i, x in enumerate(xval):
        for j, y in enumerate(yval):
            fakesys.particles.pos[0, 0] = x
            fakesys.particles.pos[0, 1] = y
            pot[i, j] = forcefield.evaluate_potential(fakesys)
    axi.contourf(xpos, ypos, pot, 10, cmap=get_cmap('viridis'), alpha=0.8)
    # add interfaces
    for inter in settings['simulation']['interfaces']:
        axi.axhline(y=inter, lw=2, ls=':', color='#262626', alpha=0.8)


def plot_ensemble(dirname, axi, maxlines=100, maxorder=None):
    """Plot trajectories from an ensemble."""
    traj_file = os.path.join(dirname, 'traj.txt')
    trajload = prepare_load('pathtrajint', traj_file)
    iplot = 0
    all_lines = []
    last_point = []
    first_point = []
    for traj in trajload:
        if traj['comment'][0].split('status:')[-1].strip() != 'ACC':
            continue
        pos = np.array([x['pos'][0] for x in traj['data']])
        if maxorder is not None:
            if max(pos[:, 1]) < maxorder:
                continue
        line, = axi.plot(pos[:, 0], pos[:, 1], lw=3, alpha=0.9)
        all_lines.append(line)
        first_point.append((pos[0, 0], pos[0, 1]))
        last_point.append((pos[-1, 0], pos[-1, 1]))
        iplot += 1
        if iplot >= maxlines:
            break
    # Add colors now that we know how many we have created:
    cmap = get_cmap(name='coolwarm')
    colors = cmap(np.linspace(0, 1, iplot))
    for i, line in enumerate(all_lines):
        line.set_color(colors[i])
        axi.scatter(first_point[i][0], first_point[i][1], s=50, marker='o',
                    color=line.get_color(), alpha=0.9)
        axi.scatter(last_point[i][0], last_point[i][1], s=50, marker='x',
                    color=line.get_color(), alpha=0.9)


if __name__ == '__main__':
    ens = sys.argv[1]
    sim_settings = parse_settings_file('retis.rst')
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    plot_potential(sim_settings, ax1)
    plot_ensemble(ens, ax1, maxorder=None)
    plt.show()
