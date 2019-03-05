.. _user-section-box:

The Box section
===============

The ``box`` section defines the simulation box.
This is useful, for instance, if periodic boundary
conditions are needed.

.. pyretis-input-example:: Box

   .. code-block:: rst

      Box settings
      ------------
      cell = [10, 10, 10]
      periodic = [True, True, False]


Keywords for the Box section
----------------------------

For the Box section the following keywords can be set:

.. |box_cell| replace:: :ref:`cell <user-section-box-keyword-cell>`

.. |box_low| replace:: :ref:`low <user-section-box-keyword-low>`

.. |box_high| replace:: :ref:`high <user-section-box-keyword-high>`

.. |box_periodic| replace:: :ref:`periodic <user-section-box-keyword-periodic>`

.. _table-box-keywords:

.. table:: Keywords for the Box section
   :class: table-striped table-hover

   +----------------+---------------------------------------------------------+
   | Keyword        | Description                                             |
   +================+=========================================================+
   | |box_cell|     | Which defines the cell parameters of the simulation     |
   |                | box.                                                    |
   +----------------+---------------------------------------------------------+
   | |box_low|      | Which defines the lower boundaries of the box.          |
   +----------------+---------------------------------------------------------+
   | |box_high|     | Which defines the upper boundaries of the box.          |
   +----------------+---------------------------------------------------------+
   | |box_periodic| | Which determines if the simulation box has periodic     |
   |                | boundaries.                                             |
   +----------------+---------------------------------------------------------+


.. _user-section-box-keyword-cell:

Keyword cell 
^^^^^^^^^^^^^^

.. pyretis-keyword:: cell list of floats

   The ``cell`` keyword defines the length of the
   simulation box in each dimension. This
   is given by a list of numbers:

   .. code-block:: rst

       Box
       ---
       cell = [2, 3, 5]
       # or
       cell = [10, 10, float('inf')]

   This will define a simulation box with limits starting from 0
   and up to the specified length.
   In case you want to explicitly define the boundaries you can do
   this by making use of the keywords
   :ref:`low <user-section-box-keyword-low>` and
   :ref:`high <user-section-box-keyword-high>` described below.
   Note that if more than three values are given, then the created box
   will be triclinic. The box is then represented by a matrix:

   * If 6 values are given:

     .. math::

        \begin{bmatrix} a_{0} & a_{3} & a_{4} \\
                        0 & a_{1} & a_{5} \\
                        0 & 0 & a_{2} \\
        \end{bmatrix}

   * If 9 values are given:

     .. math::

        \begin{bmatrix} a_{0} & a_{5} & a_{7} \\
                        a_{3} & a_{1} & a_{8} \\
                        a_{4} & a_{6} & a_{2} \\
        \end{bmatrix}

   Default:
     If the cell is not given in the box section, then the cell will
     be set to infinite in all directions. However, if present, the
     cell found in the input configuration will be used.

.. _user-section-box-keyword-low:

Keyword low
^^^^^^^^^^^

.. pyretis-keyword:: low list of floats

   Determines the lower boundaries for the simulation box.

   .. code-block:: rst

       Box
       ---
       low = [0, -1, 0]

   Default:
     The default setting is ``0`` for each dimension.

.. _user-section-box-keyword-high:

Keyword high
^^^^^^^^^^^^

.. pyretis-keyword:: high list of floats

   Determines the upper boundaries for the simulation box.

   .. code-block:: rst

       Box
       ---
       high = [10, -10, 100]

   Default:
     The default setting is ``low + cell``.

.. _user-section-box-keyword-periodic:

Keyword periodic
^^^^^^^^^^^^^^^^

.. pyretis-keyword:: periodic list of boolean

   Determines if the boundaries of the simulation box are periodic or not.
   This is defined by giving a list of boolean values:

   .. code-block:: rst

       Box
       ---
       periodic = [True, True, True]

   or for a 2D case:

   .. code-block:: rst

       Box
       ---
       periodic = [True, False]

   Default:
     The default setting is **periodic** (``True``) for all directions.
