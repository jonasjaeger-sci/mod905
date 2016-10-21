.. _user-guide-input:

The pyretis input file
======================

pyretis simulations can be set up and run with a simple input file.
The input file defines a simulation by setting values for
:ref:`keywords <user-keywords>` which are organized into
:ref:`sections <user-section>`. All keywords/sections that are not
explicitly set will assume :ref:`default <input-default>`
values. 

After the input script has been created, a pyretis simulation can
be evoked by running the ``pyretisrun`` application, 

.. code-block:: bash

    $ pyretisrun -i <input>

Here, we will discuss
the :ref:`structure of the input file <user-guide-input-structure>`
and some of the :ref:`sections <user-guide-input-sections>`
the input file is organized into. We refer to the
:ref:`pyretisrun documentation <user-guide-application>`.
for more information about the usage of the ``pyretisrun`` application.


.. _user-guide-input-structure:

Structure of the input file
---------------------------

The input file is organized into **sections** and for each
section, **keywords** are used to define your settings.
The syntax for setting keywords is ``keyword = setting``,
and sections are marked by the section title followed by a
underline of dashes ``--------``, for example:

.. code-block:: rst

    Simulation settings
    -------------------
    task = md-nve
    steps = 100


which sets the two keywords ``task`` and ``steps`` for the
``Simulation`` section. When specifying a section, only the
first word in the section title is used to
identify the title internally in pyretis. This means that you can
just as well write the following:

.. code-block:: rst

    Simulation 
    ----------
    task = md-nve
    steps = 100

or add any text you like, e.g.: 

.. code-block:: rst

    Simulation master plan
    ----------------------
    task = md-nve
    steps = 100

Both this two examples with define keywords for the ``Simulation`` section.


The format of the input file is relatively free,
you can for instance order things within sections as
you prefer and the input is in general **case insensitive**:

.. code-block:: rst

    Simulation settings
    -------------------
    task = md-nve
    units = lj
    
which is identical to:

.. code-block:: rst

    Simulation settings
    -------------------
    UNITS = lj
    tAsK = md-nve

Note that the values set by the keywords might be
**case sensitive**. Some examples:

- When using external python modules and classes, for instance:

  .. code-block:: rst

      Integrator settings
      -------------------
      class = MyExternalClass
      module = filename.py

  Here, the values given for the ``class`` and the ``module`` keywords are
  **case sensitive**. 

- When referring to external files, for instance:
   
  .. code-block:: rst

      Particles settings
      ------------------
      position = {'file': 'myfile.gro'}

  Here, we are referring to a file named ``myfile.gro``,
  and pyretis will expect this file to be present with exactly
  this file name.     

- When defining your own system of units:

  .. code-block:: rst

      Unit-system
      -----------
      length = (1.0, 'm')

  Here, we are using a unit of 1 metre which is identified with
  a ``'m'`` and not a ``'M'``.

You can also add text and comments to structure the input file:

.. code-block:: rst

    Simulation settings
    -------------------
    task = md-nve
    units = lj

    # More settings:

    System settings
    ---------------
    temperature = 1.0

Comments are marked as starting with a ``'#'`` and all following text
will be ignored, i.e.

.. code-block:: rst

    task = md-nve  # set up and run a md-nve simulation not TIS this time.

is effectively the same as writing, 

.. code-block:: rst

    task = md-nve

Summarized:

* The input file is organized into ``sections`` where ``keywords`` are set:

   .. code-block:: rst

       SectionTitle
       ------------
       keyword = value

* Comments are marked with a ``#``.

* Input is in general not case sensitive unless you are referring to
  files and python classes.

.. _user-guide-input-sections:

The sections in the input file
------------------------------

The pyretis input file is structured with sections. The most
commonly used sections are:

* :ref:`Simulation <user-section-simulation>`:
  The simulation section defines what kind of simulation we
  are to perform.

  .. code-block:: rst

      Simulation 
      ----------
      task = md-nve
      steps = 100

* :ref:`System <user-section-system>`:
  The system section defins the simulation system.
  This can for instance define the ``units``
  to use or set a
  target ``temperature`` for the system:

  .. code-block:: rst 
    
      System settings
      ---------------
      units = real
      temperature = 300.0

* :ref:`Particles <user-section-particles>`:
  The particles section is used to define the
  initial state of the system, for instance by reading it from
  a file.

  .. code-block:: rst 
    
      Particles settings
      ------------------
      position = {'file': 'configtag.xyz'}

* :ref:`Force field <user-section-forcefield>`:
  The force field is defined by the force field section and one or more
  potential sections.

  .. code-block:: rst 

      Forcefield settings
      -------------------
      description = Lennard Jones test

      potential
      ---------
      class = PairLennardJonesCutnp
      shift = True
      parameter 0 = {'sigma': 1.0, 'epsilon': 1.0, 'rcut': 2.5}

      potential
      ---------
      class = DoubleWellWCA
      parameter types = [(0, 0)]
      parameter rzero = 1.122462048309373
      parameter height = 6.0
      parameter width = 0.25

* :ref:`Order parameter <user-section-orderparameter>`:
  Defines the order parameter to use.

  .. code-block:: rst 

      Orderparameter
      --------------
      class = OrderParameterPosition
      name = Position
      index = 0
      dim = x
      periodic = False

* :ref:`Integrator <user-section-integrator>`:
  Selects the integrator to use

  .. code-block:: rst 
 
      Integrator settings
      -------------------
      class = VelocityVerlet
      timestep = 0.002

For a complete description of all sections, please see
this :ref:`overview <user-section>`.

.. _input-default:

Default settings
----------------

In case a keyword is not specified and the selected task requires the use
of that keyword, a default value is used. These default settings
are as follows:
