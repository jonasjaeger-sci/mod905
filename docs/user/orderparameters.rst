.. _user-guide-custom-order:

.. role:: python(code)
    :language: python

|

Creating custom order parameters
================================

Often, you will find the need to create custom order parameters
for your path sampling simulation(s).
In |pyretis|, you can create new order parameters by making use
of the generic :py:class:`.OrderParameter` class defined in the library.
Technically speaking, you will have to sub-class :py:class:`.OrderParameter`
and implement a method (like :py:meth:`.OrderParameter.calculate`)
which actually calculates the order parameter.
In addition, you can define additional collective variables to
be calculated.

The short version of what we need to do
in order to create a new order parameter is:

1. Create a new Python class which is a sub-class of :py:class:`.OrderParameter`

2. Write a method to initialise this class, that is the ``__init__`` method.
   This method will be called when |pyretis| is setting up a new simulation
   and it will be fed variables from the |pyretis| input file.

3. Write a method to calculate the order parameter. This should take in a
   :py:class:`.System` object as its argument.

4. Setting up the input file to use the new order parameter.

|

Example: Creating a new order parameter
---------------------------------------

Let us see how this can be done in practice. To be concrete,
we will consider an order parameter defined as follows:
The distance between a particular particle and a plane
positioned somewhere along the x-axis.

|

Step 1 and 2: Sub-classing OrderParameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to define a new class to use with |pyretis|, we import
`numpy <http://www.numpy.org/>`_ and the :py:class:`.OrderParameter` class:

.. literalinclude:: /_static/orderparameter-examples/orderparameter1.py
   :language: python
   :lines: 8-9

And we define a class, representing our new order parameter:

.. literalinclude:: /_static/orderparameter-examples/orderparameter1.py
   :language: python
   :lines: 12-35

Here, we are initialising the class by storing two variables ``index``
and ``plane_position`` which identifies the particle we will consider
and the location of the plane.
In addition, we add some more information when we initialise the parent class (the line
calling :python:`super().__init__`). This is simply following the convention
defined by :py:class:`.OrderParameter`.

.. warning::

   If the order parameter you are defining depends explicitly on the velocity
   (i.e. the direction so that it is not symmetric under time reversal) you
   should mark the order parameter as being velocity dependent.
   This can be done by setting the ``velocity``
   argument to ``True`` while initiating the order parameter:

   .. code-block:: python

      super().__init__(description='Description', velocity=True)

|

Step 3: Creating a method for calculating the order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Next, we will write a method for actually calculating the
order parameter. In order to do this, we need to know how we
can interact with the :py:class:`.System` object, and this
might be a good point to read
the :ref:`introduction to the API <user-guide-intro-api>`.
In particular, we will mostly be interacting with the
:ref:`Particles <user-guide-intro-api-particles>` class which we
can access using :py:attr:`.System.particles`.

Typically, our calculation of the order parameter
will correspond to one of the two following cases:

*  We want to access the positions of the particles directly and
   calculate the order parameter. Here, just a new method to
   the ``PlaneDistanceX`` class we are creating as follows:

   .. literalinclude:: /_static/orderparameter-examples/orderparameter1.py
      :language: python
      :lines: 37-41

   Here, we are making use of the index and position of the
   plane which we stored previously. Further, we
   are using the :py:attr:`.System.particles` object in order
   to access the positions. Finally, we are returning the order
   parameter. In this particular case, we return the negative of
   the distance, so that the order parameter will increase when
   we are approaching the place.

*  We are using an external engine (e.g. GROMACS) and we just want
   to reference the file containing the current configuration, and pass
   this file reference to another external library or program.

   Here, we will make use of some external tools to obtain the
   order parameter, for simplicity, let us here make use of
   the `mdtraj <http://mdtraj.org/>`_ library. First, at the top
   of your file, add the import of this library:

   .. literalinclude:: /_static/orderparameter-examples/orderparameter2.py
      :language: python
      :lines: 8-8

   In order to access the
   file containing the configuration, we make use of the
   :py:attr:`.ParticlesExt.config` attribute. Add the
   following method to the ``PlaneDistanceX`` class:

   .. literalinclude:: /_static/orderparameter-examples/orderparameter2.py
      :language: python
      :lines: 37-41

   Note that the method ``some_function_to_obtain_order`` has not been
   defined here and you will have to define his method yourself in order
   to complete the example.

|

Step 4: Making use of the new order parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We make use of the new order parameter by adding the
:ref:`Orderparameter section <user-section-orderparameter>`
to the input file:

.. code-block:: rst

   Orderparameter
   --------------
   class = PlaneDistanceX
   module = orderparameter1.py
   index = 0
   plane_position = 1.0

As you can see, we specify the following:

1. The name of the order parameter class.

2. The name of the file where we have stored the new class.

3. The value for the ``index`` parameter of the order parameter.

4. The value for the ``plane_position`` parameter of the order parameter.
