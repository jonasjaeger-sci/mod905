# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A script for building the C Velocity Verlet extension."""
from distutils.core import (  # pylint: disable=no-name-in-module,import-error
    setup,
    Extension,
)
import numpy as np


CMODULE = Extension(
    'vvintegrator',
    sources=['vvintegrator.c'],
    extra_compile_args=['-Ofast', '-march=native']
)
setup(
    name='PyRETIS Velocity Verlet C extension',
    description='C extension for the Velocity Verlet integrator.',
    ext_modules=[CMODULE],
    include_dirs=[np.get_include()],
)
