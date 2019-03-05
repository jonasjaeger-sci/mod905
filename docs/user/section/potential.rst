.. _user-section-potential:

The Potential section
=====================

The ``potential`` section specifies a single
potential function to add to the force field.

.. pyretis-input-example:: Potential

   .. code-block:: rst

      Potential
      ---------
      class = DoubleWell
      parameter a = 1.0
      parameter b = 2.0
      parameter c = 0.0

In order to add several potential functions to a force
field, several ``Potential`` sections can be added:

.. pyretis-input-example:: Potential

   .. code-block:: rst

       Potential
       ---------
       class = PairLennardJonesCutnp
       shift = True
       dim = 2
       mixing = geometric
       parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'factor': 1.12246205}
       parameter 1 = {'sigma': 1.0, 'epsilon': 1.0, 'factor': 1.12246205}

       Potential
       ---------
       class = DoubleWellWCA
       dim = 2
       parameter rzero = 1.122462048309373
       parameter height = 15.0
       parameter width = 0.5
       parameter types = [(1, 1)]


As the different potentials typically require different
settings, detailed information can be found below
for specific potentials:

.. contents::
   :local:
   :depth: 3

.. _user-section-potential-doublewell:

The DoubleWell potential
------------------------
This class defines a one-dimensional double well potential.
The potential energy (:math:`V_\text{pot}`) is given by

.. _user-doublewell-equation:

.. math::

   V_\text{pot} = a x^4 - b (x - c)^2

where :math:`x` is the position and :math:`a`, :math:`b`
and :math:`c` are parameters for the potential.

.. pyretis-input-example:: Potential
   :class-name: DoubleWell

   .. code-block:: rst

      Potential
      ---------
      class = DoubleWell
      parameter a = 1.0
      parameter b = 2.0
      parameter c = 0.0

Keywords for the DoubleWell potential
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following keywords can be specified for the
DoubleWell potential:

.. |dwell_class| replace:: :ref:`class <user-section-doublewell-class>`
.. |dwell_parameter| replace:: :ref:`parameter <user-section-doublewell-parameter>`


.. _table-keywords-doublewell:

.. table:: Keywords for the DoubleWell potential.
   :class: table-striped table-hover

   +-------------------+------------------------------------------------------+
   | Keyword           | Description                                          |
   +===================+======================================================+
   | |dwell_class|     | Selects the DoubleWell potential.                    |
   +-------------------+------------------------------------------------------+
   | |dwell_parameter| | Sets the parameters for the potential.               |
   +-------------------+------------------------------------------------------+


.. _user-section-doublewell-class:

Keyword class
.............

.. pyretis-keyword:: class DoubleWell
   :specific: yes

   This keyword selects the potential and should be set to: ``DoubleWell``.

.. _user-section-doublewell-parameter:

Keyword parameter
.................

For the DoubleWell potential, three parameters can be specified:

.. pyretis-keyword:: parameter a float

   The ``a`` parameter in the potential energy :ref:`function <user-doublewell-equation>`
   given above.

   Default:
     The default is: ``parameter a = 1.0``

.. pyretis-keyword:: parameter b float

   The ``b`` parameter in the potential energy :ref:`function <user-doublewell-equation>`
   given above.

   Default:
     The default is: ``parameter b = 1.0``

.. pyretis-keyword:: parameter c float

   The ``c`` parameter in the potential energy :ref:`function <user-doublewell-equation>`
   given above.

   Default:
     The default is: ``parameter c = 0.0``

.. _user-section-potential-rectangularwell:

The RectangularWell potential
-----------------------------

This class defines a one-dimensional rectangular well potential.
The potential energy is zero within the potential well and infinite
outside. The well is defined with a left and right boundary.

.. pyretis-input-example:: Potential
   :class-name: RectangularWell

   .. code-block:: rst

      Potential
      ---------
      class = RectangularWell
      parameter left = -1.0
      parameter right = 1.0

Keywords for the RectangularWell potential
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following keywords can be specified for the
RectangularWell potential:

.. |rwell_class| replace:: :ref:`class <user-section-rectangularwell-class>`
.. |rwell_parameter| replace:: :ref:`parameter <user-section-rectangularwell-parameter>`

.. _table-keywords-rectangularwell:

