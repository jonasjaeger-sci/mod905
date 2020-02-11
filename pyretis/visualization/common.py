# -*- coding: utf-8 -*-
# pylint: skip-file
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""This file contains common functions for the path density.

It contains some functions that is used to compare and process data,
like matching similar lists or attempt periodic shifts of values.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

hello_pathdensity_world (:py:func: `.hello_pathdensity_world`)
    Prints an ASCII message/image to screen.

diff_matching (:py:func: `.diff_matching`)
    Takes in two lists and their lengths, returns two lists with the
    indeces of the respective lists that differ from eachother.

try_data_shift (:py:func: `.try_data_shift`
    Takes in two lists of values, x and y, and calculates a linear
    regression and R**2-correlation of the data set. Attempts a shift of
    each data set by their respective median to increase the correlation.

shift_data (:py:func: `.shift_data`)
    Finds the median value of a given list of floats, and shifts the
    lower half of the data by the median.
"""
# pylint: disable=C0103
import scipy
from pyretis.inout import print_to_screen


def hello_pyvisa(noprint=False):
    """Pyvisa logo printing to screen."""
    msgtxt = ['Starting']
    msgtxt += [r"+------------------------------------------+"]
    msgtxt += [r"|   _______                                |"]
    msgtxt += [r"|  /   ___ \        _    ___         ___   |"]
    msgtxt += [r"| /_/\ \_/ /_  __  | |  / (_)____   /   |  |"]
    msgtxt += [r"|    /  __  / / /  | | / / / ___/  / /| |  |"]
    msgtxt += [r"|   / /   \ \/ /   | |/ / (__  )  / ___ |  |"]
    msgtxt += [r"|  /_/    _\  /    |___/_/____/  /_/  |_|  |"]
    msgtxt += [r"|        /___/                             |"]
    msgtxt += [r"|     ,       ,       ,       ,       ,    |"]
    msgtxt += [r"|   .'|     .'|     .'|     .'|     .'|    |"]
    msgtxt += [r"|   |*****  | :     | :     | :     | :    |"]
    msgtxt += [r"|   : '   **: '     : '     : '     : '    |"]
    msgtxt += [r"|   | |     |**  ***|****   | |     | |    |"]
    msgtxt += [r"|   ' :     ' :**   ' :  ***'*:     ' :    |"]
    msgtxt += [r"|   ; |     ; |     ; |     ; ***** ; |    |"]
    msgtxt += [r"|   | :     | :     | :     | :    *| :    |"]
    msgtxt += [r"|   : '     :*******: '     : ' *** : '    |"]
    msgtxt += [r"|   | |  ***| |     |*******|***    | |    |"]
    msgtxt += [r"|   :****   : ;     : ;     : ;     : ;    |"]
    msgtxt += [r"|   ,/      ,/      ,/      ,/      ,/     |"]
    msgtxt += [r"|   '       '       '       '       '      |"]
    msgtxt += [r"+------------------------------------------+"]
    msgtxt += ' '
    if not noprint:
        for txt in msgtxt:
            print_to_screen(txt, level='message')


def get_min_max(mydata, min_max, mini, maxi, acc):
    """Find minimum and maximum indeces.

    Parameters
    ----------
    mydata : list
        List of cycle numbers to be checked for index of given min/max
    min_max : list
        List of min/max values to search for
    mini : dict
        Dictionary of found min cycle number of lists acc/rej
    maxi : dict
        Dictionary of found max cycle number of lists acc/rej
    acc : string
        'a' or 'r' for acc/rej lists, respectively

    Returns/updates
    ---------------
    mini, maxi : dict
        Stores values for min/max in acc and rej lists to the correct dicts.

    """
    for i, item in enumerate(mydata):
        if item == min_max[0]:
            mini[acc] = i
            break
        elif item > min_max[0]:
            mini[acc] = i-1 if i > 0 else 0
            break

    for i, item in enumerate(mydata[mini[acc]:]):
        if item > min_max[1]:
            if i == 0:  # If first entry already is larger than max cycle
                maxi[acc] = 0
                break
            else:
                maxi[acc] = mini[acc] + i - 1
                break
        elif i == len(mydata) - 1:
            maxi[acc] = len(mydata) - 1
            # Do not need break here, is end of mydata


def get_startat(myfile, noprint=False):
    """Find last occurence of a 'Cycle: 0' in a file, and returns that line.

    Parameters
    ----------
    myfile : string
        Filename of file that is checked for restart line

    Returns
    -------
    startat : integer
        Index of file (line) with last restart line

    """
    startat = 0
    temp = open(myfile, 'r')
    for i, line in enumerate(temp):
        if 'Cycle: 0,' in line:
            startat = i
    if not noprint:
        print_to_screen('- Found last restart of ' +
                        '{} at line {}'.format(temp.name, startat),
                        level=None)
    temp.close()
    return startat+1


def diff_matching(l1, l2, lenp):
    """Check two lists for differences, returns lists of indices for each list.

    Parameters
    ----------
    l1, l2 : Lists
    lenp : list
        lengths of l1 and l2

    Returns
    -------
    d1, d2 : Lists
        Indeces of lists l1 and l2, respectively, to be deleted

    """
    d1, d2 = [], []
    t1, t2 = 0, 0

    # Early return if one of the lists is 0
    if lenp[0] == 0:
        return [], list(range(lenp[1]))
    elif lenp[1] == 0:
        return list(range(lenp[0])), []

    c1 = l1[0]
    c2 = l2[0]
    n1 = l1[t1]
    n2 = l2[t2]

    # Loop through lists
    while t1 < lenp[0] and t2 < lenp[1]:
        # set currect list values
        c1, c2 = l1[t1], l2[t2]
        if c1 > c2:
            t2 += 1
        elif c1 < c2:
            t1 += 1
        elif c1 == c2:
            # Common starting point found
            n1 = l1[t1]
            n2 = l2[t2]
            break
    if t1 == lenp[0] or t2 == lenp[1]:
        # Case if lists don't match at all
        d1 = [i for i in range(len(l1))]
        d2 = [i for i in range(len(l2))]
        return d1, d2
    else:
        # Add delete before commmon start
        d1 = [i for i in range(t1)]
        d2 = [i for i in range(t2)]

    # Continue looping from common start
    while t1 < lenp[0] and t2 < lenp[1]:
        if n1 == n2:
            t1 += 1
            t2 += 1
            try:
                n1 = l1[t1]
            except IndexError:
                # Reached end of l1
                for i in range(t2, lenp[1]):
                    d2.append(i)
                break
            try:
                n2 = l2[t2]
            except IndexError:
                # Reached end of l2
                for i in range(t1, lenp[0]):
                    d1.append(i)
                break
        elif n1 != n2:
            if n1 < n2:
                d1.append(t1)
                t1 += 1
                try:
                    n1 = l1[t1]
                except IndexError:
                    # Reached end of l1
                    for i in range(t2, lenp[1]):
                        d2.append(i)
                    break
            elif n1 > n2:
                d2.append(t2)
                t2 += 1
                try:
                    n2 = l2[t2]
                except IndexError:
                    # Reached end of l2
                    for i in range(t1, lenp[0]):
                        d1.append(i)
                    break
    return d1, d2


def try_data_shift(x, y, op1):
    """Check if shifting increases correlation.

    Function that checks if correlation of data increases by shifting
    either sets of values, x or y, or both. Correlation is checked by
    doing a simple linear regression on the different sets of data:
    - x and y , x and yshift, xshift and y, xshift and yshift.
    If linear correlation increases (r-squared value), data sets are
    updated.

    As a precoursion, no shift
    is performed on x values if they are of the first order parameter 'op1'

    Parameters
    ----------
    x, y : list
        Floats, data values
    op1 : string
        Label of x values in PathDensity dictionary

    Returns
    -------
    x, y : list
        Floats, updated (or unchanged) data values
        (If changed, returns x_temp or y_temp or both)

    """
    # The unshifted data
    _, _, r_val, _, _ = scipy.stats.linregress(x, y)
    r_2 = r_val**2
    # The Y-shifted data
    y_temp = shift_data(y)
    _, _, r_y, _, _ = scipy.stats.linregress(x, y_temp)
    r_y2 = r_y**2
    yshift = bool(r_y2 > r_2)
    # The X-shifted data
    x_temp = shift_data(x)
    _, _, r_x, _, _ = scipy.stats.linregress(x_temp, y)
    r_x2 = r_x**2
    xshift = bool(r_x2 > r_2 and r_x2 > r_y2)
    # Comparing effectiveness of both shifts individually, and combined
    _, _, r_xy, _, _ = scipy.stats.linregress(x_temp, y_temp)
    r_xy2 = r_xy**2
    xyshift = bool(r_xy2 > r_2 and r_xy2 > r_y2 and r_xy2 > r_x2)

    # If first op is op1, don't shift data
    if (xyshift) and op1 != 'op1':
        return x_temp, y_temp
    elif (xshift) and op1 != 'op1':
        return x_temp, y
    elif yshift:
        return x, y_temp
    return x, y


def shift_data(x):
    """Shifts the data under the median.

    Function that takes in a list of data, and shifts all values
    below the median value of the data by the max difference,
    effectively shifting parts of the data periodically in order to
    give clusters for visualization.

    Parameters
    ----------
    x : list
        Floats, data values

    Returns
    -------
    xnorm : list
        Floats where some values are shifted values of x,
        and some are left unchanged.

    """
    xmin, xmax = min(x), max(x)
    xnorm = []
    # The max difference in x-data
    dx = xmax-xmin
    # The Median of x-data
    medix = xmin + 0.5*dx

    for i in x:
        if i < medix:
            xnorm.append(i+dx)
        else:
            xnorm.append(i)
    return xnorm
