#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This is just for testing that we can execute external programs."""
import sys


if __name__ == '__main__':
    # pylint: disable=invalid-name
    print('This is a program for testing external commands')
    args = sys.argv
    if len(args) > 1:
        print('ERROR: Program were given arguments!', file=sys.stderr,
              end='\n')
        sys.exit(1)
    else:
        sys.exit(0)
