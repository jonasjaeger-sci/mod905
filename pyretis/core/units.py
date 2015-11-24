# -*- coding: utf-8 -*-
r"""This module defines natural constants and unit conversions.

This module defines some natural constants and conversions between units
which can be used by the pyretis program.
The :ref:`natural constants <natural-constants>` are mainly used for
conversions but it is also used to define the Boltzmann constant which is used
by simulations in pyretis.
The :ref:`unit conversions <unit-conversions>` are mainly useful for the
pyretis input and output. All numerical values are from [NIST]_.

Internally, all computations are carried out in units which are defined by
a length scale, an energy scale and a mass scale. This means that the time
scale is given by these choice. Typically will the input to pyretis be in a
more human-readable form (e.g. femtoseconds) which is converted to the interal
units when pyretis is setting up a new simulation.

Charges are typically given (in the input) in units of the electron charge.
The internal unit for charge is not yet implemented, but one choice here is
to include the factor :math:`\frac{1}{\sqrt{4\pi\varepsilon_0}}`. An internal
calculation of :math:`q_1 q_2` will then include coulombs constant in the
correct units.

The different sets of sytem of units are deseribed below in
the section on :ref:`unit systems <unit-conversions-systems>`.


.. _natural-constants:

Natural constants
~~~~~~~~~~~~~~~~~
The keys for `CONSTANTS` defines the natural constant and its units,
for instance `CONSTANTS['kB']['J/K']` is the Boltzmann constants in units
of Joule per Kelvin. The currently defined natural constants are

- ``kB`` : The Boltzmann constant [KB]_.

- ``NA`` : The Avogadro constant [NA]_.

- ``e`` : The elementary charge [E]_.

- ``c0`` : The velocity of light in vaccuum [C0]_.

- ``mu0``: Vacuum permeability [M0]_.

- ``e0``: Vacuum permittivity (or permittivity of free space or electric
  constant) [E0]_.


.. _unit-conversions:

Unit conversions
~~~~~~~~~~~~~~~~
For defining the different unit conversions a simple set of base conversions
are defined. These represent some common units that are convenient for input
and output. For each dimension [#]_ we define some units and the conversion
between these. The base units are:

- Charge

  * ``e``: Electron charge.
  * ``C``: Coulomb.

- Energy

  * ``kcal``: Kilocalorie.
  * ``kcal/mol``: Kilocalorie per mol.
  * ``J``: Joule.
  * ``J/mol``: Joule per mol.
  * ``kJ/mol``: Kilojoule per mol.
  * ``eV``: Electronvolt.
  * ``hartree``: Hartree (atomic unit of energy).

- Force

  * ``N``: Newton.
  * ``pN``: Piconewton.
  * ``dyn``: Dyne.

- Length

  * ``A``: Ångström.
  * ``nm``: Nanometre.
  * ``bohr``: Bohr radius.
  * ``m``: Meter.

- Mass

  * ``g/mol``: Grams per mol, numerically equal to the atomic mass unit.
  * ``g``: Gram.
  * ``kg``: Kilogram.

- Pressure

  * ``Pa``: Pascal.
  * ``bar``: Bar.
  * ``atm``: Atmosphere.

- Temperature

  * ``K``: Kelvin.

- Time

  * ``s``: Second.
  * ``ps``: Picosecond.
  * ``fs``: Femtosecond
  * ``ns``: Nanosecond.
  * ``us``: Microsecond.
  * ``ms``: Millisecond.

- Velocity

  * ``m/s``: Meter per second.
  * ``nm/ps``: Nanometer per picosecond.
  * ``A/fs``: Ångström per femtosecond.
  * ``A/ps``: Ångström per picosecond.


.. _unit-conversions-systems:

Unit conversions and internal systems of units
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following system of units are defined for pyretis:

- ``lj``: A Lennard-Jones type of units.

- ``real``: A system of units similar to the [LAMMPS]_ unit ``real``.

- ``metal``: A system of units similar to the LAMMPS_ unit ``metal``.

- ``au``: Atomic units [ATOMUNITS]_.

- ``electron``: A system of units similar to the LAMMPS_ unit ``electron``.

- ``si``: A system of units similar to the LAMMPS_ unit ``si``.

- ``gromacs``: A system of units similar to the units used by [GROMACS]_.


The defining units for the Lennard-Jones units (``lj``) are typically based
on the Lennard-Jones parameters for one of the components, e.g.
:math:`\varepsilon`, :math:`\sigma` and the atomic mass
of argon (119.8 kB, 3.405 Å, 39.948 g/mol [ROWLEY]_). The defining units for
the other systems are given in the table below:


.. table:: Defining units for energy systems

  +-------------+--------------+-------------+--------------------+
  | System name | Energy unit  | Length unit | Mass unit          |
  +=============+==============+=============+====================+
  | real        | 1 kcal/mol   | 1 Å         |  1 g/mol           |
  +-------------+--------------+-------------+--------------------+
  | metal       | 1 eV         | 1 Å         |  1 g/mol           |
  +-------------+--------------+-------------+--------------------+
  | au          | 1 hartree    | 1 bohr      |  9.10938291e-31 kg |
  +-------------+--------------+-------------+--------------------+
  | electron    | 1 hartree    | 1 bohr      | 1 g/mol            |
  +-------------+--------------+-------------+--------------------+
  | si          | 1 J          | 1 m         | 1 kg               |
  +-------------+--------------+-------------+--------------------+
  | gromacs     | 1 kJ/mol     | 1 nm        | 1 g/mol            |
  +-------------+--------------+-------------+--------------------+


The input units for the different energy systems are given in the table
below. For the ``lj`` system all input units are in reduced quantities.
Further, all system of units expect an input temperature in Kelvin (``K``)
and all systems, with the exception of ``si``, expects a charge in units of
electron charges. The ``si`` system uses here Coulomb as it's unit for charge.
The time unit ``at`` given below for ``au`` is the atomic time unit which is
not explicitly shown here, but it's implicitly given by the energy, length
and mass unit (``at`` is approximately 2.41888433e-17 s).


.. table:: Input units for energy systems

  +-------------+----------+--------+---------------+----------+------+
  | System name | Energy   | Length | Mass          | Velocity | Time |
  +=============+==========+========+===============+==========+======+
  | real        | kcal/mol |  Å     | g/mol         | Å/fs     | fs   |
  +-------------+----------+--------+---------------+----------+------+
  | metal       | eV       |  Å     | g/mol         | Å/ps     | ps   |
  +-------------+----------+--------+---------------+----------+------+
  | au          | hartree  | bohr   | electron mass | bohr/at  | at   |
  +-------------+----------+--------+---------------+----------+------+
  | electron    | hartree  | bohr   | g/mol (amu)   | bohr/fs  | fs   |
  +-------------+----------+--------+---------------+----------+------+
  | si          | J        | m      | kg            | s        | s    |
  +-------------+----------+--------+---------------+----------+------+
  | gromacs     | kJ/mol   | nm     | g/mol         | ps       | ps   |
  +-------------+----------+--------+---------------+----------+------+


.. rubric:: Footnotes

.. [#] Note that 'dimension' here is, strictly speaking, not a true dimension,
       for instance we define conversions for the dimension `velocity` which
       in reality is composed of the dimensions `length` and `time`.


References
~~~~~~~~~~

.. [KB] https://en.wikipedia.org/wiki/Boltzmann_constant

.. [NA] https://en.wikipedia.org/wiki/Avogadro_constant

.. [E] https://en.wikipedia.org/wiki/Elementary_charge

.. [C0] https://en.wikipedia.org/wiki/Speed_of_light

.. [M0] https://en.wikipedia.org/wiki/Vacuum_permeability

.. [E0] https://en.wikipedia.org/wiki/Vacuum_permittivity

.. [NIST] National Institute of Standards and Technology,
   http://physics.nist.gov/cuu/Constants/Table/allascii.txt

.. [LAMMPS] The LAMMPS manual, http://lammps.sandia.gov/doc/units.html

.. [ROWLEY] Rowley et al., J. Comput. Phys., vol. 17, pp. 401-414, 1975,
   doi: http://dx.doi.org/10.1016/0021-9991

.. [ATOMUNITS] https://en.wikipedia.org/wiki/Atomic_units

.. [GROMACS] The GROMACS manual, tables 2.1 and 2.2 on page. 8,
   http://manual.gromacs.org/documentation/5.1.1/manual-5.1.1.pdf
"""
from __future__ import print_function
from collections import deque
import warnings
import numpy as np


