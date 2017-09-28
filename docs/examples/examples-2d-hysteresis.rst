.. _examples-retis-2d:

RETIS in a 2D potential
=======================

In this example  you will explore a rare event
with the Replica Exchange Transition Interface
Sampling (RETIS) algorithm.

In this example we will implement a new potential for |pyretis| and we
will create three new order parameters which we will use to investigate
a transition between two stable states in the potential.
Using the RETIS algorithm, we will compute the rate constant for
the transition between the two stable states.

This example is structured as follows:

.. contents::
   :local:

Creating the potential function
-------------------------------

We will consider a relatively simple 2D potential where a single particle is moving.
The potential energy (:math:`V_\text{pot}`) is given by

.. math::

   V_\text{pot}(x, y) = (x^2 + y^2)^2 -
   10 \exp(-30 (x - 0.2)^2  -3 (y - 0.4)^2)
   -10 \exp(-30 (x + 0.2)^2 -3 (y + 0.4)^2)

where :math:`x` and :math:`y` gives the positions.
The potential energy is shown in
:numref:`fig2dpot_ex_retis` below.

.. _fig2dpot_ex_retis:

.. figure:: /_static/examples/retis2d-hysteresis/potential-2d-hyst.png
    :alt: The 2D potential example
    :align: center

    The potential energy as a function of the position. We have two
    stable states, at (x, y) = (-0.2, -0.4) and (x, y) = (0.2, 0.4)
    (indicated with the circles), separated by a saddle point
    at (x, y) = (0, 0).

We begin by creating a new potential function to use with
|pyretis|, see the :ref:`user guide <user-guide-intro-api-forcefield>` for
a short introduction on how custom potential functions can be created.
In short, we will now have to define a new class which calculates the
potential energy and the corresponding force.

We begin by simply creating a new class for the new potential function.
Here, we define the parameters our new potential should accept. We
implement the potential slightly more general than the potential
given above so that we can change the parameters more easily, if we
wish to do so, later. The potential we will be implementing is
given by:

.. math::

   V_\text{pot}(x, y) = \gamma_1 (x^2 + y^2)^2 +
   \gamma_2 \exp(\alpha_1 (x - x_0)^2 + \alpha_2 (y - y_0)^2) +
   \gamma_3 \exp(\beta_1 (x + x_0)^2 + \beta_2(y + y_0)^2)

where :math:`\gamma_1`,
:math:`\gamma_2`, :math:`\gamma_3`, :math:`\alpha_1`, :math:`\alpha_2`,
:math:`\beta_1`, :math:`\beta_2`, :math:`x_0` and :math:`y_0` are
potential parameters.

Next, we define a new method as part of our new potential class which
will be responsible for calculating the potential energy and
a method responsible for calculating the force. Finally, we
add a method that will calculate both the potential and the force
at the same time. The full Python code for the new potential class
can be found below.

.. pyretis-collapse-block::
   :heading: Show/hide the new potential class

   .. literalinclude:: /_static/examples/retis2d-hysteresis/potential.py
      :language: python

This new potential function can be included in a |pyretis| simulation by
referencing it in the input file as follows (assuming that it has been
stored in a file named ``potential.py``):

.. literalinclude:: /_static/examples/retis2d-hysteresis/potential.txt
   :language: rst

Creating the order parameters
-----------------------------

In this case, it is not so obvious how to define the order parameter.
Three simple possibilities are (see :numref:`fig2dpot_order`
for an illustration):

1. The x coordinate of the particle, where we include the potential
   energy in order to define the two stable states.

2. The y coordinate of the particle, where we include the potential
   energy in order to define the two stable states.

3. The projection of the distance vector from the position of
   the particle (x, y) to (-0.2, -0.4) onto the straight line
   between (-0.2, -0.4) and (0.2, 0.4). Here, we also include the
   potential energy in order to define the two stable states.

.. _fig2dpot_order:

