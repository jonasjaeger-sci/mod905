md_forward_backward.py
======================

This example will run a specified steps with the
Velocity Verlet integrator and then reverse
the velocities and run for the same number of steps.

The subfolder ``external`` contains the same
example using a FORTRAN or C extension for calculating
the forces. This will run faster in case you want to try
the example out for bigger systems.
