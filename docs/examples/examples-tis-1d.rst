.. _examples-tis-1d:

TIS in a 1D potential
=====================

In this example, you will explore a rare event
with the Transition Interface Sampling (TIS) algorithm.

We will consider a simple 1D potential where a particle is moving.
The potential is given by
:math:`V_{\text{pot}} = x^4 - 2 x^2` where :math:`x` is the position.
By plotting this potential, we see that we have two states
(at :math:`x=-1` and :math:`x=1`) separated by a barrier (at :math:`x=0`):

.. _fig1dpot_ex_tis:

.. figure:: /_static/img/examples/1dpot.png
    :alt: The 1D potential example
    :width: 60%
    :align: center

    The potential energy as a function of the position. We have two
    stable states (at x = -1 and x = 1) separated by a barrier (at x = 0).
    In addition, three paths are shown. One is reactive while the two others
    are not able to escape the state at x = -1. Using the TIS method, we can
    generate such paths which gives information about the reaction rate and
    the mechanism. The vertical dotted lines show two TIS interfaces.

Using the TIS algorithm, we will compute the rate constant for
the transition between the two states. This particular problem has been
considered before by van Erp [1]_ [2]_ and we will here try to reproduce these
results.

In order to obtain a rate constant, we will have to obtain both the
crossing probability and an initial flux. To obtain to the
crossing probability, we need to carry out TIS simulations for
each path ensemble we define and in order to obtain the
initial flux, we will have to carry out a MD simulation.
Below we describe the two kinds of input files we need to create.

.. _examples-tis-1d-input:

Creating and running the TIS simulations with |pyretis|
-------------------------------------------------------

We will now create the input file for |pyretis|. We will do this section by section in order
to explain the different keywords and settings. The full input file is given at the end of
this section.

Setting up the simulation task
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first thing we will define is the type of simulation we will run. This
is done by creating a :ref:`simulation section <user-section-simulation>`.

Here, we are going to do a ``tis`` simulation and we will do
20000 steps [2]_. Since we will be running a path sampling simulation, we will also need to specify the
positions of the interfaces we will be using.

.. literalinclude:: /_static/examples/tis1d/tis-1d.txt
   :language: rst
   :lines: 1-8

Setting up the system
^^^^^^^^^^^^^^^^^^^^^
We will now set up the system we are going to consider. Here, we will actually
define several |pyretis| input sections:

* The :ref:`system section <user-section-system>` which defines
  the units, dimensions and temperature we are considering:

  .. literalinclude:: /_static/examples/tis1d/tis-1d.txt
     :language: rst
     :lines: 10-14

* The :ref:`box section <user-section-box>`, but since
  we are here just considering a single particle in a 1D potential, we will simply use
  a 1D box without periodic boundaries:

  .. literalinclude:: /_static/examples/tis1d/tis-1d.txt
     :language: rst
     :lines: 16-18

* The :ref:`particles section <user-section-particles>` which add particles to
  the system and defines the initial state:

  .. literalinclude:: /_static/examples/tis1d/tis-1d.txt
     :language: rst
     :lines: 43-51

  In this case, we will read the initial configuration from
  a file :download:`initial.xyz </_static/examples/tis1d/initial.xyz>`
  and velocities are generated from a Maxwell distribution. Further, we
  specify the mass, particle type and we label the particle as ``Ar``. Note that
  this does not mean that we are simulating Argon, it is just a label used in
  the output of trajectories.

* The :ref:`force field <user-section-forcefield>` and
  :ref:`potential <user-section-potential>` sections which setup up
  the :ref:`1D double well potential <user-section-potential-doublewell>`:

  .. literalinclude:: /_static/examples/tis1d/tis-1d.txt
     :language: rst
     :lines: 53-62

Selecting the engine
^^^^^^^^^^^^^^^^^^^^

Here, we will make use of a stochastic :ref:`Langevin engine<user-section-engine-langevin>`.
We set it up by setting the time step, the friction parameter and whether
we are in the high friction limit. The seed given is a seed for the
random number generator used by the integrator.

.. literalinclude:: /_static/examples/tis1d/tis-1d.txt
   :language: rst
   :lines: 20-26

TIS specific settings
^^^^^^^^^^^^^^^^^^^^^

The TIS settings control how the TIS algorithm is carried out.
Here we set that 50 % of the moves should be shooting moves (keyword ``freq``)
and we limit all paths to a maximum length of 20 000 steps.
Further, we select aimless shooting and we tell |pyretis| to not set the
momentum to zero and to not rescale the energy after drawing new random velocities.
We also set ``allowmaxlength = False`` which means that for shooting,
we determine (randomly) the length of new paths based on the length of
the path we are shooting from. The given seed is a seed for the random number
generator used by the TIS algorithm.

.. literalinclude:: /_static/examples/tis1d/tis-1d.txt
   :language: rst
   :lines: 28-37


Initial path settings
^^^^^^^^^^^^^^^^^^^^^

These settings determine how we find the initial path(s).
Here, we ask |pyretis| to generate these using the
:ref:`kick method <user-section-initial-path-kick>`.

.. literalinclude:: /_static/examples/tis1d/tis-1d.txt
   :language: rst
   :lines: 39-41

Selecting the order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For this system, we simply define the order parameter as
the :ref:`position <user-section-orderparameter-position>`
of the single particle we are simulating.

