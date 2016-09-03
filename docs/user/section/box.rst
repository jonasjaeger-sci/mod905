.. _user-section-box:

The box section
---------------
Defines the simulation box.

Example:

.. code-block:: rst

    Box settings
    ------------
    size = [10, 10, 10]
    periodic = [True, True, False]

For the ``box`` section, we can set two keywords: ``size`` and ``periodic``.

.. _user-section-box-keyword-size:

size
~~~~
The size of the simulation box. This is set by a list of numbers,
one length for each dimension.

.. code-block:: rst

    Box
    ---
    size = [10]
    # or
    size = [10, 10, float('inf')]

In case you want to explicitly define the boundaries you can also do
this:

.. code-block:: rst

    Box
    ---
    size = [(-10, 10), 10]
    
.. _user-section-box-keyword-periodic:

periodic
~~~~~~~~
Determines if we have periodic boundaries. This is defined by
giving a list of boolean values:

.. code-block:: rst

    Box
    ---
    periodic = [True, False, True]
