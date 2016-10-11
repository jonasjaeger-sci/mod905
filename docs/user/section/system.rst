.. _user-section-system:

The system section
------------------

The system section defines some properties of the system.

.. _user-section-system-keyword-units:

units
~~~~~
The ``units`` keyword defines the system of units to use by pyretis.

Example:

.. code-block:: rst

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

The system of units should be one of the systems defined by
pyretis listed above. Alternatively, you can define your own unit system by
making use of a special :ref:`unit-system <user-section-unit-system>` section
in combination with the ``units`` keyword.

References
~~~~~~~~~~

.. [1]  Rowley et al., J. Comput. Phys., vol. 17, pp. 401-414, 1975,
   doi: http://dx.doi.org/10.1016/0021-9991

.. [2]  The LAMMPS manual, http://lammps.sandia.gov/doc/units.html

.. [3]  https://en.wikipedia.org/wiki/Atomic_units

.. [4]  The GROMACS manual, tables 2.1 and 2.2 on page. 8,
   http://manual.gromacs.org/documentation/5.1.1/manual-5.1.1.pdf

