# -*- coding: utf-8 -*-
"""Dummy integrator for tests."""
from pyretis.core.integrators import Integrator


__all__ = []


class FooIntegrator(Integrator):
    """FooIntegrator(Integrator) - Dummy integrator for tests."""

    def __init__(self, timestep, parameter=0.0,
                 desc='Dummy test integrator'):
        super(FooIntegrator, self).__init__(timestep, desc=desc,
                                            dynamics=None)
        self.parameter = parameter

    def integration_step(self, system):
        """Perform the integration step."""
        return NotImplementedError


class BarIntegrator(object):
    """FailingIntegrator(object) - Dummy integrator for tests."""
    def __init__(self, desc='Dummy test integrator'):
        self.desc = desc


class BazIntegrator(object):
    """FailingIntegrator(object) - Dummy integrator for tests."""
    def __init__(self, desc='Dummy test integrator'):
        self.desc = desc
        self.integration_step = 'fake_step'
