# -*- coding: utf-8 -*-
u"""This module defines natural constants and unit conversions.

The natural constants and units are available as the dictionaries
`CONSTANTS` and `CONVERT`. These are further described in the
:ref:`natural constants <natural-constants>` and the
:ref:`unit conversion <unit-conversions>` sections below.

.. _natural-constants:

Natural constants
-----------------
The keys for `CONSTANTS` defines the
natural constant and its units, for instance `CONSTANTS['kB']['J/K']` is
the Boltzmann constants in units of Joule per Kelvin. The currently defined
natural constants are

- ``kB`` : The Boltzmann constant [KB]_.

- ``NA`` : The Avogadro constant [NA]_.

- ``e`` : The elementary charge [E]_.


.. _unit-conversions:

Unit conversions
----------------
The keys for `CONVERT` defines how a unit conversion should be done. The
format is CONVERT['quantity']['from', 'to'] where 'quantity' is one of the
defined quantities
(:ref:`length <units-length>`,
:ref:`mass <units-mass>`,
:ref:`energy <units-energy>`,
:ref:`time <units-time>`,
:ref:`velocity <units-velocity>` and
:ref:`charge <units-charge>`)
and 'from' and 'to' defines the unit conversion.
The known units are given below.

Defined units
-------------

.. _units-length:

Length
~~~~~~

- ``m``, ``nm``, ``A`` : Meter, nano-meter and Ångström.

- ``lj`` : Lennard-Jones units (based on the Lennard-Jones parameters
  by Rowley et al. [ROWLEY]_).


.. _units-mass:

Mass
~~~~

- ``kg`` : Kilograms.

- ``g/mol`` : Grams per mole.

- ``lj`` : Lennard-Jones units (based on the Lennard-Jones parameters
  by Rowley et al. [ROWLEY]_).


.. _units-energy:

Energy
~~~~~~

- ``kcal`` : Kilo-calories. This is the
  `thermo-chemical calorie <http://www.aps.org/policy/reports/popa-reports/energy/units.cfm>`_
  equal to 4184 Joule.

- ``J`` : Joule.

- ``kcal/mol`` : Kilo-calories per mole.

- ``lj`` : Lennard-Jones units (based on the Lennard-Jones parameters
  by Rowley et al. [ROWLEY]_).


.. _units-time:

Time
~~~~

- ``s``, ``ps``, ``fs`` : Seconds, pico-seconds and femto-seconds.

- ``lj`` : Lennard-Jones units (based on the Lennard-Jones parameters
  by Rowley et al. [ROWLEY]_).


.. _units-velocity:

Velocity
~~~~~~~~

- ``nm/ps`` : Nano-meter per pico-second.

- ``lj`` : Lennard-Jones units (based on the Lennard-Jones parameters
  by Rowley et al. [ROWLEY]_).


.. _units-charge:

Charge
~~~~~~

- ``e`` : Charge in units of elementary charge.

- ``C`` : Coulomb.


.. _unit-references:

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
import numpy as np


__all__ = ['create_conversion_factors', 'generate_inverse', 'convert_from_to',
           'convert_bases']

CONSTANTS = {}
CONSTANTS['kB'] = {'eV/K': 8.6173324e-05, 'J/K': 1.3806488e-23,
                   'kJ/mol/K': 8.3144598e-3, 'kcal/mol/K': 0.0019872041,
                   'kJ/K': 1.3806488e-26, 'kcal/K': 1.3806488e-23/4184.}
CONSTANTS['NA'] = {'1/mol': 6.02214129e23}
CONSTANTS['c0'] = {'m/s': 299792458.}
CONSTANTS['mu0'] = {'H/m': 4.0 * np.pi * 1.0e-7}
CONSTANTS['e'] = {'C':  1.6021766208e-19}
CONSTANTS['e0'] = {'F/m': 1.0 / (CONSTANTS['mu0']['H/m'] *
                                 CONSTANTS['c0']['m/s']**2)}
# Set value of kB in the system of units we have defined.
# These values will be used in the simulations. We don't really have to
# set all these values here, this is just to be sure that they are set in case
# we wish to have simpler scripts that just need the Boltzmann constant.
CONSTANTS['kB']['lj'] = 1.0
CONSTANTS['kB']['si'] = CONSTANTS['kB']['J/K']
CONSTANTS['kB']['real'] = 0.00198720414567
CONSTANTS['kB']['metal'] = CONSTANTS['kB']['eV/K']
CONSTANTS['kB']['amu'] = 1.0
CONSTANTS['kB']['electron'] = 3.16681534e-6
CONSTANTS['kB']['gromacs'] = CONSTANTS['kB']['kJ/mol/K']
# define 'dimensions'. Note that not all of these are True dimensions,
# for instance is 'velocity' in reality 'length'/'time'.
DIMENSIONS = set(['length', 'mass', 'time', 'energy', 'velocity',
                  'charge', 'temperature', 'pressure', 'force'])
# for each dimension we want conversion factors and units
CONVERT = {key: {} for key in DIMENSIONS}
UNITS = {key: {} for key in DIMENSIONS}

# Define a few units and some base conversions:
UNITS['length'] = set(['A', 'nm', 'bohr', 'm'])
CONVERT['length']['A', 'nm'] = 0.1
CONVERT['length']['A', 'bohr'] = 1.0 / 0.52917721092  # wikipedia
CONVERT['length']['A', 'm'] = 1.0e-10

UNITS['mass'] = set(['g/mol', 'g', 'kg'])
CONVERT['mass']['g', 'kg'] = 1.e-3
CONVERT['mass']['g/mol', 'g'] = 1.0 / CONSTANTS['NA']['1/mol']
CONVERT['mass']['g/mol', 'kg'] = (CONVERT['mass']['g', 'kg'] /
                                  CONSTANTS['NA']['1/mol'])

UNITS['time'] = set(['s', 'ps', 'fs', 'ns', 'us', 'ms'])
CONVERT['time']['s', 'ps'] = 1.0e12
CONVERT['time']['s', 'fs'] = 1.0e15
CONVERT['time']['s', 'ns'] = 1.0e9
CONVERT['time']['s', 'us'] = 1.0e6
CONVERT['time']['s', 'ms'] = 1.0e3

UNITS['energy'] = set(['kcal', 'kcal/mol', 'J', 'J/mol', 'kJ/mol',
                       'eV', 'hartree'])
CONVERT['energy']['kcal', 'kcal/mol'] = CONSTANTS['NA']['1/mol']
CONVERT['energy']['kcal', 'J'] = 4184.
CONVERT['energy']['kcal', 'J/mol'] = (CONSTANTS['NA']['1/mol'] *
                                      CONVERT['energy']['kcal', 'J'])
CONVERT['energy']['kcal', 'kJ/mol'] = (CONVERT['energy']['kcal', 'J/mol'] *
                                       1.0e-3)
CONVERT['energy']['kcal', 'eV'] = (CONVERT['energy']['kcal', 'J'] /
                                   1.602176565e-19)
CONVERT['energy']['kcal', 'hartree'] = (CONVERT['energy']['kcal', 'J'] /
                                        4.35974434e-18)

UNITS['velocity'] = set(['m/s', 'nm/ps', 'A/fs', 'A/ps'])
CONVERT['velocity']['m/s', 'nm/ps'] = 1.0e9 / 1.0e12
CONVERT['velocity']['m/s', 'A/fs'] = 1.0e10 / 1.0e15
CONVERT['velocity']['m/s', 'A/ps'] = 1.0e10 / 1.0e12

UNITS['charge'] = set(['e', 'C'])
CONVERT['charge']['e', 'C'] = CONSTANTS['e']['C']
CONVERT['charge']['C', 'e'] = 1.0 / CONSTANTS['e']['C']

UNITS['pressure'] = set(['Pa', 'bar', 'atm'])
CONVERT['pressure']['Pa', 'bar'] = 1.0e-5
CONVERT['pressure']['Pa', 'atm'] = 1.0 / 101325.

UNITS['temperature'] = set(['K'])


def convert_temperature(temp, unit_from, unit_to):
    """Convert a temperature between two given units.

    This will convert a temperature between two given units. Since
    temperature conversions is not just simple scalings we handle it with
    this function. Well, in some cases we can get away with a simple scaling,
    for instance converting from 'lj' units to 'K'. Such conversions should
    be handled by `CONVERT['temperature']`.

    Parameters
    ----------
    temp : float
        The value of the temperature in the input units.
    unit_from : string
        The input unit.
    unit_to : string
        The desired output unit.

    Returns
    -------
    out : float
        The value of the temperature in the desired output units.
    """
    # check if this is a simple transformation:
    if unit_from == 'K':
        return _convert_kelvin_to(temp, unit_to)
    elif unit_from == 'C':
        return _convert_celcius_to(temp, unit_to)
    elif unit_from == 'F':
        return _convert_fahrenheit_to(temp, unit_to)
    else:
        msg = 'Unknown temperature unit {}'.format(unit_from)
        raise ValueError(msg)


def _convert_celcius_to(temp, unit_out):
    """Method to convert a temperature in celcius (°C) to something else.

    Parameters
    ----------
    temp : float
        The celcius temperature to convert.
    unit_out : string
        The desired output unit.

    Returns
    -------
    out : float
        The converted temperature in the desired unit.
    """
    if unit_out == 'K':
        return temp + 273.15
    elif unit_out == 'F':
        return temp * 9.0 / 5.0 + 32.0
    elif unit_out == 'C':
        return temp
    else:
        msg = 'Conversion "C" to "{}" not defined.'.format(unit_out)
        raise ValueError(msg)


def _convert_kelvin_to(temp, unit_out):
    """Method to convert a temperature in Kelvin (K) to something else.

    Parameters
    ----------
    temp : float
        The kelvin temperature to convert.
    unit_out : string
        The desired output unit.

    Returns
    -------
    out : float
        The converted temperature in the desired unit.
    """
    if unit_out == 'K':
        return temp
    elif unit_out == 'F':
        return temp * 9.0 / 5.0 - 459.67
    elif unit_out == 'C':
        return temp - 273.15
    else:
        msg = 'Conversion "K" to "{}" not defined.'.format(unit_out)
        raise ValueError(msg)


def _convert_fahrenheit_to(temp, unit_out):
    """Method to convert a temperature in Fahrenheit (F) to something else.

    Parameters
    ----------
    temp : float
        The Fahrenheit temperature to convert.
    unit_out : string
        The desired output unit.

    Returns
    -------
    out : float
        The converted temperature in the desired unit.
    """
    if unit_out == 'K':
        return (temp + 459.67) * 5.0 / 9.0
    elif unit_out == 'F':
        return temp
    elif unit_out == 'C':
        return (temp - 32.0) * 5.0 / 9.0
    else:
        msg = 'Conversion "F" to "{}" not defined.'.format(unit_out)
        raise ValueError(msg)


def _add_conversion_and_inverse(conv_dict, value, unit1, unit2):
    """Helper function that will add a specific conversion and it's inverse.

    This function is mainly here to ensure that we don't forget to add the
    inverse conversions.

    Parameters
    ----------
    conv_dict : dict
        This is where we store the conversion.
    value : float
        The conversion factor to add
    unit1 : string
        The unit we are converting from.
    unit2 : string
        The unit we are converting to.

    Returns
    -------
    None, but updates the given `conv_dict`.
    """
    conv_dict[unit1, unit2] = value
    conv_dict[unit2, unit1] = 1.0 / conv_dict[unit1, unit2]


def _generate_conversion_for_dim(conv_dict, dim, unit):
    """Generate conversion factors for the specified dimension.

    It will generate all conversions for the given dimension considering
    all units defined in `UNITS`.

    Parameters
    ----------
    conv_dict : dict
        A dictionary with conversions which we wish to update.
    dim : string
        The dimension to consider

    Returns
    -------
    None, but updates the given `conv_dict`
    """
    convert = conv_dict[dim]
    for unit_to in UNITS[dim]:
        value = convert_from_to(convert, unit, unit_to)[1]
        _add_conversion_and_inverse(convert, value, unit, unit_to)


def create_conversion_factors(unit, distance, energy, mass, charge_unit='e'):
    u"""Create conversions for a system of units from fundamental units.

    This will create a system of units from the three fundamental units
    distance, energy and mass.

    Parameters
    ----------
    unit : string
        This is a label for the unit
    distance : tuple
        This is the distance unit. The form is assumed to be `(value, unit)`
        where unit is one of the known distance units, 'nm', 'A', 'm'.
    energy : tuple
        This is the energy unit. The form is assumed to be `(value, unit)`
        where unit is one of the known energy units, 'J', 'kcal', 'kcal/mol',
        'kb'.
    mass : tuple
        This is the mass unit. The form is assumed to be `(value, unit)`
        where unit is one of the known mass units, 'g/mol', 'kg', 'g'.
    charge_unit : string, optional
        This selects the base charge. It can be 'C' or 'e' for Coulomb or
        the electron charge. This will determine how we treat Coulomb's
        constant.
    """
    CONVERT['length'][unit, distance[1]] = distance[0]
    CONVERT['mass'][unit, mass[1]] = mass[0]
    if energy[1] == 'kB':  # in case the energy is given in units of kB.
        CONVERT['energy'][unit, 'J'] = energy[0] * CONSTANTS['kB']['J/K']
    else:
        CONVERT['energy'][unit, energy[1]] = energy[0]
        # let us also check if we can define kB now:
        if not unit in CONSTANTS['kB']:
            try:
                kboltz = CONSTANTS['kB']['{}/K'.format(energy[1])] / energy[0]
                CONSTANTS['kB'][unit] = kboltz
            except KeyError:
                msg = 'For "{}" you need to define kB'.format(unit)
                raise ValueError(msg)
    # First, set up simple conversions:
    for dim in ('length', 'energy', 'mass'):
        _generate_conversion_for_dim(CONVERT, dim, unit)
    # We can now set up time conversions (since it's using length, mass and
    # energy:
    value = (CONVERT['length'][unit, 'm']**2 * CONVERT['mass'][unit, 'kg'] /
             CONVERT['energy'][unit, 'J'])**0.5
    _add_conversion_and_inverse(CONVERT['time'], value, unit, 's')
    # And velocity (since it's using time and length):
    value = CONVERT['length'][unit, 'm'] / CONVERT['time'][unit, 's']
    _add_conversion_and_inverse(CONVERT['velocity'], value, unit, 'm/s')
    # And pressure (since it's using energy and length):
    value = CONVERT['energy'][unit, 'J'] / CONVERT['length'][unit, 'm']**3
    _add_conversion_and_inverse(CONVERT['pressure'], value, unit, 'Pa')
    # And force (since it's using energy and length):
    value = CONVERT['energy'][unit, 'J'] / CONVERT['length'][unit, 'm']
    _add_conversion_and_inverse(CONVERT['force'], value, unit, 'N')
    # Generate the rest of the conversions:
    for dim in ('time', 'velocity', 'pressure', 'force'):
        _generate_conversion_for_dim(CONVERT, dim, unit)
    # Now, figure out the Temperature conversion:
    kboltz = CONSTANTS['kB']['J/K'] * CONVERT['energy']['J', unit]
    # kboltz in now in units of 'unit'/K, temperature conversion is:
    value = CONSTANTS['kB'][unit] / kboltz
    _add_conversion_and_inverse(CONVERT['temperature'], value, unit, 'K')
    # convert permittivity:
    if charge_unit == 'C':
        CONSTANTS['e0'][unit] = CONSTANTS['e0']['F/m']
    else:
        CONSTANTS['e0'][unit] = (CONSTANTS['e0']['F/m'] *
                                 CONVERT['charge']['C', 'e']**2 /
                                 (CONVERT['force']['N', unit] *
                                  CONVERT['length']['m', unit]**2))
    value = np.sqrt(4.0 * np.pi * CONSTANTS['e0'][unit])
    _add_conversion_and_inverse(CONVERT['charge'], value, unit, charge_unit)
    #CONVERT['charge'][unit, charge_unit] = 1.0 / CONVERT['charge'][charge_unit, unit]
    # convert [charge] * V/A to force, in case it's needed in the future:
    #qE = CONVERT['energy']['J', unit] / CONVERT['charge']['C', 'e']
    _generate_conversion_for_dim(CONVERT, 'charge', unit)


def generate_inverse(conversions):
    """Generate all simple inverse conversions.

    A simple inverse conversion is something we can obtain by doing
    a ``1 / unit`` type of conversion.

    Parameters
    ----------
    conversions : dictionary
        The unit conversions, assumed to be of type `convert[quantity]`.

    Returns
    -------
    None, but it will update the given parameter `conversions`.
    """
    newconvert = {}
    for unit in conversions:
        unit_from, unit_to = unit
        newunit = (unit_to, unit_from)
        if newunit not in conversions:
            newconvert[newunit] = 1.0 / conversions[unit]
    for newunit in newconvert:
        conversions[newunit] = newconvert[newunit]


def convert_from_to(conversions, unit_from, unit_to):
    """Generate unit conversion between the provided units.

    The unit conversion can be obtained given that a "path" between these
    units exist. This path is obtained by a Breadth-first search.

    Parameters
    ----------
    conversions : dictionary
        The unit conversions, assumed to be of type `convert[quantity]`.
    unit_from : string
        Starting unit.
    unit_to : string
        Target unit.

    Returns
    -------
    out[0] : tuple
        A tuple containing the two units: `(unit_from, unit_to)`.
    out[1] : float
        The conversion factor.
    out[2] : list of tuples
        The 'path' between the units, i.e. the traversal from `unit_from` to
        `unit_to`. `out[2][i]` gives the `(unit_from, unit_to)` tuple for step
        `i` in the conversion.
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


