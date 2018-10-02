.. _examples-for-back-md:

Molecular dynamics in |pyretis| with C or FORTRAN
=================================================

In this example, we will implement a Lennard-Jones potential
in C or FORTRAN and use this to run a MD simulation with
|pyretis| for a simple system. The system we consider is a
Lennard-Jones mixture starting for a specific configuration as
shown below. After running for some steps (which melt the
initial configuration), we reverse the velocities and continue
the simulation.


.. figure:: /_static/examples/extending-example/potentialfb/config.png
    :alt: Initial configuration.
    :align: center
    :width: 90%

    Snapshots from the MD simulation. To the left, the initial (and
    final) configuration and to the right, the configuration after
    running 2000 steps, just before reversing the velocities. The
    system consist of two types of particles, labeled Ar (colored silver)
    and Kr (colored purple), which are initially arranged in a particular
    configuration.



.. contents::
   :local:

Creating a new potential in C or FORTRAN
----------------------------------------

In this example, we will create a new potential function to
use with |pyretis| in C or FORTRAN.

As discussed in the
:ref:`introduction to the library <user-guide-intro-api-forcefield>`,
we need to create a new potential class which |pyretis| will make use of.
This new potential class will import routines from a C or FORTRAN
library and use these routines to do the actual computation of the forces.

We will in the following show how this can be done, both with
FORTRAN and with C. Essentially, we are going to complete
the following steps:

1. We write the code responsible for the evaluation of the
   force in an external C or FORTRAN library.

2. We compile the external code. Here we do one of the following:

   * For C, we create a ``setup.py`` which is used to compile.

   * For FORTRAN, make use of a ``Makefile`` and the program
     `f2py <https://docs.scipy.org/doc/numpy/f2py/>`_.

3. We write a Python module containing a new :py:class:`.PotentialFunction` sub-class
   representing the new potential. This class imports the library
   which we created in steps 1 and 2.

Writing a new potential function with FORTRAN
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now create a potential function writing the external library in FORTRAN.
This is done in the following steps:

.. contents::
   :local:

Step 1. Creating the FORTRAN code
.................................

The FORTRAN code for evaluating the potential and forces is
relative simply and we assume that we are handed positions, velocities, and forces
as double precision arrays and that we can directly make use of them.

.. pyretis-collapse-block::
   :heading: Show/hide the FORTRAN-code for the potential function

   .. literalinclude:: /_static/examples/extending-example/potentialfb/ljfortran.f90
      :language: fortran

Step 2. Creating the Makefile and compiling
...........................................

In order to compile the FORTRAN code created in the previous step, we
make use of `f2py <https://docs.scipy.org/doc/numpy/f2py/>`_.

Note that in some systems you might actually need to use ``f2py3``
(or, for a specific version: ``f2py3.7`` etc.) if you have several
versions of Python installed on your system. This is to ensure that
the FORTRAN code is compiled with a version that matches the version of
Python you are using. You will then have to modify the ``F2PY = f2py``
setting in the Makefile.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the Makefile

   .. literalinclude:: /_static/examples/extending-example/potentialfb/Makefile
      :language: make

Note that the FORTRAN compiler is specified using ``--fcompiler=gfortran``
and other choices can be seen by running:

.. code-block:: pyretis

   f2py -c --help-fcompiler

Further, the Makefile assumes that the FORTRAN module is named
``ljfortran.f90``.

Step 3. Creating a new Python class for the potential function
..............................................................

For the Python class representing the potential function,
we import the module we just compiled and make use of the methods defined
in that module.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the new Python class

   .. literalinclude:: /_static/examples/extending-example/potentialfb/ljpotentialf.py
      :language: python


Writing a new potential function with C
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now create a new potential function by writing the external
library in C. This is done by the following steps:

.. contents::
   :local:

Step 1. Creating the C code
...........................

The C code is more involved, and perhaps cumbersome compared to the FORTRAN
code above. We are here explicitly assuming that our system is going to be 3D.

.. pyretis-collapse-block::
   :heading: Show/hide the C-code for the potential

   .. literalinclude:: /_static/examples/extending-example/potentialfb/ljc.c
      :language: c

As can be seen in the C-code, there is some boilerplate code and we
make use of
`PyArg_ParseTuple <https://docs.python.org/3/c-api/arg.html#c.PyArg_ParseTuple>`_ in
order to parse the parameters to the function.

Step 2. Creating a setup.py file and compiling
..............................................

The C-code can be compiled using a ``setup.py`` file.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the setup.py file

   .. literalinclude:: /_static/examples/extending-example/potentialfb/setup.py
      :language: python

The ``setup.py`` file is used to compile via the command

.. code-block:: pyretis

   python setup.py build_ext --inplace

Here, ``build_ext`` is used to tell ``setup.py`` to compile the C extension and
the ``--inplace`` will put the compiled extensions into the directory you
have the source code in.

Step 3. Creating a new Python class for the potential function
..............................................................

The final step is to create a Python class which is
making use of the C-code.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the new Python class

   .. literalinclude:: /_static/examples/extending-example/potentialfb/ljpotentialc.py
      :language: python

Running the MD simulation using the |pyretis| library
-----------------------------------------------------

Below we give a Python script which makes use of the |pyretis| library
to run a MD simulation of 2000 steps in the forward and backward directions.
It will generate a trajectory (named ``traj.xyz``) and display a plot of
the energies (an example is shown in the figure below).

Before running the script you will have to download the initial configuration
:download:`initial.gro </_static/examples/extending-example/potentialfb/initial.gro>`
and place it in the same directory as the script. Further, the script makes the
following assumptions:

* If you are using FORTRAN (that is if ``USE = fortran``) the script assumes
  that there is a folder named ``fortran`` which contains the compiled
  library and the Python script named ``ljpotentialf.py``.

* If you are using C (that is if ``USE = cpython3``) the script assumes
  that there is a folder named ``cpython3`` which contains the compiled
  library and the Python script named ``ljpotentialc.py``.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the Python MD script

   .. literalinclude:: /_static/examples/extending-example/potentialfb/md_forward_backward_ext.py
      :language: python

Copy this script and store it in a new Python file,
say ``md_forward_backward_py``. Before running the script, you will have to
set the ``USE`` variable in the script to
either ``USE = fortran`` or ``USE = cpython3`` to select the external
library to use. After this has been done, you can execute the script as
usual

.. code-block:: pyretis

   python md_forward_backward.py

This will run the simulation, and when it is done, it should display
a figure similar to the one given below. Further, you may wish to
inspect the generated trajectory ``traj.xyz`` visually.

.. figure:: /_static/examples/extending-example/potentialfb/energy.png
    :width: 90%
    :alt: Illustration of energies from the MD run.
    :align: center

    Energies obtained from the MD run. The velocities were reversed at
    step 2000.
