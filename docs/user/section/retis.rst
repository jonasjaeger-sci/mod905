.. _user-section-retis:

The RETIS section
=================

The ``RETIS`` section specifies settings for RE(PP)TIS simulations. Note 
that the section for :ref:`TIS <user-section-tis>` also needs
to be defined for a RE(PP)TIS simulation.

.. pyretis-input-example:: RETIS

   .. code-block:: rst

       RETIS settings
       --------------
       swapfreq = 0.5
       relative_shoots = None
       nullmoves = True
       swapsimul = True
       rgen = None
       seed = None

Keywords for the RETIS section
------------------------------

The following keywords can be set for the RETIS section:

.. |retis_nullmoves| replace:: :ref:`nullmoves <user-section-retis-nullmoves>`

.. |retis_relatives| replace:: :ref:`relative_shoots <user-section-retis-relatives>`

.. |retis_priority| replace:: :ref:`priority_shooting <user-section-retis-priority>`

.. |retis_rgen| replace:: :ref:`rgen <user-section-retis-rgen>`

.. |retis_seed| replace:: :ref:`seed <user-section-retis-seed>`

.. |retis_swapsimul| replace:: :ref:`swapsimul <user-section-retis-swapsimul>`

.. |retis_swapfreq| replace:: :ref:`swapfreq <user-section-retis-swapfreq>`

.. _table-retis-keywords:

.. table:: Keywords for the RETIS section.
   :class: table-striped table-hover

   +-------------------+------------------------------------------------------+
   | Keyword           | Description                                          |
   +===================+======================================================+
   | |retis_nullmoves| | Determines if we do null moves or not.               |
   +-------------------+------------------------------------------------------+
   | |retis_relatives| | Selects and defines relative shooting.               |
   +-------------------+------------------------------------------------------+
   | |retis_priority|  | Prioritize the ensembles with less cycles.           |
   +-------------------+------------------------------------------------------+
   | |retis_rgen|      | Determines the rgen to use in retis function.        |
   +-------------------+------------------------------------------------------+
   | |retis_seed|      | Determines the seed for rgen in the retis function.  |
   +-------------------+------------------------------------------------------+
   | |retis_swapfreq|  | Defines how often we perform swapping moves.         |
   +-------------------+------------------------------------------------------+
   | |retis_swapsimul| | Determines if we swap multiple path ensebles at the  |
   |                   | same time or not.                                    |
   +-------------------+------------------------------------------------------+


.. _user-section-retis-nullmoves:

Keyword nullmoves
^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: nullmoves boolean

   If ``True`` we perform null moves in the ensembles
   not included in a swapping move. Otherwise, no move is done in these
   ensembles.

   Default
       No default, this setting **must** be specified.

.. _user-section-retis-relatives:

Keyword relative_shoots
^^^^^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: relative_shoots None or list of floats

   This keyword selects and defines relative shooting.
   Relative shooting means that we perform TIS moves in the
   ensembles with unequal frequencies. This is selected by
   specifying the relative frequency for each ensemble in a list,
   e.g. ``relative_shoots = [0.1, 0.1, 0.2, 0.6]`` for four ensembles,
   where these numbers give the relative probability of choosing an
   ensemble. TIS moves are then carried out in the selected ensemble
   and a null move or no move is carried out in the other ensembles
   depending on the keyword setting for
   :ref:`nullmove <user-section-retis-nullmoves>`.

   If ``relative_shoots = None`` we are not performing relative shooting
   and TIS moves are performed in all path ensembles.

   Default
       No default, this setting **must** be specified.

.. _user-section-retis-priority:

Keyword priority_shooting
^^^^^^^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: Priority_shooting boolean

   This keyword automatically and dynamically internally select the
   relative shooting such that ensembles with a lower cycle number,
   will be prioritized until they reach a cyclen number equal to the others.
   This setting simplify the use of |pyretis| in cluster environments
   in which walltime is rather short. Each ensemble can be, therefore,
   investigated also if launching several runs.

   Default
       The default value is ``priority_shooting = False``.

.. _user-section-retis-rgen:

Keyword rgen
^^^^^^^^^^^^

.. pyretis-keyword:: rgen string

   Select the function to use to generate the random number used in the
   retis function. That is, (1) the selection of the swap move vs shooting
   or time reversal, (2) detail balance for swap when Stone Skipping or
   Wire Fencing with high acceptance is used.

   Default
       The default value is ``rgen = None``.


.. _user-section-retis-seed:

Keyword seed
^^^^^^^^^^^^

.. pyretis-keyword:: seed integer

   Select the seed for the random number generator to be used in the
   retis function.

   Default
       The default value is ``seed = None``.


.. _user-section-retis-swapfreq:

Keyword swapfreq
^^^^^^^^^^^^^^^^

.. pyretis-keyword:: swapfreq float

   This defines how often we perform swapping moves.
   This gives the percentage of swapping moves in the simulation,
   e.g.: ``swapfreq = 0.5`` corresponds to 50% swapping moves, the 50% other
   moves will be :ref:`TIS moves <user-section-tis>`.

   Default
       No default, this setting **must** be specified.

.. _user-section-retis-swapsimul:

Keyword swapsimul
^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: swapsimul boolean

   If ``True`` several swaps are performed at the same
   time, that is we attempt to swap several pairs of path
   ensembles. If this is ``False``, we will only attempt to
   swap one pair.

   Default
       No default, this setting **must** be specified.
