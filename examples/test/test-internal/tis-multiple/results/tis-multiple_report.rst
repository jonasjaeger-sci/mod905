##############################
PyRETIS - TIS analysis
##############################

Please note that the flux (and thus the rate constant)
was **not** calculated in this analysis!

The main result is:

* The crossing probability:
  :math:`P_{\text{cross}} = 0.103484118  \pm  82.283801772 \%`

Detailed results are given below for the different path
ensembles and the overall results are summarized
in the `Combined results`_.

.. _figure-results:

Results for path ensembles
==========================

The following interfaces were used in the simulation and in
the analysis:

+------------------------------------------------------+
|Interfaces                                            |
+----------+----------+----------+----------+----------+
| Ensemble |   Left   |  Middle  |  Right   |  Detect  |
+==========+==========+==========+==========+==========+
|  [0^+]   | -0.9000  | -0.9000  |  1.0000  | -0.8000  |
+----------+----------+----------+----------+----------+
|  [1^+]   | -0.9000  | -0.8000  |  1.0000  | -0.7000  |
+----------+----------+----------+----------+----------+
|  [2^+]   | -0.9000  | -0.7000  |  1.0000  | -0.6000  |
+----------+----------+----------+----------+----------+
|  [3^+]   | -0.9000  | -0.6000  |  1.0000  | -0.5000  |
+----------+----------+----------+----------+----------+
|  [4^+]   | -0.9000  | -0.5000  |  1.0000  | -0.4000  |
+----------+----------+----------+----------+----------+
|  [5^+]   | -0.9000  | -0.4000  |  1.0000  | -0.3000  |
+----------+----------+----------+----------+----------+
|  [6^+]   | -0.9000  | -0.3000  |  1.0000  |  1.0000  |
+----------+----------+----------+----------+----------+

The calculated crossing probabilities are:

+-----------------------------------------------------+
|Probabilities                                        |
+----------+------------+------------+----------------+
| Ensemble |   Pcross   |   Error    | Rel. error (%) |
+==========+============+============+================+
|  [0^+]   |  0.823529  |  0.205051  |   24.899090    |
+----------+------------+------------+----------------+
|  [1^+]   |  0.843137  |  0.117912  |   13.984901    |
+----------+------------+------------+----------------+
|  [2^+]   |  0.803922  |  0.092015  |   11.445810    |
+----------+------------+------------+----------------+
|  [3^+]   |  0.686275  |  0.138790  |   20.223719    |
+----------+------------+------------+----------------+
|  [4^+]   |  0.745098  |  0.086199  |   11.568874    |
+----------+------------+------------+----------------+
|  [5^+]   |  0.803922  |  0.036059  |    4.485331    |
+----------+------------+------------+----------------+
|  [6^+]   |  0.450980  |  0.327112  |   72.533575    |
+----------+------------+------------+----------------+

The crossing probabilities are also displayed in the figures below

.. _prob-figures-output:

Crossing probabilities
----------------------


.. image:: 001_pcross.png
   :width: 30%
.. image:: 001_prun.png
   :width: 30%
.. image:: 001_perror.png
   :width: 30%

.. image:: 002_pcross.png
   :width: 30%
.. image:: 002_prun.png
   :width: 30%
.. image:: 002_perror.png
   :width: 30%

.. image:: 003_pcross.png
   :width: 30%
.. image:: 003_prun.png
   :width: 30%
.. image:: 003_perror.png
   :width: 30%

.. image:: 004_pcross.png
   :width: 30%
.. image:: 004_prun.png
   :width: 30%
.. image:: 004_perror.png
   :width: 30%

.. image:: 005_pcross.png
   :width: 30%
.. image:: 005_prun.png
   :width: 30%
.. image:: 005_perror.png
   :width: 30%

.. image:: 006_pcross.png
   :width: 30%
.. image:: 006_prun.png
   :width: 30%
.. image:: 006_perror.png
   :width: 30%

.. image:: 007_pcross.png
   :width: 30%
.. image:: 007_prun.png
   :width: 30%
.. image:: 007_perror.png
   :width: 30%



.. _len-shoot-figures-output:

Distributions for path lengths and shooting moves
-------------------------------------------------

The average path lengths in the different ensembles are given in
the table below and some distributions for the path lengths and
shooting moves can also be found here:

