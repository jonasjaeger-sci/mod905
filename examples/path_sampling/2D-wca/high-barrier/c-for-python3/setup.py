# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A script for building the C extension (order parameter and potential)."""
from distutils.core import (  # pylint: disable=no-name-in-module,import-error
    setup,
    Extension,
)

WCAORDER = Extension(
    'wcalambda',
    sources=['wcalambda.c'],
    extra_compile_args=['-Ofast', '-march=native'],
)
WCAFORCE = Extension(
    'wcaforces',
    sources=['wcaforces.c'],
    extra_compile_args=['-Ofast', '-march=native'],
)
setup(
    name='PyRETIS WCA C extension',
    description='C extensions for the WCA potential.',
    ext_modules=[WCAORDER, WCAFORCE],
)
