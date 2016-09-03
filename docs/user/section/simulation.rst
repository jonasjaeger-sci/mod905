.. _user-section-simulation:

The simulation section
======================

Specifies what kind of simulation to run

.. code-block:: rst

    Simulation
    ----------
    task = retis
    steps = 10000

.. _user-section-simulation-keyword-task:

task
----

The ``task`` keyword specified the kind of simulation to run.

Example:

.. code-block:: rst 

    task = md-nve

The possible tasks are:

.. table:: Possible values for the ``task`` keyword

    +------------+-------------------------------------------------------------+
    |   Task     | Description                                                 |
    +============+=============================================================+
    |   md-nve   | A MD NVE simulation                                         |
    +------------+-------------------------------------------------------------+
    |   md-flux  | A MD FLUX simulation                                        |
    +------------+-------------------------------------------------------------+
    |   tis      | A transition interface sampling simulation                  |
    +------------+-------------------------------------------------------------+
    |   retis    | A replica exchange transition interface sampling simulation |
    +------------+-------------------------------------------------------------+
