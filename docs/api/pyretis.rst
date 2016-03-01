
.. _api-doc:

###############
The pyretis API
###############

This is the documentation for the pyretis API.
An overview of the main classes and routines are
given in the :ref:`introduction to the API <user-guide-intro-api>` in
the :ref:`user guide <user-guide-index>`.
It might also be a good idea to have a look at the
:ref:`developer guide <developer-guide-index>`
before makeing changes or reading through the API :ref:`docs <api-doc>`.

The pyretis package
===================

The pyretis library contains methods and classes that handle
the different parts of simulations. These are further grouped
into sub-modules:

* :ref:`pyretis.core <api-core>` for setting up and running
  simulations

* :ref:`pyretis.forcefield <api-forcefield>` for defining
  force fields to use in simulations

* :ref:`pyretis.analysis <api-analysis>` for analysing the
  output from simulations

* :ref:`pyretis.inout <api-inout>` for handling the input
  and output to pyretis

* :ref:`pyretis.tools <api-tools>` for performing some simple
  tasks useful for setting up simulations.

The pyretis library can be imported by:

.. code-block:: python

    import pyretis
    print(pyretis.__version__)

However it is more common to import specific functions and classes from
the subpackages:

.. code-block:: python

    from pyretis.tools import generate_lattice
    xyz = generate_lattice('diamond', [10, 10, 10], lcon=1.0)

The usage of these subpackages are described in the following:

Contents -- pyretis subpackages
-------------------------------

.. toctree::
    :maxdepth: 2

    pyretis.core
    pyretis.analysis
    pyretis.forcefield
    pyretis.inout
    pyretis.tools
