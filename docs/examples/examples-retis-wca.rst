.. _examples-retis-wca:

Breaking a bond with RETIS
==========================

In this example, you will explore bond breaking in
a simple model system
with the Replica Exchange Transition Interface
Sampling (RETIS) algorithm.

The system we consider consist of a simple diatomic
bistable molecule immersed in a fluid of purely repulsive
particles. This system was actually considered in the
article introducing the TIS method, [1]_ and we will here
largely follow this simulation set-up. We refer to the
original article for more details.

The potential we use to describe the bond for the
diatomic molecule is a double-well potential,
similar to the
:ref:`DoubleWellWCA <user-section-potential-doublewellwca>` potential
implemented in |pyretis|. By tuning the potential parameters, we will consider two cases:
one with a high barrier and one with a low barrier.

This example is structured as follows:

.. contents::
   :local:

The high barrier case
---------------------

For the low barrier case, we will consider a 2D system consisting
of 25 particles and the kinetic energy is scaled so that
the energy of the system is 25 in reduced units. [1]_ Further, the
number density of the system is set to 0.7,
the barrier height is :math:`h = 15`, the width parameter is :math:`w = 0.5`
and :math:`r_0 = 2^{1/6}`.

Defining the potential functions and the order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For this example, we implement both the potential functions and
the order parameter in C. The code can be downloaded as this
zip-archive: :download:`high.zip </_static/examples/retis2d-wca/high.zip>`.

In this case, we define the order parameter as the distance between
the two atoms in the diatomic molecule.

Running the RETIS simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The script for running the RETIS simulation is given below.
Note that before running the simulation with |pyretis| you will
have to compile the C code for the order parameter and the potential
functions:

.. code-block:: pyretis

   python setup.py build_ext --inplace

The input script given below assumes that the order parameter and the
potential functions are stored in a sub-folder named ``c-for-python3``.
The initial configuration can be downloaded here:
:download:`initial-high.xyz </_static/examples/retis2d-wca/initial-high.xyz>`.

.. pyretis-collapse-block::
   :heading: Show/hide the RETIS input file.
   
   .. literalinclude:: /_static/examples/retis2d-wca/retis-high.rst
      :language: rst

The |pyretis| simulation can be executed in the usual way:

.. code-block:: pyretis

   pyretisrun -i retis-high.rst -p

Before running the simulation: 
Ensure that the files and directories (i.e. the initial configuration
and the modules referenced) are named correctly with respect to the files
you have downloaded for this example.

The low barrier case
--------------------

For the low barrier case, we will consider a 2D system consisting
of 9 particles and the kinetic energy is scaled so that
the energy of the system is 9 in reduced units. [1]_ Further, the
number density of the system is set to 0.6,
the barrier height is :math:`h = 6`, the width parameter
is :math:`w = 0.25` and :math:`r_0 = 2^{1/6}`.


Defining the potential functions and the order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For this example, we implement the potential functions in C.
The code can be downloaded as a zip-archive
here: :download:`low.zip </_static/examples/retis2d-wca/low.zip>`.

For the order parameter, we include a kinetic energy and potential
energy [1]_ in the definition to ensure the stability of the initial
and final states. The Python code for the order parameter can
be found below.

.. pyretis-collapse-block::
   :heading: Show/hide the order parameter Python script
   
   .. literalinclude:: /_static/examples/retis2d-wca/orderp.py
      :language: python


Running the RETIS simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The script for running the RETIS simulation is given below.
Note that before running the simulation with |pyretis| you will
have to compile the C code for the potential

.. code-block:: pyretis

   python setup.py build_ext --inplace

and create the script for the order parameter (the input script
given below assumes that the order parameter is stored in a file
``orderp.py``.
The initial configuration can be downloaded
here: :download:`initial-low.xyz </_static/examples/retis2d-wca/initial-low.xyz>`.

.. pyretis-collapse-block::
   :heading: Show/hide the RETIS input file.
   
   .. literalinclude:: /_static/examples/retis2d-wca/retis-low.rst
      :language: rst

The |pyretis| simulation can be executed in the usual way:

.. code-block:: pyretis

   pyretisrun -i retis-low.rst -p

Before running the simulation: 
Ensure that the files and directories (i.e. the initial configuration
and the modules referenced) are named correctly with respect to the files
you have downloaded for this example.

References
----------

.. [1] Titus S. van Erp, Daniele Moroni, and Peter G. Bolhuis,
       A novel path sampling method for the calculation of rate constants,
       The Journal of Chemical Physics, 118, pp. 7762 - 7774, 2003. 
