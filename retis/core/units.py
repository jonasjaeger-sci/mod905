# -*- coding: utf-8 -*-
u"""This module defines natural constants and unit conversions.

The natural constants and units are available as the dictionaries
`CONSTANTS` and `CONVERT`. These are further described in the
:ref:`natural constants <natural-constants>`and the
:ref:`unit conversion <unit-conversions>` sections below.

.. _natural-constants:

Natural constants
-----------------
The keys for `CONSTANTS` defines the
natural constant and its units, for instance `CONSTANTS['kB']['J/K']` is
the Boltzmann constants in units of Joule per Kelvin. The currently defined
natural constants are

- ``kB``: The Boltzmann constant [KB]_.

- ``NA``: The Avogadro constant [NA]_.

- ``e``: The elementary charge [E]_.


.. _unit-conversions:

Unit conversions
----------------
The keys for `CONVERT` defines how a unit conversion should be done. The
format is CONVERT['quantity']['from', 'to'] where 'quantity' is one of the
defined quantities ('length',  'mass', 'time', 'energy' and 'velocity')
and 'from' and 'to' defines the unit conversion.
The known units are given below.

Defined units
-------------

Length
~~~~~~

- `m`, `nm`, `Å`: Meter, nanometer and Ångstrøm.

- `lj`: Lennard-Jones units (based on the Lennard-Jones parameters
   by Rowley et al. [ROWLEY]_).


Mass
~~~~

- `kg`: Kilograms.

- `g/mol`: Grams per mole.

- `lj`: Lennard-Jones units (based on the Lennard-Jones parameters
   by Rowley et al. [ROWLEY]_).

Energy
~~~~~~
- `kcal`: Kilocalories. This is the *Thermochemical calorie*, equal to
   4184 Joule.

- `J`: Joule.

- `kcal/mol`: Kilocalories per mole.

- `lj`: Lennard-Jones units (based on the Lennard-Jones parameters
   by Rowley et al. [ROWLEY]_).

Time
~~~~

- `s`, `ps`, `fs`: Seconds, pico-seconds and femto-seconds.

- `lj`: Lennard-Jones units (based on the Lennard-Jones parameters
   by Rowley et al. [ROWLEY]_).

Velocity
~~~~~~~~

- `nm/ps`: Nanometer per picosecond.

- `lj`: Lennard-Jones units (based on the Lennard-Jones parameters
   by Rowley et al. [ROWLEY]_).

Charge
~~~~~~

- `e`: Charge in units of elementary charge.

- `C`: Coulomb.

References
----------
.. [KB] https://en.wikipedia.org/wiki/Boltzmann_constant

.. [NA] https://en.wikipedia.org/wiki/Avogadro_constant

.. [E] https://en.wikipedia.org/wiki/Elementary_charge

.. [ROWLEY] Rowley et al., J. Comput. Phys., vol. 17, pp. 401-414, 1975
    doi: http://dx.doi.org/10.1016/0021-9991
"""
from __future__ import print_function
from collections import deque

CONSTANTS = {'kB': {'eV/K': 8.6173324e-05, 'J/K': 1.3806488e-23, 'lj': 1.0},
             'NA': {'1/mol': 6.02214129e23},
             'e': {'C':  1.6021766208e-19}}

CONVERT = {'length': {}, 'mass': {}, 'time': {},
           'energy': {}, 'velocity': {}, 'charge': {}}

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
CONVERT['energy']['lj', 'kcal/mol'] = (CONVERT['energy']['lj', 'J'] *
                                       (1.0 / CONVERT['energy']['kcal', 'J']) *
                                       CONVERT['energy']['kcal', 'kcal/mol'])
CONVERT['time']['lj', 's'] = (CONVERT['length']['lj', 'm'] *
                              (CONVERT['mass']['lj', 'kg'] /
                               CONVERT['energy']['lj', 'J'])**0.5)
CONVERT['time']['lj', 'ps'] = 1.0e12 * CONVERT['time']['lj', 's']
CONVERT['time']['lj', 'fs'] = 1.0e15 * CONVERT['time']['lj', 's']
CONVERT['velocity']['lj', 'nm/ps'] = (CONVERT['length']['lj', 'nm'] /
                                      CONVERT['time']['lj', 'ps'])
CONVERT['charge']['e', 'C'] = CONSTANTS['e']


def _generate_inverse(conversions):
    """
    Generate all simple inverse conversions.

    A simple inverse conversion is something we can obtain by doing
    a ``1 / unit`` type of conversion.

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
    Generate unit conversion between the provided units.

    The unit conversion can be obtained given that a "path" between these
    units exist. This path is obtained by a BFS.

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
