.. _user-section-retis:

The RETIS section
=================

Specifies settings for RETIS simulations. Note that
the section for :ref:`TIS <user-section-tis>` also needs
to be defined for a RETIS simulation.

Example:

.. code-block:: rst

    RETIS settings
    --------------
    swapfreq = 0.5
    relative_shoots = None
    nullmoves = True
    swapsimul = True

The following keywords can be set:

* ``swapfreq``: This defines how often we perform swapping moves.
  This gives the percentage of swapping moves in the simulation,
  e.g.: ``swapfreq = 0.5`` corresponds to 50% swapping moves.

* ``relative_shoots``: This defines if we perform relative shooting
  moves.

* ``nullmoves``: If ``True`` we perform null moves in the ensembles
  not included in a swapping move. Otherwise no move is done in these
  ensembles.

* ``swapsimul``: If ``True`` several swaps are performed at the same
  time.
