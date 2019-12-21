##############################
PyRETIS - TIS analysis
##############################

Please note that the flux (and thus the rate constant)
was **not** calculated in this analysis!

The main result is:

* The crossing probability:
  :math:`P_{\text{cross}} = 0.119435130  \pm  56.233322668 \%`

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
|  [0^+]   |  0.921569  |  0.102494  |   11.225526    |
+----------+------------+------------+----------------+
|  [1^+]   |  0.843137  |  0.123323  |   14.738629    |
+----------+------------+------------+----------------+
|  [2^+]   |  0.745098  |  0.134735  |   17.019187    |
+----------+------------+------------+----------------+
|  [3^+]   |  0.725490  |  0.174519  |   24.432679    |
+----------+------------+------------+----------------+
|  [4^+]   |  0.784314  |  0.095718  |   12.342585    |
+----------+------------+------------+----------------+
|  [5^+]   |  0.803922  |  0.072250  |    8.458505    |
+----------+------------+------------+----------------+
|  [6^+]   |  0.450980  |  0.306667  |   41.333433    |
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
|  [0^+]   | 834.065217 | 459.565217 |   0.550994   |
+----------+------------+------------+--------------+
|  [1^+]   | 727.591837 | 373.285714 |   0.513043   |
+----------+------------+------------+--------------+
|  [2^+]   | 789.125000 | 363.812500 |   0.461033   |
+----------+------------+------------+--------------+
|  [3^+]   | 872.387755 | 343.122449 |   0.393314   |
+----------+------------+------------+--------------+
|  [4^+]   | 1.2134e+03 | 508.510204 |   0.419069   |
+----------+------------+------------+--------------+
|  [5^+]   | 1.1895e+03 | 454.208333 |   0.381835   |
+----------+------------+------------+--------------+
|  [6^+]   | 1.3431e+03 | 518.258065 |   0.385868   |
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
|  [0^+]   |     51     | 2.3438e+04 |     0.843137     |  5.954088   | 295.345769 |
+----------+------------+------------+------------------+-------------+------------+
|  [1^+]   |     51     | 1.9038e+04 |     0.862745     |  5.343789   | 413.547810 |
+----------+------------+------------+------------------+-------------+------------+
|  [2^+]   |     51     | 1.8554e+04 |     0.764706     |  5.173198   | 537.434360 |
+----------+------------+------------+------------------+-------------+------------+
|  [3^+]   |     51     | 1.7499e+04 |     0.686275     |  7.163470   | 1.0446e+03 |
+----------+------------+------------+------------------+-------------+------------+
|  [4^+]   |     51     | 2.5934e+04 |     0.490196     |  2.526065   | 395.077353 |
+----------+------------+------------+------------------+-------------+------------+
|  [5^+]   |     51     | 2.3165e+04 |     0.470588     |  1.969568   | 165.734332 |
+----------+------------+------------+------------------+-------------+------------+
|  [6^+]   |     51     | 2.6431e+04 |     0.156863     | 14.735404   | 4.5156e+03 |
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
:math:`P_{\text{cross}} = 0.119435130  \pm  56.233322668 \%`

Other statistics:

* :math:`\text{sim.time} = 1.540588866e+05`

* :math:`\tau_{\text{eff}} = 4.871629435e+04`

* :math:`\tau_{\text{eff}}^{\text{opt}} = 3.723883815e+04`
