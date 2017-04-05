# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""A scripy for building the c Velocity Verlet extension."""
from distutils.core import setup, Extension


CMODULE = Extension('vvintegrator', sources=['vvintegrator.c'],
                    extra_compile_args=['-Ofast', '-march=native'])
setup(name='pyretis Velocity Verley c extension',
      description='A c extension for the Velocity Verlet integrator.',
      ext_modules=[CMODULE])
