# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the MIT License. See LICENSE for more info.
"""
pyretis - A simulation package for rare event simulations.
Copyright (C) 2015  The pyretis team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
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


FULL_VERSION = '0.2.0.dev0'  # copied from version.py generated.

setup(name='pyretis',
      version=FULL_VERSION,
      description='A simulation package for rare events',
      long_description=get_long_description(),
      url='http://www.pyretis.org',
      author='The pyretis team',
      author_email='pyretis@pyretis.org',
      license='MIT',
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: MIT License',
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
      install_requires=['numpy>=1.6.0',
                        'scipy>=0.13.3',
                        'matplotlib>=1.1',
                        'jinja2>=2.7.2',
                        'docutils>=0.11',
                        'tqdm>=4.7.0'],
      scripts=['bin/pyretisrun.py', 'bin/pyretisanalyse.py'])
