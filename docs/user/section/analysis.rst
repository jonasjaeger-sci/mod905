.. _user-section-analysis:

The Analysis section
====================

The ``analysis`` section defines parameters for the analysis.

.. pyretis-input-example:: Analysis

   .. code-block:: rst

      Analysis settings
      -----------------
      maxblock = 1000
      blockskip = 1
      bins = 100
      ngrid = 1001
      plot = {'plotter': 'mpl', 'output': 'png', 'style': 'pyretis'}
      report = ['latex', 'rst', 'html']
      maxordermsd = 100
      report-dir = report
      txt-output = 'txt.gz'
      skipcross = 1000


Keywords for the Analysis section
---------------------------------

For the analysis section the following keywords can be set:

.. |analysis_bins| replace:: :ref:`bins <user-section-analysis-keyword-bins>`

.. |analysis_blockskip| replace:: :ref:`blockskip <user-section-analysis-keyword-blockskip>`

.. |analysis_maxblock| replace:: :ref:`maxblock <user-section-analysis-keyword-maxblock>`

.. |analysis_maxordermsd| replace:: :ref:`maxordermsd <user-section-analysis-keyword-maxordermsd>`

.. |analysis_ngrid| replace:: :ref:`ngrid <user-section-analysis-keyword-ngrid>`

.. |analysis_plot| replace:: :ref:`plot <user-section-analysis-keyword-plot>`

.. |analysis_report| replace:: :ref:`report <user-section-analysis-keyword-report>`

.. |analysis_dir| replace:: :ref:`report-dir <user-section-analysis-keyword-report-dir>`

.. |analysis_skipcross| replace:: :ref:`skipcross <user-section-analysis-keyword-skipcross>`

.. |analysis_output| replace:: :ref:`txt-output <user-section-analysis-keyword-txt-output>`

.. _table-analysis-keywords:

.. table:: Supported keywords for the analysis section.
   :class: table-striped table-hover

   +------------------------+-------------------------------------------------+
   | Keyword                | Description                                     |
   +========================+=================================================+
   | |analysis_bins|        | Set the number of bins to use when creating     |
   |                        | histograms.                                     |
   +------------------------+-------------------------------------------------+
   | |analysis_blockskip|   | Selects certain block lengths to skip in the    |
   |                        | in the block error analysis                     |
   +------------------------+-------------------------------------------------+
   | |analysis_maxblock|    | Set maximum length of blocks to consider in     |
   |                        | the block error analysis.                       |
   +------------------------+-------------------------------------------------+
   | |analysis_maxordermsd| | Set the maximum number of time origins to       |
   |                        | consider when calculating a mean square         |
   |                        | displacement.                                   |
   +------------------------+-------------------------------------------------+
   | |analysis_ngrid|       | Number of points used for calculating the       |
   |                        | crossing probability.                           |
   +------------------------+-------------------------------------------------+
   | |analysis_plot|        | Settings related to plotting of results.        |
   +------------------------+-------------------------------------------------+
   | |analysis_report|      | Define output format(s) for the report.         |
   +------------------------+-------------------------------------------------+
   | |analysis_dir|         | Defines the directory where the analysis        |
   |                        | results should be written.                      |
   +------------------------+-------------------------------------------------+
   | |analysis_skipcross|   | Set time window for initial flux calculation.   |
   +------------------------+-------------------------------------------------+
   | |analysis_output|      | Select format for text-based output.            |
   +------------------------+-------------------------------------------------+


.. _user-section-analysis-keyword-bins:

Keyword bins
^^^^^^^^^^^^

.. pyretis-keyword:: bins integer

   The ``bins`` keyword defines the number of bins to use when histograms
   are created.

   Default
      The default value is: ``bins = 100``

.. _user-section-analysis-keyword-blockskip:

