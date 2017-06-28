# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Helper methods for testing pyretis.core.common"""


def function5(arg1, arg2, *args, arg3=100, arg4=100):
    pass


def function6(arg1, arg2, arg3=100, *, arg4=10):
    pass


def function7(arg1, arg2, arg3=100, *args, arg4, arg5=10):
    pass
