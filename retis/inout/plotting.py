# -*- coding: utf-8 -*-
"""
This file contains methods for creating plots.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
import os


__all__ = ['set_plotting_style']
# These are color definitions that we will use
_COLORS = {'almost_black': '#262626'}
# next follows some hard-coded color-schemes. The default will be deep.
# In case we need more colors, we will use one of the husl schemes. Here
# they are hard-coded with different numbers of colors.
# Refs:
# colorblind_10 is from: https://jiffyclub.github.io/palettable/tableau/
# deep is from the seaborn project
# husl are from http://www.husl-colors.org/ as implemented in seaborn
_COLOR_SCHEME = {'colorblind_10': ['#006BA4', '#FF800E', '#ABABAB', '#595959',
                                   '#5F9ED1', '#C85200', '#898989', '#A2C8EC',
                                   '#FFBC79', '#CFCFCF'],
                 'deep': ['#4C72B0', '#55A868', '#C44E52', '#8172B2',
                          '#CCB974', '#64B5CD'],
                 'husl_10': ['#f67088', '#db8831', '#ad9c31', '#77aa31',
                             '#33b07a', '#35aca4', '#38a8c5', '#6e9af4',
                             '#cc79f4', '#f565cc'],
                 'husl_15': ['#f67088', '#f37932', '#ca9131', '#ad9c31',
                             '#8ea531', '#4fb031', '#33b07a', '#34ad99',
                             '#36abae', '#38a8c5', '#3ba3ec', '#9491f4',
                             '#cc79f4', '#f45fe3', '#f569b7'],
                 'husl_20': ['#f67088', '#f7754f', '#db8831', '#c29431',
                             '#ad9c31', '#96a331', '#77aa31', '#31b23e',
                             '#33b07a', '#34ae92', '#35aca4', '#36abb3',
                             '#38a8c5', '#3aa5de', '#6e9af4', '#a38cf4',
                             '#cc79f4', '#f45bf1', '#f565cc', '#f66bad']}


_STYLE_FILE = os.sep.join([os.path.dirname(__file__), 'pytismol.mplstyle'])


def set_plotting_style(style='pytismol'):
    """
    This will set up the plotting according to some given style.
    Styles can be given as string, for instance 'ggplot', 'bmh',
    'grayscale' (i.e. one of the styles in plt.style.available) or
    as a file (full path is needed). The default pytismol style
    is stored in _STYLE_FILE and can be selected with 'pytismol'.
    Style equal to None is just the default matplotlib style.

    Parameters
    ----------
    style : string, optional
        This selects the style to use, it can be a file path or the
        string with the style name.
    """
    if style is None:
        return
    if style == 'pytismol':
        style = _STYLE_FILE
    if mpl.__version__ < '1.4.0':  # default to loading from file
        rcpar = mpl.rc_params_from_file(style)
        mpl.rcParams.update(rcpar)
    else:
        if style in plt.style.available:
            plt.style.use(style)
        else:  # assume this is just a file
            rcpar = mpl.rc_params_from_file(style)
            mpl.rcParams.update(rcpar)
