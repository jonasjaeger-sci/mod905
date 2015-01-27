# -*- coding: utf-8 -*-
from __future__ import print_function
"""
This module defines some natural CONSTANTS, in different units
and unit conversions.
For the Lennard-Jones potential, the conversions are currently
hardcoded to the parameters given by Rowley et al.[1].

References
----------
[1] Rowley et al., Journal of Computational Physics, vol. 17, pp. 401-414, 1975
    doi: http://dx.doi.org/10.1016/0021-9991
"""

from collections import deque

CONSTANTS = {'kB': {'eV/K':8.6173324e-05, 'J/K': 1.3806488e-23, 'lj': 1.0},
             'NA': {'1/mol': 6.02214129e23}}

convert = {'length': {}, 'mass': {}, 'time': {},
           'energy': {}}

convert['length']['nm', 'Å'] = 10.0
convert['length']['nm', 'm'] = 1.0e-9
convert['length']['lj', 'Å'] = 3.405
convert['length']['lj', 'nm'] = 0.3405
convert['mass']['lj', 'kg'] = 6.690e-26
convert['mass']['lj', 'g/mol'] = 39.948
convert['energy']['lj', 'J'] = 119.8*CONSTANTS['kB']['J/K']
convert['energy']['kcal', 'J'] = 4184.
convert['energy']['kcal', 'kcal/mol'] = CONSTANTS['NA']['1/mol']

def _generate_inverse(conversions):
    """
    This helper method is intended to generate all inverse
    conversions for simple conversions.
        
    Parameters
    ----------
    conversions : dictionary with unit conversions, assumed to be of type
        convert[quantity] 
    """
    newconvert = {}
    for unit in conversions:
        unit_from, unit_to = unit
        newunit = (unit_to, unit_from)
        if not newunit in conversions:
            newconvert[newunit] = 1.0/conversions[unit]
    for newunit in newconvert:
        conversions[newunit] = newconvert[newunit]

def _convert_from_to(conversions, unit_from, unit_to):
    """
    This method is intented to generate a unit conversion between
    the provided units, given that a "path" between these units exist.
    This path is obtained by a BFS.
    
    Parameters
    ----------
    conversions : dictionary with unit conversions, assumed to be of type
        convert[quantity] 
    unit_from : string, starting unit
    unit_to : string, target unit
    """
    que = deque([unit_from]) # just use a list, pop(0) is not so slow here
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

if __name__ == "__main__":
    # This is intended as an example of how to use the
    # _generate_inverse and _convert_from_to to generate
    # conversion factors.
    for i in convert:
        _generate_inverse(convert[i])
    print(_convert_from_to(convert['length'], 'm', 'Å'))
    print(_convert_from_to(convert['energy'], 'lj', 'kcal/mol'))
    print(_convert_from_to(convert['length'], 'lj', 'nm'))
