.. _user-keywords-box:

box
---
Define the simulation box.

Example:

.. code-block:: python

    box = {'periodic': [False]}

The ``box`` keyword defines the simulation box to use.
For the ``box`` keyword, we can set two attributes:

size
    The size of the simulation box. This is set by a list of numbers,
    one length for each dimension.

    .. code-block:: python

        box = {'size': [10]}
        box = {'size': [10, 10, float('inf')]}

    In case you want to explicitly define the boundaries you can also do
    this:
    
    .. code-block:: python

        box = {'size': [(-10, 10), 10]}
    
periodic
    Determines if we have periodic boundaries. This is defined by
    giving a list of boolean values:

    .. code-block:: python

        box = {'periodic': [True, False, True]}
    
