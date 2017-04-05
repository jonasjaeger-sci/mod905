# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""A script for building the c Lennard-Jones extension."""
from distutils.core import setup, Extension

WCAORDER = Extension('wcalambda', sources=['wcalambda.c'],
                     extra_compile_args=['-Ofast', '-march=native'])
WCAFORCE = Extension('wcaforces', sources=['wcaforces.c'],
                     extra_compile_args=['-Ofast', '-march=native'])
setup(name='pyretis WCA c extension',
      description='A c extension for WCA potential.',
      ext_modules=[WCAORDER, WCAFORCE])
