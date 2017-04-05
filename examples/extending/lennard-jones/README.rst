Extending pyretis with a new force field
========================================

This folder contains an example on how pyretis can be extended with a new
force field implemented in C or FORTRAN.

The sub-folders are:

* ``c-python3``: Lennard-Jones implementation in C for python3

* ``fortran``: Lennard-Jones implementation in FORTRAN.

* ``fortran-pointer``: Lennard-Jones implementation in FORTRAN, with
  better memory alignment.

The examples in C are compiled with ``python setup.py build_ext --inplace``
while the FORTRAN examples can be compiled with the makefiles in the folders.
Note that you may have to specify which ``f2py`` to use (e.g. ``f2py``, ``f2py3``,
``f2py3.5``).

In each folder there is a script to run a simple MD simulation
``md_nve.py`` and a script for timing the Lennard-Jones implementations
(``time_ljforces.py``). There is also a script for testing the
implementation (``test_ljforces.py``).

The output from ``time_ljforces.py`` for the different implementation can
be compared with the plotting script in ``plot_results.py``. Note however
that this relies on finding the files ``c/timings.txt``, ``fortran/timings.txt``
etc. which contains the output from ``time_ljforces.py``.

There is also two scripts in the main folder for timing for the pure python
and numpy implementations of the Lennard-Jones potential (``time_lj.py`` and
(``time_lj_numpy.py``).
