# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This package contains functions for input/output of settings.

Package structure
-----------------

Modules
~~~~~~~

common.py
    Common methods for handing settings. Defines a method to dynamically
    import methods and classes from user specified modules.

createforcefield.py
    Handle creation of force fields from input simulation settings.

createoutput.py
    Handle creation of output tasks from input simulation settings.

createsimulation.py
    Handle creation of simulations from input simulation settings.

createsystem.py
    Handle creation of systems from input simulation settings.

__init__.py
    This file, handles imports for pyretis.

settings.py
    Handle parsion of input settings.

Important methods defined in this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

create_engine (:py:func:`.settings.common.create_engine`)
    Create an engine from input settings.

create_force_field (:py:func:`.createforcefield.create_force_field`)
    Create a force field from input settings.

create_orderparameter (:py:func:`.common.create_orderparameter`)
    Create an order parameter from input settings.

create_output_tasks (:py:func:`.createoutput.create_output_tasks`)
    Create output tasks from input settings.

create_simulation (:py:func:`.createsimulation.create_simulation`)
    Create a simulation from input settings.

create_system (:py:func:`.createsystem.create_system`)
    Create a system from input settings.

is_single_tis (:py:func:`.settings.is_single_tis`)
    A method which determines is input settings represents a
    single TIS simulation.

parse_settings_file (:py:func:`.settings.parse_settings_file`)
    For parsing input settings from file.

write_settings_file (:py:func:`..settings.write_settings_file`)
    For writing simulation settings to a file.
"""
from .settings import parse_settings_file, write_settings_file, is_single_tis
from .common import create_orderparameter, create_engine
from .createsystem import create_system
from .createsimulation import create_simulation
from .createoutput import create_output_tasks
from .createforcefield import create_force_field
