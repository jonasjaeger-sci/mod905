.. _user-section-simulation:

The simulation section
======================

Specifies what kind of simulation to run

.. code-block:: rst

    Simulation
    ----------
    task = retis
    steps = 20000
    interfaces = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]

The keywords that needs to be set for this section
depends on the selected ``task`` which specifies the
kind of simulation to run. In addition, some of the
tasks require that additional sections are defined.

The tasks recognized by pyretis are:

.. table:: Possible values for the ``task`` keyword

    +-------------+-------------------------------+----------------------------+-------------------+
    |   Task      | Description                   | Additional keywords        | Required sections |
    +=============+===============================+============================+===================+
    | ``md-nve``  | A MD NVE simulation.          | ``steps``                  |                   |
    +-------------+-------------------------------+----------------------------+-------------------+
    | ``md-flux`` | A MD FLUX simulation.         | ``steps``, ``interfaces``  |                   |
    +-------------+-------------------------------+----------------------------+-------------------+
    |   ``tis``   | A transition interface        | ``steps``, ``interfaces``, | ``tis``           |
    |             | sampling simulation.          | ``ensemble``, ``detect``   |                   |
    +-------------+-------------------------------+----------------------------+-------------------+
    |  ``retis``  | A replica exchange transition | ``steps``, ``interfaces``  | ``tis``,          |
    |             | transition interface sampling |                            | ``retis``         |
    |             | simulation.                   |                            |                   |
    +-------------+-------------------------------+----------------------------+-------------------+


``md-nve``
----------

The ``md-nve`` task is a simple molecular dynamics simulation.
The following keywords can be defined for the ``md-nve`` simulation:

* ``steps``: The number of cycles to perform.

``md-flux``
-----------

The ``md-flux`` task is a molecular dynamics simulation for
determining the initial flux for a TIS path simulation.

The following keywords can be defined for the ``md-flux`` simulation:

* ``steps``: The number of cycles to perform.

* ``interfaces``: The interfaces to use for the initial flux
  calculation.

Example:

.. code-block:: rst

    Simulation
    ----------
    task = md-flux
    steps = 10000000
    interfaces = [-0.9]


``tis``
-------

The ``tis`` task defines a transition interface sampling
simulation.

The following keywords can be defined for the ``tis`` simulation:

* ``steps``: The number of cycles to perform.

* ``interfaces``: The interfaces to use in the path simulation. If the
  number of interfaces given are 3 or less, a single TIS simulation will
  be formed, otherwise input files for several single TIS simulations will
  be written. These simulations can the be manually run.

* ``ensemble``: A number specifying the path ensemble we are simulating, ``1``
  corresponds to ``[0^+]``, 1 to ``[1^+]`` and so on. This is only needed for
  running a single TIS simulation.

* ``detect``: A number specifying the interface used for detecting successful
  paths.

Example for writing output files for several TIS simulations:

.. code-block:: rst

    Simulation
    ----------
    task = tis
    steps = 20000
    interfaces = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]

Example for performing a single TIS simulation:

.. code-block:: rst

    Simulation
    ----------
    task = tis
    steps = 20000
    interfaces = [-0.9, -0.9, 1.0]
    detect = -0.8
    ensemble = 1

In addition, this task requires that the
section :ref:`TIS <user-section-tis>` is defined.


``retis``
---------

The ``retis`` task defines a replica exchange transition
interface sampling simulation.
The following keywords can be defined for the ``retis`` simulation:

* ``steps``: The number of cycles to perform.

* ``interfaces``: The interfaces to use in the path simulation. 

Example:

.. code-block:: rst

    Simulation
    ----------
    task = retis
    steps = 20000
    interfaces = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]

In addition, this task requires that the
sections :ref:`TIS <user-section-tis>` and 
:ref:`RETIS <user-section-retis>` are defined. 

