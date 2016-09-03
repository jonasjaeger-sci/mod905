.. _user-section-integrator:

The integrator section
----------------------
Specify which integrator to use for the dynamics.
The integrator is responsible for integrating Newton's
equations of motion numerically in pyretis.

The integrator is specified by providing a ``class`` for the integrator
and a ``timestep`` and these two settings specify the type of integrator
to use and it's time step in *internal units*.
Some integrators might require additional settings
as discussed below.

Integrator setting example:

.. code-block:: rst 

    Integrator
    ----------
    class = VelocityVerlet
    timestep = 0.002

pyretis supports different integrators which are selected by setting
the ``class`` value as show in the example above. The supported integrators
are:

* :ref:`Langevin <user-section-integrator-langevin>`
* :ref:`Verlet <user-section-integrator-verlet>`
* :ref:`Velocity Verlet <user-section-integrator-velocity-verlet>`

which are described in detail below.

In addition, it is possible to extend pyretis with user defined
integrators written in for instance python, fortran or c.
Such integrators can be requested by
specifying some additional keywords as described in detail
in the section 
on :ref:`user defined integrators <user-section-integrator-user-defined>`


.. _user-section-integrator-langevin:

Langevin
~~~~~~~~

This is a stochastic (Brownian) integrator and a description of 
the implementation can be found in e.g. [ALLEN]_. The integrator
is fully specified as follows:

.. code-block:: rst 

    Integrator
    ----------
    class = Langevin # select Langevin integrator
    timestep = 0.002  # time step for the integration
    gamma = 0.3  # set gamma value,
    seed = 0  # set seed for random value generator used
    high_friction = False  # are we in the high friction limit?

**Required settings:**

* ``class``: Selects the integrator (here: ``Langevin``).

* ``timestep``: Integration time step (:math:`\Delta t`).

* ``gamma``: Parameter (:math:`\gamma`) for the integration
  (see detailed description below).


**Optional settings:**

* ``seed``: seed for the stochastic integrator (default: ``0``)
* ``high_friction``: select high friction or low friction
  limit (default: ``True``)

The optional setting ``high_friction`` determines how the equations
of motion are integrated, either in the

* high friction limit (``high_friction`` is ``True``),

  .. math::

     \mathbf{r}(t + \Delta t) = \mathbf{r}(t) + \gamma \Delta t \mathbf{f}(t)/m + \delta \mathbf{r},

  where :math:`\mathbf{f}(t)` is the force and the
  velocities (:math:`\delta \mathbf{r}`) are drawn from a
  normal distribution,

* or in the low friction limit (``high_friction`` is ``False``),

  .. math::

     \mathbf{r}(t + \Delta t) = \mathbf{r}(t) + c_1 \Delta t  \mathbf{v}(t) + c_2 \mathbf{a}(t) \Delta t^2 + \delta \mathbf{r},

  where,

  .. math::

     \mathbf{v}(r + \Delta t) = c_0 \mathbf{v}(t) + (c_1-c_2) \Delta t \mathbf{a}(t) + c_2 \Delta t \mathbf{a}(t+\Delta t) + \delta \mathbf{v},

  and :math:`c_0 = \text{e}^{-\gamma \Delta t}`,
  :math:`c_1 = (1 - c_0) / ( \gamma \Delta t)` and
  :math:`c_2 = (1 - c_1) / ( \gamma \Delta t)`. In this case,
  :math:`\delta \mathbf{r}` and :math:`\delta \mathbf{v}` are
  obtained as stochastic variables.


.. _user-section-integrator-verlet:

Verlet
~~~~~~

The integrator is specified by specifying the integrator class ``Verlet`` and
the time step:

.. code-block:: rst 

   Integrator
   ----------
   class = Verlet # select Verlet integrator
   timestep = 0.002  # time step for the integration

**Required settings:**

* ``class``: Selects the integrator (``Verlet``).

* ``timestep``: Integration time step.


.. _user-section-integrator-velocity-verlet:

Velocity Verlet
~~~~~~~~~~~~~~~

The integrator is specified by specifying the integrator
class ``VelocityVerlet`` and the time step:

.. code-block:: rst 

   Integrator
   ----------
   class = VelocityVerlet # select Velocity Verlet integrator
   timestep = 0.002  # time step for the integration

**Required settings:**

* ``class``: Selects the integrator (``VelocityVerlet``).

* ``timestep``: Integration time step.


.. _user-section-integrator-user-defined:

User defined integrators
~~~~~~~~~~~~~~~~~~~~~~~~

User defined integrators are specified in python modules that
pyretis can load. 

.. code-block:: rst 

    Integrator
    ----------
    class = VelocityVerletF # select integrator
    module = vvintegratorf.py # module defining integrator
    timestep = 0.002 # arguments for the integrator
    argument = 10.0 # additional argument for the integrator

**Required settings:**

* ``class``: selects the integrator. Note that this is case sensitive
  in this case.

* ``module``: specify the external module where the class specified with
  ``class`` is given. This module must be placed in the same folder as
  you are running pyretis in or you must specify the full path to the module.


References
~~~~~~~~~~

.. [ALLEN] M. P. Allen and D. J. Tildesley,
           Computer Simulation of Liquids,
           1989, Oxford University Press.
