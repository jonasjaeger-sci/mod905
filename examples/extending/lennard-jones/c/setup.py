# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A scripy for building the c Lennard-Jones extension."""
from distutils.core import setup, Extension


LJMODULE = Extension('ljc', sources=['ljc.c'],
                     extra_compile_args=["-Ofast", "-march=native"])
setup(name="pyretis Lennard-Jones c extension",
      description="A c extension for the Lennard-Jones potential.",
      ext_modules=[LJMODULE])
