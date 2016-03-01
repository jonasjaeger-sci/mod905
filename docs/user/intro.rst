.. _user-guide-intro:

Introduction to rare event methods
==================================

pyretis is a computational library for performing molecular
simulations of rare events with focus on transition
interface sampling [TIS2003]_
and replica exchange transition interface sampling [RETIS2007]_.

The typical goal of these simulations is to calculate the
rate constant :math:`k_{\text{AB}}` for the transition between two stable
states: :math:`\text{A} \to \text{B}`. 

This rate constant can be expressed as the
probability of reaching the end state multiplied by a flux
:math:`f_{\text{A}}` which determines how frequent such transitions are
initiated. The overall probability is conveniently obtained as a product
of probabilities for reaching intermediate states and the overall rate
constant can be obtained as:

.. math:: k_{\text{AB}} = f_{\text{A}}  \prod_{i=1}^{n-1} P_{\text{A}} (i+1|i).

The rare event methods aim to compute both the flux and the intermediate
probabilities :math:`P_{\text{A}} (i+1|i)`. This is done by generating
reactive trajectories or paths connecting the initial and final state
using a Monte Carlo algorithm. For a detailed description of the algorithms,
please see [TIS2003]_ and [RETIS2007]_.

Transition Interface Sampling
-----------------------------

Replica Exchange Transition Interface Sampling
----------------------------------------------

References
~~~~~~~~~~

.. [TIS2003] Titus S. van Erp, Daniele Moroni and Peter G. Bolhuis,
             J. Chem. Phys. 118, 7762 (2003)
             https://dx.doi.org/10.1063%2F1.1562614

.. [RETIS2007] Titus S. van Erp,
               Phys. Rev. Lett. 98, 26830 (2007)
               http://dx.doi.org/10.1103/PhysRevLett.98.268301