.. table:: Keywords for the RectangularWell potential.
   :class: table-striped table-hover

   +-------------------+------------------------------------------------------+
   | Keyword           | Description                                          |
   +===================+======================================================+
   | |rwell_class|     | Selects the RectangularWell potential.               |
   +-------------------+------------------------------------------------------+
   | |rwell_parameter| | Sets the parameters for the potential.               |
   +-------------------+------------------------------------------------------+


.. _user-section-rectangularwell-class:

Keyword class
.............

.. pyretis-keyword:: class RectangularWell
   :specific: yes

   This keyword selects the potential and should be set to: ``RectangularWell``.

.. _user-section-rectangularwell-parameter:

Keyword parameter
.................

For the RectangularWell potential, two parameters can be set.

.. pyretis-keyword:: parameter left float

   The ``left`` border for the potential well function.
   The
   potential energy is 0 for positions :math:`x` such that
   :math:`\text{left} < x < \text{right}`.

   Default:
     The default parameter is: ``parameter left = 0.0``

.. pyretis-keyword:: parameter right float

   The ``right`` border for the potential well function.
   The
   potential energy is 0 for positions :math:`x` such that
   :math:`\text{left} < x < \text{right}`.

   Default:
     The default parameter is: ``parameter right = 1.0``


.. _user-section-potential-pairlennardjonescutnp:

The PairLennardJonesCutnp potential
-----------------------------------
This class implements as simple Lennard-Jones 6-12 potential which
employs a simple cut-off and can be shifted. The potential energy
(:math:`V_\text{pot}`) is defined in the usual way for an
interacting pair :math:`(i,j)` of particles a distance :math:`r` apart,

.. math::

   V_\text{pot} = 4 \varepsilon_{ij} \left( x^{12} - x^{6} \right),

where :math:`x = \sigma_{ij}/r` and :math:`\varepsilon_{ij}`
and :math:`\sigma_{ij}` are the potential parameters.

.. pyretis-input-example:: Potential
   :class-name: PairLennardJonesCutnp

   Here is an example for defining parameters for a mixture of 3 particle types with
   geometric mixing.

   .. code-block:: rst

      Potential
      ---------
      class = PairLennardJonesCutnp
      shift = True
      dim = 3
      mixing = geometric
      parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}
      parameter 1 = {'sigma': 1.2, 'epsilon': 1.1, 'rcut': 2.5}
      parameter 2 = {'sigma': 1.4, 'epsilon': 0.9, 'rcut': 2.5}

Keywords for the PairLennardJonesCutnp potential
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following keywords can be specified for the
PairLennardJonesCutnp potential:

.. |ljnp_class| replace:: :ref:`class <user-section-pairljnp-class>`

.. |ljnp_dim| replace:: :ref:`dim <user-section-pairljnp-dim>`

.. |ljnp_shift| replace:: :ref:`shift <user-section-pairljnp-shift>`

.. |ljnp_mixing| replace:: :ref:`mixing <user-section-pairljnp-mixing>`

.. |ljnp_parameter| replace:: :ref:`parameter <user-section-pairljnp-parameter>`

.. _table-pairljnp-keywords:

.. table:: Keywords for the PairLennardJonesCutnp potential.
   :class: table-striped table-hover

   +------------------+-------------------------------------------------------+
   | Keyword          | Description                                           |
   +==================+=======================================================+
   | |ljnp_class|     | Selects the potential.                                |
   +------------------+-------------------------------------------------------+
   | |ljnp_dim|       | Set the number of dimensions to consider.             |
   +------------------+-------------------------------------------------------+
   | |ljnp_shift|     | Determines if the potential should be shifted.        |
   +------------------+-------------------------------------------------------+
   | |ljnp_mixing|    | Selects the mixing rules for generating parameters    |
   |                  | for cross interactions.                               |
   +------------------+-------------------------------------------------------+
   | |ljnp_parameter| | Sets the parameters for the potential.                |
   +------------------+-------------------------------------------------------+


.. _user-section-pairljnp-class:

Keyword class
.............

.. pyretis-keyword:: class PairLennardJonesCutnp
   :specific: yes

   This keyword selects the potential and should be set to: ``PairLennardJonesCutnp``.

.. _user-section-pairljnp-dim:

Keyword dim
...........

