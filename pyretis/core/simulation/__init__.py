# -*- coding: utf-8 -*-
"""This package defines different simulations for use with pyretis.

The different simulations are defined as objects which inherits from
the base Simulation object defined in `simulation.py`. The simulation
object defines as simulation as a series of tasks to be executed,
typically at each step of the simulation. Output is handled with a
different set out 'output' tasks which make use of the results obtained
in the simulation steps.

Package structure
~~~~~~~~~~~~~~~~~

Modules:

- __init__.py: Imports simulations from the other modules and defines a method
  for creating simulations from a dict with settings.

- md_simulation.py: Defines simulation objects for molecular dynamics
  simulations.

- mc_simulation.py: Define simulation objects for Monte Carlo simulations.

- path_simulation.py: Defines simulation objects for path simulations.

- simulation.py: Defines the Simulation object which is the base object for
  simulations.

- simulation_task.py: Defines objects for handling of simulation tasks.

Important classes and functions:

- Simulation: The base class for simulations.

- SimulationTask: A class for creating tasks for simulations.

- create_simulation: A function to create a simulation object from
  a dictionary of given settings.
"""
# local pyretis imports
from .simulation import Simulation
from .mc_simulation import create_mc_simulation
from .md_simulation import create_md_simulation
from .path_simulation import create_path_simulation
from .simulation_task import SimulationTask


# define known simulations and give them a 'family'
# the family is used to set up the simulations
_KNOWN_SIMULATIONS = {'nve': 'md',
                      'mdflux': 'md',
                      'umbrella': 'mc',
                      'umbrellawindow': 'mc',
                      'tis': 'path',
                      'retis': 'path'}


def create_simulation(settings, system):
    """Method to create simulations from settings and system.

    This method will set up some common simulation types.
    It is meant as a helper function to automate some very common set-up
    task. It will here check what kind of simulation we are to perform and
    then call the appropriate function for setting that type of simulation up.
    The rationale here is that different families of functions may handle the
    settings and especially "missing" settings differently.

    Parameters
    ----------
    settings : dict
        This dictionary contains the settings for the simulation.
    system : object like `System` from `pyretis.core.system`
        This is the system for which the simulation will run.

    Returns
    -------
    out : object like `Simulation` from `pyretis.core.simulation.simulation`.
        This object will correspond to the selected simulation type.
    """
    sim_type = settings['type'].lower()
    family = None
    simulation = None
    try:
        family = _KNOWN_SIMULATIONS[sim_type]
    except KeyError:
        msg = 'Unknown simulation type {} requested'.format(sim_type)
        raise ValueError(msg)
    if family == 'md':
        simulation = create_md_simulation(settings, system, sim_type)
    elif family == 'mc':
        simulation = create_mc_simulation(settings, system, sim_type)
    elif family == 'path':
        simulation = create_path_simulation(settings, system, sim_type)
    else:
        msg = 'Unknown simulation type {}'.format(sim_type)
        raise ValueError(msg)
    settings['type'] = sim_type  # just update for consistency.
    return simulation
