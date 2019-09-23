.. _user-section-tis:

The TIS section
===============

The ``TIS`` section defines settings for TIS and RETIS simulations.

.. pyretis-input-example:: TIS

   .. code-block:: rst

       TIS settings
       ------------
       aimless = True
       allowmaxlength = False
       freq = 0.5
       high_accept = True
       interface_sour = None
       maxlength = 20000
       n_jumps = 8
       rgen = rgen
       rescale_energy = False
       seed = 1
       shooting_move = 'sh'
       shooting_moves = []
       sigma_v = -1
       zero_momentum = False

Keywords for the TIS section
----------------------------

The following keywords can be set for the TIS section:

.. |tis_aimless| replace:: :ref:`aimless <user-section-tis-aimless>`

.. |tis_allowmaxlength| replace:: :ref:`allowmaxlength <user-section-tis-allowmaxlength>`

.. |tis_freq| replace:: :ref:`freq <user-section-tis-freq>`

.. |tis_high_accept| replace:: :ref:`high_accept <user-section-tis-high-accept>`

.. |tis_interface_sour| replace:: :ref:`interface_sour <user-section-tis-interface-sour>`

.. |tis_maxlength| replace:: :ref:`maxlength <user-section-tis-maxlength>`

.. |tis_n_jumps| replace:: :ref:`n_jumps <user-section-tis-n-jumps>`

.. |tis_rgen| replace:: :ref:`rgen <user-section-tis-rgen>`

.. |tis_seed| replace:: :ref:`seed <user-section-tis-seed>`

.. |tis_shooting_move| replace:: :ref:`shooting_move <user-section-tis-shooting-move>`

.. |tis_shooting_moves| replace:: :ref:`shooting_moves <user-section-tis-shooting-moves>`

.. |tis_sigma_v| replace:: :ref:`sigma_v <user-section-tis-sigma-v>`

.. |tis_rescale_energy| replace:: :ref:`rescale_energy <user-section-tis-rescale-energy>`

.. |tis_zero_momentum| replace:: :ref:`zero_momentum <user-section-tis-zero-momentum>`

.. _table-tis-keywords:

.. table:: Keywords for the TIS section
   :class: table-striped table-hover

   +----------------------+---------------------------------------------------+
   | Keyword              | Description                                       |
   +======================+===================================================+
   | |tis_aimless|        | Specify is the shooting is aimless or not.        |
   +----------------------+---------------------------------------------------+
   | |tis_allowmaxlength| | Specify if the maximum length should be           |
   |                      | determined randomly.                              |
   +----------------------+---------------------------------------------------+
   | |tis_freq|           | Define how often time reversal moves are          |
   |                      | performed.                                        |
   +----------------------+---------------------------------------------------+
   | |tis_interface_sour| | Sets the position of SOUR for Web Throwing.       |
   +----------------------+---------------------------------------------------+
   | |tis_high_accept|    | Set the Stone Skipping version to use.            |
   +----------------------+---------------------------------------------------+
   | |tis_maxlength|      | Set the maximum length of the paths generated.    |
   +----------------------+---------------------------------------------------+
   | |tis_n_jumps|        | Set the number of jumps for SS and WT moves.      |
   +----------------------+---------------------------------------------------+
   | |tis_rgen|           | Set the random number generator to use.           |
   +----------------------+---------------------------------------------------+
   | |tis_seed|           | Set a seed for the random number generator.       |
   +----------------------+---------------------------------------------------+
   | |tis_rescale_energy| | Selects re-scaling of velocities.                 |
   +----------------------+---------------------------------------------------+
   | |tis_shooting_move|  | Set the MC shooting moves for the TIS ensemble.   |
   +----------------------+---------------------------------------------------+
   | |tis_shooting_moves| | Set the MC shooting moves in each ensemble.       |
   +----------------------+---------------------------------------------------+
   | |tis_sigma_v|        | Set standard deviations for the random            |
   |                      | velocity generation                               |
   +----------------------+---------------------------------------------------+
   | |tis_zero_momentum|  | Specify is momentum should be set to zero when    |
   |                      | shooting.                                         |
   +----------------------+---------------------------------------------------+


.. _user-section-tis-aimless:

Keyword aimless
^^^^^^^^^^^^^^^

.. pyretis-keyword:: aimless boolean

   Determines if we are to do aimless shooting or not. If this is set to
   ``False``, then standard deviations for velocity generation can be set
   by the :ref:`keyword sigma_v <user-section-tis-sigma-v>`.

   Default
       The default is ``aimless = True``.


.. _user-section-tis-allowmaxlength:

