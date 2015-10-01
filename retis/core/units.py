# -*- coding: utf-8 -*-
"""
This module defines some natural constants, in different units
and unit conversions.
For the Lennard-Jones potential, the conversions are currently
hardcoded to the parameters given by Rowley et al. [ROWLEY]_.

References
~~~~~~~~~~
.. [ROWLEY] Rowley et al., J. Comput. Phys., vol. 17, pp. 401-414, 1975
    doi: http://dx.doi.org/10.1016/0021-9991
"""
from __future__ import print_function
from collections import deque

CONSTANTS = {'kB': {'eV/K': 8.6173324e-05, 'J/K': 1.3806488e-23, 'lj': 1.0},
             'NA': {'1/mol': 6.02214129e23}}

CONVERT = {'length': {}, 'mass': {}, 'time': {},
           'energy': {}, 'velocity': {}}

CONVERT['length']['nm', 'Å'] = 10.0
CONVERT['length']['nm', 'm'] = 1.0e-9
CONVERT['length']['lj', 'Å'] = 3.405
CONVERT['length']['lj', 'nm'] = 0.3405
CONVERT['length']['lj', 'm'] = 3.405e-10
CONVERT['mass']['lj', 'kg'] = 6.690e-26
CONVERT['mass']['lj', 'g/mol'] = 39.948
CONVERT['energy']['lj', 'J'] = 119.8 * CONSTANTS['kB']['J/K']
CONVERT['energy']['kcal', 'J'] = 4184.
CONVERT['energy']['kcal', 'kcal/mol'] = CONSTANTS['NA']['1/mol']
CONVERT['energy']['lj', 'kcal/mol'] = CONVERT['energy']['lj', 'J'] *\
                                      (1.0 / CONVERT['energy']['kcal', 'J']) *\
                                      CONVERT['energy']['kcal', 'kcal/mol']
CONVERT['time']['lj', 's'] = CONVERT['length']['lj', 'm'] *\
                             (CONVERT['mass']['lj', 'kg'] /
                              CONVERT['energy']['lj', 'J'])**0.5
CONVERT['time']['lj', 'ps'] = 1.0e12 * CONVERT['time']['lj', 's']
CONVERT['time']['lj', 'fs'] = 1.0e15 * CONVERT['time']['lj', 's']
CONVERT['velocity']['lj', 'nm/ps'] = CONVERT['length']['lj', 'nm'] /\
                                     CONVERT['time']['lj', 'ps']


def _generate_inverse(conversions):
    """
    This helper method is intended to generate all inverse
    conversions for simple conversions.

    Parameters
    ----------
    conversions : dictionary
        The with unit conversions, assumed to be of type convert[quantity].
    """
    newconvert = {}
    for unit in conversions:
        unit_from, unit_to = unit
        newunit = (unit_to, unit_from)
        if newunit not in conversions:
            newconvert[newunit] = 1.0 / conversions[unit]
    for newunit in newconvert:
        conversions[newunit] = newconvert[newunit]


def _convert_from_to(conversions, unit_from, unit_to):
    """
    This method is intented to generate a unit conversion between
    the provided units, given that a "path" between these units exist.
    This path is obtained by a BFS.

    Parameters
    ----------
    conversions : dictionary
        The unit conversions, assumed to be of type convert[quantity].
    unit_from : string
        Starting unit.
    unit_to : string
        Target unit.
    """
    que = deque([unit_from])
    visited = [unit_from]
    parents = {unit_from: None}
    while que:
        node = que.popleft()
        if node == unit_to:
            break
        for unit in conversions:
            unit1, unit2 = unit
            if not unit1 == node:
                continue
            if unit2 not in visited:
                visited.append(unit2)
                que.append(unit2)
                parents[unit2] = node
    path = []
    node = unit_to
    while parents[node]:
        new = [None, node]
        node = parents[node]
        new[0] = node
        path.append(tuple(new))
    factor = 1
    for unit in path[::-1]:
        factor *= conversions[unit]
    return (unit_from, unit_to), factor, path[::-1]

if __name__ == '__main__':
    # This is intended as an example of how to use the
    # _generate_inverse and _convert_from_to to generate
    # conversion factors.
    for i in CONVERT:
        print(i)
        for j in CONVERT[i]:
            print(j, CONVERT[i][j])
        _generate_inverse(CONVERT[i])
        print('Generating inverse conversions\n')
    print(_convert_from_to(CONVERT['length'], 'm', 'Å'))
    print(_convert_from_to(CONVERT['energy'], 'lj', 'kcal/mol'))
    print(_convert_from_to(CONVERT['length'], 'lj', 'nm'))
