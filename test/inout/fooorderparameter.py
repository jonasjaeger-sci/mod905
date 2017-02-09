# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Dummy order parameter for running tests."""
from pyretis.orderparameter import OrderParameter


__all__ = []


class FooOrderParameter(OrderParameter):
    """FooOrderParameter(OrderParameter) - Dummy order parameter for tests."""

    def __init__(self, name, desc='Dummy order parameter'):
        super().__init__(name, desc=desc)


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
