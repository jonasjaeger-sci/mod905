.. _user-section-unit-system:

The unit-system section
=======================
The ``units-system`` section is used in combination with the
``units`` keyword from the system section for defining custom
system of units.
When defining a custom unit system, the ``units`` keyword
is used to select the new system
and the ``unit-system`` section is defining the base units.

.. pyretis-input-example:: unit-system

   .. code-block:: rst

       System
       ------
       units = new-system

       unit-system
       -----------
       name = new-system
       length = (1.0, 'bohr')
       mass = (9.81e-31, 'kg')
       energy = (1.0, 'kcal/mol')
       charge = e

Note that the unit-system section is **optional**.

Keywords for the unit-system section
------------------------------------

For the ``unit-system`` section the scale for each dimension is
specified using the keywords:

.. |units_length| replace:: :ref:`length <user-section-unit-system-length>`
.. |units_mass| replace:: :ref:`mass <user-section-unit-system-mass>`
.. |units_energy| replace:: :ref:`energy <user-section-unit-system-energy>`
.. |units_charge| replace:: :ref:`charge <user-section-unit-system-charge>`

.. _table-unit-system-keywords:

.. table:: Keywords for the unit-system section
   :class: table-striped

   +----------------+---------------------------------------------------------+
   | Keyword        | Description                                             |
   +================+=========================================================+
   | |units_length| | Specify the scale and base unit for the                 |
   |                | length dimension.                                       |
   +----------------+---------------------------------------------------------+
   | |units_mass|   | Specify the scale and base unit for the mass dimension. |
   +----------------+---------------------------------------------------------+
   | |units_energy| | Specify the scale and base unit for the energy          |
   |                | dimension.                                              |
   +----------------+---------------------------------------------------------+
   | |units_charge| | Specify the base unit for the charge dimension          |
   +----------------+---------------------------------------------------------+


.. _user-section-unit-system-length:

Keyword length
^^^^^^^^^^^^^^

.. pyretis-keyword:: length tuple like (float, string)

   The ``length`` keyword specifies the scale and base unit for
   the length dimension. This is done on form:

   .. code-block:: rst

      length = (value, 'baseunit')

   For an overview of the possible base units, please see
   the description in the manual section
   :ref:`describing units in PyRETIS <user-units-custom>`.
   Also, note that the ``'baseunit'`` string is **case-sensitive**!

   Default
      None. This keyword must be specified if the unit-system section is used.


.. _user-section-unit-system-mass:

Keyword mass
^^^^^^^^^^^^

.. pyretis-keyword:: mass tuple like (float, string)

   The ``mass`` keyword specifies the scale and base unit for
   the mass dimension. This is done on form:

   .. code-block:: rst

      mass = (value, 'baseunit')

   For an overview of the possible base units, please see
   the description in the manual section
   :ref:`describing units in PyRETIS <user-units-custom>`.
   Also, note that the ``'baseunit'`` string is **case-sensitive**!

   Default
      None. This keyword must be specified if the unit-system section is used.


.. _user-section-unit-system-energy:

Keyword energy
^^^^^^^^^^^^^^

.. pyretis-keyword:: energy tuple like (float, string)

   The ``energy`` keyword specifies the scale and base unit for
   the energy dimension. This is done on form:

   .. code-block:: rst

      energy = (value, 'baseunit')

   For an overview of the possible base units, please see
   the description in the manual section
   :ref:`describing units in PyRETIS <user-units-custom>`.
   Also, note that the ``'baseunit'`` string is **case-sensitive**!

   Default
      None. This keyword must be specified if the unit-system section is used.

.. _user-section-unit-system-charge:

Keyword charge
^^^^^^^^^^^^^^

.. pyretis-keyword:: charge string

   The ``charge`` keyword specifies base unit for
   the charge dimension. This is done on form:

   .. code-block:: rst

      charge = baseunit

   For an overview of the possible base units, please see
   the description in the manual section
   :ref:`describing units in PyRETIS <user-units-custom>`.
   Also, note that the ``'baseunit'`` string is **case-sensitive**!

   Default
      None. This keyword must be specified if the unit-system section is used.

