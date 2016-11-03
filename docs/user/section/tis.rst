.. _user-section-tis:

The TIS section
===============

The TIS section defines settings for TIS simulations.

Example:

.. code-block:: rst

    TIS settings
    ------------
    allowmaxlength = False
    freq = 0.5
    zero_momentum = False
    initial_path = 'kick'
    seed = 1
    aimless = True
    maxlength = 20000
    sigma_v = -1
    rescale_energy = False

The keywords that can be specified are:

* ``allowmaxlength``:

* ``freq``: This defines how often we perform shooting moves. This
  corresponds to the percentage of the TIS moves that should be
  shooting moves. E.g. if ``freq = 0.5`` then 50% of the TIS moves
  are shooting moves. Note that if you are running a retis simulation,
  then the precentage of TIS moves will be modified by the precentage
  of swapping moves, e.g. the precentage of shooting moves will then
  be given by :math:`(1 - swapfreq) \times freq`.

* ``zero_momentum``: 

* ``initial_path``: This determines how we initiate the path ensembles.

* ``seed``: This integer is a seed for the random number generator
  used in the TIS algorithm (e.g. when selecting a shooting point).

* ``aimless``:

* ``maxlength``: This determines the maximum length of the paths generated.
  Generally, this should be set so that only a few paths are longer than
  this value.

* ``sigma_v``:

* ``rescale_energy``:
