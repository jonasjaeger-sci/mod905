# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Definition of engines.

This package defines engines for pyretis. The engines are responsible
for carrying out dynamics for a system. This can in principle both
be molecular dynamics or Monte Carlo dynamics. Typically, with RETIS,
this will be molecular dynamics in some form in order to propagate
the equations of motion and obtain new trajectories.



Package structure
-----------------

Modules
~~~~~~~

engine.py (:py:mod:`pyretis.engines.engine`)
    Defines the base engine class.

internal.py (:py:mod:`pyretis.engines.internal`)
    Defines internal pyretis engines.

external.py (:py:mod:`pyretis.engines.external`)
    Defines the interface for external engines.

gromacs.py (:py:mod:`pyretis.engines.gromacs`)
    Defines an engine for use with GROMACS.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

engine_factory (:py:func:`.engine_factory`)
    A method to create engines from settings.
"""
from pyretis.core.common import generic_factory
from .internal import MDEngine, Verlet, VelocityVerlet, Langevin
from .external import ExternalMDEngine
from .gromacs import GromacsEngine


def engine_factory(settings):
    """Create an engine according to the given settings.

    This function is included as a convenient way of setting up and
    selecting an engine. It will return the created engine.

    Parameters
    ----------
    settings : dict
        This defines how we set up and select the engine.

    Returns
    -------
    out : object like :py:class:`.EngineBase`
        The object representing the engine to use in a simulation.
    """
    engine_map = {'velocityverlet': {'cls': VelocityVerlet},
                  'verlet': {'cls': Verlet},
                  'langevin': {'cls': Langevin},
                  'gromacs': {'cls': GromacsEngine}}
    return generic_factory(settings, engine_map, name='engine')