__all__ = ['generate_conversion_factors', 'generate_inverse',
           'bfs_convert', 'convert_bases', 'print_table',
           'write_conversions', 'read_conversions']


CAL = 4184.  # Define 1 kcal = `CAL` J.
CONSTANTS = {}
CONSTANTS['kB'] = {'eV/K': 8.6173303e-5, 'J/K': 1.38064852e-23,
                   'kJ/mol/K': 8.3144598e-3}
CONSTANTS['kB']['J/mol/K'] = CONSTANTS['kB']['kJ/mol/K'] * 1000.
CONSTANTS['kB']['kJ/K'] = CONSTANTS['kB']['J/K'] / 1000.0
CONSTANTS['kB']['kcal/K'] = CONSTANTS['kB']['J/K'] / CAL
CONSTANTS['kB']['kcal/mol/K'] = CONSTANTS['kB']['J/mol/K'] / CAL
CONSTANTS['NA'] = {'1/mol': 6.022140857e23}
CONSTANTS['c0'] = {'m/s': 299792458.}
CONSTANTS['mu0'] = {'H/m': 4.0 * np.pi * 1.0e-7}
CONSTANTS['e'] = {'C':  1.6021766208e-19}
CONSTANTS['e0'] = {'F/m': 1.0 / (CONSTANTS['mu0']['H/m'] *
                                 CONSTANTS['c0']['m/s']**2)}
