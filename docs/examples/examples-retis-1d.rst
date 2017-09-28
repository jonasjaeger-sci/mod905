.. _examples-retis-1d:

RETIS in a 1D potential
=======================

In this example  you will explore a rare event
with the Replica Exchange Transition Interface
Sampling (RETIS) algorithm.

We will consider a simple 1D potential where a particle is moving.
The potential is given by
:math:`V_{\text{pot}} = x^4 - 2 x^2` where :math:`x` is the position.
By plotting this potential, we see that we have two states
(at :math:`x=-1` and :math:`x=1`) separated by a barrier (at :math:`x=0`):

.. _fig1dpot_ex_retis:

.. figure:: /_static/img/examples/1dpot.png
    :alt: The 1D potential example
    :width: 60%
    :align: center

    The potential energy as a function of the position. We have two
    stable states (at x = -1 and x = 1) separated by a barrier (at x = 0).
    In addition, three paths are shown. One is reactive while the two others
    are not able to escape the state at x = -1. Using the RETIS method, we can
    generate such paths which gives information about the reaction rate and
    the mechanism. The vertical dotted lines show two RETIS interfaces.

Using the RETIS algorithm, we will compute the rate constant for
the transition between the two states. This particular problem has been
considered before by van Erp [1]_ [2]_ and we will here try to reproduce these
results.

Creating the |pyretis| input file
---------------------------------

We will now create the input file for |pyretis|. We will do this section by section in order
to explain the different keywords and settings. The full input file is given at the end of
this section.

Setting up the simulation task
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first thing we will define is the type of simulation we will run. This
is done by creating a :ref:`simulation section <user-section-simulation>`.

Here, we are going to do a ``retis`` simulation and we will do
20000 steps [2]_. Since we will be running a path sampling simulation, we will also need to specify the
positions of the interfaces we will be using.

.. literalinclude:: /_static/examples/retis1d/retis-1d.txt
   :language: rst
   :lines: 1-8

Setting up the system
^^^^^^^^^^^^^^^^^^^^^
We will now set up the system we are going to consider. Here, we will actually
define several |pyretis| input sections:

* The :ref:`system section <user-section-system>` which defines
  the units, dimensions and temperature we are considering:

  .. literalinclude:: /_static/examples/retis1d/retis-1d.txt
     :language: rst
     :lines: 10-14

* The :ref:`box section <user-section-box>`, but since
  we are here just considering a single particle in a 1D potential, we will simply use
  a 1D box without periodic boundaries:

  .. literalinclude:: /_static/examples/retis1d/retis-1d.txt
     :language: rst
     :lines: 16-18

* The :ref:`particles section <user-section-particles>` which add particles to
  the system and defines the initial state:

  .. literalinclude:: /_static/examples/retis1d/retis-1d.txt
     :language: rst
     :lines: 51-59

  In this case, we will read the initial configuration from
  a file :download:`initial.xyz </_static/examples/retis1d/initial.xyz>`
  and velocities are generated from a Maxwell distribution. Further, we
  specify the mass, particle type and we label the particle as ``Ar``. Note that
  this does not mean that we are simulating Argon, it is just a label used in
  the output of trajectories.

* The :ref:`force field <user-section-forcefield>` and
  :ref:`potential <user-section-potential>` sections which setup up
  the :ref:`1D double well potential <user-section-potential-doublewell>`:

  .. literalinclude:: /_static/examples/retis1d/retis-1d.txt
     :language: rst
     :lines: 61-70

Selecting the engine
^^^^^^^^^^^^^^^^^^^^

Here, we will make use of a stochastic :ref:`Langevin engine<user-section-engine-langevin>`.
We set it up by setting the time step, the friction parameter and whether
we are in the high friction limit. The seed given is a seed for the
random number generator used by the integrator.

.. literalinclude:: /_static/examples/retis1d/retis-1d.txt
   :language: rst
   :lines: 20-26

TIS specific settings
^^^^^^^^^^^^^^^^^^^^^

The TIS settings controls how the TIS algorithm is carried out.
Here we set that 50 % of the TIS moves should be shooting moves (keyword ``freq``)
and we limit all paths to a maximum length of 20 000 steps.
Further we select aimless shooting and we tell |pyretis| to not set the
momentum to zero and to not rescale the energy after drawing new random velocities.
Further we set ``allowmaxlength = False`` which means that for shooting,
we determine stochastically the length of new paths based on the length of
the path we are shooting from. The given seed is a seed for the random number
generator used by the TIS algorithm.


