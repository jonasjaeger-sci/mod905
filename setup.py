# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""
pyretis - A simulation package for rare event simulations.
Copyright (C) 2015  The pyretis team

This file is part of pyretis.

pyretis is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pyretis is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with pyretis. If not, see <http://www.gnu.org/licenses/>
"""
from codecs import open as openc
import os
from setuptools import setup, find_packages


def get_long_description():
    """Return the contents of README.rst"""
    here = os.path.abspath(os.path.dirname(__file__))
    # Get the long description from the README file
    long_description = ''
    with openc(os.path.join(here, 'README.rst'), encoding='utf-8') as fileh:
        long_description = fileh.read()
    return long_description


FULL_VERSION = '0.2.1.dev0'  # copied from version.py generated.

setup(name='pyretis',
      version=FULL_VERSION,
      description='A simulation package for rare events',
      long_description=get_long_description(),
      url='http://www.pyretis.org',
      author='The pyretis team',
      author_email='pyretis@pyretis.org',
      license='LGPLv3',
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   ('License :: OSI Approved :: '
                    'GNU Lesser General Public License v3 (LGPLv3)'),
                   'Natural Language :: English',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: POSIX',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Topic :: Scientific/Engineering :: Physics'],
      keywords='rare md mc tps simulation tis retis',
      packages=find_packages(exclude=['docs']),
      install_requires=['numpy>=1.6.0',
                        'scipy>=0.13.3',
                        'matplotlib>=1.1',
                        'jinja2>=2.7.2',
                        'docutils>=0.11',
                        'tqdm>=4.7.0'],
      scripts=['bin/pyretisrun.py', 'bin/pyretisanalyse.py'])