.. literalinclude:: /_static/examples/tis1d/tis-1d.txt
   :language: rst
   :lines: 64-69

Modifying the output
^^^^^^^^^^^^^^^^^^^^

To save some disk space, we will set up the simulation to
only write output for trajectories at every 100th step.

.. literalinclude:: /_static/examples/tis1d/tis-1d.txt
   :language: rst
   :lines: 71-75

.. pyretis-collapse-block::
   :heading: Show/hide the full TIS input file

   .. literalinclude:: /_static/examples/tis1d/tis-1d.txt
      :language: rst


Running the TIS simulation(s)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now run the TIS simulation. Create a new directory and
place the input file (let's call it ``tis.rst``) here. Also, download the initial configuration
:download:`initial.xyz </_static/examples/tis1d/initial.xyz>`
and place it in the same folder. The TIS simulations are executed in two steps:

1. Input TIS files are created for each path ensemble. This is done by
   running:

   .. code-block:: pyretis

      pyretisrun -i tis.rst

   which will create files named ``tis-001.rst``, ``tis-002.rst`` and so on.
   Each one of these files defines a TIS simulation for a specific path ensemble.

2. Running the |pyretis| TIS simulations for each path ensemble.
   The individual TIS simulations can be executed by running:

   .. code-block:: pyretis

      pyretisrun -i tis-001.rst -p -f 001.log

   and so on. All these TIS simulations are independent and can, in priciple,
   be executed in parallel.

The ``-p`` option will display a progress bar for your simulation and ``-f``
will rename the log file.

Analysing the TIS results
^^^^^^^^^^^^^^^^^^^^^^^^^

When the all the TIS simulations are finished, we can analyse the results.
|pyretis| will create a file, ``out.rst_000``, which you can use for the analysis.
This is a copy of the input ``tis.rst`` with some additional settings
for the analysis. For a description of the analysis specific keywords,
we refer to the :ref:`analysis section <user-section-analysis>`.

The analysis itself is performed using:

.. code-block:: pyretis

   pyretisanalyse -i out.rst_000

This will produce a new folder, ``report`` which contains the
results from the analysis. If you have latex installed, you can
generate a pdf using the file ``tis_report.tex`` within the
``report`` folder. An example result is shown below.

.. _fig1dpot_ex_prob1:

.. figure:: /_static/examples/tis1d/prob1.png
    :alt: Crossing probability after 20000 cycles.
    :align: center

    The crossing probability after running for 20 000 cycles.
    The numerical value is :math:`8.3 \times 10^{-7}  \pm 21 \%`.


.. _examples-tis-1d-flux:

Creating and running the initial flux simulation with |pyretis|
---------------------------------------------------------------

The initial flux simulation measure effective crossings with the
first interface. In |pyretis| such a simulation is requested by
selecting the :ref:`md-flux <user-section-simulation-mdflux>` task.

This can be done by setting the following simulation settings:

.. literalinclude:: /_static/examples/tis1d/flux-1d.txt
   :language: rst
   :lines: 4-8

The other sections will be similar to the sections already defined
for the TIS simulation, however, we do not need to include the
TIS section for the md-flux simulation. The full input file
is given below.

.. pyretis-collapse-block::
   :heading: Show/hide the full MD-flux input file

   .. literalinclude:: /_static/examples/tis1d/flux-1d.txt
      :language: rst

Running the md-flux simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now run the md-flux simulation. Create a new directory and
place the input file (let's call it ``flux.rst``) here. Also, download the initial configuration
:download:`initial.xyz </_static/examples/tis1d/initial.xyz>`
and place it in the same folder. The md-flux simulation can now be executed using:

.. code-block:: pyretis

   pyretisrun -i flux.rst -p


Analysing the md-flux results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When the md-flux simulation has finished, we can analyse the results.
|pyretis| will create a file, ``out.rst``, which you can use for the analysis.
This is a copy of the input ``flux.rst`` with some additional settings
for the analysis. For a description of the analysis specific keywords,
we refer to the :ref:`analysis section <user-section-analysis>`.

The analysis itself is performed using:

.. code-block:: pyretis

   pyretisanalyse -i out.rst

This will produce a new folder, ``report`` which contains the
results from the analysis. If you have latex installed, you can
generate a pdf using the file ``md_flux_report.tex`` within the
``report`` folder. An example result is shown below.


.. _fig1dpot_ex_flux:

.. figure:: /_static/examples/tis1d/flux.png
    :alt: Initial flux
    :align: center

    The running average for the initial flux.

Improving the statistics
------------------------

We can improve the statistics by running a longer simulation.
Modify the number of steps, from 20000 to 1000000 and re-run the simulation
and the analysis. Below we show an example for the crossing probability
after performing the additional steps

.. _fig1dpot_ex_prob2:

.. figure:: /_static/examples/tis1d/prob2.png
    :alt: Crossing probability after running for longer.
    :align: center

    The crossing probability after running for 1 000 000 steps.
    The numerical value is :math:`9.73 \times 10^{-7}  \pm  2.9 \%`.

References
----------


.. [1] Titus S. Van Erp, Dynamical Rare Event Simulation Techniques for Equilibrium and Nonequilibrium Systems,
       Advances in Chemical Physics, 151, pp. 27 - 60, 2012, http://dx.doi.org/10.1002/9781118309513.ch2

.. [2] https://arxiv.org/abs/1101.0927