.. literalinclude:: /_static/examples/retis1d/retis-1d.txt
   :language: rst
   :lines: 28-37


RETIS specific settings
^^^^^^^^^^^^^^^^^^^^^^^

The RETIS section controls the RETIS algorithm.
Here we request that 50 % of the RETIS moves should be
swapping moves, while the remaining 50 % will be TIS moves.
We further say that we do not do relative shooting and that
we attempt to swap several ensembles at the say time. In case
an ensemble is not participating in the swap, a null move (that is
just accepting the last accepted path again) is carried out.

.. literalinclude:: /_static/examples/retis1d/retis-1d.txt
   :language: rst
   :lines: 39-44

Initial path settings
^^^^^^^^^^^^^^^^^^^^^

These settings determined how we find the initial path(s).
Here, we ask |pyretis| to generate these using the
:ref:`kick method <user-section-initial-path-kick>`.

.. literalinclude:: /_static/examples/retis1d/retis-1d.txt
   :language: rst
   :lines: 46-49

Selecting the order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For this system, we simply define the order parameter as
the :ref:`position <user-section-orderparameter-position>`
of the single particle we are simulating.

.. literalinclude:: /_static/examples/retis1d/retis-1d.txt
   :language: rst
   :lines: 72-77

Modifying the output
^^^^^^^^^^^^^^^^^^^^

In the Output section, we here set the frequency by which
|pyretis| will write out
information about the trajectories, energies and order parameters.

.. literalinclude:: /_static/examples/retis1d/retis-1d.txt
   :language: rst
   :lines: 79-83

.. pyretis-collapse-block::
   :heading: Show/hide the full input file

   .. literalinclude:: /_static/examples/retis1d/retis-1d.txt
      :language: rst

Running the RETIS simulation
----------------------------

We will now run the RETIS simulation. Create a new directory and
place the input file (let's call it ``retis.rst``) here. Also, download the initial configuration
:download:`initial.xyz </_static/examples/retis1d/initial.xyz>`
and place it in the same folder. The simulation can then be executed using:

.. code-block:: pyretis

   pyretisrun -i retis.rst -p

The ``-p`` option will display a progress bar for your simulation.

Analysing the results
---------------------

When the simulation has finished, we can analyse the results.
|pyretis| will create a file, ``out.rst``, which you can use for the analysis.
This is a copy of the input ``retis.rst`` with some additional settings
for the analysis:

.. literalinclude:: /_static/examples/retis1d/out.txt
   :language: rst

For a description of these keywords, we refer to
the :ref:`analysis section <user-section-analysis>`.

The analysis itself is performed using:

.. code-block:: pyretis

   pyretisanalyse -i out.rst

This will produce a new folder, ``report`` which contains the
results from the analysis. If you have latex installed, you can
generate a pdf using the file ``retis_report.tex`` within the
``report`` folder. An example result for the crossing probability
is shown below.

.. _fig1dpot_sample20000:

.. figure:: /_static/examples/retis1d/probability-20000.png
    :alt: Sample results from the RETIS 1D simulation.
    :width: 60%
    :align: center

    Sample output from the analysis. This figure shows the crossing
    probabilities for the individual ensembles and the overall
    crossing probability.

Improving the statistics
------------------------

We can improve the statistics by running a longer simulation.
Modify the number of steps, from 20000 to 1000000 and re-run the simulation
and the analysis. Below we show an example for the crossing probability
after performing the additional steps

.. _fig1dpot_sample1M:

.. figure:: /_static/examples/retis1d/probability-1M.png
    :alt: Sample results from the RETIS 1D simulation.
    :width: 60%
    :align: center

    Sample output from the analysis. This figure shows the crossing
    probabilities for the individual ensembles and the overall
    crossing probability after running 1000000 steps.


References
----------


.. [1] Titus S. Van Erp, Dynamical Rare Event Simulation Techniques for Equilibrium and Nonequilibrium Systems,
       Advances in Chemical Physics, 151, pp. 27 - 60, 2012, http://dx.doi.org/10.1002/9781118309513.ch2

.. [2] https://arxiv.org/abs/1101.0927

