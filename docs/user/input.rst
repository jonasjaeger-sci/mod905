.. _user-guide-input:

Running pyretis with input files
================================

pyretis simulations can be set up and run with a simple input file.
This input file defines a simulation by setting values for
:ref:`keywords <user-keywords>`. All keywords that are not set
will assume :ref:`default <input-default>` values if such exist. 

After the input script has been created, a pyretis simulation can
be evoked by running

.. code-block:: bash

    $ pyretisrun -i <input>


Which will run your simulation and create the different 
output file(s). For the full description of the usage
of the ``pyretisrun`` application, please see the
:ref:`pyretisrun documentation <user-guide-application>`.
Here, we will discuss
the :ref:`structure of the input file <user-guide-input-structure>`
and some of the :ref:`sections <user-guide-input-sections>`
the input file is organized into.

.. _user-guide-input-structure:

Structure of the input file
---------------------------

The structure of the input file can be summarized in three points:

1. The input file is organized into **sections** and for each
   section, **keywords** are used to define your settings.
   The syntax for setting keywords is ``keyword = setting``,
   and sections are marked by the section title followed by a
   underline of dashes ``--------``, for example:

   .. code-block:: rst

       Simulation settings
       -------------------
       task = md-nve
       steps = 100

   
   which sets the two keywords ``task`` and ``steps``. When specifying
   a section, only the first word in the section title is used to
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


2. The format of the input file is relatively free,
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

     Here, both the ``class`` keyword and the ``module`` keyword will be interpreted

   - When referring to external files, for instance:
      
     .. code-block:: rst

         Particles settings
         ------------------
         position = {'file': 'myfile.gro'}

     Here, we are referring to a file named ``myfile.gro``,
     and pyretis will expect this file to be present with exactly
     this file name.     


3. You can also add text and comments to structure the input file:

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



.. _user-guide-input-sections:

The sections in the input file
------------------------------

The pyretis input file is structured with sections. The most
commonly used sections are:

* :ref:`Simulation <user-guide-input-sec-simulation>`

* :ref:`System <user-guide-input-sec-system>`

* :ref:`Particles <user-guide-input-sec-particles>`

* :ref:`Force field <user-guide-input-sec-force>`

* :ref:`Order parameter <user-guide-input-sec-orderparameter>`

* :ref:`Integrator <user-guide-input-sec-integrator>`

For a complete description of all sections, please see
this :ref:`overview <user-section>`.

.. _user-guide-input-sec-simulation:

The simulation section
~~~~~~~~~~~~~~~~~~~~~~

The simulation section defines what kind of simulation we
are to perform.

Example

.. code-block:: rst

     task = md-nve
     steps = 100

For more information on possible keywords for this section,
see the :ref:`simulation section description <user-section-simulation>`


.. _user-guide-input-sec-system:

The system section
~~~~~~~~~~~~~~~~~~

The system section defins the simulation system.
This can for instance define the ``units``
to use or set a
target ``temperature`` for the system:

.. code-block:: rst 
    
    System settings
    ---------------
    units = real
    temperature = 300.0

For more information on the possible system of units
please see the :ref:`reference section on units <user-guide-units>`.

.. _user-guide-input-sec-particles:

The particles section
~~~~~~~~~~~~~~~~~~~~~

The particles section is used to define the
initial state of the system, for instance by reading it from
a file.

Example:

.. code-block:: rst 
    
    Particles settings
    ------------------
    position = {'file': 'configtag.xyz'}

At the same time, initial veocities, masses for the particles, lables and
types can be specified, please see the full information
in the :ref:`particles section description <user-section-particles>`

.. _user-guide-input-sec-integrator:

The integrator section
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst 

    Integrator settings
    -------------------
    class =  Langevin
    timestep = 0.002
    gamma = 0.3
    seed = 0
    high_friction = False

Note that the different integrators have different keywords that
needs to be defined. See the detailed description of the 
:ref:`integrator section <user-section-integrator>`

.. _user-guide-input-sec-force:

Settings defining the force field
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The force field is defined by the force field section and one or more
potential sections.

Example

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

.. _user-guide-input-sec-orderparameter:

The order parameter section
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst 

    Orderparameter
    --------------
    class = OrderParameterPosition
    name = Position
    index = 0
    dim = x
    periodic = False


.. _input-default:

Default settings
----------------

In case a keyword is not specified and the selected task requires the use
of that keyword, a default value is used. These default settings
are as follows:
