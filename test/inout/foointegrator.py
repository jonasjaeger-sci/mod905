# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Dummy integrator for tests."""
from pyretis.engines import MDEngine


__all__ = []


class FooIntegrator(MDEngine):
    """FooIntegrator(MDEngine) - Dummy integrator for tests."""

    def __init__(self, timestep, extra=0.0,
                 description='Dummy test integrator'):
        super(FooIntegrator, self).__init__(timestep, description,
                                            dynamics=None)
        self.extra = extra

    def integration_step(self, system):
        """Perform the integration step."""
        raise NotImplementedError


class BarIntegrator(object):
    """FailingIntegrator(object) - Dummy integrator for tests."""
    def __init__(self, description='Dummy test integrator'):
        self.description = description


class BazIntegrator(object):
    """FailingIntegrator(object) - Dummy integrator for tests."""
    def __init__(self, description='Dummy test integrator'):
        self.description = description
        self.integration_step = 'fake_step'
