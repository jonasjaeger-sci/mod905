# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Compare the energy output for GROMACS and PyRETIS."""
import sys
import colorama
from matplotlib import pyplot as plt
import numpy as np
from pyretis.inout import print_to_screen
from pyretis.inout.formats.gromacs import (
    read_xvg_file,
)


plt.style.use('seaborn-poster')


def main(energy_file, xvg_file, plot=False):
    """Perform the test."""
    print_to_screen('Reading energy file: {}'.format(energy_file),
                    level='info')
    energy = np.loadtxt(energy_file)
    print_to_screen('Reading xvg file: {}'.format(xvg_file), level='info')
    energy_xvg = read_xvg_file(xvg_file)

    mse_ok = obtain_mses(energy, energy_xvg)

    if plot:
        print_to_screen('\nPlotting for comparison', level='message')
        plot_comparison(energy, energy_xvg, energy_file, xvg_file)

    if not mse_ok:
        print_to_screen('\nComparison failed!', level='error')
        sys.exit(1)


def obtain_mses(energy, energy_xvg, tol=1.0e-5):
    """Obtain some mean squared errors."""
    pairs = ((1, 'potential'), (2, 'kinetic en.'), (3, 'total energy'),
             (4, 'temperature'))
    for pair in pairs:
        if not len(energy[:, pair[0]]) == len(energy_xvg[pair[1]]):
            return False
        mse = ((energy[:, pair[0]] - energy_xvg[pair[1]])**2).mean(axis=0)
        level = 'info'
        tol_ok = True
        if tol:
            tol_ok = abs(mse) < tol
            if not tol_ok:
                level = 'error'
        print_to_screen('MSE {}: {}'.format(pair[1], mse), level=level)
        if not tol_ok:
            return False
    return True


def plot_comparison(energy, energy_xvg, energy_file, xvg_file):
    """Just plot some properties for the paths."""
    fig1 = plt.figure()
    ax11 = fig1.add_subplot(221)
    ax12 = fig1.add_subplot(222)
    ax21 = fig1.add_subplot(223)
    ax22 = fig1.add_subplot(224)
    plabel = 'PyRETIS ({})'.format(energy_file)
    glabel = 'gmx ({})'.format(xvg_file)
    ax11.plot(energy[:, 1], lw=4, ls='-', marker='o', label=plabel)
    ax11.plot(energy_xvg['potential'], lw=2, ls='--', marker='^',
              label=glabel)
    ax11.legend()
    ax11.set_ylabel('Potential')

    ax12.plot(energy[:, 2], lw=4, ls='-', marker='o')
    ax12.plot(energy_xvg['kinetic en.'], lw=2, ls='--', marker='^')
    ax12.set_ylabel('Kinetic')

    ax21.plot(energy[:, 3], lw=4, ls='-', marker='o')
    ax21.plot(energy_xvg['total energy'], lw=2, ls='--', marker='^')
    ax21.set_ylabel('Total')

    ax22.plot(energy[:, 4], lw=4, ls='-', marker='o')
    ax22.plot(energy_xvg['temperature'], lw=2, ls='--', marker='^')
    ax22.set_ylabel('Temperature')

    fig1.tight_layout()
    plt.show()


if __name__ == '__main__':
    colorama.init(autoreset=True)
    PLOT = len(sys.argv) > 3
    main(sys.argv[1], sys.argv[2], plot=PLOT)
