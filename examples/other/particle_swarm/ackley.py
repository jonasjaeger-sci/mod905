# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""The Ackley function, used as a potential."""
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from pyretis.forcefield import PotentialFunction


TWO_PI = np.pi * 2.0
EXP = np.exp(1)


@np.vectorize
def ackley_potential(x, y):
    """Evaluate the Ackley function."""
    return (-20.0 * np.exp(-0.2*np.sqrt(0.5*(x**2 + y**2))) -
            np.exp(0.5 * (np.cos(TWO_PI * x) + np.cos(TWO_PI * y))) +
            EXP + 20)


class Ackley(PotentialFunction):
    """A implementation of the Ackley function.

    Note that the usage of this potential function differs from
    the usual usage for force fields.
    """
    def __init__(self):
        """Initiate the function."""
        super().__init__(dim=2, desc='The Ackley function')

    def potential(self, system):
        """Evaluate the potential, note that we return all values!"""
        xpos = system.particles.pos[:, 0]
        ypos = system.particles.pos[:, 1]
        pot = ackley_potential(xpos, ypos)
        return pot


if __name__ == '__main__':
    X, Y = np.meshgrid(np.linspace(-5, 5, 100),
                       np.linspace(-5, 5, 100))
    Z = ackley_potential(X, Y)

    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212, projection='3d')
    ax1.contourf(X, Y, Z)
    ax2.plot_surface(X, Y, Z, cmap=cm.viridis)
    plt.show()
