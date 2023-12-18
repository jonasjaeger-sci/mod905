.. _examples-gromacs-hydrate:

Transport of methane in a sI hydrate
====================================

In this example, we are going to study the transport
of methane in a sI hydrate structure. The initial
configuration is shown in :numref:`fig_gromacs_hydrate`.

.. _fig_gromacs_hydrate:

.. figure:: /_static/examples/gromacs-hydrate/hydrate1.png
    :alt: Snapshot of the hydrate system
    :width: 50%
    :align: center

    A snapshot of the sI hydrate system. The methane molecule is modeled
    as a single particle (united atom) and is here shown as a blue sphere.

The process we will investigate is the diffusion of the methane molecule
between different cages in the hydrate structure. The order parameter
which measures the progress of the methane molecule is defined as the
distance traveled by the methane molecule along a vector pointing
between the geometric center of selected rings in the hydrate
structure (see :numref:`fig_gromacs_hydrate_order` for an illustration).

In this example, we will make use of GROMACS [1]_ for running the
dynamics. The example is structured as follows:

.. contents::
   :local:


Defining the order parameter
----------------------------

The order parameter we make use of is illustrated :ref:`below <fig_gromacs_hydrate_order>`.

.. _fig_gromacs_hydrate_order:

.. figure:: /_static/examples/gromacs-hydrate/order.png
    :alt: Order parameter for the hydrate example
    :width: 80%
    :align: center

    Illustration of the order parameter used for the hydrate example.
    Oxygen atoms in two cages/rings are identified (colored cyan and orange)
    and the geometric center of these two groups is obtained (shown
    as the magenta and green spheres in the right image). This is used to
    define a vector between the two centers (illustrated with the black
    arrow in the right image). The order parameter is taken
    as the distance vector between the methane and the first center
    (green sphere) projected onto the vector joining the two centers.

This is a custom order parameter and we will now create a Python script
for calculating it. We refer to the section on
:ref:`creating custom order parameters <user-guide-custom-order>` for more
detailed information on how this can be done. Here, we just give the full
Python script for calculating the order parameter:

.. pyretis-collapse-block::
   :heading: Show/hide the Python script for the order parameter.

   .. literalinclude:: /_static/examples/gromacs-hydrate/orderp.py
      :language: python

This order parameter can be used in a simulation in |pyretis|
by adding the following order parameter section to the input file:

.. literalinclude:: /_static/examples/gromacs-hydrate/order.rst
   :language: rst

In addition, we can add extra order parameters, for instance
the position (z-coordinate) of the diffusing methane molecule:

.. literalinclude:: /_static/examples/gromacs-hydrate/orderc.rst
   :language: rst


Creating the |pyretis| input file
---------------------------------

The input file for |pyretis| follows the structure we have used in the
previous examples and we will not go into details about all sections here.
In the following, we will just describe the section for using the
GROMACS engine in more detail. The full input file for the RETIS simulation
is given at the end of this section.

In order to make use of GROMACS, we add the following engine section
to the input file:

.. literalinclude:: /_static/examples/gromacs-hydrate/retis.rst
   :language: rst
   :lines: 17-24

Here, we make use of the following keywords:

* ``class = gromacs`` which specifies the engine we will use
  (here: :ref:`gromacs <user-section-engine-gromacs>`).

* ``gmx = gmx_5.1.4`` which specifies the GROMACS gmx executable.
  On your system, this might be named differently, for instance ``gmx = gmx``.

* ``mdrun = gmx_5.1.4 mdrun`` which specifies the command for running
  GROMACS. Note that you here can tune how to run GROMACS, for instance by
  adding a ``mpirun`` or something similar if that fits your system.

* ``input_path = gromacs_input`` which specifies the directory where |pyretis|
  will look for the input files for GROMACS. |pyretis| assumes that, at least,
  the following files are in this folder:

  1. ``conf.g96`` which contains the initial configuration to use.

  2. ``topol.top`` which contains the topology for GROMACS.

  3. ``grompp.mdp`` which contains simulation settings for GROMACS.

  The files needed for this example can be downloaded as a zip
  archive here: :download:`gromacs_input.zip </_static/examples/gromacs-hydrate/gromacs_input.zip>`.

* ``timestep = 0.002`` which is the time step to use in the GROMACS simulations.

* ``subcycles = 5`` which is the number of subcycles GROMACS will complete
  before |pyretis| re-calculated order parameter. This will also be the
  frequency by which GROMACS write information (trajectory and energies) to
  the disk.

This specifies and selects the GROMACS engine for use with |pyretis|.
The full input file for the RETIS simulation is given below:

.. pyretis-collapse-block::
   :heading: Show/hide the input file for the hydrate simulation.

   .. literalinclude:: /_static/examples/gromacs-hydrate/retis.rst
      :language: rst

Running the RETIS simulation with |pyretis|
-------------------------------------------

In order to run the RETIS simulation, the following steps
are suggested:

1. Create a new folder for the simulation named ``gromacs-hydrate``
   and enter this directory.

2. Create a new file ``orderp.py`` containing the script for
   calculating the order parameter.

3. Create a new file ``retis.rst`` with the input settings for
   the simulation.

4. Download the input files
   (:download:`gromacs_input.zip </_static/examples/gromacs-hydrate/gromacs_input.zip>`)
   for GROMACS and store these in a new
   directory named ``gromacs_input``.

5. Run the RETIS simulation using:

   .. code-block:: pyretis

      pyretisrun -i retis.rst -p

This will execute the |pyretis| simulation. An example of a reactive trajectory (obtained
in the last path ensemble) is shown in :numref:`fig_gromacs_hydrate_traj`.

.. _fig_gromacs_hydrate_traj:

.. figure:: /_static/examples/gromacs-hydrate/trajectory.png
    :alt: Snapshots from a representative trajectory
    :width: 100%
    :align: center

    Snapshots from a trajectory in the last path ensemble.
    The methane molecule (colored blue) exits from the starting cage
    and enter the next cage. This can be visualized by selecting a
    reactive trajectory from the simulation, and pressing the Play-
    button in the Analysis-tab of PyVisA


References
----------

.. [1] The GROMACS web-page, http://www.gromacs.org/
