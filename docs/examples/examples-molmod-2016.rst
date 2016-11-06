.. _examples-molmod-2016:

Molecular modeling: Introduction to RETIS
=========================================

In this exercise you will explore how rare transitions
can investigated with the Replica Exchange Transition Interface
Sampling (RETIS) algorithm.

We will consider a simple 1D potential where a particle is moving.
The potential is given by
:math:`V_{\text{pot}} = x^4 - 2x^2` where :math:`x` is the position. 
By plotting this potential, we see that we have two states
(at :math:`x=-1` and :math:`x=1`) separated by a barrier (at :math:`x=0`):

.. figure:: ../img/examples/thumbnails/tis-1d-pot.png
    :class: img-responsive center-block
    :alt: The 1D potential example
    :align: center

    The potential energy as a function of the position. We have two
    stable states separated by a barrier.


In this example we will make use of the pyretis library for carrying
out the RETIS simulations and we will use 
`matplotlib <http://matplotlib.org/>`_ for
plotting some results. These two libraries will have
to be installed before we start:

1. The pyretis library is distributed in the Python Package Index and
   can be installed using pip:[1]_

   .. code-block:: bash
 
       pip install pyretis


   If you want to install the library system wide, you will need
   super-user access (typically a `sudo` will do). If you don't have
   super-user access, pip works well
   with `virtualenv <https://pypi.python.org/pypi/virtualenv>`_ and we refer
   to the virtualenv user guide for more information about setting this up. [2]_
   
   Note: If you have a previous installation of the library, it can
   be upgraded using

   .. code-block:: bash

       pip install --upgrade pyretis

2. Matplotlib can also be installed using pip. However, for the best
   performance we recommend that you follow a guide specific for your
   operative system. Please see the matplotlib documentation. [3]_ 
   If you are sure that all matplotlib requirements are satisfied,
   you can install it directly using pip:

   .. code-block:: bash

      pip install matplotlib

Running the exercise
--------------------

We will use two python scripts in this example to run the RETIS simulation.
One will display an animation on the fly showing the methods, while the
other script will just output some text results.

Download the example script `retis_move.py <http://pyretis.org/examples/retis_movie.py>`_ to
a location on your computer. Now this script can be executed by running

.. code-block:: bash

   python retis_move.py

which should display an animation similar to the image shown below.

.. figure:: ../img/examples/retismovie.png
    :class: img-responsive center-block
    :scale: 75%
    :alt: The 1D potential example, animation.
    :align: left

    Snapshot from the RETIS animation. The left panel shows accepted trajectories
    for the different ensembles and the upper text shows the kind of move performed:
    TR = Time Reversal, SH = Shooting, NU = Null (no move) and SW = Swapping. The
    upper right panel displays the calculated initial flux, while the lower right
    panel shows the probabilities for the different ensembles (values on the left y-axis)
    and the overall matched probability (in gray, values on the right y-axis). Vertical
    dotted lines display the positions of the RETIS interfaces.

The bulk of this script handles the plotting, and we will not go into details on how
matplotlib is used to plot the result. We will rather in the following consider
how we can make some simple changes and see how this influences the output
from the RETIS simulation.

But before we do that, let up try the text-based script. 
Download the example script `retis.py <http://pyretis.org/examples/retis.py>`_ to
a location on your computer. Now this script can be executed by running

.. code-block:: bash

   python retis.py

which should print out some text similar to the image shown below:

.. figure:: ../img/examples/retistxt.png
    :class: img-responsive center-block
    :scale: 75%
    :alt: The 1D potential example, text output.
    :align: left

    Sample output from the text based RETIS script. After each completed RETIS cycle
    the script outputs the cycle number, and then some results for each ensemble.
    The ensemble names are given in the first column (green color),
    the type of move executed is shown in the next column (orange color), the
    status after the move (blue color) and the current estimate of the crossing
    probability for each ensemble (purple color). Then the current estimates for the
    flux, the crossing probability and the rate constant is outputted. Finally
    the number of force evaluations are given.

As show in figures above, we make use of some abbreviations to describe the type
of moves we are making and the outcome of these moves. These abbreviations
are described in the table below.

.. table:: Abbreviations for the RETIS moves

    +----------------+-------------------------------+
    |  Abbreviation  | Description                   |
    +================+===============================+
    | ``swap``       | A RETIS swapping move.        |
    +----------------+-------------------------------+
    | ``nullmove``   | Just accepting the last       |
    |                | accepted path once again.     |
    +----------------+-------------------------------+
    |   ``tis (sh)`` | A TIS shooting move           |
    +----------------+-------------------------------+
    |  ``tis (tr)``  | A TIS time-reversal move      |
    +----------------+-------------------------------+

