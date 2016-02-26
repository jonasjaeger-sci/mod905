# -*- coding: utf-8 -*-
"""Dummy order parameter for running tests."""
from pyretis.core.orderparameter import OrderParameter


__all__ = []


class FooOrderParameter(OrderParameter):
    """FooOrderParameter(OrderParameter) - Dummy order parameter for tests."""

    def __init__(self, name, desc='Dummy order parameter'):
        super(FooOrderParameter, self).__init__(name, desc=desc)


class BarOrderParameter(object):
    """FailingIntegrator(object) - Dummy integrator for tests."""
    def __init__(self, desc='Dummy test integrator'):
        self.desc = desc

class BazOrderParameter(object):
    """FailingIntegrator(object) - Dummy integrator for tests."""
    def __init__(self, desc='Dummy test integrator'):
        self.desc = desc

    def calculate(self, system):
        raise NotImplementedError
