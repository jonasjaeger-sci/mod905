# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Methods and classes for text based output and input.

This file contains some methods and classes that handle output and
input of 'table-based' output. Typically the data created here will be
written to the screen during the simulation or as a simple column
output.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

txt_save_columns
    For writing a simple column-based output using numpy.
"""
import logging
import numpy as np
from pyretis.inout.common import create_backup
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['txt_save_columns']


def txt_save_columns(outputfile, header, variables, backup=False):
    """Save variables to a text file using `numpy.savetxt`.

    Note that the variables are assumed to be numpy.arrays of equal
    shape and that the output file may also be a compressed file in
    gzip format (this is selected by letting the output file name
    end with '.gz').

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    header : string
        String that will be written at the beginning of the file.
    variables : tuple of numpy.arrays
        These are the variables that will be save to the text file.
    backup : boolean
        Determines if we should backup old files or not.
    """
    if backup:
        msg = create_backup(outputfile)
        if msg:
            logger.warning(msg)
    nvar = len(variables)
    mat = np.zeros((len(variables[0]), nvar))
    for i, vari in enumerate(variables):
        try:
            mat[:, i] = vari
        except ValueError:
            msg = 'Could not align variables, skipping (writing zeros)'
            logger.warning(msg)
    np.savetxt(outputfile, mat, header=header)