.. table:: Abbreviations for the RETIS statuses

    +----------------+--------------------------------------------+
    |  Abbreviation  | Description                                |
    +================+============================================+
    | ``ACC``        | The path has been accepted                 |
    +----------------+--------------------------------------------+
    | ``BWI``        | Backward trajectory end at wrong interface |
    +----------------+--------------------------------------------+
    | ``BTL``        | Backward trajectory too long               |
    |                | (detailed balance condition)               |
    +----------------+--------------------------------------------+
    | ``BTX``        | Backward trajectory too long               |
    |                | (memory condition)                         |
    +----------------+--------------------------------------------+
    | ``FTL``        | Forward trajectory too long                |
    |                | (detailed balance condition)               |
    +----------------+--------------------------------------------+
    | ``FTX``        | Forward trajectory too long                |
    |                | (memory condition)                         |
    +----------------+--------------------------------------------+
    | ``KOB``        | Kicked outside of boundaries               |
    +----------------+--------------------------------------------+
    | ``NCR``        | No crossing with middle interface          |
    +----------------+--------------------------------------------+


If you complete the full 20000 cycles, you can compare your results with the
previously reported data of van Erp. [4]_ [5]_



The 1D potential
----------------


.. code-block:: python

    INTERFACES = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]
    # Let us define the simulation:
    SETTINGS = {}
    # Basic settings for the simulation:
    SETTINGS['simulation'] = {'task': 'retis',
                              'steps': 20000,
                              'interfaces': INTERFACES}
    # Basic settings for the system:
    SETTINGS['system'] = {'units': 'lj', 'temperature': 0.07}
    # Basic settings for the Langevin integrator:
    SETTINGS['integrator'] = {'class': 'Langevin',
                              'gamma': 0.3,
                              'high_friction': False,
                              'seed': 0,
                              'timestep': 0.002}
    # Potential parameters:
    # The potential is: `V_\text{pot} = a x^4 - b (x - c)^2`
    SETTINGS['potential'] = [{'a': 1.0, 'b': 2.0, 'c': 0.0,
                              'class': 'DoubleWell'}]
    # Settings for the order parameter:
    SETTINGS['orderparameter'] = {'class': 'OrderParameterPosition',
                                  'dim': 'x', 'index': 0, 'name': 'Position',
                                  'periodic': False}
    # TIS specific settings:
    SETTINGS['tis'] = {'freq': 0.5,
                       'maxlength': 20000,
                       'aimless': True,
                       'allowmaxlength': False,
                       'sigma_v': -1,
                       'seed': 0,
                       'zero_momentum': False,
                       'rescale_energy': False,
                       'initial_path': 'kick'}
    # RETIS specific settings:
    SETTINGS['retis'] = {'swapfreq': 0.5,
                         'relative_shoots': None,
                         'nullmoves': True,
                         'swapsimul': True}
    # For convenience:
    TIMESTEP = SETTINGS['integrator']['timestep']
    ANALYSIS = {'ngrid': 100, 'nblock': 5}



Modifying the RETIS simulation
------------------------------

The dictionary ``SETTINGS`` in the ``retis_move.py`` script defines
the simulation. Changing the values in this dictionary will modify the simulation.

Here are some examples:

* Changing the number of steps:

  The number of steps is changed by changing the dictionary
  for ``SETTINGS['simulation']``. From 20000 steps

  .. code-block:: python

     SETTINGS['simulation'] = {'task': 'retis',
                               'steps': 20000}

  to just 100:

  .. code-block:: python
   
     SETTINGS['simulation'] = {'task': 'retis',
                               'steps': 100}

* Changing the interfaces:

  The interfaces are defined in a list:

  .. code-block:: python

     SETTINGS['interfaces'] = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, 1.0]

  We can for instance see what happens if we just use two interfaces:

  .. code-block:: python
   
     SETTINGS['interfaces'] = [-0.9, 1.0]

* Changing the temperature:

  The temperature is defined by:

  .. code-block:: python

     SETTINGS['system'] = {'units': 'lj', 'temperature': 0.07}

  and can be changed by giving it a different value:

  .. code-block:: python

     SETTINGS['system'] = {'units': 'lj', 'temperature': 0.21}

* Changing the potential parameters:

  The potential parameters is defined by:

  .. code-block:: python

     SETTINGS['potential'] = [{'a': 1.0, 'b': 2.0, 'c': 0.0,
                               'class': 'DoubleWell'}]

  We can change the parameters directly, e.g.:
  
  .. code-block:: python

     SETTINGS['potential'] = [{'a': 0.5, 'b': 1.0, 'c': 0.0,
                               'class': 'DoubleWell'}]

  Note: It is a good idea to plot the potential if you change the
  parameters. This will allow you to check the position of the
  interfaces.


References
----------

.. [1] The pip user documentation, https://pip.pypa.io/en/stable

.. [2] The virtualenv user guide, https://virtualenv.pypa.io/en/stable/userguide/

.. [3] The matplotlib installation instructions, http://matplotlib.org/users/installing.html

.. [4] Titus S. Van Erp, Dynamical Rare Event Simulation Techniques for Equilibrium and Nonequilibrium Systems,
       Advances in Chemical Physics, 151, pp. 27 - 60, 2012, http://dx.doi.org/10.1002/9781118309513.ch2

.. [5] https://arxiv.org/abs/1101.0927
