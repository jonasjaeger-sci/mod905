Extending PyRETIS with a new force field
========================================

This folder contains an example of how PyRETIS can be extended with a new
force field implemented in C or FORTRAN.

The sub-folders are:

* ``c``: Lennard-Jones implementation in C.

* ``fortran``: Lennard-Jones implementation in FORTRAN.

* ``fortran-pointer``: Lennard-Jones implementation in FORTRAN, with
  better memory alignment.

* ``omp-potential``: Lennard-Jones implementation in FORTRAN, with the use
  of OpenMP directives.

The examples in C are compiled with ``python setup.py build_ext --inplace``
while the FORTRAN examples can be compiled with the Makefiles in the folders.
Note that you may have to edit the Makefile depending on your version
of Python. In case you have several Python versions installed, you
may have to specify the precise version of ``f2py`` to use as this should
correspond to the Python version you are currently using. This can for instance
be: ``f2py``, ``f2py3`` or ``f2py3.X`` (where ``X`` denotes the minor version number).

In each folder, there is a script to run a simple MD simulation
``md_nve.py`` and a script for timing the Lennard-Jones implementations
(``time_ljforces.py``). There is also a script for testing the
implementation (``test_ljforces.py``).

The output from ``time_ljforces.py`` for the different implementation can
be compared with the plotting script in ``plot_results.py``. Note however
that this relies on finding the files ``c/timings.txt``, ``fortran/timings.txt``
etc. which contains the output from ``time_ljforces.py``.

There is also two scripts in the main folder for timing a
pure python (``time_lj.py``), a numpy implementation (``time_lj_numpy.py``)
and a numba implementation (``time_lj_numba.py``).
