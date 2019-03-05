.. _user-section-orderparameter:

The orderparameter section
==========================

The ``orderparameter`` section defines which order parameter to use
for a path sampling simulation.

.. pyretis-input-example:: Orderparameter

   .. code-block:: rst

      Orderparameter
      --------------
      class = Distance
      index = (0, 1)
      periodic = False

Different order parameters require different settings and this is
described in detail below for the different types:

.. contents::
   :local:

.. _user-section-orderparameter-position:

Order parameter Position
------------------------

This order parameter is defined as the position of a single particle in a
specified dimension. It is defined by specifying the class ``Position``,
selecting the index of the particle to use,
dimension to consider and
whether to consider periodic boundaries:

.. pyretis-input-example:: Orderparameter
   :class-name: Position

   .. code-block:: rst

      Orderparameter
      --------------
      class = Position
      index = 0
      dim = x
      periodic = False


Keywords for order parameter Position
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following keywords can be set for order parameter Position:

.. |op_pos_class| replace:: :ref:`class <user-section-orderp-position-class>`
.. |op_pos_index| replace:: :ref:`index <user-section-orderp-position-index>`
.. |op_pos_dim| replace:: :ref:`dim <user-section-orderp-position-dim>`
.. |op_pos_periodic| replace:: :ref:`periodic <user-section-orderp-position-periodic>`

.. _table-keyword-op-pos:

.. table:: Keywords for the Position order parameter.
   :class: table-striped table-hover

   +-------------------+------------------------------------------------------+
   | Keyword           | Description                                          |
   +===================+======================================================+
   | |op_pos_class|    | Selects the Position order parameter.                |
   +-------------------+------------------------------------------------------+
   | |op_pos_index|    | Selects the particle to use.                         |
   +-------------------+------------------------------------------------------+
   | |op_pos_dim|      | Selects the dimension to consider for the position.  |
   +-------------------+------------------------------------------------------+
   | |op_pos_periodic| | Determines if periodic boundaries should be used.    |
   +-------------------+------------------------------------------------------+

.. _user-section-orderp-position-class:

Keyword class
.............

.. pyretis-keyword:: class Position
   :specific: yes

   Selects the order parameter, should be set to ``Position``.

.. _user-section-orderp-position-index:

Keyword index
.............

.. pyretis-keyword:: index integer

   The ``index`` selects the particle to use. The particles are numbered
   sequentially, from 0, in the sequence they appear in the input to |pyretis|.

   Default:
      Not any. This keyword must be specified.

.. _user-section-orderp-position-dim:

Keyword dim
...........

.. pyretis-keyword:: dim string

   The dimension to consider for the position. This can be one of:

   - ``x``: For the x-coordinate of the particle
   - ``y``: For the y-coordinate of the particle
   - ``z``: For the z-coordinate of the particle

   Default:
     Not any. This keyword must be specified.

.. _user-section-orderp-position-periodic:

Keyword periodic
................

.. pyretis-keyword:: periodic boolean

   This keyword determines if we should apply periodic boundaries to
   the position or not. If it is set to ``True`` periodic boundaries
   will be applied.

   Default:
      The default is: ``periodic = False``

.. _user-section-orderparameter-distance:

Order parameter Distance
------------------------

This order parameter is defined as the distance between two
particles. It is defined by selecting the class ``Distance``,
selecting the indices of the particles to
consider and then determining if periodic boundaries should
be used or not:

.. pyretis-input-example:: Orderparameter
   :class-name: Distance

   .. code-block:: rst

      Orderparameter
      --------------
      class = Distance
      index = (10, 11)
      periodic = True


Keywords for order parameter Distance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following keywords can be set for order parameter Distance:

.. |op_dist_class| replace:: :ref:`class <user-section-orderp-distance-class>`
.. |op_dist_index| replace:: :ref:`index <user-section-orderp-distance-index>`
.. |op_dist_periodic| replace:: :ref:`periodic <user-section-orderp-distance-periodic>`

.. _table-keyword-distance:

.. table:: Keywords for the Distance order parameter.
   :class: table-striped table-hover

   +--------------------+-----------------------------------------------------+
   | Keyword            | Description                                         |
   +====================+=====================================================+
   | |op_dist_class|    | Selects the Distance order parameter.               |
   +--------------------+-----------------------------------------------------+
   | |op_dist_index|    | Selects the particles to use for the distance.      |
   +--------------------+-----------------------------------------------------+
   | |op_dist_periodic| | Determines if periodic boundaries should be         |
   |                    | applied.                                            |
   +--------------------+-----------------------------------------------------+


.. _user-section-orderp-distance-class:

Keyword class
.............

.. pyretis-keyword:: class Distance
   :specific: yes

   Selects the order parameter, should be set to ``Distance``.

.. _user-section-orderp-distance-index:

Keyword index
.............

.. pyretis-keyword:: index tuple of integers

   The ``index`` selects the particles to use. The particles are numbered
   sequentially, from 0, in the sequence they appear in the input to |pyretis|.
   This index is selected by specifying the indices as a Python tuple:
   ``index = (0, 1)``

   Default:
      Not any. This keyword must be specified.


.. _user-section-orderp-distance-periodic:

Keyword periodic
................

.. pyretis-keyword:: periodic boolean

   This keyword determines if we should apply periodic boundaries to
   the distance or not. If it is set to ``True`` periodic boundaries
   will be applied.

   Default:
      The default is: ``periodic = False``.

.. _user-section-orderparameter-custom:

User-defined order parameters
-----------------------------

You can also define custom order parameters to use with
|pyretis|. Such order parameters should subclass the
generic :py:class:`.OrderParameter` class as described
in the :ref:`user guide <user-guide-custom-order>`.

.. pyretis-input-example:: Orderparameter
   :class-name: a user-defined order parameter

   .. code-block:: rst

      Orderparameter
      --------------
      class = WCAJCP1
      module = ../orderp/orderp.py
      index = (7,8)
      periodic = True


Keywords for user-defined order parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At least the following keywords can be set for user-defined
order parameters:


.. |op_user_class| replace:: :ref:`class <user-section-orderp-user-class>`

.. |op_user_module| replace:: :ref:`module <user-section-orderp-user-module>`

.. _table-user-defined-order-parameters:

.. table:: Keywords for user-defined order parameters.
   :class: table-striped table-hover

   +------------------+-------------------------------------------------------+
   | Keyword          | Description                                           |
   +==================+=======================================================+
   | |op_user_class|  | Selects a Python class to use as the order parameter. |
   +------------------+-------------------------------------------------------+
   | |op_user_module| | Defines the module where the Python class can be      |
   |                  | located.                                              |
   +------------------+-------------------------------------------------------+


In addition, user-defined keywords can be specified, e.g.:

.. pyretis-input-example:: Orderparameter
   :class-name: a user-defined order parameter

   .. code-block:: rst

      Orderparameter
      --------------
      class = MyOrderParameter
      module = order.py
      setting1 = input
      setting3 = 123.456
      setting2 = True

.. _user-section-orderp-user-class:

Keyword class
.............

.. pyretis-keyword:: class string

   This keyword selects the order parameter and it should be set to
   the class name of the custom order parameter class defined
   in the given :ref:`module <user-section-orderp-user-module>`.

.. _user-section-orderp-user-module:

Keyword module
..............

.. pyretis-keyword:: module string

   This keyword specified the location of the file containing the
   user-defined class for the order parameter.
   This file must be accessible by |pyretis|.

   Default
       Not any. This keyword must be specified.


