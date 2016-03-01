.. _user-keywords-integrator:

integrator
----------
Specify which integrator to use for the dynamics.
The integrator is responsible for integrating Newton's
equations of motion numerically in pyretis.

The integrator is specified by providing a ``name`` for the integrator
and a ``timestep``:


Example:

.. code-block:: python

   integrator = {'name': 'VelocityVerlet',
                 'timestep': 0.002}

pyretis supports different integrators which are selected by setting
the ``name`` value as show in the example above. The supported integrators
are:

* :ref:`Langevin <user-keywords-integrator-langevin>`
* :ref:`Verlet <user-keywords-integrator-verlet>`
* :ref:`Velocity Verlet <user-keywords-integrator-velocity-verlet>`

which are described in detail below.

.. _user-keywords-integrator-langevin:

Langevin
........

This is a stochastic (Brownian) integrator and a description of the implementation
can be found in e.g. [ALLEN]_. The integrator is fully specified as follows:

.. code-block:: python

   integrator = {'name': 'Langevin', # select Langevin integrator
                 'timestep': 0.002,  # time step for the integration
                 'gamma': 0.3,  # set gamma value,
                 'seed': 0,  # set seed for random value generator used
                 'high-friction': False}  # are we in the high friction limit?

**Required settings:**

* ``name``: Selects the integrator (here: ``Langevin``).

* ``timestep``: Integration time step (:math:`\delta t`).

* ``gamma``: Prameter (:math:`\gamma`) for the integration
  (see detailed description below).


**Optional settings:**

* ``seed``: seed for the stochastic integrator (default: ``0``)
* ``high-friction``: select high friction or low friction limit (default: ``True``)

The optional ``high-fiction`` determines how the equations of motion
are integrated, either in the

* high friction limit

  .. math::

     \mathbf{r}(t + \delta t) = \mathbf{r}(t) + \gamma \delta t \mathbf{f}(t)/m + \delta \mathbf{r},

  where :math:`\mathbf{f}(t)` is the force and the velocities (:math:`\delta \mathbf{r}`)
  are drawn from a normal distribution,

* or in the low friction limit,

  .. math::

     \mathbf{r}(t + \delta t) = \mathbf{r}(t) + c_1 \delta t  \mathbf{v}(t) + c_2 \mathbf{a}(t) \delta t^2 + \delta \mathbf{r},

  where,

  .. math::

     \mathbf{v}(r + \delta t) = c_0 \mathbf{v}(t) + (c_1-c_2) \delta t \mathbf{a}(t) + c_2 \delta t \mathbf{a}(t+\delta t) + \delta \mathbf{v},

  and :math:`c_0 = \text{e}^{-\gamma \text{d} t}`,
  :math:`c_1 = (1 - c_0) / ( \gamma \text{d} t)` and
  :math:`c_2 = (1 - c_1) / ( \gamma \text{d} t)`. In this case,
  :math:`\delta \mathbf{r}` and :math:`\delta \mathbf{v}` are
  obtained as stochastic variables.


.. _user-keywords-integrator-verlet:

Verlet
......

The integrator is specified by specifying the integrator name ``Verlet`` and
the time step:

.. code-block:: python

   integrator = {'name': 'Verlet', # select Verlet integrator
                 'timestep': 0.002}  # time step for the integration

**Required settings:**

* ``name``: Selects the integrator (``Verlet``).

* ``timestep``: Integration time step.


.. _user-keywords-integrator-velocity-verlet:

Velocity Verlet
...............

The integrator is specified by specifying the integrator name ``VelocityVerlet`` and
the time step:

.. code-block:: python

   integrator = {'name': 'VelocityVerlet', # select Velocity Verlet integrator
                 'timestep': 0.002}  # time step for the integration

**Required settings:**

* ``name``: Selects the integrator (``VelocityVerlet``).

* ``timestep``: Integration time step.

References
~~~~~~~~~~

.. [ALLEN] M. P. Allen and D. J. Tildesley,
           Computer Simulation of Liquids,
           1989, Oxford University Press.
