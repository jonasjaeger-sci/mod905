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
    cycle : dict of ints
        This dict stores information about the number of cycles.
        The int in cycle['end'] represents the cycle number where the
        simulation should end.
        The int in cycle['step'] represents the current cycle number.
        The int in cycle['start'] is the cycle number we started at.
    task : list of dicts
        Each dich contain the tasks to be done. This are represented as a
        dict with the key-words 'func', 'args', 'kwargs'. Tasks are called as
        task['func'](*args, **kwargs)
    """
    def __init__(self, endcycle=0, startcycle=0):
        """
        Initialization of the system.

        Parameters
        ----------
        startcycle : int, optional.
            The cycle we start the simulation on, can be usefull if
            restarting.
        endcycle : int, optional.
            This number represents the cycle number where the simulation
            should end. It some simulations (e.g. MD) this would be the number
            of steps to perform, in other simulations this could be the
            minimum or maximum number of cycles to perform

        Returns
        -------
        N/A, but initiates self.tasks.
        """
        self.cycle = {'step': startcycle, 'end': endcycle,
                      'start': startcycle}
        self.task = []

    def is_finished(self):
        """
        Function to determine if simulation is finished. In this
        version, the simulation is done if the current step number
        is larger than the end cycle. Note that the number of steps
        performed is dependent of the value of self.cycle['start'].

        Returns
        -------
        out : True if simulation is finished, false otherwise.
        """
        return self.cycle['step'] >= self.cycle['end']

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
        self.cycle['step'] += 1
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
    startcycle : int
        The current simulation cycle.
    mincycle : int
        The MINIMUM number of cycles to perform.
    """
    def __init__(self, umbrella, overlap, mincycle=0, startcycle=0):
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
        super(UmbrellaWindowSimulation, self).__init__(endcycle=mincycle,
                                                       startcycle=startcycle)
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
        return (self.cycle['step'] > self.cycle['end'] and
                np.all(system.particles.pos > self.overlap))
