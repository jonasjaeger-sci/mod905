# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Dummy order parameter for running tests."""
from pyretis.orderparameter import OrderParameter


class FooOrderParameter(OrderParameter):  # pylint: disable=abstract-method
    """FooOrderParameter(OrderParameter) - Dummy order parameter for tests."""

    def __init__(self, name, desc='Dummy order parameter'):
        super().__init__(description=desc)
        self.name = name


class BarOrderParameter:  # pylint: disable=too-few-public-methods
    """BarOrderParameter - Dummy order parameter for tests."""

    def __init__(self, description='Dummy test order parameter'):
        self.description = description


class BazOrderParameter:  # pylint: disable=too-few-public-methods
    """BazOrderParameter - Dummy order parameter for tests."""

    def __init__(self, description='Dummy test order parameter'):
        self.description = description

    def calculate(self, system):
        """Obtain the order parameter."""
