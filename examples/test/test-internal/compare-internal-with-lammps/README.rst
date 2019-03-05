PyRETIS vs LAMMPS
=================

This example is a test of the Velocity Verlet integration.

Here, we compare the outcome of simulations which are
performed with equal "settings" such that the only difference
is that one is performed with PyRETIS and the other with LAMMPS.

There are two tests:

1. A plain MD simulation of a one-component Lennard-Jones system.

2. A plain MD simulation of a multi-component Lennard-Jones system.

The output from the PyRETIS simulation is automatically compared with
the LAMMPS output by running `run.sh`.

Plotting
--------

Comparison plots are created by passing a plot argument to the scripts,
e.g.:

.. code-block:: bash

   python run_md_comparison.py md-lammps.rst output_data/lammps-output.txt.gz
