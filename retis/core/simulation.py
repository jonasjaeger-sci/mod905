#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
simulation.py
"""

import numpy as np

__all__ = ["Simulation", "UmbrellaSimulation"]

class Simulation(object):
    """This class defines the simulation."""
    def __init__(self, cycle=0, maxcycle=0):
        """ 
        Initialization of the system.
    
        Parameters
        ----------
        self : 
        cycle : int, optional. The current cycle
        maxcycle : int, optional. Maximum number of cycles to perform

        Returns
        -------
        N/A, but initiates self.tasks.
        """
        self.cycle = cycle
        self.maxcycle = maxcycle
        self.task = []

    def simulation_finished(self):
        """
        Function to determine if simulation is finished

        Parameters
        ----------
        self : 
        system : the system object, optional.

        Returns
        -------
        True if simulation is finished, false otherwise.
        """
        return self.cycle > self.maxcycle

    def step(self):
        """ 
        Run a simulation step. Here, the tasks in self.task
        will be executed.
    
        Parameters
        ----------
        self : 

        Returns
        -------
        N/A, but my modify the system and other external variabales.

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
        for task in self.task:
            func, args, kwargs = task['func'], task['args'], task['kwargs']
            if callable(func): 
                func(*args, **kwargs)
        return True


class UmbrellaSimulation(Simulation):
    """This is a special case of the simulation class with settings
    to help set up a umbrella simulation.
    """
    def __init__(self, umbrella, overlap, cycle=0, maxcycle=0):
        """ 
        Initialization of a umbrella simulation.
    
        Parameters
        ----------
        self : 
        umbrella : list = [float, float]. The umbrella window to consider.
        overlap : float, the position we have to cross before the simulation
            is done.
        cycle : int, optional. The current simulation cycle.
        maxcycle : int, optional. The ``minimum`` number of cycles to perform.
            Note that in the Simulation class this is the ``maximum`` number of
            cycles to perform. The meaning is redefined by redefining 
            the ``simulation_finished`` method.

        Returns
        -------
        N/A
        """

        super(UmbrellaSimulation, self).__init__(cycle=cycle, 
                                                 maxcycle=maxcycle)
        self.umbrella = umbrella
        self.overlap = overlap
    def simulation_finished(self, system):
        """
        Check if simulation is done. 
    
        In the umbrella simulation, the simulation is finished when we
        cycle is larger than maxcycle and at least one particle has
        crossed self.overlap.

        Parameters
        ----------
        self :
        system : the system object we are acting on.
    
        """
        return (self.cycle>self.maxcycle and
                np.any(system.particles['r']>self.overlap))
        