.. pyretis-keyword:: dim integer

   Sets the dimensionality for the potential.
   Should be 1, 2, or 3 for 1D, 2D or 3D, respectively.

   Default:
     The default value is ``dim = 3``.

.. _user-section-pairljnp-shift:

Keyword shift
.............

.. pyretis-keyword:: shift boolean

   Determines if the potential should be shifted or not. This
   should be either ``True`` (enables shifting) or ``False`` (disables
   shifting). If shifting is ``True``, the following value will be added
   to the potential (for a given :math:`(i, j)` pair):

   .. math::

      V_{\text{shift}} = 4 \varepsilon_{ij} \left( x_{\text{c}}^{12} - x_{\text{c}}^{6} \right),

   where :math:`x_{\text{c}} = \sigma_{ij} / r_{\text{c}, ij}` and
   :math:`r_{\text{c}, ij}` is the cut-off.

   Default:
      The default value is ``shift = True``.

.. _user-section-pairljnp-mixing:

Keyword mixing
..............

.. pyretis-keyword:: mixing string

   Determines how mixing parameters for the potential should be
   determined. The supported mixing rules are:

   * ``mixing = geometric``:

     * :math:`\epsilon_{ij} = \sqrt{\epsilon_{i} \times \epsilon_{j}}`
     * :math:`\sigma_{ij} = \sqrt{\sigma_{i} \times \sigma_{j}}`
     * :math:`r_{\text{c},ij} = \sqrt{r_{\text{c},i} \times r_{\text{c},j}}`

   * ``mixing = arithmetic``:

     * :math:`\epsilon_{ij} = \sqrt{\epsilon_{i} \times \epsilon_{j}}`
     * :math:`\sigma_{ij} = \frac{\sigma_{i} \times \sigma_{j}}{2}`
     * :math:`r_{\text{c},ij} = \frac{r_{\text{c},i} \times r_{\text{c},j}}{2}`

   * ``mixing = Sixthpower``:

     * :math:`\epsilon_{ij} = 2 \sqrt{\epsilon_{i} \times \epsilon_{j}} \frac{\sigma_i^3 \times \sigma_j^3}{\sigma_i^6 + \sigma_j^6}`
     * :math:`\sigma_{ij} = \left( \frac{\sigma_{i}^6 \times \sigma_{j}^6}{2} \right)^{1/6}`
     * :math:`r_{\text{c},ij} = \left(\frac{r_{\text{c},i}^6 \times r_{\text{c},j}^6}{2}\right)^{1/6}`

   Default
      The default value is ``mixing = geometric``.

.. _user-section-pairljnp-parameter:

Keyword parameter
.................

The following parameters can be set for the PairLennardJonesCutnp
potential:

.. pyretis-keyword:: parameter i dictionary

   The parameters for the ``PairLennardJonesCutnp`` potentials are given for each particle type
   on the form:

   .. code-block:: rst

      parameter i = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}

   Where ``i`` is the particle type, identified as an integer. Here, ``sigma`` is
   :math:`\sigma_i`, ``epsilon`` is :math:`\varepsilon_i` and ``rcut`` is :math:`r_{\text{c},i}`.

   Note that several parameters can be given in this way and that they will be combined
   according to the selected :ref:`mixing rule <user-section-pairljnp-mixing>`.


.. _user-section-potential-doublewellwca:

The DoubleWellWCA potential
---------------------------

This class defines a n-dimensional Double Well potential.
The potential energy (:math:`V_\text{pot}`) for a pair of particles
separated by a distance :math:`r` is given by,

.. _user-doublewellwca-equation:

.. math::

   V_\text{pot} = h (1 - (r - r_0 - w)^2/w^2)^2,

where :math:`h` gives the 'height' of the potential, :math:`r_0` the
minimum and :math:`w` the width.

.. pyretis-input-example:: Potential
   :class-name: DoubleWellWCA

   .. code-block:: rst

      Potential
      ---------
      class = DoubleWellWCA
      dim = 2
      parameter rzero = 1.122462048309373
      parameter height = 6.0
      parameter width = 0.25
      parameter types = [(1, 1)]


Keywords for the DoubleWellWCA potential
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following keywords can be specified for the
DoubleWellWCA potential:

.. |dwca_class| replace:: :ref:`class <user-section-dwwca-class>`

