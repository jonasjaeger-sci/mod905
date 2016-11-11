.. _user-section-unit-system:

unit-system
-----------
The ``units-system`` section is used in combination with the
``units`` keyword from the system section for defining custom
system of units.
When defining a custom unit system, the ``units`` keyword
is used to select the new system and 
and the ``unit-system`` section is defining the base units.

Example:

.. code-block:: rst

    System
    ------
    units = new-system

    Unit-system
    -----------
    name = new-system
    length = (1.0, 'bohr')
    mass = (9.81e-31, 'kg')
    energy = (1.0, 'kcal/mol')
    charge = e

For the ``unit-system`` section the scale for each dimension
(``'length'``, ``'mass'``, ``'energy'`` and ``'charge'``)
need to be supplied on the form

.. code-block:: rst

    dimension =  (value, 'baseunit')

Where ``'dimension'`` is a text string selecting a dimension,
``value`` is a number defining the scale and ``'baseunit'``
a text string selecting the base unit to use for the
selected ``'dimension'``.
For an overview of the possible base units, please see
the description in the manual section
:ref:`describing units in pyretis <user-units-custom>`.
Also note that the ``baseunit`` is **case sensitive**!
