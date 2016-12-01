# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of integrators.

This package defines MD integrators for pyretis.


Package structure
-----------------

Modules
~~~~~~~

integrator.py
    Defines the base integrator class.

internal_integrators.py
    Defines internal pyretis integrators.

external_integrators.py
    Defines the interface for external integrators.

gromacs.py
    Defines an integrator for use with GROMACS version 5.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

integrator_factory
    A method to create integrators from settings.
"""
from pyretis.core.common import generic_factory
from .integrator import Integrator
from .internal_integrators import Verlet, VelocityVerlet, Langevin
from .external_integrators import ExternalScript
from .gromacs import GromacsExt


def integrator_factory(settings):
    """Create an integrator according to the given integrator settings.

    This function is included as a convenient way of setting up and
    selecting a integrator. It will return the selected integrator.

    Parameters
    ----------
    settings : dict
        This defines how we set up and select the integrator.

    Returns
    -------
    out : object like `Integrator`.
        This object represents the integrator and will be one of the
        classes defined in `pyretis.integrators`.
    """
    integrator_map = {'velocityverlet': {'cls': VelocityVerlet},
                      'verlet': {'cls': Verlet},
                      'langevin': {'cls': Langevin}}
    return generic_factory(settings, integrator_map, name='integrator')
