.. _user-guide-input:

Running pyretis with input files
================================

pyretis simulations can be set up and run with a simple input file.
This input file defines a simulation by setting
:ref:`keywords <user-keywords>`
explicitly, while all undefined keywords will be
given :ref:`default <input-default>` values.

After the input script has been created, a pyretis simulation can
be evoked by running

.. code-block:: bash

    $ pyretisrun -i <input>


Which will run your simulation, create the requested output and
write a simulation log both to the screen and to a file ``pyretis.log``.

Structure of the input file
---------------------------

The input file consist of keywords with corredponding values.
The syntax for setting keywords is ``keyword = setting``,
for example:

.. code-block:: python

   task = md-nve

   integrator = {'class': 'velocityverlet', 'timestep': 0.002}


Other than keywords, the format of the input file is relatively free.
You can for instance order things as you prefer and the input
is in general case insensitive:

.. code-block:: python

    task = md-nve
    units = lj
    # is identical to:
    UNITS = lj
    tAsK = md-nve

There are some important exceptions to the case sensitiveness: When
referring to files and python class names case will in general matter!

You can also add other text and comments to structure the input file:

.. code-block:: python

    Simulation settings
    -------------------
    task = md-nve
    units = lj

    # More settings:
    System settings
    ---------------
    temperature = 1.0


The most important input settings
---------------------------------

This is a short list of the most important settings. For the
complete list, please consult the section listing 
:ref:`all keywords <user-keywords>` which also gives a more complete
description of the usage of the keywords with several examples.

* units
    Specify the units to use.

    Examples:

    .. code-block:: python

        units = lj  # Select Lennard-Jones units

* task
    Specify the kind of simulation to run.

    Example:

    .. code-block:: python

        task = md-nve

    Note that the different tasks require setting of different keywords as
    described in the detailed description of
    the :ref:`task keyword <user-keywords-task>`.

* integrator
    Specify which integrator we should use and sets parameters for the
    integrator.

    Example:

    .. code-block:: python

        integrator = {'class': 'Langevin',
                      'timestep': 0.002,
                      'gamma': 0.3,
                      'seed': 0,
                      'high-friction': False}

.. _user-keywords:

All pyretis keywords
--------------------

The pyretis keywords are:

* :ref:`box <user-keywords-box>`: for setting up the simulation box
* :ref:`integrator <user-keywords-integrator>`: for selecting the integration routine
* :ref:`orderparameter <user-keywords-task>`: for selecting the order parameter
* :ref:`particles-position <user-keywords-particles-position>`: for setting the initial particle positions
* :ref:`particles-velocity <user-keywords-particles-velocity>`: for setting the initial particle velocities
* :ref:`particles-mass <user-keywords-particles-mass>`: for setting the masses of the particles
* :ref:`particles-name <user-keywords-particles-name>`: for setting the names of the particles
* :ref:`particles-type <user-keywords-particles-type>`: for setting the types of the particles
* :ref:`task <user-keywords-task>`: for selecting what kind of simulation to run
* :ref:`units <user-keywords-units>`: for selecting units to use for input/output

.. _input-default:

Default settings
----------------

In case a keyword is not specified and the selected task requires the use
of that keyword, a default value is used. These default settings
are as follows:

* units
    The default system of units is ``lj``:

    .. code-block:: python

        units = lj