+---------------------------------------------------+
|Path lengths                                       |
+----------+------------+------------+--------------+
| Ensemble |  Accepted  |    All     | All/Accepted |
+==========+============+============+==============+
|  [0^+]   | 780.039216 | 422.800000 |   0.542024   |
+----------+------------+------------+--------------+
|  [1^+]   | 726.274510 | 365.820000 |   0.503694   |
+----------+------------+------------+--------------+
|  [2^+]   | 789.882353 | 349.260000 |   0.442167   |
+----------+------------+------------+--------------+
|  [3^+]   | 870.725490 | 336.260000 |   0.386184   |
+----------+------------+------------+--------------+
|  [4^+]   | 1.2057e+03 | 498.340000 |   0.413311   |
+----------+------------+------------+--------------+
|  [5^+]   | 1.1873e+03 | 450.040000 |   0.379053   |
+----------+------------+------------+--------------+
|  [6^+]   | 1.2144e+03 | 445.180000 |   0.366575   |
+----------+------------+------------+--------------+


.. image:: 001_lpath.png
   :width: 30%
.. image:: 001_shoots.png
   :width: 30%
.. image:: 001_shoots_scaled.png
   :width: 30%

.. image:: 002_lpath.png
   :width: 30%
.. image:: 002_shoots.png
   :width: 30%
.. image:: 002_shoots_scaled.png
   :width: 30%

.. image:: 003_lpath.png
   :width: 30%
.. image:: 003_shoots.png
   :width: 30%
.. image:: 003_shoots_scaled.png
   :width: 30%

.. image:: 004_lpath.png
   :width: 30%
.. image:: 004_shoots.png
   :width: 30%
.. image:: 004_shoots_scaled.png
   :width: 30%

.. image:: 005_lpath.png
   :width: 30%
.. image:: 005_shoots.png
   :width: 30%
.. image:: 005_shoots_scaled.png
   :width: 30%

.. image:: 006_lpath.png
   :width: 30%
.. image:: 006_shoots.png
   :width: 30%
.. image:: 006_shoots_scaled.png
   :width: 30%

.. image:: 007_lpath.png
   :width: 30%
.. image:: 007_shoots.png
   :width: 30%
.. image:: 007_shoots_scaled.png
   :width: 30%



.. _tis-efficiency:

Efficiency analysis
-------------------

+----------------------------------------------------------------------------------+
|Efficiency                                                                        |
+----------+------------+------------+------------------+-------------+------------+
| Ensemble | TIS cycles |  Tot sim.  | Acceptance ratio | Correlation | Efficiency |
+==========+============+============+==================+=============+============+
|  [0^+]   |     51     | 2.1563e+04 |     0.941176     | 14.465842   | 1.3368e+03 |
+----------+------------+------------+------------------+-------------+------------+
|  [1^+]   |     51     | 1.8657e+04 |     0.901961     |  5.256144   | 364.885341 |
+----------+------------+------------+------------------+-------------+------------+
|  [2^+]   |     51     | 1.7812e+04 |     0.823529     |  2.685634   | 233.352291 |
+----------+------------+------------+------------------+-------------+------------+
|  [3^+]   |     51     | 1.7149e+04 |     0.725490     |  4.473424   | 701.402687 |
+----------+------------+------------+------------------+-------------+------------+
|  [4^+]   |     51     | 2.5415e+04 |     0.529412     |  1.956106   | 340.155980 |
+----------+------------+------------+------------------+-------------+------------+
|  [5^+]   |     51     | 2.2952e+04 |     0.509804     |  0.412423   | 46.175368  |
+----------+------------+------------+------------------+-------------+------------+
|  [6^+]   |     51     | 2.2704e+04 |     0.411765     | 21.608169   | 1.1945e+04 |
+----------+------------+------------+------------------+-------------+------------+

.. _combined-results:

Combined results
================

The overall matched probability distributions are shown in the left figure
while the matched probability distribution is shown in the right figure below.
The overall crossing probability as a function of cycles
and its relative error block analysis are reported in the two following
plots, respectively.

.. image:: total-probability.png
   :width: 45%
.. image:: matched-probability.png
   :width: 45%

.. image:: overall-prun.png
   :width: 45%
.. image:: overall-err.png
   :width: 45%

The overall crossing probability is:
:math:`P_{\text{cross}} = 0.103484118  \pm  82.283801772 \%`

Other statistics:

* :math:`\text{sim.time} = 1.462527000e+05`

* :math:`\tau_{\text{eff}} = 9.902220457e+04`

* :math:`\tau_{\text{eff}}^{\text{opt}} = 5.380351263e+04`