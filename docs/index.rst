.. pyretis documentation master file, created by
   sphinx-quickstart on Fri Jun 19 11:01:24 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. container:: jumbotron

  .. image:: img/logo3.png
     :class: img-responsive

  pyretis is a `Python <https://www.python.org>`_ library for **rare event molecular simulations**
  with emphasis on methods based on `transition interface
  sampling <http://en.wikipedia.org/wiki/Transition_path_sampling#Transition_interface_sampling>`_
  and `replica exchange transition interface sampling <http://www.van-erp.org>`_.

  pyretis is :ref:`open source <pyretis-license>`, designed to be easy to use
  and simulations can be performed by using the :ref:`library <api-doc>`,

  .. code-block:: python

    from pyretis.core import create_system, create_simulation, create_force_field
    settings = {'task': 'tis',
                'interfaces': [-1.0, 0.0, 1.0],
                # more settings...
               }
    system = create_system(settings)
    system.forcefield = create_force_field(settings)
    simulation = create_simulation(settings, system)
    for results in simulation.run():
        print(results)  # print out calculated properties

  or with a python flavored :ref:`input file <user-guide-input>`. The usage of pyretis is
  described in the :ref:`user guide <user-guide-index>`
  where you can learn how to use pyretis. 

Installation
============

pyretis is currently in closed beta. When pyretis is
released, the current version can be installed by pip:

.. code-block:: bash

    pip install pyretis

The development version can be cloned
from `gitlab <https://gitlab.com/andersle/>`_,

.. code-block:: bash

    git clone git@gitlab.com:andersle/pyretis.git

and sourced in your python path:

.. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:/some/dir/pyretis

In order to run pyretis, the following python libraries are needed:

* `SciPy <http://www.scipy.org/>`_, `NumPy <http://www.numpy.org/>`_,
  and `matplotlib <http://matplotlib.org/>`_
  (see also the information on
  `installing the SciPy Stack <http://www.scipy.org/install.html>`_).

* `Jinja2 <http://jinja.pocoo.org/docs/dev/>`_

* `Docutils <http://docutils.sourceforge.net/>`_

* `Sphinx <http://sphinx-doc.org/>`_ (for building the documentation).

* `tqdm <https://github.com/tqdm/tqdm/>`_

These packages can be installed by:

.. code-block:: bash

    pip install -r requirements.txt

using the `requirements.txt <https://gitlab.com/andersle/pyretis/blob/master/requirements.txt>`_
file in the source code directory.


Contents
========

.. toctree::
    :maxdepth: 2

    about/index.rst
    user/index.rst
    api/pyretis.rst
    examples/index.rst
    developer/index.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
