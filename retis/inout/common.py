# -*- coding: utf-8 -*-
"""
This file contains common methods and functions for the input/output.
"""
from __future__ import absolute_import
import os


__all__ = ['create_backup']


def create_backup(outputfile):
    """
    This method will check if the given filename exist and if it
    does, it will move that file to a new filename such that the given
    one can be used without overwriting.

    Parameters
    ----------
    outputfile : string
        This is the name of the file we wish to create

    Returns
    -------
    out : string
        This string is None if no backup is made, otherwise it will just
        say what file was moved (and to where).

    Note
    ----
    No warning is issued here. This is just in case the msg returned here
    will be part of some more elaborate message.
    """
    filename = '{}'.format(outputfile)
    fileid = 0
    msg = None
    while os.path.isfile(filename) or os.path.isdir(filename):
        filename = '{}_{}'.format(outputfile, fileid)
        fileid += 1
    if fileid > 0:
        msg = 'Backup existing file {} to {}'.format(outputfile, filename)
        os.rename(outputfile, filename)
    return msg
