1D Langevin TIS example
=======================

In this example, we aim to reproduce the TIS results reported
by van Erp  [vanerp2012]_. The system we investigate is a one-dimensional
particle moving in a double well potential under Langevin dynamics.

The double well potential, :math:`V` is defined by

.. math::
    V(r) = k_4 r^4 - k_2 r^2

where :math:`r` is the position and the parameters are set to :math:`k_4 = 1` and :math:`k_2 = 2`.
 
The initial flux reported in the original paper [vanerp2012]_ was,

.. math:: 
    f_\text{A} = 0.263 \pm 0.01\%,

and the crossing probability :math:`P_\text{A}` was found to be,

.. math::
    P_\text{A} = 1.52 \times 10^{-6} \pm 20 \%.



References
----------

.. [vanerp2012] Dynamical Rare Event Simulation Techniques for Equilibrium and nonequilibrium Systems, Adv. Chem. Phys., 151, 27-60, (2012), Titus S. van Erp,
