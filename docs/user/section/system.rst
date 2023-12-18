.. _user-section-system:

The System section
==================

The ``system`` section defines some properties of the system.

.. pyretis-input-example:: System

   .. code-block:: rst

      System
      ------
      units = reduced
      dimensions = 2
      temperature = 1.0

Keywords for the System section
-------------------------------

The following keywords can be set for the System section:

.. |system_dimensions| replace:: :ref:`dimensions <user-section-system-keyword-dimensions>`
.. |system_temperature| replace:: :ref:`temperature <user-section-system-keyword-temperature>`
.. |system_units| replace:: :ref:`units <user-section-system-keyword-units>`

.. _table-system-keywords:

.. table:: Keywords for the System section
   :class: table-striped table-hover

   +----------------------+---------------------------------------------------+
   | Keyword              | Description                                       |
   +======================+===================================================+
   | |system_dimensions|  | Specify the dimensionality of the system.         |
   +----------------------+---------------------------------------------------+
   | |system_temperature| | Specify a set temperature for the system.         |
   +----------------------+---------------------------------------------------+
   | |system_units|       | Sepcify the unit system to use.                   |
   +----------------------+---------------------------------------------------+

.. _user-section-system-keyword-dimensions:

Keyword dimensions
^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: dimensions integer

   Specify the dimensionality of the system.
   Should be 1, 2, or 3 for 1D, 2D or 3D, respectively.

   Default:
     The default value is ``dimensions = 3``.


.. _user-section-system-keyword-temperature:

Keyword temperature
^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: temperature float

   Specify a set temperature for the system. This temperature, :math:`T`, is
   used:

   - to obtain :math:`\beta = 1/(k_\text{B} \times T)`
     where :math:`k_\text{B}` is the Boltzmann constant for the system.

   - as a target temperature for velocity generation if no temperature is given in the
     :ref:`velocity keyword <user-section-particles-keyword-velocity>` of the
     :ref:`particles section <user-section-particles>`.

   Default:
     The default value is ``temperature = 1.0``.

.. _user-section-system-keyword-units:

Keyword units
^^^^^^^^^^^^^

.. pyretis-keyword:: units string

   The ``units`` keyword defines the system of units to use by |pyretis|.
   Currently, the following system of units are defined by |pyretis|
   (see the :ref:`definitions of unit systems <user-units-system>`):

   - ``lj``: A Lennard-Jones type of (reduced) units (based on Argon [1]_).

   - ``real``: A system of units similar to the LAMMPS [2]_ unit real.

   - ``metal``: A system of units similar to the LAMMPS [2]_ unit metal.

   - ``au``: Atomic units. [3]_

   - ``electron``: A system of units similar to the LAMMPS [2]_ unit electron.

   - ``si``: A system of units similar to the LAMMPS [2]_ unit si.

   - ``gromacs``: A system of units similar to the units used by GROMACS. [4]_

   The system of units should be one of the systems defined by
   |pyretis| listed above. Alternatively, you can define your own unit system by
   making use of a special :ref:`unit-system <user-section-unit-system>` section
   in combination with the ``units`` keyword.

   Default:
     The default value is ``units = lj``.

References
----------

.. [1]  Rowley et al., J. Comput. Phys., vol. 17, pp. 401-414, 1975,
   doi: https://doi.org/10.1016/0021-9991(75)90042-X

.. [2]  The LAMMPS manual, http://lammps.sandia.gov/doc/units.html

.. [3]  https://en.wikipedia.org/wiki/Atomic_units

.. [4]  The GROMACS manual, version 5.1.1, tables 2.1 and 2.2 on page. 8,
   http://manual.gromacs.org/documentation/5.1.1/manual-5.1.1.pdf

