# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Dummy order parameter for running tests."""
from pyretis.orderparameter import OrderParameter


class FooOrderParameter(OrderParameter):
    """FooOrderParameter(OrderParameter) - Dummy order parameter for tests."""
    def __init__(self, name, desc='Dummy order parameter'):
        super().__init__(description=desc)
        self.name = name


class BarOrderParameter(object):
    """BarOrderParameter(object) - Dummy order parameter for tests."""
    def __init__(self, description='Dummy test order parameter'):
        self.description = description


class BazOrderParameter(object):
    """BazOrderParameter(object) - Dummy order parameter for tests."""
    def __init__(self, description='Dummy test order parameter'):
        self.description = description

    def calculate(self, system):
        """Obtain the order parameter."""
        pass
