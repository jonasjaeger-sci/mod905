# -*- coding: utf-8 -*-

from .simulation import Simulation
from .md_simulation import SimulationNVE
from .simulation_task import create_output_task
from retis.core.integrators import create_integrator

_OUTPUT = {'nve': [{'target': 'file', 'type': 'thermo', 'every': 10},
                   #{'target': 'file', 'type': 'traj', 'every': 10,
                   # 'header': 'NVE simulation. Step: {}'},
                    {'target': 'screen', 'type': 'thermo', 'every': 10}]}

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
