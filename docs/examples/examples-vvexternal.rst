.. _examples-vvexternal:

Using C or FORTRAN
==================

In this section, we will show some examples on how C or FORTRAN
can be used together with Python and |pyretis|:

.. contents::
   :local:

.. _examples-external-vvE:

Creating a new Molecular Dynamics engine with C or FORTRAN
----------------------------------------------------------

In this example, we will create a new molecular dynamics engine
using C or FORTRAN. As described in
the :ref:`user guide <user-guide-engine>`
we have to make a new class and implement a method which performs
an integration step. When we now make use of C or FORTRAN in a |pyretis| engine,
we essentially just call a method from an external library which we have
prepared ourselves (in C or FORTRAN).

In this part, we are here going to create such a library
and access it from a piece of Python code. We
are going to complete three steps:

1. We write the code responsible for the actual integration in an
   external library.

2. We compile the code. Here we do one of the following:

   * For C, we create a ``setup.py`` which is used to compile.

   * For FORTRAN, make use of a ``Makefile`` and the program
     `f2py <https://docs.scipy.org/doc/numpy/f2py/>`_.

3. We write a Python module containing a new :py:class:`.MDEngine` sub-class
   representing the new engine. This class makes use of the code
   which we created in steps 1 and 2.

Writing a new engine with FORTRAN
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now create a new engine by writing the external library in FORTRAN.
This is done in the following steps:

.. contents::
   :local:

Step 1. Creating the FORTRAN code
.................................

The FORTRAN code for creating the new integrator is relatively simple.
We can assume that we are handed positions, velocities, and forces
as double precision arrays and that we can directly make use of them.
Since we need to evaluate the forces during the Velocity Verlet integration,
the integration routine is split up in two steps (before/after the
evaluation of the forces). The responsibility for updating the
forces between these two steps is delegated to the
Python script which we will
:ref:`create below <examples-vvexternal-fortran-python>`.

.. pyretis-collapse-block::
   :heading: Show/hide the FORTRAN-code for the engine

   .. literalinclude:: /_static/examples/extending-example/engine/vvintegrator.f90
      :language: fortran

.. _examples-vvexternal-fortran-makefile:

Step 2. Creating the Makefile and compiling
...........................................

In order to compile the FORTRAN code created in the previous step, we
make use of `f2py <https://docs.scipy.org/doc/numpy/f2py/>`_.

Note that
in some cases you might actually need to use ``f2py3`` (or, for a specific version: ``f2py3.7`` etc.)
to compile the FORTRAN code so that it can be used with the version of Python you are using to run
this example. You will then have to modify the ``F2PY = f2py`` setting in the Makefile

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the Makefile

   .. literalinclude:: /_static/examples/extending-example/engine/Makefile
      :language: make

Note that the FORTRAN compiler is specified using ``--fcompiler=gfortran``
and other choices can be seen by running:

.. code-block:: pyretis

   f2py -c --help-fcompiler

Further, the Makefile assumes that the FORTRAN module is named
``vvintegrator.f90``.


.. _examples-vvexternal-fortran-python:

Step 3. Creating a new Python class for the engine
..................................................

For the Python class representing the engine, we just import the
module we just compiled and make use of the two methods defined within
that module. Note that we here make an explicit call to ``system.potential_and_force()``
so that forces are updated between the two "steps" of the Velocity Verlet integration.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the Python class

   .. literalinclude:: /_static/examples/extending-example/engine/vvintegratorf.py
      :language: python

You can now use the new integrator, for instance by adding the
following :ref:`engine section <user-section-engine>` to the input file:

.. code-block:: rst

   Engine
   ------
   class = VelocityVerletF
   delta_t = 0.002
   module = vvintegratorf.py


Writing a new engine with C
^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now create a new engine by writing the external library in C.
This is done in the following steps:

.. contents::
   :local:

.. _example-vvexternal-c-code:

Step 1. Creating the C code
...........................

The C code is more involved, and perhaps cumbersome compared to the FORTRAN
code above. We are here explicitly assuming that our system is going to be 3D
and we split the Velocity Verlet integration into two steps as in the
FORTRAN code.

.. pyretis-collapse-block::
   :heading: Show/hide the C-code for the engine

   .. literalinclude:: /_static/examples/extending-example/engine/vvintegrator.c
      :language: c

