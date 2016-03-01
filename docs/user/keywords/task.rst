.. _user-keywords-task:

task
====

The ``task`` keyword specified the kind of simulation to run.

Example:

.. code-block:: python

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

.. _user-keywords-task-md-nve:

Settings for task md-nve
~~~~~~~~~~~~~~~~~~~~~~~~

For ``md-nve`` the following keywords are required:

* :ref:`integrator <user-keywords-integrator>`

.. _user-keywords-task-md-flux:

Settings for task md-flux
~~~~~~~~~~~~~~~~~~~~~~~~~

For ``md-flux`` the following keywords are required:

* :ref:`integrator <user-keywords-integrator>`

.. _user-keywords-task-tis:

Settings for task tis
~~~~~~~~~~~~~~~~~~~~~

For ``tis`` the following keywords are required:

* :ref:`integrator <user-keywords-integrator>`

.. _user-keywords-task-retis:

Settings for task retis
~~~~~~~~~~~~~~~~~~~~~~~

For ``retis`` the following keywords are required:

* :ref:`integrator <user-keywords-integrator>`
