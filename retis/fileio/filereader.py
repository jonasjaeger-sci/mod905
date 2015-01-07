#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
filereader.py: This file handles input/output
"""
import os
def readinputfile(filename):
    """
    readinputfile: This function reads the input parameters
    """
    if not os.path.isfile(filename):
        raise IOError('Could not locate file: {}'.format(filename))

