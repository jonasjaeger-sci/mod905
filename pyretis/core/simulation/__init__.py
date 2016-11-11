# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""This package defines different simulations for use with pyretis.

The different simulations are defined as objects which inherits from
the base Simulation object defined in `simulation.py`. The simulation
object defines as simulation as a series of tasks to be executed,
typically at each step of the simulation. Output is handled with a
different set out 'output' tasks which make use of the results obtained
in the simulation steps.

Package structure
-----------------

Modules
~~~~~~~

md_simulation.py
    Defines simulation classes for molecular dynamics simulations.

mc_simulation.py
    Define simulation classes for Monte Carlo simulations.

path_simulation.py
    Defines simulation classes for path simulations.

simulation.py
    Defines the Simulation class which is the base class for
    simulations.

simulation_task.py
    Defines classes for handling of simulation tasks.

Important classes defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simulation
    The base class for simulations.

SimulationTask
    A class for creating tasks for simulations.
"""
# local pyretis imports
from .simulation import Simulation
from .simulation_task import SimulationTask
from .mc_simulation import UmbrellaWindowSimulation
from .md_simulation import SimulationNVE, SimulationMDFlux
from .path_simulation import SimulationSingleTIS, SimulationRETIS
