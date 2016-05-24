.. _user-keywords-units:

units
-----
The ``units`` keyword defines the system of units to use by pyretis.
The system of units should be one of the systems defined by
pyretis  or you define your own system of units by making use of the
keyword :ref:`units-base <user-keywords-units-base>` in combination
with the ``units`` keyword.

Example:

.. code-block:: python

    units = lj

Currently, the following system of units are defined by pyretis
(see the :ref:`definitions of unit systems <user-units-system>`):

- ``lj``: A Lennard-Jones type of (reduced) units (based on Argon [1]_).

- ``real``: A system of units similar to the LAMMPS [2]_ unit real.

- ``metal``: A system of units similar to the LAMMPS [2]_ unit metal.

- ``au``: Atomic units. [3]_

- ``electron``: A system of units similar to the LAMMPS [2]_ unit electron.

- ``si``: A system of units similar to the LAMMPS [2]_ unit si.

- ``gromacs``: A system of units similar to the units used by GROMACS. [4]_



.. _user-keywords-units-base:

units-base
----------
The ``units-base`` keyword is used in combination with the
``units`` keyword for defining custom unit systems.
When defining a custom unit system, ``units`` is used to define
it's name and ``units-base`` is defining the base units for

Example:

.. code-block:: python

    units = new-system

    units-base = {'length': (1.0, 'bohr'),
                  'mass': (9.81e-31, 'kg'),
                  'energy': (1.0, 'kcal/mol'),
                  'charge_unit': 'e'}

For the keyword ``units-base`` the scale for each dimension
(``'length'``, ``'mass'``, ``'energy'`` and ``'charge_unit'``)
need to be supplied on the form

.. code-block:: python

    units-base = {'dimension': (value, 'baseunit'), ...}

Where ``'dimension'`` is a text string selecting a dimension,
``value`` is a number defining the scale and ``'baseunit'``
a text string selecting the base unit to use for the
selected ``'dimension'``.
For an overview of the possible base units, please see
the description in the manual section
:ref:`describing units in pyretis <user-units-custom>`.


References
----------

.. [1]  Rowley et al., J. Comput. Phys., vol. 17, pp. 401-414, 1975,
   doi: http://dx.doi.org/10.1016/0021-9991

.. [2]  The LAMMPS manual, http://lammps.sandia.gov/doc/units.html

.. [3]  https://en.wikipedia.org/wiki/Atomic_units

.. [4]  The GROMACS manual, tables 2.1 and 2.2 on page. 8,
   http://manual.gromacs.org/documentation/5.1.1/manual-5.1.1.pdf

