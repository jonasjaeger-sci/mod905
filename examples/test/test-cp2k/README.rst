test-cp2k
=========

Here, we test come core functionality when using CP2K as an
external engine. The different tests as described below.

test-cp2k
---------
This test that we can use CP2K for running dynamics, generating velocities
and so on.

test-integrate
--------------
Test that we can use the integrate method for CP2K. This can, for
instance, be used for obtaining external order parameters with CP2K.
Note that this will be a lot slower than just running CP2K and calculating
the order parameter in post-processing.