def convert_bases(dimension):
    """Method that will create all conversions between base units.

    This method will generate all conversions between base units defined in
    a `UNITS[dimension]` dictionary. It assumes that one of the bases have
    been used to defined conversions to all other bases.

    Parameters
    ----------
    dimension : string
        The dimension to convert for.
    """
    convert = CONVERT[dimension]
    # start by generating inverses
    generate_inverse(convert)
    for key1 in UNITS[dimension]:
        for key2 in UNITS[dimension]:
            if key1 == key2:
                continue
            unit1 = (key1, key2)
            unit2 = (key2, key1)
            if unit1 in convert and not unit2 in convert:
                convert[unit2] = 1.0 / convert[unit1]
            elif not unit1 in convert and unit2 in convert:
                convert[unit1] = 1.0 / convert[unit2]
            else:
                convert[unit1] = convert_from_to(convert, key1, key2)[1]
                convert[unit2] = 1.0 / convert[unit1]


def print_table(unit):
    """print out a table with conversion factors"""
    row_fmt = '| {:10s} | {:16.8e} | {:16.8e} |'
    row_head = '| {:10s} | {:16s} | {:16s} |'
    row_line = ''.join(['+-', ('-')*10, '-+-', ('-')*16, '-+-',
                        ('-')*16, '-+'])
    for i in sorted(CONVERT):
        head = i.capitalize()
        print('\n.. _{}-{}:\n'.format(i, unit))
        print('{}'.format(head))
        print(('-') * len(head))

        header = 'Conversion factors for: {}'.format(unit)
        line = ''.join(['+', ('-') * 50, '+'])
        print('\n{}'.format(line))
        print('|{:49s} |'.format(header))
        print(row_line)
        row = row_head.format('Unit', '{} -> unit'.format(unit),
                              'unit -> {}'.format(unit))
        print(row)
        print(row_line)
        for j in CONVERT[i]:
            un1, un2 = j
            if un1 == unit:
                row = row_fmt.format(un2, CONVERT[i][j], CONVERT[i][un2, un1])
                print(row)
                print(row_line)
        print('\n')
    print('kB:', CONSTANTS['kB'][unit])


if __name__ == '__main__':
    # This is intended as an example of how to use the functions
    # here to generate conversion factors for a system.
    # First, we just generate conversions between bases:
    for key in DIMENSIONS:
        convert_bases(key)
    # Next we generate conversion factors for certain units.
    UNIT_SYSTEMS = {'lj': {'length': (3.405, 'A'),
                           'energy': (119.8, 'kB'),
                           'mass': (39.948, 'g/mol'),
                           'charge': 'e'},
                    'real': {'length': (1.0, 'A'),
                             'energy': (1.0, 'kcal/mol'),
                             'mass': (1.0, 'g/mol'),
                             'charge': 'e'},
                    'metal': {'length': (1.0, 'A'),
                              'energy': (1.0, 'eV'),
                              'mass': (1.0, 'g/mol'),
                              'charge': 'e'},
                    'amu': {'length': (1.0, 'bohr'),
                            'energy': (1.0, 'hartree'),
                            'mass': (9.10938291e-31, 'kg'),
                            'charge': 'e'},
                    'electron': {'length': (1.0, 'bohr'),
                                 'energy': (1.0, 'hartree'),
                                 'mass': (1.0, 'g/mol'),
                                 'charge': 'e'},
                    'si': {'length': (1.0, 'm'),
                           'energy': (1.0, 'J'),
                           'mass': (1.0, 'kg'),
                           'charge': 'e'},
                    'gromacs': {'length': (1.0, 'nm'),
                                'energy': (1.0, 'kJ/mol'),
                                'mass': (1.0, 'g/mol'),
                                'charge': 'e'}}
    for uni in UNIT_SYSTEMS:
        unit_system = UNIT_SYSTEMS[uni]
        create_conversion_factors(uni, unit_system['length'],
                                  unit_system['energy'], unit_system['mass'],
                                  charge_unit=unit_system['charge'])
    for uni in UNIT_SYSTEMS:
        print_table(uni)
    # test, can we convert real to gromacs?
    print(convert_from_to(CONVERT['energy'], 'lj', 'gromacs'))
    print(convert_from_to(CONVERT['energy'], 'lj', 'real'))
    print(convert_from_to(CONVERT['length'], 'lj', 'real'))
    print(convert_from_to(CONVERT['mass'], 'lj', 'real'))
    print(convert_from_to(CONVERT['time'], 'lj', 'real'))
    print(convert_from_to(CONVERT['time'], 'lj', 'ps'))
