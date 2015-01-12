#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
simulation.py
"""

import numpy as np

class Simulation(object):
    """This class defines the simulation."""
    def __init__(self, cycle=0, maxcycle=0):
        """Initialization of the simulation

        Keyword arguments:
        cycle: the current cycle 
        maxcycle: maximum number of cycles to perform
        """
        self.cycle = cycle
        self.maxcycle = maxcycle
        self.task = []

    def step(self, system):
        """Run a simulation step"""
        if self.simulation_finished(system): return False
        self.cycle += 1
        for t in self.task:
            f, args, kwargs = t['func'], t['args'], t['kwargs']
            if callable(f): f(*args, **kwargs)
        return True

    def calculate_properties(self):
        """Calculate properties"""
        pass

    def simulation_finised(self):
        """Function to determine if simulation is finished"""
        if self.cycle>self.maxcycle:
            # do apropriate action
            return True
        else:
            return False

class UmbrellaSimulation(Simulation):
    """This is a special case of the simulation class with settings
    to help set up a umbrella simulation.
    """
    def __init__(self, umbrella=[None,None], overlap=None, cycle=0,
                 maxcycle=0):
        """Initialization of the umbrella simulation
        
        Keyword arguments:
        umbrella: the umbrella window to consider
        overlap: the overlap with the next umbrella
        """
        super(UmbrellaSimulation, self).__init__(cycle=cycle, 
                                                 maxcycle=maxcycle)
        self.umbrella = umbrella
        self.overlap = overlap
    def simulation_finished(self, system):
        """Check if simulation is done. 
        The simulation is done if we have exceeded the maximum
        number of steps or if we have passed the point we have to pass"""
        return (self.cycle>self.maxcycle and
                np.any(system.r>self.overlap))
        

