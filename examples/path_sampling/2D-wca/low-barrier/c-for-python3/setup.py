# -*- coding: utf-8 -*-
"""A scripy for building the c Lennard-Jones extension."""
from distutils.core import setup, Extension

WCAFORCE = Extension('wcaforces', sources=['wcaforces.c'],
                     extra_compile_args=['-Ofast', '-march=native'])
setup(name='pyretis WCA c extension',
      description='A c extension for WCA potential.',
      ext_modules=[WCAFORCE])
