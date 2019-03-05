# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Test the restart methods."""
import logging
import os
import unittest
import tempfile
from pyretis.simulation.simulation import Simulation
from pyretis.inout.settings import add_default_settings
from pyretis.inout.setup.createsystem import create_system_from_settings
from pyretis.core.units import units_from_settings
from pyretis.inout.restart import (
    write_restart_file,
    write_path_ensemble_restart,
    read_restart_file,
)
from pyretis.core.pathensemble import PathEnsemble
from pyretis.inout.common import make_dirs


logging.disable(logging.CRITICAL)
HERE = os.path.abspath(os.path.dirname(__file__))


class TestRestartMethods(unittest.TestCase):
    """Test methods defined in the module."""

    def test_write_and_read(self):
        """Test write/read for simulation restart files."""
        simulation = Simulation(steps=100)
        settings = {
            'system': {
                'dimensions': 3,
                'units': 'reduced',
                'temperature': 1.0
            },
            'particles': {
                'position': {
                    'generate': 'fcc',
                    'repeat': [2, 2, 2],
                    'density': 0.9,
                }
            },
            'potential': [
                {
                    'class': 'PairLennardJonesCutnp',
                    'shift': True,
                    'parameter': {
                        0: {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}
                    }
                }
            ]
        }
        add_default_settings(settings)
        units_from_settings(settings)
        system = create_system_from_settings(settings, None)
        simulation.system = system

        with tempfile.NamedTemporaryFile() as tmp:
            write_restart_file(tmp.name, simulation)
            tmp.flush()
            read = read_restart_file(tmp.name)
            self.assertEqual(read['simulation'], simulation.restart_info())

    def test_read_write_ensemble(self):
        """Test read/write for path ensemble restart files."""
        ensemble = PathEnsemble(0, [-1, 0, 1])
        startdir = os.getcwd()
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            ensemble_dir = os.path.join(tempdir, ensemble.ensemble_name_simple)
            make_dirs(ensemble_dir)
            write_path_ensemble_restart(ensemble)
            files = [i.name for i in os.scandir(ensemble_dir) if i.is_file()]
            self.assertEqual(1, len(files))
            self.assertIn('ensemble.restart', files)
            restart_file = os.path.join(ensemble_dir, 'ensemble.restart')
            read = read_restart_file(restart_file)
            self.assertEqual(read, ensemble.restart_info())
        os.chdir(startdir)
        with tempfile.TemporaryDirectory() as tempdir:
            ensemble = PathEnsemble(0, [-1, 0, 1], exe_dir=tempdir)
            for name in ensemble.directories():
                make_dirs(name)
            write_path_ensemble_restart(ensemble)
            restart_file = os.path.join(ensemble.directory['path-ensemble'],
                                        'ensemble.restart')
            read = read_restart_file(restart_file)
            self.assertEqual(read, ensemble.restart_info())


if __name__ == '__main__':
    unittest.main()
