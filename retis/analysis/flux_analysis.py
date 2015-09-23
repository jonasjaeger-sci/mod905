# -*- coding: utf-8 -*-
"""
This file contains methods for analysis of crossings for the
flux data
"""
from __future__ import absolute_import
#from .analysis import analyse_data
import numpy as np

__all__ = ['analyse_flux']


def analyse_flux(fluxdata, interfaces, endstep, settings):
    """
    This method will run the analysis on several order parameters and
    collect the results into a structure which is convenient for plotting.

    Parameters
    ----------
    fluxdata : list of tuples of ints
        The contents of this array is the data obtained from a MD simulation
        for the fluxes.
    interfaces : list of floats
        These are the interfaces used in the simulation.
    endstep : int
        This is the last step done in the simulation.
    settings : dict
        This dict contains the settings for the analysis.

    Returns
    -------
    results : numpy.array

    """
    results = {}
    eff_cross, ncross, neffcross, times = _effective_crossings(fluxdata,
                                                               len(interfaces),
                                                               endstep)
    results['effective crossings'] = eff_cross
    results['ncross'] = ncross
    results['neffcross'] = neffcross
    results['times'] = times
    time_step = 0.002
    _calculate_flux(eff_cross[0], times['OA'], settings['skipcross'],
                    time_step)
    return results


def _effective_crossings(fluxdata, nint, endstep):
    """
    This method will analyse the flux output and obtain the effective
    crossings.

    Parameters
    ----------
    fluxdata : list of tuples of ints
        The contents of this array is the data obtained from a MD simulation
        for the fluxes.
    nint : int
        The number of interfaces used.
    endstep : int
        This is the last step done in the simulation.

    Returns
    -------
    eff_cross : list
    ncross : list of ints
        ncross[i] = the number of crossings for interface i.
    neffcross : list of ints
        neffcross[i] = the number of effective crossings for interface i.
    time_in_state : dict
        The time spent in the different states which are labelled with the
        keys 'A', 'B', 'OA', 'OB' where 'O' is taken to mean overall state.

    Note
    ----
    We do here a lot of intf - 1. This is just to be compatible with the old
    fortran code where the interfaces are numberes 1, 2, 3 rather than 0, 1, 2.
    If this is to be changed in the future the '-1' can just be removed.
    """
    # first line is used to determine if we start in B or A
    overallstate_a = not (fluxdata[0][1] == 2 and fluxdata[0][2] < 0)
    firstcross = [False] * nint
    ncross = [0] * nint
    neffcross = [0] * nint
    end = {'A': 0, 'B': 0, 'OA': 0, 'OB': 0}
    start = {'A': 0, 'B': 0, 'OA': 0, 'OB': 0}
    time_in_state = {'A': 0, 'B': 0, 'OA': 0, 'OB': 0}
    eff_cross = {key: [] for key in range(nint)}
    time, intf, sign = None, None, None
    for (time, intf, sign) in fluxdata:
        if sign > 0:  # positive direction
            if intf - 1 == 0:  # moving out of a
                end['A'] = time
                time_in_state['A'] += (end['A'] - start['A'])
            elif intf - 1 == 2:  # moving into B
                start['B'] = time
                if overallstate_a:  # if we came from A
                    end['OA'] = time
                    start['OB'] = time
                    time_in_state['OA'] += (end['OA'] - start['OA'])
                    overallstate_a = not overallstate_a
            ncross[intf - 1] += 1
            if firstcross[intf - 1]:
                firstcross[intf - 1] = True
                neffcross[intf - 1] += 1
                eff_cross[intf - 1].append((time - time_in_state['OB'], time))
        elif sign < 0:
            if intf - 1 == 0:  # moving into A
                firstcross = [True] * nint
                start['A'] = time
                if not overallstate_a:  # if we came from B
                    end['OB'] = time
                    start['OA'] = time
                    time_in_state['OB'] += (end['OB'] - start['OB'])
                    overallstate_a = not overallstate_a
            elif intf - 1 == 2:  # moving out of B
                end['B'] = time
                time_in_state['B'] += (end['B'] - start['B'])
    # now, just add up the remaining:
    state = 'OA' if overallstate_a else 'OB'
    time_in_state[state] += (endstep - start[state])
    if intf - 1 == 0 and sign < 0:
        # note that the sign < 0 works for sign=None
        time_in_state['A'] += (endstep - start['A'])
    elif intf - 1 == 2 and sign > 0:
        # note that the sign > 0 works for sign=None
        time_in_state['B'] += (endstep - start['B'])
    return eff_cross, ncross, neffcross, time_in_state


def _calculate_flux(effective_cross, time_in_state, time_window, time_step):
    """
    This method will calculate the flux in different time windows.

    Parameters
    ----------
    effective_cross : list
        The number of effective crossings, obtained from
        ``_effective_crossings``.
    time_in_state : int
        Time spent in over-all state A.
    time_window : int
        This is the time window we consider for calculating the flux.
    time_step : float
        This is the time-step for the simulation.

    Returns
    -------
    time : np.array
        The times for wich we have calculated the flux.
    ncross : np.array
        The number of crossings within a time window.
    flux : np.array
        The flux within a time window.
    """
    delta_t = time_step * time_window
    max_windows = int(1.0 * time_in_state / time_window)
    ncross = np.zeros(max_windows, dtype=np.int)
    #ncross = {}
    for crossing in effective_cross:
        idx = np.floor((crossing[0] - 0.0) / time_window)
        ncross[idx] += 1
    flux = (1.0 * ncross) / delta_t
    time = np.arange(1, max_windows+1) * time_window
    return time, ncross, flux
