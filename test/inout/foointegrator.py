# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Dummy integrator for tests."""
from pyretis.integrators import Integrator


__all__ = []


class FooIntegrator(Integrator):
    """FooIntegrator(Integrator) - Dummy integrator for tests."""

    def __init__(self, timestep, extra=0.0,
                 desc='Dummy test integrator'):
        super(FooIntegrator, self).__init__(timestep, desc=desc,
                                            dynamics=None)
        self.extra = extra

    def integration_step(self, system):
        """Perform the integration step."""
        raise NotImplementedError


class BarIntegrator(object):
    """FailingIntegrator(object) - Dummy integrator for tests."""
    def __init__(self, desc='Dummy test integrator'):
        self.desc = desc


class BazIntegrator(object):
    """FailingIntegrator(object) - Dummy integrator for tests."""
    def __init__(self, desc='Dummy test integrator'):
        self.desc = desc
        self.integration_step = 'fake_step'
