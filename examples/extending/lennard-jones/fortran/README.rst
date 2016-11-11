Extending pyretis with Fortran
==============================

This folder contains an example of extending pyretis with a new
force field which is implemented in Fortran.

The Fortran code must be compiled before it can be executed and this
is done by running ``make``.

Note that you may have to edit the makefile depending on your version
of python. For python3 change ``f2py`` to ``f2py3`` in the makefile. If you
have several python versions installed (perhaps you are running in a virtual
environment) you may have to specify which f2py to use more explicitly, e.g.
``f2py3.5``.