.. figure:: /_static/examples/retis2d-hysteresis/orderparameters.png
    :alt: Order parameters for the 2D example.
    :align: center

    Illustration of the three different order parameters with location
    of interfaces (dotted lines).
    From left to right: using the x position as the
    order parameter, using the y position as the order parameter and,
    finally, in the rightmost figure,
    using a combination of x and y as the order parameter. The white line
    in the rightmost figure show the line which we project the order
    parameter onto.
    The blue paths are valid paths for the final path ensembles and in the
    bottom row, the corresponding order parameters are shown for these
    paths. The light dotted interface lines represents the location where
    we include the potential energy in the definition of the order parameters.
    The two marked points (cross and triangle) in the paths in the bottom row
    show the second last and last points in the paths, respectively. The two
    marked points (cross and circle) in the paths in the top row show the
    first and last points in the paths, respectively.

Since we include the potential energy in the order parameter
definition, we will have to create customized order parameters.
There is a short :ref:`introduction <user-guide-intro-api-orderparameterc>` to
how the order parameters are implemented in |pyretis| in the user guide and
there is also a more lengthy recipe for
:ref:`creating custom order parameters <user-guide-custom-order>` available.

Here, we will first consider the x (or y) order parameter and then the more
involved combination.

Creating the x (or y) positional order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The order parameter we are now creating will just be the position
of the particle with two extra conditions:

1. If the position is below a certain value (``inter_a``)
   close to the first interface and if the potential energy
   is above a certain threshold value (``energy_a``), then the
   order parameter will not be allowed to come closer to
   the first interface.

2. If the position is closer to the last interface than
   a certain value (``inter_b``) and if the potential energy
   is above a certain threshold value (``energy_b``), then the
   order parameter will not be allowed to come closer to the
   last interface.

Thus, in addition to the position of the particle, we need to
consider the 4 additional parameters ``inter_a``, ``inter_b``,
``energy_a``, ``energy_b``. The Python code for this new
order parameter is given below:

.. pyretis-collapse-block::
   :heading: Show/hide the new order parameter

   .. literalinclude:: /_static/examples/retis2d-hysteresis/order-x.py
      :language: python

This new order parameter can be included in a |pyretis| simulation by
adding the following order parameter section (assuming that the order
parameter is stored in a file ``order.py``):

.. literalinclude:: /_static/examples/retis2d-hysteresis/order-x.txt
   :language: rst

Creating the projection-of-positions order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For this order parameter, we will consider the distance from
the particle to the stable A state and project the distance vector
onto the line joining states A and B. In addition, as in the
previously defined order parameters, we will include the energy
in the definition of the states.

The Python code for this new
order parameter is given below:

.. pyretis-collapse-block::
   :heading: Show/hide the new order parameter

   .. literalinclude:: /_static/examples/retis2d-hysteresis/order-xy.py
      :language: python

Note that this order parameter is defined less general than the previous
ones, for instance we make explicit use of the location of the two minimums.
If you are feeling adventurous, please try to add these locations
as parameters for the order parameter.

This new order parameter can be included in a |pyretis| simulation by
adding the following order parameter section (assuming that the order
parameter is stored in a file ``order.py``):

.. literalinclude:: /_static/examples/retis2d-hysteresis/order-xy.txt
   :language: rst

Running the RETIS simulation with |pyretis|
-------------------------------------------

We have now defined the potential and the order parameters we are going
to use and we are ready to run the RETIS simulations.

Running the RETIS simulation using x as the order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to run the RETIS simulation, the following steps are suggested:

1. Create a new folder, for instance ``2D-hysteresis``.

2. Place the order parameter script in this folder and name it ``order.py``.

3. Download the initial configuration
   :download:`initial.xyz </_static/examples/retis2d-hysteresis/initial.xyz>` and
   place it in the same directory.

4. Create a new sub-directory, ``retis-x``.

5. Add the following input script
   :download:`retis-x.rst </_static/examples/retis2d-hysteresis/retis-x.rst>` to the
   ``retis-x`` folder.

6. Run the simulation using (in the ``retis-x`` folder):

   .. code-block:: pyretis

      pyretisrun -i retis-x.rst -p

Some examples from the analysis can be found below:

.. _fig2dpot_retisx:

.. figure:: /_static/examples/retis2d-hysteresis/retis-x-many.png
    :alt: Example paths harvested.
    :align: center

    Example of paths harvested for the RETIS simulation. All paths
    shown are accepted paths for the last path ensemble.

