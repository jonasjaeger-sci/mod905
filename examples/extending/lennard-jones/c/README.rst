Extending pyretis with C
========================

This folder contains an example of extending pyretis with a new
force field which is implemented in C.

The C code must be compiled before it can be executed and this
is done by running ``python setup.py build_ext --inplace``.

Note
----

The code in this folder will only work with python version 2.x.
That is, it will not work with python 3!
