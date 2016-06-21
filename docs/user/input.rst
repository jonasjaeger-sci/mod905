.. _user-guide-input:

Running pyretis with input files
================================

pyretis simulations can be set up and run with a simple input file.
This input file defines a simulation by setting values for
:ref:`keywords <user-keywords>`. All keywords that are not set
will assume :ref:`default <input-default>` values.

After the input script has been created, a pyretis simulation can
be evoked by running

.. code-block:: bash

    $ pyretisrun -i <input>


Which will run your simulation and create the different 
output file(s). For the full description of the usage
of the ``pyretisrun`` application, please see the
:ref:`pyretisrun documentation <user-guide-application>`.
Here, we will discuss
the :ref:`structure of the input file <user-guide-input-structure>` and
some of the most :ref:`common input settings <user-guide-input-commonkey>`
for :ref:`defining the system <user-guide-input-commonsys>`,
:ref:`force field <user-guide-input-commonforce>`,
:ref:`simulation <user-guide-input-commonsim>`
and :ref:`output <user-guide-input-commonout>`.

.. _user-guide-input-structure:

Structure of the input file
---------------------------

The structure of the input file can be summarized in three points:

1. The input file consist of keywords with corredponding values.
   The syntax for setting keywords is ``keyword = setting``,
   for example:

   .. code-block:: python

      task = md-nve
      integrator = {'class': 'velocityverlet', 'timestep': 0.002}

   which  sets the two keywords :ref:`task <user-keywords-task>` and
   :ref:`integrator <user-keywords-integrator>`.

2. The format of the input file is relatively free,
   you can for instance order things as you prefer and the input
   is in general **case insensitive**:

   .. code-block:: python

       task = md-nve
       units = lj
       
   which is identical to:

   .. code-block:: python

       UNITS = lj
       tAsK = md-nve

   Note that there are two important exceptions where the setting is
   in fact **case sensitive**: when referring to files or python class names!

3. You can also add text and comments to structure the input file:

   .. code-block:: python

       Simulation settings
       -------------------
       task = md-nve
       units = lj

       # More settings:

       System settings
       ---------------
       temperature = 1.0

   Comments are marked as starting with a ``'#'`` and all following text
   will be ignored. This means that the setting:

   .. code-block:: python

       task = md-nve

   is interpreted identical to the following:

   .. code-block:: python

       task = md-nve  # set up and run a md-nve simulation not TIS this time.


.. _user-guide-input-commonkey:

Some common pyretis keywords
----------------------------

We give below an overview of the most common keywords used for defining
rare event simulations for pyretis. For convenience we have grouped
these settings into categories:

* :ref:`Keywords defining the system <user-guide-input-commonsys>`

* :ref:`Keywords defining the force field <user-guide-input-commonforce>`

* :ref:`Keywords defining the output <user-guide-input-commonout>`

* :ref:`Keywords defining the simulation <user-guide-input-commonsim>`

For a complete description of all pyretis settings,
please see the :ref:`keyword reference section <user-keywords>`.


.. _user-guide-input-commonsys:

Settings defining the system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


* :ref:`units <user-keywords-units>`:
    Specify a system of units to use for the simulation and the
    input file. The possible system of units are described
    in detail in the :ref:`reference section on units <user-guide-units>`.

    Examples:

    .. code-block:: python

        units = lj  # Select Lennard-Jones units


.. _user-guide-input-commonsim:

Settings defining the simulations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
                      'high_friction': False}


.. _user-guide-input-commonforce:

Settings defining the force field
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test here.

.. _user-guide-input-commonout:

Settings defining the output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test here.

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
