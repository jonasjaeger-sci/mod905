# -*- coding: utf-8 -*-
"""
simulation.py
"""

import numpy as np

__all__ = ['Simulation', 'UmbrellaWindowSimulation']


class Simulation(object):
    """
    This class defines a generic simulation.

    Attributes
    ----------
    cycle : int
        The current cycle number for the simulation.
    maxcycle : int
        Maximum number of cycles to perform.
    """
    def __init__(self, cycle=0, maxcycle=0):
        """
        Initialization of the system.

        Parameters
        ----------
        cycle : int, optional.
            The current cycle
        maxcycle : int, optional.
            Maximum number of cycles to perform

        Returns
        -------
        N/A, but initiates self.tasks.
        """
        self.cycle = cycle
        self.maxcycle = maxcycle
        self.task = []

    def is_finished(self):
        """
        Function to determine if simulation is finished

        Returns
        -------
        out : True if simulation is finished, false otherwise.
        """
        return self.cycle > self.maxcycle

    def step(self):
        """
        Run a simulation step. Here, the tasks in self.task
        will be executed sequentially.

        Returns
        -------
        N/A, but may modify the system and other external variables.

        Note
        ----
        This function will have ``side effects`` and update/change
        the state of the system and other variables that are not
        explicitly shown. This is intended. In order to see what actually
        is happening when running ``step()``, investigate the definition
        of self.task and its functions in the script where the simulation
        is defined.
        """
        self.cycle += 1
        results = []
        for task in self.task:
            args = task.get('args', None)
            kwargs = task.get('kwargs', None)
            func = task['func']
            if callable(func):
                if args is None:
                    if kwargs is None:
                        result = func()
                    else:
                        result = func(**kwargs)
                else:
                    if kwargs is None:
                        result = func(*args)
                    else:
                        result = func(*args, **kwargs)
                results.append(result)
        return results


class UmbrellaWindowSimulation(Simulation):
    """
    This class defines a Umbrella simulation which is a special case of
    the simulation class with settings to simplify the
    execution of the umbrella simulation.

    Attributes
    ----------
    umbrella : list = [float, float]
        The umbrella window.
    overlap : float
        The positions that must be crossed before the simulation is done.
    cycle : int
        The current simulation cycle.
    maxcycle : int
        The MINIMUM number of cycles to perform.
    """
    def __init__(self, umbrella, overlap, cycle=0, maxcycle=0):
        """
        Initialization of a umbrella simulation.

        Parameters
        ----------
        umbrella : list = [float, float]
            The umbrella window to consider.
        overlap : float
            The position we have to cross before the simulation is done.
        cycle : int, optional.
            The current simulation cycle.
        maxcycle : int, optional.
            The MINIMUM number of cycles to perform. Note that in the
            ``Simulation`` class this is the MAXIMUM number of
            cycles to perform. The meaning is redefined by redefining
            the ``simulation_finished`` method.

        Returns
        -------
        N/A
        """
        super(UmbrellaWindowSimulation, self).__init__(cycle=cycle,
                                                       maxcycle=maxcycle)
        self.umbrella = umbrella
        self.overlap = overlap

    def is_finished(self, system):
        """
        Check if simulation is done.

        In the umbrella simulation, the simulation is finished when we
        cycle is larger than maxcycle and all particles have
        crossed self.overlap.

        Parameters
        ----------
        system : system object
            Used to check if current position(s) satisfy the ending criterion.

        Returns
        -------
        out : True if simulation is finished, false otherwise.
        """
        return (self.cycle > self.maxcycle and
                np.all(system.particles.pos > self.overlap))
