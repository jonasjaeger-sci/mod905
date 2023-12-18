.. _examples-openmm:

Running a PyRETIS simulation with OpenMM
========================================

In this example we will show the interface between ``OpenMM`` and |pyretis|. 

First we will have to generate an file with a OpenMM ``Simulation`` object. We use the online tool `OpenMM Script Builder <http://builder.openmm.org/>`_ to generate the
example with this :download:`pdb</_static/engine-examples/input.pdb>` of 2 water molecules. 

.. literalinclude:: /_static/engine-examples/openmm_sim.py


With this ``simulation`` object we can now construct the needed rst options in the engine section:

.. literalinclude:: /_static/engine-examples/openmm_retis.rst    
   :language: rst
   :lines: 14-20

Here we say that:
  * The engine ``type`` is ``openmm``, to tell |pyretis| it is has a special
    system representation.
  * The engine ``class`` is also ``openmm`` to tell |pyretis| we want to use the
    ``OpenMM`` engine.
  * The ``openmm_module`` where we want to load the simulation from, here it is ``openmm_sim.py``.
  * And the name of the ``openmm_simulation`` object in that file, in this case ``simulation``.

Finally we give the number of ``subcycles``, which indicates how many MD-steps
``OpenMM`` does before we ask for another frame.  This should be relatively high when
using GPUs, as it dictates how often we have to communicate with the GPU. However, keep in mind that this also lowers the time-resolution of your |pyretis| simulation. 

After this, it is run as a regular |pyretis| simulation, using ``pyretisrun``

.. code-block:: pyretis

   pyretisrun -i openmm_retis.rst -p
