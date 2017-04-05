PyRETIS vs LAMMPS
-----------------

This example is a test of the Velocity Verlet integration.

Here, we compare the outcome of simulations which are
performed with equal "settings" such that the only difference
is that one is performed with PyRETIS and the other with LAMMPS.

There are two tests:

1) ``md_lammps_one_component.py`` which is a plain MD simulation of a
   one-component Lennard-Jones system.

2) ``md_lammps_mixture.py`` which is a plain MD simulation of a
   multi-component Lennard-Jones system.

The output from the PyRETIS simulation is automatically compared with
the LAMMPS output by running these scripts.
