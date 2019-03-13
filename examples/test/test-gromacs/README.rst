Test GROMACS
============

This folder contains some tests for using GROMACS as an
external integrator. The folder `gmx` contain common
Python scripts used while running the tests. Each
test is defined, and can be run using an accompanying
`run.sh` script. If you want to use a specific GROMACS
executable, this can be given as an argument to the `run.sh`
script: `run.sh gmx_2016.4_d`. If no such argument is given,
the default `gmx_d` will be used.

The different tests are described below:

test-gromacs
------------
This test will check that the core functionality of the
GROMACS engines are in place and that they give comparable results
to running just plain MD simulations with GROMACS.

test-gromacs-gromacs2
---------------------
This test will compare the two engines ``GROMACS``
and ``GROMACS2`` by running two short RETIS simulations.

test-integrate
--------------
Test that the integration of the equation of motion works as intended
with the PyRETIS GROMACS engines.

test-load
---------
Test that we can load already existing GROMACS trajectories and
use these with PyRETIS.

test-restart
------------
Test that the restart method works with GROMACS.

test-retis
----------
Test that the RETIS simulation works with GROMACS.
