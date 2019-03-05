# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""
Compare a PyRETIS simulation to LAMMPS.

In this example, we re-run a LAMMPS simulation using PyRETIS, and
compare different thermodynamic output.

"""
import sys
import tempfile
import colorama
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import gridspec
from pyretis.core.units import units_from_settings
from pyretis.inout.setup import (
    create_system,
    create_force_field,
    create_simulation,
    create_engine,
)
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file


LAMMPS_HEAD = '#Step Temp Press PotEng KinEng TotEng Pxx Pyy Pzz Pxy Pxz Pyz'
LAMMPS_FMT = '{:8d}' + ' {:>12.7f}' * 11
TOL_ENERGY = 1.0
TOL_PRESS = 2.0


def set_up(settings_file):
    """Set up the simulation from a settings file."""
    print_to_screen('Loading settings: {}'.format(settings_file),
                    level='info')
    settings = parse_settings_file(settings_file)
    units_from_settings(settings)
    engine = create_engine(settings)
    system = create_system(settings, engine=engine)
    system.forcefield = create_force_field(settings)
    keyargs = {'system': system, 'engine': engine}
    simulation = create_simulation(settings, keyargs)
    return simulation


def format_thermo(result):
    """Format the thermo output similar to LAMMPS."""
    step = result['cycle']['step']
    thermo = result['thermo']
    press = thermo['press-tens']
    return LAMMPS_FMT.format(step, thermo['temp'], thermo['press'],
                             thermo['vpot'], thermo['ekin'], thermo['etot'],
                             press[0, 0], press[1, 1], press[2, 2],
                             press[0, 1], press[0, 2], press[1, 2])


def run_simulation(simulation, outputfile):
    """Run the simulation and write output to screen/file."""
    print_to_screen('Running simulation: {}'.format(simulation))
    with open(outputfile, 'w') as output:
        output.write('{}\n'.format(LAMMPS_HEAD))
        print(LAMMPS_HEAD)
        try:
            for step in simulation.run():
                txt = format_thermo(step)
                print(txt)
                output.write('{}\n'.format(txt))
        except KeyboardInterrupt:
            print_to_screen('Aborting simulation!')
            return 1
    return 0


def mean_squared_error(value1, value2):
    """Compute the mean squared error."""
    nmax = min(len(value1), len(value2))
    return ((value1[:nmax] - value2[:nmax])**2).mean()


def mean_absolute_percentage_error(value1, value2):
    """Compute the mean absolute percentage error."""
    nmax = min(len(value1), len(value2))
    return 100.0 * (np.abs(value1[:nmax] - value2[:nmax])).mean()


def plot_energy(lammps, pyret):
    """Just plot the energy terms."""
    print_to_screen('Plotting energy terms...')
    fig = plt.figure()
    grid = gridspec.GridSpec(3, 2)

    axes = (fig.add_subplot(grid[0, 0]),
            fig.add_subplot(grid[0, 1]),
            fig.add_subplot(grid[1, 0]),
            fig.add_subplot(grid[1, 1]),
            fig.add_subplot(grid[2, :]))

    labels = ('Temperature', 'Pressure', 'Potential energy',
              'Kinetic energy', 'Total energy')

    last = len(axes) - 1

    retval = 0

    for i, (axi, labi) in enumerate(zip(axes, labels)):
        linel, = axi.plot(lammps[:, 0], lammps[:, i + 1], lw=5, ls='-')
        linep, = axi.plot(pyret[:, 0], pyret[:, i + 1], lw=2, ls=':')
        axi.set_ylabel(labi)
        axi.set_xlabel('Step')
        mse = mean_squared_error(lammps[:, i + 1], pyret[:, i + 1])
        mape = mean_absolute_percentage_error(lammps[:, i + 1],
                                              pyret[:, i + 1])
        if mape > TOL_ENERGY:
            retval += 1
            print_to_screen(
                'Too large MAPE for {:}: {:.3e}'.format(labi, mape),
                level='error'
            )
        rec = plt.Rectangle((0, 0), 1, 1, fill=False, edgecolor='none',
                            visible=False)
        if i < last:
            axi.legend(
                (rec, rec),
                ('MSE = {:.3e}'.format(mse), 'MAPE = {:.3e}'.format(mape)),
                frameon=False
            )
        else:
            axi.legend((linel, linep, rec, rec),
                       ('LAMMPS', 'PyRETIS', 'MSE = {:.3e}'.format(mse),
                        'MAPE = {:.3e}'.format(mape),),
                       frameon=False, ncol=2, columnspacing=0.0)
    fig.tight_layout()
    return retval


def plot_pressure(lammps, pyret):
    """Plot the pressure components."""
    print_to_screen('Plotting pressure terms...')
    fig = plt.figure()
    grid = gridspec.GridSpec(3, 2)
    last = 5
    retval = 0
    for i, term in enumerate(('Pxx', 'Pyy', 'Pzz', 'Pxy', 'Pxz', 'Pyz')):
        axi = fig.add_subplot(grid[i % 3, int(i / 3)])
        linel, = axi.plot(lammps[:, 0], lammps[:, i + 6], lw=5, ls='-')
        linep, = axi.plot(pyret[:, 0], pyret[:, i + 6], lw=2, ls=':')
        axi.set_ylabel(term)
        mse = mean_squared_error(lammps[:, i + 6], pyret[:, i + 6])
        mape = mean_absolute_percentage_error(lammps[:, i + 6],
                                              pyret[:, i + 6])
        if mape > TOL_PRESS:
            retval += 1
            print_to_screen(
                'Too large MAPE for {:}: {:.3e}'.format(term, mape),
                level='error'
            )
        rec = plt.Rectangle((0, 0), 1, 1, fill=False, edgecolor='none',
                            visible=False)
        if i < last:
            axi.legend(
                (rec, rec),
                ('MSE = {:.3e}'.format(mse), 'MAPE = {:.3e}'.format(mape)),
                frameon=False
            )
        else:
            axi.legend((linel, linep, rec, rec),
                       ('LAMMPS', 'PyRETIS',
                        'MSE = {:.3e}'.format(mse),
                        'MAPE = {:.3e}'.format(mape)),
                       frameon=False, ncol=1)
    fig.tight_layout()
    return retval


def plot_all_vs(lammps, pyret):
    """Plot terms vs each other."""
    print_to_screen('Plotting all terms...')
    fig = plt.figure()
    nrow, ncol = 3, 4
    grid = gridspec.GridSpec(nrow, ncol)
    labels = ('Temperature', 'Pressure', 'Potential energy',
              'Kinetic energy', 'Total energy', 'Pxx', 'Pyy',
              'Pzz', 'Pxy', 'Pxz', 'Pyz')
    nmax = min(len(lammps), len(pyret))
    for i, labi in enumerate(labels):
        row = i // ncol
        col = i % ncol
        axi = fig.add_subplot(grid[row, col])
        xval = lammps[:nmax, i + 1]
        yval = pyret[:nmax, i + 1]
        axi.scatter(xval, yval)
        axi.set_xlabel('LAMMPS')
        axi.set_ylabel('PyRETIS')
        axi.set_title(labi)
        fit_line = np.poly1d(np.polyfit(xval, yval, 1))
        newx = np.linspace(min(xval), max(xval), 3)
        rval = np.corrcoef(fit_line(xval), yval)
        # Since scatter don't influence the color cycler:
        axi.plot([], [], lw=3)
        linef, = axi.plot(newx, fit_line(newx), lw=3)
        axi.legend((linef, ), ('Rsq = {:.3f}'.format(rval[0, 1]**2), ),
                   frameon=False)
    fig.tight_layout()


def plot_comparison(lammps_file, pyretis_file):
    """Plot comparison with LAMMPS."""
    print_to_screen('Loading LAMMPS data: {}'.format(lammps_file),
                    level='info')
    lammps = np.loadtxt(lammps_file)
    print_to_screen('Loading PyRETIS data: {}'.format(pyretis_file),
                    level='info')
    pyret = np.loadtxt(pyretis_file)
    if lammps.shape != pyret.shape:
        print_to_screen('LAMMPS and PyRETIS data have different shape!',
                        level='warning')

    plt.style.use('seaborn-poster')
    ret1 = plot_energy(lammps, pyret)
    if ret1 == 0:
        print_to_screen('RMSD comparison for thermodynamic properties is OK!',
                        level='info')
    ret2 = plot_pressure(lammps, pyret)
    if ret2 == 0:
        print_to_screen('RMSD comparison for pressure components is OK!',
                        level='info')
    # plot_all_vs(lammps, pyret)

    if len(pyret) < len(lammps):
        print_to_screen(
            'PyRETIS data too short: {} vs LAMMPS: {}'.format(len(pyret),
                                                              len(lammps)),
            level='error'
        )
        return 1
    return ret1 + ret2


def main(settings_file, lammps_file, show_plot=True):
    """Parse input, run simulation and the comparison."""
    simulation = set_up(settings_file)
    retval = 1
    with tempfile.NamedTemporaryFile(prefix='thermo_', suffix='.txt') as tmp:
        run_simulation(simulation, tmp.name)
        retval = plot_comparison(lammps_file, tmp.name)
        if show_plot:
            plt.show()
        if retval == 0:
            print_to_screen('Comparison was successful!', level='success')
        else:
            print_to_screen('Comparison FAILED!', level='error')
    return retval


if __name__ == '__main__':
    colorama.init(autoreset=True)
    sys.exit(main(sys.argv[1], sys.argv[2], show_plot='plot' in sys.argv[1:]))