# Set value of kB in the system of units we have defined.
# These values will be used in the simulations.
CONSTANTS['kB']['lj'] = 1.0
CONSTANTS['kB']['si'] = CONSTANTS['kB']['J/K']
CONSTANTS['kB']['real'] = CONSTANTS['kB']['kcal/mol/K']
CONSTANTS['kB']['metal'] = CONSTANTS['kB']['eV/K']
CONSTANTS['kB']['au'] = 1.0
CONSTANTS['kB']['electron'] = 3.16681534e-6
CONSTANTS['kB']['gromacs'] = CONSTANTS['kB']['kJ/mol/K']

# Define 'dimensions'. Note that not all of these are true dimensions,
# for instance: 'velocity' in reality 'length'/'time'.
DIMENSIONS = set(['length', 'mass', 'time', 'energy', 'velocity',
                  'charge', 'temperature', 'pressure', 'force'])
# For each dimension we want conversion factors and units
CONVERT = {key: {} for key in DIMENSIONS}
UNITS = {key: {} for key in DIMENSIONS}

# Define a few units and some base conversions:
UNITS['length'] = set(['A', 'nm', 'bohr', 'm'])
CONVERT['length']['A', 'nm'] = 0.1
# http://physics.nist.gov/cuu/Constants/Table/allascii.txt
CONVERT['length']['A', 'bohr'] = 1.0 / 0.52917721067
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
CONVERT['energy']['kcal', 'J'] = CAL
CONVERT['energy']['kcal', 'J/mol'] = (CONSTANTS['NA']['1/mol'] *
                                      CONVERT['energy']['kcal', 'J'])
CONVERT['energy']['kcal', 'kJ/mol'] = (CONVERT['energy']['kcal', 'J/mol'] *
                                       1.0e-3)
CONVERT['energy']['kcal', 'eV'] = (CONSTANTS['kB']['eV/K'] /
                                   CONSTANTS['kB']['kcal/K'])
