Comparison of the two engines ``gromacs`` and ``gromacs2``
==========================================================

This example will compare the two engines ``gromacs`` and ``gromacs2``.
For this test GROMACS **must** have been compiled with support for
**double precision**. The test will run a RETIS simulation with the
same input using the two engines, the expected result is that both
engines should produce the same output. To ensure this, we let PyRETIS
determine the seed for the generation of velocities in GROMACS.
This implies that we need to change ``gromacs`` and ``gromacs2``
accordingly and this is done by overriding the class methods responsible
for creating the shooting point.

Description of files
--------------------

- gromacs.py: Contains the two integrators where the seeds for GROMACS is
  excplicitly set.

- orderp.py: The order parameter used in the example.

- gromacs_input: The input files for GROMACS.

- run-gromacs1: The input script for using the ``gromacs`` engine.

- run-gromacs2: The input script for using the ``gromacs2`` engine.

Running the test
----------------

Execute the two simulations.

1. First, in ``run-gromacs1``: pyretisrun -i retis.rst -p -l DEBUG

2. Then, in ``run-gromacs2``: pyretisrun -i retis.rst -p -l DEBUG

You can then compare the output. This can also be done by running the
script ``compare.py``, e.g.: python compare.py

Results
-------
The two simulations should give the same output, that is the same information in
the output files.

Note: The potential energies in the two cases will differ. This difference is due
to the continuation runs not writing the dispersion correction to the energy file.
This means that the energy from the ``gromacs`` engine will be shifted with a
constant amount relative to the ``gromacs2`` engine.