.. _fig2dpot_prob_x:

.. figure:: /_static/examples/retis2d-hysteresis/prob-x.png
    :alt: Crossing probability.
    :align: center

    The crossing probability after 1 000 000 RETIS cycles.
    The numerical value is :math:`3.77 \times 10^{-7} \pm 6.6 \%`. The
    initial flux is :math:`1.97 \pm  0.7 \%`.


Running the RETIS simulation using y as the order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to run the RETIS simulation, the following steps are suggested:

1. Create a new folder, for instance ``2D-hysteresis``.

2. Place the order parameter script in this folder and name it ``order.py``.

3. Download the initial configuration
   :download:`initial.xyz </_static/examples/retis2d-hysteresis/initial.xyz>` and
   place it in the same directory.

4. Create a new sub-directory, ``retis-y``.

5. Add the following input script
   :download:`retis-y.rst </_static/examples/retis2d-hysteresis/retis-y.rst>` to the
   ``retis-y`` folder.

6. Run the simulation using (in the ``retis-y`` folder):

   .. code-block:: pyretis

      pyretisrun -i retis-y.rst -p

Some examples from the analysis can be found below:

.. _fig2dpot_retisy:

.. figure:: /_static/examples/retis2d-hysteresis/retis-y-many.png
    :alt: Example paths harvested.
    :align: center

    Example of paths harvested for the RETIS simulation. All paths
    shown are accepted paths for the last path ensemble.

.. _fig2dpot_prob_y:

.. figure:: /_static/examples/retis2d-hysteresis/prob-y.png
    :alt: Crossing probability.
    :align: center

    The crossing probability after 1 000 000 RETIS cycles.
    The numerical value is :math:`4.94 \times 10^{-7} \pm 5.6 \%`. The
    initial flux is :math:`1.66 \pm  0.4 \%`.    


Running the RETIS simulation using the projection-of-position as the order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to run the RETIS simulation, the following steps are suggested:

1. Create a new folder, for instance ``2D-hysteresis``.

2. Create a new sub-directory, ``retis-xy`` and move into this directory.

3. Place the order parameter script in this folder and name it ``order.py``.

4. Download the initial configuration
   :download:`initial2.xyz </_static/examples/retis2d-hysteresis/initial2.xyz>` and
   place it in the same directory and rename it to ``initial.xyz``.

5. Add the following input script
   :download:`retis-xy.rst </_static/examples/retis2d-hysteresis/retis-xy.rst>` to the
   ``retis-xy`` folder.

6. Run the simulation using (still in the ``retis-xy`` folder):

   .. code-block:: pyretis

      pyretisrun -i retis-xy.rst -p

Some examples from the analysis can be found below:

.. _fig2dpot_retisxy:

.. figure:: /_static/examples/retis2d-hysteresis/retis-xy-many.png
    :alt: Example paths harvested.
    :align: center

    Example of paths harvested for the RETIS simulation. All paths
    shown are accepted paths for the last path ensemble.

.. _fig2dpot_prob_xy:

.. figure:: /_static/examples/retis2d-hysteresis/prob-xy.png
    :alt: Crossing probability.
    :align: center

    The crossing probability after 1 000 000 RETIS cycles.
    The numerical value is :math:`5.03 \times 10^{-7} \pm 9.0 \%`. The
    initial flux is :math:`1.54 \pm  0.6 \%`.

Comparing results from the analysis
-----------------------------------

By using the three different order parameters, we different estimates for rate constant
as summarized in the table below.

.. _table_2d_hysteresis:

.. table:: Comparison of the rate constant for the 2D potential
   :class: table-hover

   +-------------------+-------------+-------------+
   | Order parameter   | Rate constant / 1e-7      |  
   +                   +-------------+-------------+
   |                   | Lower bound | Upper bound |
   +===================+=============+=============+
   | x                 | 7.3         | 8.3         |
   +-------------------+-------------+-------------+
   | y                 | 7.7         | 8.6         |
   +-------------------+-------------+-------------+
   | xy                | 7.3         | 8.3         |
   +-------------------+-------------+-------------+
