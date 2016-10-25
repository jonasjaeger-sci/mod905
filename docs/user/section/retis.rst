.. _user-section-retis:

The RETIS section
=================

Specifies settings for RETIS simulations

.. code-block:: rst

    Simulation
    ----------
    task = retis
    steps = 10000

    TIS settings
    ------------
    allowmaxlength = False
    freq = 0.5
    zero_momentum = False
    initial_path = 'kick'
    seed = 1
    aimless = True
    maxlength = 20000
    sigma_v = -1
    rescale_energy = False
    interfaces = [-0.9, -0.9, 1.0]
    detect = -0.8
    ensemble = 1
