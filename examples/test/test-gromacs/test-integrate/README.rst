Testing the integration of the equations of motion with GROMACS
===============================================================

This directory contains tests for checking the behavior when
integrating the equations of motion with GROMACS:

1. ``gromacs`` which will test the integration using the PyRETIS
   ``GromacsEngine``.

2. ``gromacs2`` which will test the integration using the PyRETIS
   ``GromacsEngine2``.

Instructions
------------

In each folder, there is a ``run.sh`` file which can be used to
run the tests. This test will use the ``compare_energies.py`` script
to compare energies with a similar integration of motion, performed
with a pure GROMACS simulation.