.. |dwca_dim| replace:: :ref:`dim <user-section-dwwca-dim>`

.. |dwca_parameter| replace:: :ref:`parameter <user-section-dwwca-parameter>`

.. _table-keywords-doublewellwca:

.. table:: Keywords for the DoubleWellWCA potential
   :class: table-striped table-hover

   +------------------+-------------------------------------------------------+
   | Keyword          | Description                                           |
   +==================+=======================================================+
   | |dwca_class|     | Selects the potential.                                |
   +------------------+-------------------------------------------------------+
   | |dwca_dim|       | Sets the number of dimensions to consider.            |
   +------------------+-------------------------------------------------------+
   | |dwca_parameter| | Sets the parameters for the potential.                |
   +------------------+-------------------------------------------------------+


.. _user-section-dwwca-class:

Keyword class
.............

.. pyretis-keyword:: class DoubleWellWCA
   :specific: yes

   Selects the potential, should be set to: ``DoubleWellWCA``.

.. _user-section-dwwca-dim:

Keyword dim
...........

.. pyretis-keyword:: dim integer

   Sets the dimensionality for the potential.
   Should be 1, 2, or 3 for 1D, 2D or 3D, respectively.

   Default:
      The default value is ``dim = 3``.

.. _user-section-dwwca-parameter:

Keyword parameter
.................

The following parameters can be set for the DoubleWellWCA potential:

.. pyretis-keyword:: parameter zero float

   This is the :math:`r_0` parameter in the
   potential energy :ref:`function <user-doublewellwca-equation>` given above.

   Default
        The default is ``rzero = 0``

.. pyretis-keyword:: parameter height float

   This is the :math:`h` parameter in the
   potential energy :ref:`function <user-doublewellwca-equation>` given above.

   Default
        The default is ``height = 0``

.. pyretis-keyword:: parameter width float

   This is the :math:`w` parameter in the
   potential energy :ref:`function <user-doublewellwca-equation>` given above.

   Default
        The default is ``width = 0``

.. pyretis-keyword:: parameter types list of tuples of integers

   This parameter determines for which pair of particles the interaction should
   act on. If this is not set, it will turn on the interaction for all
   particles. For example, if ``types = [(1,2)]`` the interaction will be
   turned on between particles of type ``1`` and type ``2`` only. (See
   the :ref:`particle section <user-section-particles-keyword-type>` for a
   description about the particle type.) Note that several types can be
   specified at the same time: ``types = [(1, 2), (0, 1), (0, 2)]``.

   Default
        The default is activated for all pairs.

.. _user-section-potential-custom:

User-defined potential functions
--------------------------------

User-defined potential functions are selected as follows:

.. pyretis-input-example:: Potential
   :class-name: a user-defined class

   .. code-block:: rst

       Potential
       ---------
       class = PotentialName
       module = potential.py
       keyword1 = value
       parameter p = 123.

Here, the user can both define custom keywords and parameters. However,
the ``class`` and the ``module`` **must** always be specified in this case.

Keywords for user-defined potential functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At least, the following keywords can be specified for
user-defined potential functions:

.. |user_class| replace:: :ref:`class <user-section-potential-user-class>`

.. |user_module| replace:: :ref:`module <user-section-potential-user-module>`

.. _table-keywords-user-potential:

.. table:: Keywords for user.defined potential functions.
   :class: table-striped table-hover

   +---------------+----------------------------------------------------------+
   | Keyword       | Description                                              |
   +===============+==========================================================+
   | |user_class|  | Selects the Python class which implements the potential. |
   +---------------+----------------------------------------------------------+
   | |user_module| | Defines the file where the Python class with the         |
   |               | potential can be found.                                  |
   +---------------+----------------------------------------------------------+


.. _user-section-potential-user-class:

Keyword class
.............

.. pyretis-keyword:: class string

   This keyword selects the potential function and it should be set to
   the class name of the custom potential function class defined
   in the given :ref:`module <user-section-potential-user-module>`.

.. _user-section-potential-user-module:

Keyword module
..............

.. pyretis-keyword:: module string

   This keyword specified the location of the file containing the
   user-defined class for the potential function.
   This file must be accessible by |pyretis|.

   Default
       Not any. This keyword must be specified.
