Specification for integrators
=============================

Integrators are used to propagate the equations of motion or alter the state of the system
in some way. pyretis assumes that it can call various methods of the integrators.

Modify the velocities
---------------------

This method is used to draw random velocities, typically when
performing the shooting move. The method is called as follows

.. code-block:: python

   dek, _, = integrator.modify_velocities(
           system,
           rgen,
           sigma_v=tis_settings['sigma_v'],
           aimless=tis_settings['aimless'],
           momentum=tis_settings['zero_momentum'],
           rescale=tis_settings['rescale_energy'])

Parameters
~~~~~~~~~~

* ``system`` : object like :py:class:`pyretis.core.system.System`,
  System is used here since we need access to the particles.

* ``rgen`` : object like :py:class:`pyretis.core.random_gen.RandomGenerator`,
  A random generator which we can use to generate velocities, if needed.

* ``sigma_v`` : numpy.array,
  These values can be used to set a standard deviation (one
  for each particle) for generating the velocities.

* ``aimless`` : boolean, optional,
  Determines if we should do aimless shooting or not.

* ``momentum`` : boolean, optional,
  If True, we reset the linear momentum to zero after generating.

* ``rescale`` : float, optional,
  In some NVE simulations, we may wish to rescale the energy to
  a fixed value. If ``rescale`` is a float > 0, we will rescale
  the energy (after modification of the velocities) to match the
  given float.


Return values
~~~~~~~~~~~~~

* ``dek`` : float,
  The change in the kinetic energy

* ``kin_new`` : float,
  The new kinetic energy

And it should **update the velocities of the particles**.

Example -- Internal integrators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For internal integrators, the current implementation is as follows:

.. literalinclude:: ../../pyretis/integrators/integrator.py
   :pyobject: Integrator.modify_velocities


Calculating the order parameter
-------------------------------

.. code-block:: python

   orderp = integrator.calculate_order(order_function, system)


Propagating the equations of motion
-----------------------------------

.. code-block:: python

   success_back, _ = integrator.propagate(path_back, system, order_function,
                                         interfaces, reverse=True)

   success_forw, _ = integrator.propagate(path_forw, system, order_function,
                                          interfaces, reverse=False)


Performing a single integration step
------------------------------------

.. code-block:: python

   integrator.integration_step(system)

