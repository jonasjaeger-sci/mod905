.. _examples-pso:

Particle Swarm Optimization
===========================

In this example, we will perform a task that |pyretis| is **NOT** intended
to do. We will optimize a function using a method called
`particle swarm optimization <https://en.wikipedia.org/wiki/Particle_swarm_optimization>`_
and the purpose of this example is to illustrate how
the |pyretis| library can be used to set up special simulations.

The function we will optimize is the `Ackley function <https://www.sfu.ca/~ssurjano/ackley.html>`_
which is relatively complex with many local minima as illustrated in the figure below.
We will set up our optimization
by first creating a *new potential* and a *new engine* to do the job for us.


.. figure:: /_static/img/pso_illustration.png
    :class: img-responsive center-block
    :alt: Illustration of particle swarm optimization
    :align: center

    Illustration of the particle swarm optimization method.
    The particles (black circles)
    start in a random initial configuration as shown in the left image
    and search for the global minimum. All particles keep a record of the
    smallest value they have seen so far and they communicate this
    estimate to the other particles. Thus, the current best estimate based
    on all the particles is known, and the particles are drawn towards this
    position, but also towards their own best estimate. In the middle
    image, the positions have been updated and the particles have moved. After
    some more steps, the particles converge towards the global minimum at (0, 0).
    However, convergence is not guaranteed.


.. contents:: Table of Contents
   :local:

Creating the Ackley function as a PotentialFunction
---------------------------------------------------

Here, we will create the function we will optimize as a
:py:class:`.PotentialFunction`. This can be done by creating a new
file ``ackley.py`` and adding the following code:

.. literalinclude:: /_static/examples/pso-example/ackley.py
   :language: python
   :lines: 5-39

If you add:

.. literalinclude:: /_static/examples/pso-example/ackley.py
   :language: python
   :lines: 42-52

you can also plot the potential by running:

.. code-block:: pyretis

   python ackley.py

Creating a custom engine for particle swarm optimization
--------------------------------------------------------

Here, we will create a new engine for performing the "dynamics" in the
particle swarm optimization. The equations of motion are

* For the velocity :math:`v_i` of particle *i*:

  .. math::

     v_i(t + 1) = \omega v_i(t) + c_1 r_1 (x_i^\ast - x_i(t)) + c_2 r_2 (x^\dagger - x_i(t))

  where :math:`\omega` is the co-called inertia weight (a parameter), :math:`c_1` and
  :math:`c_2` are acceleration coefficients (parameters), :math:`r_1` and :math:`r_2` are
  random numbers drawn from a uniform distribution between 0 and 1, :math:`x_i^\ast` is
  particle *i*'s best estimate of the minimum of the potential and :math:`x^\dagger` is
  the global best estimate.

* For the position :math:`x_i` of particle *i*:

  .. math::

     x_i(t + 1) = x_i(t) + v_i(t)

In both equations, :math:`t` is the current step and :math:`t+1` is the next step.
Before updating the positions, the potential energies for the individual particles
are obtained and :math:`x_i^\ast` and :math:`x^\dagger` are updated.

These equations are similar to the equations used by the MD integrators in
|pyretis|, and the engine can be implemented as a sub-class of the
:py:class:`.MDEngine` class. Create a new file name ``psoengine.py``
and add the following code:


.. literalinclude:: /_static/examples/pso-example/psoengine.py
   :language: python


Putting it all together and running the optimization
----------------------------------------------------

We will now create a simulation for performing the optimization.
First we need to import the new potential function and the new
engine we have created:


.. literalinclude:: /_static/examples/pso-example/pso_run.py
   :language: python
   :lines: 6-11

We next use this to define a method for setting everything up
for us:

.. literalinclude:: /_static/examples/pso-example/pso_run.py
   :language: python
   :lines: 16-48

Finally, we can make a method to execute the optimization:

.. literalinclude:: /_static/examples/pso-example/pso_run.py
   :language: python
   :lines: 51-58

Which is used as follows:

.. code-block:: python

   if __name__ == '__main__':
       main()

Execute the script a couple of time (save the code above in a
new file, say ``pso_run.py``) and execute it using:

.. code-block:: pyretis

   python pso_run.py

Adding plotting and animation
-----------------------------

If you wish, you can also animate the results/optimization process.
First modify the imports as follows:

.. literalinclude:: /_static/examples/pso-example/pso_run.py
   :language: python
   :lines: 6-13

And add the following methods:

.. literalinclude:: /_static/examples/pso-example/pso_run.py
   :language: python
   :lines: 61-110
