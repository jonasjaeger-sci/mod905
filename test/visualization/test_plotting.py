# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the common methods in pyretis.visualization.common."""

import os
from unittest.mock import patch
from io import StringIO
import logging
import unittest
from pyretis.visualization import HAS_PYQT5

if HAS_PYQT5:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt  # noqa: E402
    from matplotlib.lines import Line2D  # noqa: E402
    from mpl_toolkits.mplot3d import Axes3D  # noqa: E402
    from pyretis.inout import print_to_screen  # noqa: E402
    from pyretis.visualization.plotting import (
        plot_regline,
        plot_int_plane,
        gen_surface)  # noqa: E402

logging.disable(logging.CRITICAL)

HERE = os.path.abspath(os.path.dirname(__file__))


@unittest.skipIf(HAS_PYQT5 is False, "PyQt5 is not installed")
class TestMethods(unittest.TestCase):
    """Test some of the methods from pyretis.visualization.plotting."""

    def test_plot_regline(self):
        """Test of the regression plotting"""
        fig, ax = plt.subplots()
        x = [i for i in range(10)]
        y = [i**2 - 1. for i in x]
        # Expected regression line points
        m = [x[0]*9. - 13., x[-1]*9. - 13.]
        line = Line2D([x[0], x[-1]], m)
        # Regression line
        regline = plot_regline(ax, x, y)
        # Loop over y-values and compare
        for i, j in zip(regline[0].get_ydata(), line.get_ydata()):
            self.assertEqual(i, j)

    def test_plot_int_plane(self):
        """Test if we can make an interface plane in 3d plot"""
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        # Interface plane specifics
        pos = 1.0
        ymin, ymax, zmin, zmax = 0.0, 1.0, 0.0, 1.0
        visible = False
        _ = plot_int_plane(ax, pos, ymin, ymax, zmin, zmax,
                           visible=visible)
        # Nothing to check, only if any errors should arise from plotting
        fig.clear()

    def test_gen_surface(self):
        """Test if we can generate a surface/plot with given settings"""
        # Create data
        x, y, z = [], [], []
        for i in range(-10, 10):
            for j in range(-10, 10):
                x.append(i/10.)
                y.append(j/10.)
                z.append((i/10.)**2 + (j/10.)**2)
        # Create figure and plot+colorbar axes
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        cbar_ax = fig.add_axes([0.86, 0.1, 0.03, 0.8])
        # Generate surface 3d
        _ = gen_surface(x, y, z, fig, ax, cbar_ax=cbar_ax,
                        resX=200, resY=200, method='surface')
        ax.clear()
        _ = gen_surface(x, y, z, fig, ax, cbar_ax=cbar_ax,
                        resX=200, resY=200, method='contour')
        ax.clear()
        _ = gen_surface(x, y, z, fig, ax, cbar_ax=cbar_ax,
                        resX=200, resY=200, method='contourf')
        ax.clear()
        _ = gen_surface(x, y, z, fig, ax, cbar_ax=cbar_ax,
                        method='scatter')
        ax.clear()
        # Generate Error
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            _ = gen_surface(x, y, z, fig, ax, cbar_ax=cbar_ax,
                            method='blub')
            self.assertIn("Method not recognized!", fakeOutput.getvalue())

        fig.clear()
        # Generate surface 2d
        ax = fig.add_subplot(111)
        cbar_ax = fig.add_axes([0.1, 0.03, 0.8, 0.1])
        _ = gen_surface(x, y, z, fig, ax, cbar_ax=cbar_ax, dim=2,
                        method='contourf')
        ax.clear()
        _ = gen_surface(x, y, z, fig, ax, cbar_ax=cbar_ax, dim=2,
                        method='contour')
        ax.clear()
        _ = gen_surface(x, y, len(x)*[0.0], fig, ax, cbar_ax=cbar_ax, dim=2,
                        method='scatter')
        ax.clear()
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            _ = gen_surface(x, y, z, fig, ax, cbar_ax=cbar_ax, dim=2,
                            method='blub')
            self.assertIn("Method not recognized!", fakeOutput.getvalue())
        fig.clear()
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            _ = gen_surface(x, y, z, fig, ax, cbar_ax=cbar_ax, dim=6,
                            method='blub')
            self.assertIn("Error! Dimension: 6", fakeOutput.getvalue())
        fig.clear()


if __name__ == '__main__':
    unittest.main()
