.. _examples-cp2k-hydrogen:

Dissociation of Hydrogen with CP2K
==================================

In this example, we are going to study dissociation
of hydrogen using CP2K. The goal of this example is to
show how CP2K can be interfaced with |pyretis| for a relatively
simple system.

In this example, we will make use of CP2K [1]_ for running the
dynamics. The example is structured as follows:

.. contents::
   :local:

The order parameter we will consider in this example will
just be given by the distance between the two hydrogen atoms.


Creating the |pyretis| input file
---------------------------------

The input file for |pyretis| follows the structure we have used in the
previous examples and we will not go into details about all sections here.
In the following, we will just describe the section for using the
CP2K engine in more detail. The full input file for the RETIS simulation
is given at the end of this section.

In order to make use of CP2K, we add the following engine section
to the input file:

.. literalinclude:: /_static/examples/cp2k-hydrogen/retis.rst
   :language: rst
   :lines: 14-21

Here, we make use of the following keywords:

* ``class = cp2k`` which specifies the engine we will use
  (here: :ref:`cp2k <user-section-engine-cp2k>`).

* ``cp2k = cp2k`` which specifies the CP2K executable.
  On your system, this might be named differently.

* ``input_path = cp2k_input`` which specifies the directory where |pyretis|
  will look for the input files for CP2K. |pyretis| assumes that, at least,
  the following files are in this folder:

  1. ``initial.xyz`` which contain the initial configuration.
     This file can be downloaded
     here: :download:`initial.xyz </_static/examples/cp2k-hydrogen/initial.xyz>`.

  2. ``cp2k.inp`` which contains the settings for the CP2K simulation.
     This file can be downloaded
     here: :download:`cp2k.inp </_static/examples/cp2k-hydrogen/cp2k.inp>`.

* ``timestep = 0.5`` which is the time step to use in the CP2K simulations.

* ``subcycles = 3`` which is the number of subcycles CP2K will complete
  before |pyretis| re-calculates the order parameter.

* ``extra_files = ['BASIS_SET', 'GTH_POTENTIALS']`` which contain extra
  files CP2K will need in order to execute. Here, we are using two files
  to define the basis set and the potential functions. These files are
  part of the CP2K distribution and can be found in the folder
  ``$CP2K_HOME/data/`` (or ``/usr/share/cp2k``). |pyretis| expects
  that all the files you list here are included in the ``cp2k_input``
  directory.

This specifies and selects the CP2K engine for use with |pyretis|.
The full input file for the RETIS simulation is given below:

.. pyretis-collapse-block::
   :heading: Show/hide the input file for the CP2K simulation.

   .. literalinclude:: /_static/examples/cp2k-hydrogen/retis.rst
      :language: rst

Running the RETIS simulation with |pyretis|
-------------------------------------------

In order to run the RETIS simulation, the following steps
are suggested:

1. Create a new folder for the simulation named ``cp2k-hydrogen``
   and enter this directory.

2. Create a new file ``retis.rst`` with the input settings for
   the simulation.

3. Download the input files given above and store them in
   a new directory named ``cp2k_input``.

4. Copy the extra files ``BASIS_SET`` and ``GTH_POTENTIALS`` from
   your CP2K distribution and place them in the ``cp2k_input`` folder.

5. Run the RETIS simulation using:

   .. code-block:: pyretis

      pyretisrun -i retis.rst -p

References
----------

.. [1] The CP2K web-page, https://www.cp2k.org/