As can be seen in the C-code, there is some boilerplate code and we
make use of
`PyArg_ParseTuple <https://docs.python.org/3/c-api/arg.html#c.PyArg_ParseTuple>`_ in
order to parse the parameters to the function.

.. _examples-vvexternal-c-compile:

Step 2. Creating a setup.py file and compiling
..............................................

The C-code can be compiled using a ``setup.py`` file.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the setup.py file

   .. literalinclude:: /_static/examples/extending-example/engine/setup.py
      :language: python

The ``setup.py`` file is used to compile via the command

.. code-block:: pyretis

   python setup.py build_ext --inplace

Here, ``build_ext`` is used to tell ``setup.py`` to compile the C extension and
the ``--inplace`` will put the compiled extensions into the directory you
have the source code in.

Step 3. Creating a new Python class for the engine
..................................................

The final step is to create a Python class which is
making use of the C-code.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the new Python class

   .. literalinclude:: /_static/examples/extending-example/engine/vvintegratorc.py
      :language: python

You can now use the new integrator, for instance by adding the
following :ref:`engine section <user-section-engine>` to the input file:

.. code-block:: rst

   Engine
   ------
   class = VelocityVerletC
   delta_t = 0.002
   module = vvintegratorc.py


Comparison of the FORTRAN and C code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As you may have noticed, the FORTRAN code we have added
is somewhat more to the point compared to the C-code we wrote.
The C-code could, for instance, be simplified by making use
of `Cython <http://cython.org/>`_, and you are encouraged to
try this out.

The two Python classes we created are very similar. This means
that it is relatively little work to switch between the two
libraries from Python's point of view. This is also evident in the
``diff`` of the two modules shown below.

.. pyretis-collapse-block::
   :heading: Show/hide the diff of the two Python classes

   .. literalinclude:: /_static/examples/extending-example/engine/vvintegratorc.py
      :diff: /_static/examples/extending-example/engine/vvintegratorf.py

.. _examples-external-ff:

Creating a force field with C or FORTRAN
----------------------------------------

Evaluation of the forces will typically be the most time-consuming part
of your simulation. If you are running |pyretis| with internal engines, there
can be a lot to gain by implementing the force evaluation in C or FORTRAN.
In this section, we will give a short example of how this can be done.
The approach is similar to the :ref:`approach for the engine <examples-external-vvE>`,
and we will do the following:

1. We write the code responsible for the actual evaluation of forces in an
   external library.

2. We compile the code. Here we do one of the following:

   * For C, we create a ``setup.py`` which is used to compile.

   * For FORTRAN, make use of a ``Makefile`` and the program
     `f2py <https://docs.scipy.org/doc/numpy/f2py/>`_.

3. We write a python module containing a new :py:class:`.PotentialFunction` sub-class
   representing the new engine. This class makes use of the code
   which we created in steps 1 and 2.

As you may have noticed, in step 3 above, we said that we will sub-class
:py:class:`.PotentialFunction`. This is because a force field is made up
of several potential functions, and the actual computations are carried out
by the potential functions, and not the force field. So effectively, we will
be creating new potential functions to use in a force field.
To be concrete, we will implement the **Lennard-Jones** potential function.


.. _examples-ljexternal-fortran:

Writing a new potential with FORTRAN
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now create a new potential function by writing the external library in FORTRAN.
This is done in the following steps:

.. contents::
   :local:

Step 1. Creating the FORTRAN code
.................................

For the new potential function, we add methods for calculating
the potential and the force. In addition, we calculate the virial.
Note: Here we also add a method to apply the periodic boundaries. Ideally, we
should use the :py:class:`.Box` object, but in order to not complicate the
FORTRAN code, by calling methods from the Python class, we simply make a new
FORTRAN method to do this.

.. pyretis-collapse-block::
   :heading: Show/hide the FORTRAN-code for the potential

   .. literalinclude:: /_static/examples/extending-example/potential/ljfortranp.f90
      :language: fortran


Step 2. Creating the Makefile and compiling
...........................................
The step is almost identical to the
:ref:`compilation for the external engine <examples-vvexternal-fortran-makefile>`.
The Makefile is given below, and note here that we are assuming that the FORTRAN code
is stored in a module named ``ljfortranp.f90``.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the Makefile

   .. literalinclude:: /_static/examples/extending-example/potential/Makefile
      :language: make

Step 3. Creating a new Python class for the potential
.....................................................

