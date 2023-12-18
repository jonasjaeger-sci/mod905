Testing the GROMACS engine by running a RETIS simulation
========================================================

This test will run a RETIS simulation with the GROMACS engine
and compare the results to previously obtained results.

The folders are:

* ``gromacs1``: Which contains a test using the PyRETIS ``GromacsEngine``.

* ``gromacs2``: Which contains a test using the PyRETIS ``GromacsEngine2``.

Instructions
------------

The tests are run using the ``run.sh`` script. Note that you can
provide the GROMACS executable you want to use as an argument to
this script, e.g. ``run.sh my_gmx_executable``. Further note that
GROMACS should have been compiled with double precision.
