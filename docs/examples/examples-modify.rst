.. _examples-modify:

Extending pyretis
=================

By making use of the :ref:`pyretis API <api-doc>` it is possible
to extend the program with custom order parmaters, new force fields,
new simulation types, new path sampling methods and so on.


.. _examples-modify-orderparameter:

Adding a new order parameter
----------------------------

This example will show you how you can create a new order parameter
in pyretis. In order to do this, we will need to reference the
:ref:`pyretis API <api-doc>` documentation and in particular the
:ref:`order parameter module <api-core-orderparameter>`.
We will also need basic understanding of the system object
which is described in the :ref:`system module <api-core-system>`.

The order parameter module defines the base class ``OrderParameter``
which implements two special functions,

* ``calculate(system)``
   This the function that calculates the order parameter given
   a system object.

* ``calculate_velocity(system)``
    This the function that calculates the velocity for the
    order parameter given a system object.

In order to implement our new order parameter we will create a new
object which inherits from ``OrderParameter`` but overrides
the ``calculate(system)`` and ``calculate_velocity(system)`` functions.