CONVERT['energy']['kcal', 'hartree'] = (CONVERT['energy']['kcal', 'eV'] *
                                        (1.0 / 27.21138602))
# 27.21138602 is hartee to eV from:
# http://physics.nist.gov/cuu/Constants/Table/allascii.txt

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

UNITS['force'] = set(['N', 'pN', 'dyn'])
CONVERT['force']['N', 'pN'] = 1.0e12
CONVERT['force']['N', 'dyn'] = 1.0e5

# Definitions for systems of units, these were generated using
# `generate_conversion_factors` as shown in the __main__ routine.
#CONVERT['


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

    It will generate all conversions from a specified unit for a given
    dimension considering all other units defined in `UNITS`.

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
    convertdim = conv_dict[dim]
    for unit_to in UNITS[dim]:
        if unit == unit_to:  # just skip
            continue
        value = bfs_convert(convertdim, unit, unit_to)[1]
        _add_conversion_and_inverse(convertdim, value, unit, unit_to)


def generate_conversion_factors(unit, distance, energy, mass, charge_unit='e'):
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


def bfs_convert(conversions, unit_from, unit_to):
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
    if unit_from == unit_to:
        return (unit_from, unit_to), 1.0, None
    if (unit_from, unit_to) in conversions:
        return (unit_from, unit_to), conversions[unit_from, unit_to], None
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
                convert[unit1] = bfs_convert(convert, key1, key2)[1]
                convert[unit2] = 1.0 / convert[unit1]


def generate_system_conversions(system1, system2):
    """This will generate conversions between two different systems.

    Parameters
    ----------
    system1 : string
        The system we convert from.
    system2 : string
        The system we convert to.
    """
    for dim in CONVERT:
        convert = CONVERT[dim]
        convert[system1, system2] = bfs_convert(convert, system1, system2)[1]
        convert[system2, system1] = 1.0 / convert[system1, system2]


def print_table(unit, system=False):
    """Print out tables with conversion factors.

    This is a table in rst format which is useful for displaying conversions.
    Parameters
    ----------
    unit : string
        The unit we would like to print out conversions for.
    system : boolean
        Determines if we print out information for system conversions or not.

    Returns
    -------
    None, but print output to screen
    """
    row_fmt = '  | {:10s} | {:16.8e} | {:16.8e} |'
    row_head = '  | {:10s} | {:16s} | {:16s} |'
    row_line = ''.join(['+-', ('-')*10, '-+-', ('-')*16, '-+-',
                        ('-')*16, '-+'])
    row_line = '  {}'.format(row_line)
    if system:
        title = 'Conversions for {} to other systems'.format(unit)
        print('\n.. _conversions-{}-system:'.format(unit))
    else:
        title = 'Conversions for {}'.format(unit)
        print('\n.. _conversions-{}:'.format(unit))
    print('\n{}'.format(title))
    print(('-') * len(title))
    for dim in sorted(CONVERT):
        header = '.. table:: Conversion factors for: {}'
        header = header.format(dim.capitalize())
        if system:
            print('\n.. _{}-{}-system:'.format(dim, unit))
        else:
            print('\n.. _{}-{}:'.format(dim, unit))
        print('\n{}\n'.format(header))
        row = row_head.format('Unit', '{} -> unit'.format(unit),
                              'unit -> {}'.format(unit))
        print(row_line)
        print(row)
        print(row_line.replace('-', '='))
        for unt in sorted(CONVERT[dim]):
            un1, un2 = unt
            if system and (un1 in UNITS[dim] or un2 in UNITS[dim]):
                continue
            if un1 == unit:
                row = row_fmt.format(un2, CONVERT[dim][unt],
                                     CONVERT[dim][un2, un1])
                print(row)
                print(row_line)
    print('\n')
    print('Value of kB: {}'.format(CONSTANTS['kB'][unit]))
    print('\n')


