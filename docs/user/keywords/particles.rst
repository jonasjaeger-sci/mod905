.. _user-keywords-particles:

particles
----------
Define how we initiate particles.

Example:

.. code-block:: python

    particles-position = {'file': 'initial.gro'}

    particles-velocity = {'generate': 'maxwell',
                          'set-temperature': 2.0,
                          'momentum': True,
                          'seed': 0}

    particle-mass = {'Ar': 1.0}
