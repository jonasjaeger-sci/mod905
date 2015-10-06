# -*- coding: utf-8 -*-
"""
This package defines different simulations for use with pytismol

Package structure
=================

Modules:

- __init__.py: Imports simulations from the other modules and defines a method
  for creating simulations from a dict with settings.

- simulation.py: Defines the Simulation object which is the base object for
  simulations.

- md_simulation.py: Defines simulation objects for molecular dynamics
  simulations.

- mc_simulation.py: Define simulation objects for monte carlo simulations.

- simulation_task: Defines objects for handling of simulation tasks and
  output tasks.

- path_simulation.py: Defines simulation objects for path simulations.
"""
from .simulation import Simulation
from .mc_simulation import UmbrellaWindowSimulation
from .md_simulation import SimulationNVE
from .path_simulation import SimulationTIS
from .simulation_task import create_output_task
from retis.core.integrators import create_integrator
import warnings

_OUTPUT = {'nve': [{'target': 'file', 'type': 'thermo', 'every': 10},
                   {'target': 'file', 'type': 'traj', 'every': 10,
                    'header': 'NVE simulation. Step: {}'},
                   {'target': 'screen', 'type': 'thermo', 'every': 10}]}


def _check_settings(settings, required):
    """
    Helper function to check if required settings actually are set

    Parameters
    ----------
    settings : dict
        This dict contains the given settings
    required : list of strings
        This list contains the settings that are required and which
        we will check the presence of.

    Returns
    -------
    out : boolean
        True if all required settings are present, False otherwise.
    """
    result = True
    for setting in required:
        if setting not in settings:
            warnings.warn('Setting `{}` not found!'.format(setting))
            result = False
    return result


def create_simulation(settings, system):
    """
    This method will set up some common simulation types.
    It is meant as a helper function to automate some very common set-up
    tasks

    Parameter
    ---------
    settings : dict
        This dictionary contains the settings for the simulation.
    system : object of type restis.core.system.System
        This is the system for which the simulation will run.

   Returns
    -------
    out : object that represents the simulation.
        This object will correspond to the selected simulation type.
    """
    simulation_type = settings.get('type', 'nve').lower()
    simulation = None
    required = {'nve': ['endcycle']}
    if not _check_settings(settings, required[simulation_type]):
        return None
    if simulation_type == 'nve':
        # set up a MD NVE simulation.
        intg = create_integrator(settings.get('integrator', None),
                                 simulation_type)
        simulation = SimulationNVE(system, intg,
                                   endcycle=settings['endcycle'],
                                   startcycle=settings.get('startcycle', 0))
        # add default output:
        for output in _OUTPUT['nve']:
            task = create_output_task(output, system)
            simulation.add_output_task(task)
        return simulation
