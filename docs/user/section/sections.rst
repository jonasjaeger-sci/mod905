.. _user-section:

Input file sections
===================

The pyretis input file is structured with sections
as described in :ref:`the user guide <user-guide-input-structure>`:

* The input file is organized into sections where keywords are set:

  .. code-block:: rst

      Section Title
      -------------
      keyword = value

* Comments are marked with a #.

* Input is in general not case sensitive unless you are referring to files and python classes.

Here, you can find information about the different sections recognized by pyretis:

.. toctree::
    :maxdepth: 1
    :hidden:

    box.rst
    forcefield.rst
    integrator.rst
    orderparameter.rst
    particles.rst
    unitsystem.rst
    simulation.rst
    system.rst

* :ref:`box <user-section-box>`: for defining a simulation box.
* :ref:`forcefield <user-section-forcefield>`: for defining a forcefield.
* :ref:`integrator <user-section-integrator>`: for defining the integrator for the simulation.
* :ref:`orderparameter <user-section-orderparameter>`: for defining the order parameter.
* :ref:`particles <user-section-particles>`: for defining initial state of partices.
* :ref:`unit-system <user-section-unit-system>`: for defining initial state of partices.
* :ref:`simulation <user-section-simulation>`: for defining initial state of partices.
* :ref:`system <user-section-system>`: for defining system properties.
