# -*- coding: utf-8 -*-
"""
pyretis - A simulation package for rare event simulations.
Copyright (C) 2015  The pyretis team

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
from codecs import open as openc
import os
import re
from setuptools import setup, find_packages


def get_long_description():
    """Return the contents of README.rst"""
    here = os.path.abspath(os.path.dirname(__file__))
    # Get the long description from the README file
    long_description = ''
    with openc(os.path.join(here, 'README.rst'), encoding='utf-8') as fileh:
        long_description = fileh.read()
    return long_description


def find_version(*file_paths):
    """Look for the version in __init__.py of pyretis."""
    here = os.path.abspath(os.path.dirname(__file__))
    dirname = os.path.join(here, *file_paths)
    with openc(dirname, encoding='utf-8') as fileinit:
        version_file = fileinit.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


setup(name='pyretis',
      version=find_version('pyretis', '__init__.py'),
      description='A simulation package for rare events',
      long_description=get_long_description(),
      url='http://www.pyretis.org',
      author='The pyretis team',
      author_email='pyretis@pyretis.org',
      license='GPLv3',
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   ('License :: OSI Approved :: '
                    'GNU General Public License v3 (GPLv3)'),
                   'Natural Language :: English',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: POSIX',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Topic :: Scientific/Engineering :: Physics'],
      keywords='simulation TIS RETIS',
      packages=find_packages(exclude=['docs']),
      install_requires=['numpy>=1.6.0', 'scipy>=0.13.3',
                        'matplotlib>=1.1', 'jinja2>=2.7.2',
                        'docutils>=0.11'],
      scripts=['bin/pyretisrun.py'])