For the Python class representing the potential, we just
import the module we compiled in the previous step.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the new Python class

   .. literalinclude:: /_static/examples/extending-example/potential/ljpotentialfp.py
      :language: python

You can now use the new potential, for instance by adding the
following :ref:`forcefield<user-section-forcefield>`
and :ref:`potential <user-section-potential>` sections
to the input file:

.. code-block:: rst

   Forcefield
   ----------
   description = Lennard-Jones evaluated in FORTRAN

   Potential
   ---------
   class = PairLennardJonesCutFp
   module = ljpotentialfp.py
   shift = True
   dim = 3
   mixing = geometric
   parameter 0 = {'sigma': 1, 'epsilon': 1, 'factor': 2.5}

.. _examples-ljexternal-c:

Writing a new potential with C
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now create a new potential function by writing the external library in C.
This is done in the following steps:

.. contents::
   :local:

Step 1. Creating the C-code
...........................

We set up the C-code as in the :ref:`engine example <example-vvexternal-c-code>`.

.. pyretis-collapse-block::
   :heading: Show/hide the C-code for the potential

   .. literalinclude:: /_static/examples/extending-example/potential/ljc.c
      :language: c

Step 2. Creating a setup.py file and compiling
..............................................

In order to compile the C-code we just created, we make use of a ``setup.py`` file
which is almost identical to the :ref:`one we created for the engine <examples-vvexternal-c-compile>`.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the setup.py file

   .. literalinclude:: /_static/examples/extending-example/potential/setup.py
      :language: python

As before, the ``setup.py`` file is used to compile via the command

.. code-block:: pyretis

   python setup.py build_ext --inplace

Note that we assume that the C-code is stored in a file named ``ljc.c``.

Step 3. Creating a new Python class for the potential
.....................................................


The final step is to create a Python class which is
making use of the C-code.

.. pyretis-collapse-block::
   :heading: Show/hide the contents of the new Python class

   .. literalinclude:: /_static/examples/extending-example/potential/ljpotentialc.py
      :language: python


You can now use the new potential, for instance by adding the
following :ref:`forcefield<user-section-forcefield>`
and :ref:`potential <user-section-potential>` sections
to the input file:

.. code-block:: rst

   Forcefield settings
   --------------------
   description = Lennard-Jones evaluated in C

   Potential
   ---------
   class = PairLennardJonesCutC
   module = ljpotentialc.py
   shift = True
   dim = 3
   mixing = geometric
   parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}


Again, we note that the two Python classes we created (for FORTRAN and C) are very similar.
The  ``diff`` of the two modules shown below.

.. pyretis-collapse-block::
   :heading: Show/hide the diff of the two Python classes

   .. literalinclude:: /_static/examples/extending-example/potential/ljpotentialc.py
      :diff: /_static/examples/extending-example/potential/ljpotentialfp.py

Comparison of the C, FORTRAN and a Numpy implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the figure below, we show some sample timings using the modules you have just created
two Python implementations (one is in pure Python, while the other is using Numpy).

.. figure:: /_static/img/examples/ext-compare.png
    :class: img-responsive center-block
    :alt: Timings for C, FORTRAN and PYTHON
    :width: 80%
    :align: center

    Sample timing results when using the external modules written in C and
    FORTRAN compared with Python implementations.

OpenMP: Parallel evaluation of the force
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In both the :ref:`C module <examples-ljexternal-c>` and the
:ref:`FORTRAN module <examples-ljexternal-fortran>`, we created
for evaluation of the force, it is possible to speed up the force evaluation
by, for instance, making use of `OpenMP <http://www.openmp.org/>`_ directives. We just
give a very brief example below, and leave the rest to you.

.. figure:: /_static/img/examples/potential-omp.png
    :class: img-responsive center-block
    :alt: Speed-up using OpenMP
    :width: 80%
    :align: center

    Sample results using OpenMP while calculating the Lennard-Jones
    potential energy. The left figure shows the actual time used
    (average over 5 independent runs), while the right figure shows
    the time used relative to each other.


.. pyretis-collapse-block::
   :heading: Show/hide a short OpenMP aware FORTRAN example

    .. literalinclude:: /_static/examples/extending-example/potential/ljfortranpomp.f90
       :language: fortran

Note that you will have to modify the flags in your Makefile accordingly, for instance, setting:

.. code-block:: make

   F2PY_FLAGS = --fcompiler=gfortran --f90flags='-fopenmp' -lgomp
