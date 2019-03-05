.. _user-section-simulation:

The simulation section
======================

The ``simulation`` section defines and selects the simulation |pyretis| will run.

.. pyretis-input-example:: Simulation

   .. code-block:: rst

       Simulation
       ----------
       task = retis
       steps = 20000
       interfaces = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]

For this section, the keyword ``task`` specifies
the type of simulation to run and this will
also determine the keyword that can be set in
this section. Further, a specific task might also require
*additional sections* to be defined
as detailed in the table below:

.. table:: Possible values for the task keyword
   :class: table-striped table-hover

   +-------------+-------------------------------+----------------------------+-------------------+
   |   Task      | Description                   | Keywords                   | Required sections |
   +=============+===============================+============================+===================+
   |  ``retis``  | A replica exchange transition | ``task``, ``steps``,       | ``tis``,          |
   |             | interface sampling            | ``interfaces``             | ``retis``         |
   |             | simulation.                   |                            |                   |
   +-------------+-------------------------------+----------------------------+-------------------+
   |   ``tis``   | A transition interface        | ``task``, ``steps``,       |                   |
   |             | sampling simulation.          | ``interfaces``,            | ``tis``           |
   |             |                               | ``ensemble``, ``detect``   |                   |
   +-------------+-------------------------------+----------------------------+-------------------+
   | ``md-flux`` | A MD FLUX simulation.         | ``task``, ``steps``,       |                   |
   |             |                               | ``interfaces``             |                   |
   +-------------+-------------------------------+----------------------------+-------------------+
   | ``md-nve``  | A MD NVE simulation.          | ``task``, ``steps``        |                   |
   +-------------+-------------------------------+----------------------------+-------------------+


Since the different tasks may require different keywords, these are described below
individually. In addition, there are some settings which typically are
used in relation to the analysis, or when extending simulations. These are
described in the section on :ref:`common keywords <user-section-simulation-common>`.

.. contents::
   :local:


.. _user-section-simulation-retis:

The retis task
--------------

The ``retis`` task defines a replica exchange transition
interface sampling simulation.

.. pyretis-input-example:: Simulation
   :class-name: task retis

   .. code-block:: rst

       Simulation
       ----------
       task = retis
       steps = 20000
       interfaces = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]

Keywords for the retis task
^^^^^^^^^^^^^^^^^^^^^^^^^^^

For the ``retis`` task, the following keywords can be set:

.. |simretis_steps| replace:: :ref:`steps <user-section-task-retis-steps>`
.. |simretis_interfaces| replace:: :ref:`interfaces <user-section-task-retis-interfaces>`

.. _table-simulation-retis-keywords:

.. table:: Keywords for the retis task.
   :class: table-striped table-hover

   +-----------------------+--------------------------------------------------+
   | Keyword               | Description                                      |
   +=======================+==================================================+
   | |simretis_steps|      | The number of retis steps to perform.            |
   +-----------------------+--------------------------------------------------+
   | |simretis_interfaces| | The location of the interfaces to consider.      |
   +-----------------------+--------------------------------------------------+


In addition, this task requires that the
sections :ref:`TIS <user-section-tis>` and
:ref:`RETIS <user-section-retis>` are defined.

.. _user-section-task-retis-steps:

Keyword steps
.............

.. pyretis-keyword:: steps integer

   The ``steps`` keyword defines the number of RETIS cycles to perform.

   Default
     Not any, this keyword must be specified.

.. _user-section-task-retis-interfaces:

Keyword interfaces
..................

.. pyretis-keyword:: interfaces list of floats

   The ``interfaces`` keyword specifies the interfaces to use in the
   path simulation.

   Default
     Not any, this keyword must be specified.


.. _user-section-simulation-tis:

The tis task
------------

The ``tis`` task defines a transition interface sampling
simulation.

.. pyretis-input-example:: Simulation
   :class-name: task tis (multiple path ensembles)

   .. code-block:: rst

       Simulation
       ----------
       task = tis
       steps = 20000
       interfaces = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]

.. pyretis-input-example:: Simulation
   :class-name: task tis (a single path ensemble)

   .. code-block:: rst

       Simulation
       ----------
       task = tis
       steps = 20000
       interfaces = [-0.9, -0.9, 1.0]
       detect = -0.8
       ensemble = 1

