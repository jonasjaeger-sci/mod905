.. pytismol documentation master file, created by
   sphinx-quickstart on Fri Jun 19 11:01:24 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

####################
Welcome to pytismol!
####################

**pytismol - rare event simulations with python**

Overview
========

pytismol is a molecular simulation toolkit for **rare events** with
emphasis on `transition interface
sampling <http://en.wikipedia.org/wiki/Transition_path_sampling#Transition_interface_sampling>`_
and `replica exchange transition interface
sampling <http://www.van-erp.org>`_.

pytismol is open source (:ref:`license <pytismol-license>`), written in
`python <https://www.python.org>`_ and simulations are defined, set up
and executed using a high-level python script:


.. code-block:: python

  from retis.core import Simulation, System
  from retis.core import Tis
  mysystem = System() # create empty system 
  run_fancy_tis_calculation()

Installation
============

The current version of pytismol (|version|) can be
installed by:

.. tip::
    Equations within a note
    :math:`G_{\mu\nu} = 8 \pi G (T_{\mu\nu}  + \rho_\Lambda g_{\mu\nu})`.

.. note::
    Equations within a note
    :math:`G_{\mu\nu} = 8 \pi G (T_{\mu\nu}  + \rho_\Lambda g_{\mu\nu})`.

.. danger::
    Equations within a note
    :math:`G_{\mu\nu} = 8 \pi G (T_{\mu\nu}  + \rho_\Lambda g_{\mu\nu})`.

.. warning::
    Equations within a note
    :math:`G_{\mu\nu} = 8 \pi G (T_{\mu\nu}  + \rho_\Lambda g_{\mu\nu})`.

Contents:

.. toctree::
    :maxdepth: 2

    about/index.rst
    user/index.rst
    examples/index.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

