.. _examples-permeability:

Studying permeability with a PyRETIS simulation.
================================================

This example will show how to set up a permeability simulation with |pyretis|.
For further details on the derivation of the formulas and description of the
monte-carlo moves, please read and cite the permeability form (RE)TIS paper [1]_. 

This example will use 3 non-interacting particles on a :download:`flat potential</_static/examples/permeability/flat-potential.py>`. 
It will walk trough this :download:`retis_perm.rst</_static/examples/permeability/retis_perm.rst>`, with 
this :download:`initial.xyz</_static/examples/permeability/initial.xyz>`.

New options simulation settings.
-------------------------------------
The ``Simulation`` section has a couple extra options

.. literalinclude:: /_static/examples/permeability/retis_perm.rst
   :language: rst
   :lines: 9-12

Here we have:
  * ``zero_left``; which tells |pyretis| that the [0^-] ensemble has a left
    boundary that is not located at ``-inf``.
  * ``permeability``; if ``True`` any path in the [0^-] ensemble that starts and ends at one of the 
    interfaces is accepted. If ``False``, any path that hits the ``zero_left``
    interface will be rejected. This leads to incorrect flux calculations if
    ``False``. This option also triggers ``pyretisanalyse`` to calculate 
    :math:`\xi`, :math:`\frac{\tau}{dz}` and the permeability.
  * ``swap_attributes``; This is a list of ``path_ensemble`` attributes that
    need to be swapped with every REPEX swap. The newly implemented monte-carlo moves alter the order
    parameter in [0^-]. These altered order parameters need to be swapped with the path whenever the 
    path is exchanged between ensembles.


New options tis settings.
-------------------------
For the new ``mirror`` and ``target-swap`` moves, there are a couple exra
options in the ``TIS`` section.

.. literalinclude:: /_static/examples/permeability/retis_perm.rst
   :language: rst
   :lines: 43-45

Here we have:
  * ``mirror_freq``; This is the probability of attempting the ``mirror`` move in the [0^-]
    ensemble.
  * ``target_freq``; This is the probability of attempting the ``target-swap``
    move in the [0^-] ensemble.
  * ``target_indices``; This is a list of atom indices. The target swap is only
    attempted between these atoms. (Make sure that the original
    orderparameter.index is included in this list)

New orderparameter class
------------------------
This simulation can be run using the new orderparameter class ``Permeability``.
This class is a subclass of position, but alters the output depending on
``mirror_pos``, ``relative`` and ``offset``.

.. literalinclude:: /_static/examples/permeability/retis_perm.rst
   :language: rst
   :lines: 73-80

Here we have:
  * ``dim``; this is the same as for the class ``Position``.
  * ``index``; this is the index of the particle that will be tracked at the
    start of the simulation. This attribute will be changed by the ``target-swap`` move.
  * ``offset``; This orderparameter adds an ``offset`` to the value of
    ``compute_s()`` before wrapping it into the periodic box. This will alter
    the number that comes out of the OP, but they will all fall within the
    boxvectors. If you want to alter the boxvectors instead and don't have access
    to them, you can use ``PermeabilityMinusOffset``, which subtracts the offset
    after wrapping, before returning the value.
  * ``relative``; If ``True`` the output is mapped as a relative to the
    boxvector (between 0 and 1). Both ``offset`` and ``mirror_pos`` should be
    defined as relative to this boxvector as well.
  * ``mirror_pos``; the position of the mirror plane (on the values without
    offset). For the current
    implementation this **must** be set half way between the 0-R and 0-L
    interfaces

The ``Permeability`` classes call the function ``compute_s()`` before applying
the offset and mirror. For the base class this calls the ``compute`` function of
Position. Now, if you want use this with your own OP, you can make a subclass
of ``Permeability`` and override the ``self.compute_s()`` function to return
your own custom OP before applying the offset and mirroring

Output of the new moves
-----------------------

The new moves also lead to some new possible responses in pathensemble.txt.
For the ``mirror`` move, which is an always accept move with the constraint on
``mirror_pos`` this is just a new move type called ``mr``.

For the ``target_swap`` move:
  * A new generated label  ``ts`` to indicate target-swap.
  * A new rejection reason: ``TSS``, which means there are no valid indices to
    swap to.
  * Another new rejection reason ``TSA``, which is a rejection based on the
    monte carlo acceptance.

Another thing that is changed: ``BTS`` (backward to short) is a more common
rejection for the [0^-]<->[0^+] swap. This indicates that the attempted
trajectory in [0^-] ended at the ``L`` interface, so we do not attempt to
extend that into the [0^+] ensemble.

New analysis options
--------------------
Adding ``Permeability = True`` to the ``Simulation`` settings, triggers
``pyretisanalysis`` to also calculate and plot :math:`\xi`, :math:`\frac{\tau}{dz}` and the
Permeability. This follows the formulas as described in the paper [1]_. 
For the calculation of :math:`tau` to work, a reference region has to be
chosen. This is done by adding ``tau_ref_bin`` to the ``Analysis`` section of
the rst. 

.. literalinclude:: /_static/examples/permeability/retis_perm.rst
   :language: rst
   :lines: 148-150


This value can be altered in ``out.rst`` and then rerun, for an analysis with
another reference region. The analysis also plots a 10 bin histogram of the
[0^-] region in order to help the user to select a flat histogram region in this
space.



References
----------

.. [1] Permeability from (RE)TIS, A. Ghysels et al. (manuscript in preperation)
