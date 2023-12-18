# -*- coding: utf-8 -*-
# Copyright (c) 2023, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A script for building the C Lennard-Jones extension."""
from setuptools import (
    setup,
    Extension,
)
import numpy as np


LJMODULE = Extension(
    'ljc',
    sources=['ljc.c'],
    extra_compile_args=["-Ofast", "-march=native"]
)
setup(
    name="PyRETIS Lennard-Jones C extension",
    description="C extension for the Lennard-Jones potential.",
    ext_modules=[LJMODULE],
    include_dirs=[np.get_include()],
)
