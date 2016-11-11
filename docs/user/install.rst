.. _user-guide-install:

Obtaining and installing pyretis
================================

pyretis is currently in closed beta. When pyretis is
released, the current version can be installed by pip:

.. code-block:: bash

    pip install pyretis

The development version can be cloned
from `gitlab <https://gitlab.com/andersle/pyretis/>`_,

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
