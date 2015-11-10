# -*- coding: utf-8 -*-
"""This file contains methods for setting up plotters.

Specifically it defines colors, colorschemes and a method
for selecting a plotter.
Here we also hard-code some color schemes which may be usefull for
the plotting: the colorblind 10 scheme [cb10]_, the deep color scheme
from the seaborn project [deep]_ and the husl color scheme [husl]_.

Important functions
-------------------

- create_plotter: Method to create a plotter.

Folders
-------

- styles: This folder contains style files for matplotlib.

References
----------

.. [cb10] The colorblind_10 color scheme,
          https://jiffyclub.github.io/palettable/tableau/
.. [deep] The deep color scheme, from the seaborn project
          http://stanford.edu/~mwaskom/software/seaborn/index.html
.. [husl] The husl color scheme, http://www.husl-colors.org/
"""
from .mpl_plotting import MplPlotter, mpl_set_style


__all__ = ['create_plotter']


# Custom named colors:
_COLORS = {'almost_black': '#262626'}
# Custom color-schemes. The default will be defined by the style file.
# The husl schemes are suited when many different colors are needed. They
# are hard-coded with different number of colors.
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


def create_plotter(plotter, out_fmt, style):
    """
    Method to create a plotter.

    Parameters
    ----------
    plotter : string
        This string selects the plotter
    out_fmt : string
        This string selects the output format for the plot. Typically,
        'png', 'eps', 'svg', 'pdf' and so on.
    style : string
        This string defines a style for the plotter. It can be
        a filepath or a string which have a meaning to the plotter.
        How the style should be handled is defined in the plotter.
    """
    if plotter.lower() in ['mpl', 'matplotlib']:
        return MplPlotter(out_fmt, style)
    else:
        msg = 'Unknown plotter: {}'.format(plotter)
        raise ValueError(msg)
