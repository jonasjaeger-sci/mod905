.. _user-section-simulation:

The simulation section
======================

Specifies what kind of simulation to run

.. code-block:: rst

    Simulation
    ----------
    task = retis
    steps = 10000

The keywords that needs to be set for this section
depends on the selected ``task``.
The ``task`` keyword specified the kind of simulation to run.

Example:

.. code-block:: rst 

    task = retis

The tasks recognized by pyretis are:

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

The ``tis`` and ``retis`` tasks requires that other sections are set.
For ``tis``:

* The section :ref:`TIS <user-section-tis>` for transition interface
  sampling settings.

For ``retis``:

* The section :ref:`TIS <user-section-tis>` for transition interface
  sampling settings.

* The section :ref:`RETIS <user-section-retis>` for replica exchange
  transition interface sampling settings.