Keywords for the tis task
^^^^^^^^^^^^^^^^^^^^^^^^^

For the ``tis`` task, the following keywords can be set:

.. |simtis_steps| replace:: :ref:`steps <user-section-task-tis-steps>`
.. |simtis_interfaces| replace:: :ref:`interfaces <user-section-task-tis-interfaces>`
.. |simtis_ensemble| replace:: :ref:`ensemble <user-section-task-tis-ensemble>`
.. |simtis_detect| replace:: :ref:`detect <user-section-task-tis-detect>`

.. _table-simulation-tis-keywords:

.. table:: Keywords for the tis task.
   :class: table-striped table-hover

   +---------------------+----------------------------------------------------+
   | Keyword             | Description                                        |
   +=====================+====================================================+
   | |simtis_steps|      | The number of steps to perform.                    |
   +---------------------+----------------------------------------------------+
   | |simtis_interfaces| | The interfaces defining the TIS ensemble.          |
   +---------------------+----------------------------------------------------+
   | |simtis_ensemble|   | For defining the ensemble considered.              |
   +---------------------+----------------------------------------------------+
   | |simtis_detect|     | The interface used for detecting successful paths. |
   +---------------------+----------------------------------------------------+

In addition, this task requires that the
section :ref:`TIS <user-section-tis>` is defined.

.. _user-section-task-tis-steps:

Keyword steps
.............

.. pyretis-keyword:: steps integer

   The ``steps`` keyword defines the number of TIS cycles to perform.

   Default
     Not any, this keyword must be specified.

.. _user-section-task-tis-interfaces:

Keyword interfaces
..................

.. pyretis-keyword:: interfaces list of floats

   The ``interfaces`` keyword specifies the interfaces to use in the
   path simulation. If the number of interfaces given is 3 or less,
   a single TIS simulation will be performed, otherwise, input files
   for several single TIS simulations will be written.
   These simulations can then be run manually.

   Default
     Not any, this keyword must be specified.

.. _user-section-task-tis-ensemble:

Keyword ensemble
................

.. pyretis-keyword:: ensemble integer

   A number specifying the path ensemble we are simulating, ``ensemble = 1``
   corresponds to ``[0^+]``, 1 to ``[1^+]`` and so on. This is only needed for
   running a single TIS simulation.

   Default
     Not any, this keyword must be specified.

.. _user-section-task-tis-detect:

Keyword detect
..............

.. pyretis-keyword:: detect float

   A number specifying the interface used for detecting successful
   paths. This is only needed for a single TIS simulation.

   Default
     Not any, this keyword must be specified.


.. _user-section-simulation-mdflux:

The md-flux task
----------------

The ``md-flux`` task is a molecular dynamics simulation for
determining the initial flux for a TIS path simulation.

.. pyretis-input-example:: Simulation
   :class-name: task md-flux

   .. code-block:: rst

       Simulation
       ----------
       task = md-flux
       steps = 10000000
       interfaces = [-0.9]

Keywords for the md-flux task
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For the ``md-flux`` task, the following keywords can be specified:

.. |simmdflux_steps| replace:: :ref:`steps <user-section-task-mdflux-steps>`
.. |simmdflux_interfaces| replace:: :ref:`interfaces <user-section-task-mdflux-interfaces>`

.. _table-simulation-mdflux-keywords:

.. table:: Keywords for the md-flux task
   :class: table-striped table-hover

   +------------------------+-------------------------------------------------+
   | Keyword                | Description                                     |
   +========================+=================================================+
   | |simmdflux_steps|      | Defines the number of steps to carry out.       |
   +------------------------+-------------------------------------------------+
   | |simmdflux_interfaces| | Defines the interfaces to consider for the      |
   |                        | flux simulation.                                |
   +------------------------+-------------------------------------------------+


.. _user-section-task-mdflux-steps:

Keyword steps
.............

.. pyretis-keyword:: steps integer

   The ``steps`` keyword specifies the number of MD steps to perform.

   Default
      Not any, this keyword must be specified.

.. _user-section-task-mdflux-interfaces:

Keyword interfaces
..................

.. pyretis-keyword:: interfaces list of floats

   The ``interfaces`` keyword specifies for which interfaces the
   initial flux should be obtained. This can be given as a list
   of floats.

   Default
      Not any, this keyword must be specified.


The md-nve task
---------------

The ``md-nve`` task is a NVE molecular dynamics simulation.

.. pyretis-input-example:: Simulation
   :class-name: task md-nve

   .. code-block:: rst

       Simulation
       ----------
       task = md-nve
       steps = 10000000

Keywords for the md-nve task
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following keywords can be specified for the ``md-nve`` task:

.. |simmdnve_steps| replace:: :ref:`steps <user-section-task-mdnve-steps>`

.. _table-simulation-mdnve-keywords:

.. table:: Keywords for the md-nve task
   :class: table-striped table-hover

   +------------------+-------------------------------------------------------+
   | Keyword          | Description                                           |
   +==================+=======================================================+
   | |simmdnve_steps| | The number of steps to consider for the simulation.   |
   +------------------+-------------------------------------------------------+


.. _user-section-task-mdnve-steps:

Keyword steps
.............

.. pyretis-keyword:: steps integer

   The ``steps`` keyword specifies the number of MD steps to perform.

   Default
      Not any, this keyword must be specified.


.. _user-section-simulation-common:

Common keywords
---------------

The following keywords are common to all simulation tasks:

.. |endcycle| replace:: :ref:`endcycle <user-section-simulation-endcycle>`
.. |startcycle| replace:: :ref:`startcycle <user-section-simulation-startcycle>`
.. |exepath| replace:: :ref:`exe-path <user-section-simulation-exe-path>`
.. |restart| replace:: :ref:`restart <user-section-simulation-restart>`

.. _table-simulation-common-keywords:

.. table:: Common keywords
   :class: table-striped table-hover

   +------------------------+-------------------------------------------------+
   | Keyword                | Description                                     |
   +========================+=================================================+
   | |endcycle|             | Specifies the cycle step the simulation ended.  |
   +------------------------+-------------------------------------------------+
   | |exepath|              | Specifies the directory from where the          |
   |                        | simulation was executed.                        |
   +------------------------+-------------------------------------------------+
   | |restart|              | Specifies the restart file to use, and          |
   |                        | specifies that a restart should be done.        |
   +------------------------+-------------------------------------------------+
   | |startcycle|           | Specifies the cycle step the simulation should  |
   |                        | start at.                                       |
   +------------------------+-------------------------------------------------+


.. _user-section-simulation-endcycle:

Keyword endcycle
^^^^^^^^^^^^^^^^

.. pyretis-keyword:: endcycle integer

   The ``endcycle`` keyword specifies the cycle number at which the
   simulation ended. If the simulation was stopped before the specified
   number of steps were reached, the ``endcycle`` will be difference
   from the ``steps`` keyword. This keyword will be set and updated
   by |pyretis| and written to the processed input file.

   Default
      Not any, note that this keyword will be updated and modified by
      |pyretis| as part of the output process. This keyword is **only**
      used by the analysis program.


.. _user-section-simulation-exe-path:

Keyword exe-path
^^^^^^^^^^^^^^^^

.. pyretis-keyword:: exe-path string

   The ``exe-path`` keyword specifies the location from where the simulation
   was executed. This will be set and updated by |pyretis|.


   Default
      Not any, note that this keyword will be updated and modified by
      |pyretis| as part of the output process. This keyword **does not**
      need to be set in the input file by the user since |pyretis| will
      update this setting automatically. 


.. _user-section-simulation-restart:

Keyword restart
^^^^^^^^^^^^^^^

.. pyretis-keyword:: restart string

   The ``restart`` keyword specifies the path to the restart file to use
   for restarting/continuing the selected simulation task.

   Default
      Not any.


.. _user-section-simulation-startcycle:

Keyword startcycle
^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: startcycle integer

   The ``startcycle`` keyword specifies the cycle number the simulation
   starts at. This can be used, for instance, when extending a simulation
   to tell |pyretis| that the simulation should start at a specified
   step number.

   Default
      The default value is ``0``.
