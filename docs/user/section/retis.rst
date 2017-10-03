.. _user-section-retis:

The RETIS section
=================

Specifies settings for RETIS simulations. Note that
the section for :ref:`TIS <user-section-tis>` also needs
to be defined for a RETIS simulation.

.. pyretis-input-example:: RETIS

   .. code-block:: rst

       RETIS settings
       --------------
       swapfreq = 0.5
       relative_shoots = None
       nullmoves = True
       swapsimul = True

Keywords for the RETIS section
------------------------------

The following keywords can be set for the RETIS section:

.. |retis_swapfreq| replace:: :ref:`swapfreq <user-section-retis-swapfreq>`

.. |retis_relatives| replace:: :ref:`relative_shoots <user-section-retis-relatives>`

.. |retis_nullmoves| replace:: :ref:`nullmoves <user-section-retis-nullmoves>`

.. |retis_swapsimul| replace:: :ref:`swapsimul <user-section-retis-swapsimul>`

.. _table-retis-keywords:

.. table:: Keywords for the RETIS section.
   :class: table-striped

   +-------------------+------------------------------------------------------+
   | Keyword           | Description                                          |
   +===================+======================================================+
   | |retis_swapfreq|  | Defines how often we perform swapping moves.         |
   +-------------------+------------------------------------------------------+
   | |retis_relatives| | Selects and defines relative shooting.               |
   +-------------------+------------------------------------------------------+
   | |retis_nullmoves| | Determines if we do null moves or not.               |
   +-------------------+------------------------------------------------------+
   | |retis_swapsimul| | Determines if we swap multiple path ensebles at the  |
   |                   | same time or not.                                    |
   +-------------------+------------------------------------------------------+


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

.. _user-section-retis-nullmoves:

Keyword nullmoves
^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: nullmoves boolean

   If ``True`` we perform null moves in the ensembles
   not included in a swapping move. Otherwise, no move is done in these
   ensembles.

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
