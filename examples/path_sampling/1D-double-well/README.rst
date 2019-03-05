1D Langevin TIS example
=======================

In this example, we aim to reproduce the 
Transition Interfaces Sampling (TIS) results reported
by van Erp [vanerp2012]_ for a one-dimensional
particle moving in a double well potential under Langevin dynamics.
Our goal is to calculate the rate constant for the transition
between the two stable states using TIS and Replica Exchange TIS (RETIS).

Definition of the system
------------------------

The system we investigate is determined by the double well 
potential, :math:`V`, given by

.. math::
    V(r) = k_4 r^4 - k_2 r^2

where :math:`r` is the position and the parameters are
set to :math:`k_4 = 1` and :math:`k_2 = 2`.
For this particular choice of parameters, there are two stable
states located at :math:`r = -1` and :math:`r = 1`, separated
by a barrier located at :math:`r = 0`.
 
Obtaining the rate constant from TIS
------------------------------------

In order to obtain the rate constant using TIS the following steps
are performed:

1. Obtaining the initial flux by running the simulation defined by
   flux.rst

2. Obtaining the crossing probability by running the simulations defined
   by tis-multiple.rst

Obtaining the rate constant from RETIS
--------------------------------------

In order to obtain the rate constant using RETIS the following steps
are performed:

1. Running the simulation using RETIS.rst

Comparison of results
---------------------

The initial flux reported in the original paper [vanerp2012]_ was,

.. math:: 
    f_\text{A} = 0.263 \pm 0.01\%,

and the crossing probability :math:`P_\text{A}` was found to be,

.. math::
    P_\text{A} = 1.52 \times 10^{-6} \pm 20 \%.

References
----------

.. [vanerp2012] Dynamical Rare Event Simulation Techniques for Equilibrium and nonequilibrium Systems, Adv. Chem. Phys., 151, 27-60, (2012), Titus S. van Erp,