Keyword blockskip
^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: blockskip integer

   The ``blockskip`` keyword can be used to skip certain block lengths
   in the block error analysis. That is:

   - ``blockskip = 1`` will consider all blocks up to the value given
     in the :ref:`keyword maxblock <user-section-analysis-keyword-maxblock>`

   - ``blockskip = n`` will consider every n'th block up to the value given
     in the :ref:`keyword maxblock <user-section-analysis-keyword-maxblock>`,
     That is, it will use block lengths equal to ``1``, ``1 + n``, ``1 + 2*n``
     and so on.

   Default
      The default value is: ``blockskip = 1``

.. _user-section-analysis-keyword-maxblock:

Keyword maxblock
^^^^^^^^^^^^^^^^

.. pyretis-keyword:: maxblock integer

   The ``maxblock`` keyword defines the maximum length of the blocks to
   consider for the block error analysis. If a negative number is
   set, |pyretis| will set ``maxblock`` equal to (1/2) * length of the
   data we are analysing. This is also the maximum length that |pyretis|
   will consider, even if the input ``maxblock`` is set higher.

   Default
      The default value is: ``maxblock = 1000``

.. _user-section-analysis-keyword-maxordermsd:

Keyword maxordermsd
^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: maxordermsd integer

   The ``maxordermsd`` keyword defines the maximum number of
   time origins to consider when calculating a mean square
   displacement. If this is set to a value < 0,
   |pyretis| will internally set ``maxordermsd`` to (1/5) * length of
   the data for which the mean
   square displacement will be obtained.

   Default
      The default value is: ``maxordermsd = -1``

.. _user-section-analysis-keyword-ngrid:

Keyword ngrid
^^^^^^^^^^^^^

.. pyretis-keyword:: ngrid integer

   The ``ngrid`` keyword defines the number of points used for the
   order parameter when |pyretis| is calculating the crossing probability
   as a function of the order parameter.

   Default
      The default value is: ``ngrid = 1001``

.. _user-section-analysis-keyword-plot:

Keyword plot
^^^^^^^^^^^^

.. pyretis-keyword:: plot dictionary

   The ``plot`` keyword defines how plotting should be carried out. It is
   given as a dictionary, where the following keys can be used:

   * ``'plotter'``: Which selects the kind of plotter to use. Currently,
     |pyretis| only implements a plotter using matplotlib which is selected by
     setting ``plot = {'plotter': 'mpl'}``.

   * ``'output'``: Which selects the output format for plots. This can be set
     to any of the supported output formats by the plotter. Often this will depend
     on your specific system, but common choices are ``'png'``, ``'pdf'`` and ``'svg'``.

   * ``'style'``: Selects a style for creating plots. Here you can, for instance, create your
     own matplotlib style or use one of the built-in styles.
     Please see `<http://matplotlib.org/users/style_sheets.html>`_ for more information.

   Default
      The default value is: ``plot = {'plotter': 'mpl', 'style': 'pyretis', 'output': 'png'}``

.. _user-section-analysis-keyword-report:

Keyword report
^^^^^^^^^^^^^^

.. pyretis-keyword:: report list of strings

   The ``report`` keyword defines the output format for the report.
   This is provided as a list of strings, where each item in the list
   correspond to a specific format:

   - ``'latex'`` selects latex output.
   - ``'rst'`` selects output in reStructuredText.
   - ``'html'`` selects html output.

   Default
      The default value is: ``report = ['latex', 'rst', 'html']``

.. _user-section-analysis-keyword-report-dir:

Keyword report-dir
^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: report-dir string

   The ``report-dir`` keyword defines where the analysis results should
   be written.

   Default
      The default value is a sub-folder named ``report`` within the
      directory where the analysis program was executed.

.. _user-section-analysis-keyword-skipcross:

Keyword skipcross
^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: skipcross integer

   The ``skipcross`` keyword defines a time window for which we
   calculate the initial flux. This is used when analysing a md-flux
   simulation.

   Default
      The default value is: ``skipcross = 1000``

.. _user-section-analysis-keyword-txt-output:

Keyword txt-output
^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: txt-output string

   The ``txt-output`` keyword defines the format for how text-based output
   should be written. Valid choices are:

   - ``txt`` for writing plain text files.
   - ``txt.gz`` for creating gzipped files.

   Default
      The default value is: ``txt-output = txt.gz``

