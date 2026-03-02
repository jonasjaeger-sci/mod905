.. _examples-md:

Molecular dynamics examples
===========================

In this example, we will perform a MD simulation of a Lennard-Jones fluid.
The purpose of this example is to illustrate two different ways we
can use |pyretis|:

* :ref:`Running the simulation using an input file and the PyRETIS executable <examples-md-nve>`

* :ref:`Running the simulation by making explicit use of the PyRETIS library <examples-md-nve-lib>`

The simulation we set up is rather ordinary and we will
start from a regular lattice and simulate the melting
at a specified temperature as illustrated in the figure below.

.. figure:: /_static/img/nve_md.png
    :class: img-responsive center-block
    :alt: NVE simulation of a LJ fluid
    :align: center

    The initial (left) and the final structure (right) of the Lennard-Jones simulation.
    The initial structure is a FCC lattice, while the final structure is less ordered.

.. contents:: Table of Contents
   :local:


.. _examples-md-nve:

Molecular dynamics using an input file
--------------------------------------
We can execute |pyretis| by creating an input file and using
the |pyretis| application.
In order to run this example, merge the code-snippets given below
into one file, say ``md.rst``, which then can be executed by:

.. code-block:: pyretis

   pyretisrun -i md.rst

In the first part of the input file,
we will specify the type of
simulation to run and the number
of steps to perform by defining the
:ref:`simulation section <user-section-simulation>`:

.. literalinclude:: /_static/examples/md-settings.txt
   :language: rst
   :lines: 1-7

In order to produce some actual dynamics, we
will have to integrate the equations of motion. The
engine to use for this is selected
using the :ref:`engine section <user-section-engine>`:

.. literalinclude:: /_static/examples/md-settings.txt
   :language: rst
   :lines: 9-12

and we define the system we are studying using
the :ref:`system section <user-section-system>`
and the :ref:`particles section <user-section-particles>`:
and the particles:

.. literalinclude:: /_static/examples/md-settings.txt
   :language: rst
   :lines: 14-32

We also need to specify a force field,
which is done by specifying the
:ref:`forcefield section <user-section-forcefield>`
and one or more
:ref:`potential sections <user-section-potential>`.
In this case, the force field is set up using a single
type of potential function:

.. literalinclude:: /_static/examples/md-settings.txt
   :language: rst
   :lines: 34-42

and we modify the output created by specifying the
:ref:`output section <user-section-output>`:

.. literalinclude:: /_static/examples/md-settings.txt
   :language: rst
   :lines: 44-50

What we are essentially modifying here is
the frequency of the output, and we are also telling |pyretis|
not to back-up, but to **overwrite** old output files that might
be present in the same directory (this is controlled
by the ``backup = False`` keyword setting).

After running this example, the following files
should have been created:

* ``energy.txt``
    This file contains energies and temperature as a
    function of time/step in the MD simulation:

* ``thermo.txt``
    This file contains the same energies as ``energy.txt``
    and in addition the pressure.

* ``traj.xyz``
    This file contains the trajectory and can be visualised
    using for instance `VMD <http://www.ks.uiuc.edu/Research/vmd/>`_.

* ``pyretis.log``
    This file contains output messages from the |pyretis| application.

* ``out.rst``
    This file contains the input settings you provided as |pyretis|
    read them. This can be used to check the correctness of the
    input file.

Plotting the pressure from ``thermo.txt`` should then give
a figure similar to:

.. figure:: /_static/img/examples/md-energies.png
    :class: img-responsive center-block
    :alt: Pressure, obtained from the MD NVE simulation
    :width: 75%
    :align: center

    A representative output from the MD NVE simulation:
    The eneriges, pressure and the temperature as
    a function of the simulation step.


.. _examples-md-nve-lib:

Molecular dynamics using the |pyretis| library
----------------------------------------------
In this part of the example, we will make explicit use
of the |pyretis| library
If you want
to try this example, you will have to copy the code-snippets
given below into a Python script, say ``md.py``, and run it as

.. code-block:: pyretis

   python md.py

This example is best understood if you have read
about the :ref:`PyRETIS API <api-doc>`.

We begin the example by importing from the |pyretis| library:

.. literalinclude:: /_static/examples/md.py
   :language: python
   :lines: 9-16

We also import `Numpy <http://www.numpy.org/>`_
and `matplotlib <http://matplotlib.org/>`_ here in order
to do some plotting. If you want a more fancy plot and
have a recent version of matplotlib installed you can try
to use one of the many styles, e.g.:

.. literalinclude:: /_static/examples/md.py
   :language: python
   :lines: 22

Next, we create the initial positions and use this to set up
a simulation box:

.. literalinclude:: /_static/examples/md.py
   :language: python
   :lines: 25-30

We can use the lattice we generated to populate a system
with particles. The system contains information about the box,
the particles and the temperature:

.. literalinclude:: /_static/examples/md.py
   :language: python
   :lines: 33-43

In the last lines in the above code, we generated initial velocities,
from a Maxwellian distribution such that the total
momentum of the system is zero (requested by setting the
key ``'momentum'`` to ``True`` in the dictionary).

Now, we just have to set-up a force field:

.. literalinclude:: /_static/examples/md.py
   :language: python
   :lines: 45-50

select an engine and a simulation to run:

.. literalinclude:: /_static/examples/md.py
   :language: python
   :lines: 58-62

Now, we are ready to run the simulation and plot the energies
as a function of the simulation step:

.. literalinclude:: /_static/examples/md.py
   :language: python
   :lines: 68-78

This should result in a plot similar to:

.. figure:: /_static/img/examples/md-energies-2.png
    :class: img-responsive center-block
    :width: 60%
    :alt: Energies obtained from the MD simulation.
    :align: center

    Energies as a function of the time in the MD simulation.
