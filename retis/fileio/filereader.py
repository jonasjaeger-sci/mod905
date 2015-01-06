#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fileio.py: This file handles input/output
"""
import os
def readinputfile(filename):
    if not os.path.isfile(filename):
        raise IOError('Could not locate file: {}'.format(filename))

