# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
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

parse_settings_file
    For parsing input settings from file.
"""
from __future__ import absolute_import
from .settings import parse_settings_file, write_settings_file
from .common import create_orderparameter
from .createsystem import create_system
from .createsimulation import create_simulation
from .createoutput import create_output
from .createforcefield import create_force_field