Keyword allowmaxlength
^^^^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: allowmaxlength boolean

   If ``True``, the maximum length for all paths are set to
   the value given by the keyword ``maxlength``. If ``False``,
   the maximum length is determined at random based on the length
   of the current path we are shooting from.

   Default
       The default is ``allowmaxlength = False``.


.. _user-section-tis-freq:

Keyword freq
^^^^^^^^^^^^

.. pyretis-keyword:: freq float

   This defines how often time reversal moves are performed:
   It corresponds to the percentage of the TIS moves that should be
   shooting moves. E.g. if ``freq = 0.5`` then 50% of the TIS moves
   are time reversal. Note that if you are running a RETIS simulation,
   then the percentage of TIS moves will be modified by the percentage
   of swapping moves, e.g. the percentage of shooting moves will then
   be given by :math:`(1 - swapfreq) \times freq`.

   Default
       No default, this keyword **must** be specified.


.. _user-section-tis-interface-sour:

Keyword interface_sour
^^^^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: interface_sour float

   This defines the position of the SOUR interface for Web Throwing. 
   It HAS to be smaller then the interface defining the ensemble where
   WT is used. Note that an improper selection of interface_sour will 
   hinder the sampling efficiency.

   Default
       No default, this keyword **must** be specified if WT is used.


.. _user-section-tis-high-accept:

Keyword high_accept
^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: high_accept boolean

   This select the version of Stone Skipping that is going to be used.
   Potential High Accept should always been choosen since it is more
   efficient. Note that this version DOES NOT ALLOW (in the present 
   implementation, due to detailed balance) to have multiple shooting
   methods used in the same ensemble. 

   Default
       The default is ``high_accept = True``.


.. _user-section-tis-maxlength:

Keyword maxlength
^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: maxlength integer

   This determines the maximum length of the paths generated.
   Generally, this should be set so that only a few paths are longer than
   this value.

   Default
       No default, this keyword **must** be specified.


.. _user-section-tis-n-jumps:

Keyword n_jumps
^^^^^^^^^^^^^^^

.. pyretis-keyword:: n_jumps integer

   The number of jumps for Stone Skipping and of web for Web Throwing. 
   The number is the same for all the ensembles. 

   Default
       No default, this keyword **must** be specified if Stone Skipping
       or Web Throwing are going to be used.


.. _user-section-tis-rgen:

Keyword rgen
^^^^^^^^^^^^

.. pyretis-keyword:: rgen string

   Selection of the random number generator to use. The option allows
   the use of bias random number generator (mock) or an easy implementation
   of more advanced random number generators. 

   Default
       The default is ``rgen = rgen``.


.. _user-section-tis-rescale-energy:

Keyword rescale_energy
^^^^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: rescale_energy float or boolean

   If this keyword is set to a number, then
   the velocities are re-scaled so that the total energy is equal
   to the given number. This is useful for performing NVE simulations.
   If the keyword is set to ``False``, then the energies will not be
   re-scaled.

   Default
       The default value is ``rescale_energy = False``.

       
.. _user-section-tis-seed:

Keyword seed
^^^^^^^^^^^^

.. pyretis-keyword:: seed integer

   This integer is a seed for the random number generator
   used in the TIS algorithm (e.g. when selecting a shooting point).

   Default
       The default is ``seed = 0``.


.. _user-section-tis-shooting-move:

Keyword shooting_move
^^^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: shooting move strings

   The string contains the flag for the selected ensemble, that determines the shooting move to be used (`` `` or 'sh' for shooting, 'ss' for Stone Skipping and 'wt' for Web Throwing.

   Default
       The default value is ``sh``.


.. _user-section-tis-shooting-moves:

Keyword shooting_moves
^^^^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: shooting moves list of strings

   The list contain the flag, for each ensemble, that determines the shooting
   move to use (`` `` or 'sh' for shooting, 'ss' for Stone Skipping and 'wt' for Web Throwing.

   Default
       The default value is ``[]``.


.. _user-section-tis-sigma-v:

Keyword sigma_v
^^^^^^^^^^^^^^^

.. pyretis-keyword:: sigma_v float

   This keyword can be used to set standard deviations for the
   random velocity generation if the
   :ref:`keyword aimless <user-section-tis-aimless>` is set to ``False``.

   Default
       The default value is ``sigma_v = -1``.


.. _user-section-tis-zero-momentum:

Keyword zero_momentum
^^^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: zero_momentum boolean

   If this keyword is set to ``True``, then
   the momentum of the system is set to zero after creating random
   velocities for shooting. If ``False``, this is not done.

   Default
       The default is ``zero_momentum = False``.