def write_conversions(filename='units.txt'):
    """This method will print out the information in CONVERT.

    This method is intended for creating a big list of conversion factors
    that can be included in this script for defining unit conversions.

    Parameters
    ----------
    filename : string, optional
        The file to write units to.
    """
    with open(filename, 'wb') as fileh:
        for dim in sorted(CONVERT):
            convert = CONVERT[dim]
            for unit in sorted(convert):
                out = '{} {} {} {}\n'.format(dim, unit[0], unit[1],
                                             convert[unit])
                fileh.write(out.encode('utf-8'))


def read_conversions(filename='units.txt', units=None):
    """Load conversion factors from a file.

    This will load unit conversions from a file.

    Parameters
    ----------
    filename : string, optional
        The file to load units from.

    Returns
    -------
    out : dict
        A dictionary with the conversions.
    units : string, optional
        If `select` is different from None, it can be used to pick out only
        conversions for a specific system of units, e.g. real or gromacs etc.
    """
    convert = {}
    with open(filename, 'r') as fileh:
        for lines in fileh:
            try:
                dim, unit1, unit2, conv = lines.strip().split()
                conv = float(conv)
                if dim not in CONVERT:
                    raise ValueError
            except ValueError:
                msg = 'Skipping line "{}" in {}'.format(lines.strip(),
                                                        filename)
                warnings.warn(msg)
                continue
            if not dim in convert:
                convert[dim] = {}
            if not units:
                convert[dim][unit1, unit2] = conv
            else:
                if units in (unit1, unit2):
                    convert[dim][unit1, unit2] = conv
    return convert


for key in DIMENSIONS:
    convert_bases(key)

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
                'au': {'length': (1.0, 'bohr'),
                       'energy': (1.0, 'hartree'),
                       'mass': (9.10938356e-31, 'kg'),
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
    generate_conversion_factors(uni, UNIT_SYSTEMS[uni]['length'],
                                UNIT_SYSTEMS[uni]['energy'],
                                UNIT_SYSTEMS[uni]['mass'],
                                charge_unit=UNIT_SYSTEMS[uni]['charge'])

if __name__ == '__main__':
    # This is intended as an example of how to use the functions
    # here to generate conversion factors for systems. This in case you
    # would like to generate your own system of units.
    # To make use of this example, just comment out the line where the
    # units are read above.
    # First, we just generate conversions between the bases:
    NEW_UNITS = {}
    NEW_UNITS['pyretis'] = {'length': (10, 'A'),
                            'energy': (42.0, 'J'),
                            'mass': (42.0, 'g/mol'),
                            'charge': 'e'}
    for uni in NEW_UNITS:
        generate_conversion_factors(uni, NEW_UNITS[uni]['length'],
                                    NEW_UNITS[uni]['energy'],
                                    NEW_UNITS[uni]['mass'],
                                    charge_unit=NEW_UNITS[uni]['charge'])
    # Units can be stored by:
    #write_conversions()
    # and loaded by:
    #ccc = read_conversions(units='metal')
    #for key in ccc:
    #    print(key)
    #    for key2 in ccc[key]:
    #        print(key2, ccc[key][key2])
    # just write out a table:
    for uni in NEW_UNITS:
        print_table(uni)
    # Also add some conversions between systems:
    #print(bfs_convert(CONVERT['energy'], 'lj', 'gromacs'))
    #print(bfs_convert(CONVERT['time'], 'gromacs', 'real'))
    #print(bfs_convert(CONVERT['energy'], 'lj', 'real'))
    #print(bfs_convert(CONVERT['length'], 'lj', 'real'))
    #print(bfs_convert(CONVERT['mass'], 'lj', 'real'))
    # To generate conversions between different systems:
    #for sys1 in UNIT_SYSTEMS:
    #    for sys2 in UNIT_SYSTEMS:
    #        if sys1 != sys2:
    #            generate_system_conversions(sys1, sys2)
    #for uni in UNIT_SYSTEMS:
    #    print_table(uni, system=True)
