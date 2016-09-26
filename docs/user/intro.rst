.. _user-guide-intro:

Introduction to rare event methods
==================================

pyretis is a computational library for performing molecular
simulations of rare events with focus on transition
interface sampling [1]_
and replica exchange transition interface sampling [2]_.

Rare events are called rare because they happen at time or length scales
much longer than we are able to simulate through brute-force simulations.
Raindrops forms every day, but compared to the motion of water molecules,
raindrop formation is rare, and simulating it through brute-force
simulations would take forever and a day.

Rare event methods aim to sample these rare events inaccessible through brute-force simulation.


.. _user-guide-tis-theory:

Transition Interface Sampling
-----------------------------

The typical goal of TIS and RETIS is to calculate the
rate constant :math:`k_{\text{AB}}` for the transition between two stable
states: :math:`\text{A} \to \text{B}`.

The rate constant can be viewed as the flux of trajectories starting before A and going through B. As this is a rare event, the flux is extremely low and impossible to compute by brute-force simulations. Transition interface sampling divides the region between A and B into subregions using interfaces, denoted :math:`\lambda_i` (see figure X). :math:`\lambda_0` is positioned at the exact interface A, and the next interface, :math:`\lambda_1` is put very close to :math:`\lambda_0`. The flux between :math:`\lambda_0` and :math:`\lambda_1`, effectively the flux through interface A, :math:`f_{\text{A}}` is not any longer a rare event, and the flux can be computed through a direct (brute-force) simulation. The probability of going from A to B are obtained by a product of probabilities going from interface :math:`\lambda_i \to \lambda_{i+1}`. The rate constant can now be expressed as the probability going from A to B multiplied by the flux through interface A:

.. math::
   
   k_{\text{AB}} = f_{\text{A}}  \prod_{i=1}^{n-1} P_{\text{A}} (i+1|i).

The rare event methods aim to compute both the flux and the intermediate
probabilities :math:`P_{\text{A}} (i+1|i)`. This is done by generating
reactive trajectories or paths connecting the initial and final state
using a Monte Carlo algorithm. For a detailed description of the algorithms,
please see [1]_ and [2]_.


.. _user-guide-retis-theory:

Replica Exchange Transition Interface Sampling
----------------------------------------------

RETIS is an improvement of the TIS method, where many TIS simulations are performed in parallell at each interface, and exchanges are allowed between the interface ensembles. 


References
~~~~~~~~~~

.. [1] Titus S. van Erp, Daniele Moroni and Peter G. Bolhuis,
       J. Chem. Phys. 118, 7762 (2003)
       https://dx.doi.org/10.1063%2F1.1562614

.. [2] Titus S. van Erp,
       Phys. Rev. Lett. 98, 26830 (2007)
       http://dx.doi.org/10.1103/PhysRevLett.98.268301
