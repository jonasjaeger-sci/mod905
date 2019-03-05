.. _user-section-tis:

The TIS section
===============

The ``TIS`` section defines settings for TIS and RETIS simulations.

.. pyretis-input-example:: TIS

   .. code-block:: rst

       TIS settings
       ------------
       allowmaxlength = False
       freq = 0.5
       zero_momentum = False
       seed = 1
       aimless = True
       maxlength = 20000
       sigma_v = -1
       rescale_energy = False


Keywords for the TIS section
----------------------------

The following keywords can be set for the TIS section:

.. |tis_freq| replace:: :ref:`freq <user-section-tis-freq>`

.. |tis_maxlength| replace:: :ref:`maxlength <user-section-tis-maxlength>`

.. |tis_allowmaxlength| replace:: :ref:`allowmaxlength <user-section-tis-allowmaxlength>`

.. |tis_momentum| replace:: :ref:`zero_momentum <user-section-tis-zero-momentum>`

.. |tis_seed| replace:: :ref:`seed <user-section-tis-seed>`

.. |tis_aimless| replace:: :ref:`aimless <user-section-tis-aimless>`

.. |tis_sigmav| replace:: :ref:`sigma_v <user-section-tis-sigma-v>`

.. |tis_renergy| replace:: :ref:`rescale_energy <user-section-tis-rescale-energy>`

.. _table-tis-keywords:

.. table:: Keywords for the TIS section
   :class: table-striped table-hover

   +----------------------+---------------------------------------------------+
   | Keyword              | Description                                       |
   +======================+===================================================+
   | |tis_freq|           | Define how often time reversal moves are          |
   |                      | performed.                                        |
   +----------------------+---------------------------------------------------+
   | |tis_maxlength|      | Sets the maximum length of the paths generated.   |
   +----------------------+---------------------------------------------------+
   | |tis_allowmaxlength| | Specify if the maximum length should be           |
   |                      | determined randomly.                              |
   +----------------------+---------------------------------------------------+
   | |tis_momentum|       | Specify is momentum should be set to zero when    |
   |                      | shooting.                                         |
   +----------------------+---------------------------------------------------+
   | |tis_seed|           | Set a seed for the random number generator.       |
   +----------------------+---------------------------------------------------+
   | |tis_aimless|        | Specify is the shooting is aimless or not.        |
   +----------------------+---------------------------------------------------+
   | |tis_sigmav|         | Set standard deviations for the random            |
   |                      | velocity generation                               |
   +----------------------+---------------------------------------------------+
   | |tis_renergy|        | Selects re-scaling of velocities.                 |
   +----------------------+---------------------------------------------------+


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


.. _user-section-tis-maxlength:

Keyword maxlength
^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: maxlength integer

   This determines the maximum length of the paths generated.
   Generally, this should be set so that only a few paths are longer than
   this value.

   Default
       No default, this keyword **must** be specified.


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


.. _user-section-tis-zero-momentum:

Keyword zero_momentum
^^^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: zero_momentum boolean

   If this keyword is set to ``True``, then
   the momentum of the system is set to zero after creating random
   velocities for shooting. If ``False``, this is not done.

   Default
       The default is ``zero_momentum = False``.


.. _user-section-tis-initial-path:

.. _user-section-tis-seed:

Keyword seed
^^^^^^^^^^^^

.. pyretis-keyword:: seed integer

   This integer is a seed for the random number generator
   used in the TIS algorithm (e.g. when selecting a shooting point).

   Default
       The default is ``seed = 0``.


.. _user-section-tis-aimless:

Keyword aimless
^^^^^^^^^^^^^^^

.. pyretis-keyword:: aimless boolean

   Determines if we are to do aimless shooting or not. If this is set to
   ``False``, then standard deviations for velocity generation can be set
   by the :ref:`keyword sigma_v <user-section-tis-sigma-v>`.

   Default
       The default is ``aimless = True``.


.. _user-section-tis-sigma-v:

Keyword sigma_v
^^^^^^^^^^^^^^^

.. pyretis-keyword:: sigma_v float

   This keyword can be used to set standard deviations for the
   random velocity generation if the
   :ref:`keyword aimless <user-section-tis-aimless>` is set to ``False``.

   Default
       The default value is ``sigma_v = -1``.

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
