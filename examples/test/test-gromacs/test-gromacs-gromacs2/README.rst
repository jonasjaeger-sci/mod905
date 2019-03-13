Comparison of the two engines ``gromacs`` and ``gromacs2``
==========================================================

This example will compare the two engines ``gromacs`` and ``gromacs2``.

For this test GROMACS **must** have been compiled with support for
**double precision**. The test will run a RETIS simulation with the
same input using the two engines. The expected result is that both
engines should produce the same output. To ensure this, we let PyRETIS
determine the seed for the generation of velocities in GROMACS.
This implies that we need to change the two engines ``gromacs`` and
``gromacs2`` accordingly and this is done by overriding the class methods
responsible for creating the shooting point. The modified engines can be
found in ``gromacs.py`` in the folder ``gmx`` in the parent directory.

Description of files and folders
--------------------------------

- ``gromacs_input``: Contains the input files for GROMACS.

- ``run-gromacs1``: Contains the input script for using the ``gromacs`` engine.

- ``run-gromacs2``: Contains the input script for using the ``gromacs2`` engine.

- ``Makefile``: A makefile which can be used for removing temporary files, i.e. by
  doing a ``make clean``.

- ``run.sh``: A script which will automatically run the test and compare the results.

Running the test
----------------

Either use the ``run.sh`` script or run the tests manually.

To manually execute the tests do the following:

1. Copy the following files from the ``gmx`` parent directory:

   - ``gromacs.py``
   - ``orderp.py``

   into ``run-gromacs1`` or ``run-gromacs2``.

2. Move into the folder containing the test you want to run,
   either ``run-gromacs1`` or ``run-gromacs2``. Note: you will
   have to execute both these.

3. Manually specify the name of the GROMACS executable in the file
   ``retis.rst``, before running the test. This is done by replacing
   the text ``GMXCOMMAND`` with the name of your GROMACS executable
   in the file ``retis.rst``

4. Execute the simulation by running:

   pyretisrun -i retis.rst -p -l DEBUG

5. After having executed both simulations (``run-gromacs1`` and
   ``run-gromacs2``) you can compare them. This is done using the
   script ``compare.py`` from the parent ``gmx`` directory. You
   first need to copy this script and then run the comparison using:

   python compare.py run-gromacs1 run-gromacs2 --energy_skip 'vpot'


Results
-------
The two simulations should give the same output, that is the same information in
the output files.

Note: The potential energies in the two cases will differ. This difference is due
to the continuation runs not writing the dispersion correction to the energy file.
This means that the energy from the ``gromacs`` engine will be shifted relative
to the ``gromacs2`` engine for some points.
