.. _user-guide-install:

Obtaining and installing |pyretis|
==================================

Via conda
---------
The long term stable release of |pyretis| release can be installed using ``conda``:

.. code-block:: pyretis

    conda install pyretis -c conda-forge


Via pip
-------

The latest |pyretis| release can be installed using ``pip``:

.. code-block:: pyretis

    pip install pyretis

This will automatically install |pyretis| and its :ref:`requirements <user-guide-install-requirements>`.

**Note:** |pyretis| will **only work with Python 3.5 and newer**,
but ``pip`` might actually try to install for **Python 2**
if that is your system default. In this case, use ``pip3``
in the command above.


Setting up a virtual environment (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also install |pyretis| in a `virtual environment <https://virtualenv.pypa.io>`_.
Using a virtual environment is recommended as it will help you maintain different
versions of |pyretis| and it's dependencies. The following steps are needed to
set up a virtual environment:

1. Install the `virtualenv package <https://virtualenv.pypa.io/en/stable/installation/>`_,
   for instance using

   ``apt``

   .. code-block:: pyretis

      sudo apt-get install virtualenv

   or ``pip``:

   .. code-block:: pyretis

      pip install virtualenv

2. Create a folder dedicated to your virtual environments, for instance in your home directory

   .. code-block:: pyretis

      mkdir ~/myenvfolder
      cd ~/myenvfolder

3. Install the new environment with the desired Python3 interpreter,
   using the path to the desired Python executable (usually found in ``/usr/bin/``),
   and a name for the virtual environment folder (``python-3.5-env``):

   .. code-block:: pyretis

      virtualenv -p /usr/bin/python3.5 ~/myenvfolder/python-3.5-env


4. Activate the environment:

   .. code-block:: pyretis

      source ~/myenvfolder/python-3.5-env/bin/activate

5. Install |pyretis|:

   .. code-block:: pyretis

      pip install pyretis

Inside the folder ``~/myenvfolder/python-3.5-env`` the Python environment has been
created and it is characterised by its own packages
which can be installed using ``pip``. Since you have sourced the
virtual environment, ``pip`` will now refer to the version of ``pip``
installed in the environment.

**Note:** that you will have to source the environment each time you want to make use of it
using the ``source`` command given above.


The |pyretis| git repository (optional)
---------------------------------------

Previous versions and the latest (*possibly unstable*) sources can be
obtained using ``git``:

.. code-block:: pyretis

   git clone git@gitlab.com:pyretis/pyretis.git

and installed via ``pip`` (after navigating to the correct source directory):

.. code-block:: pyretis

   pip install -e .

.. _user-guide-install-requirements:

Requirements for |pyretis|
--------------------------

In order to run |pyretis|, the following Python libraries are needed:

* `SciPy <http://www.scipy.org/>`_, `NumPy <http://www.numpy.org/>`_,
  and `matplotlib <http://matplotlib.org/>`_
  (see also the information on
  `installing the SciPy Stack <http://www.scipy.org/install.html>`_).

* `Jinja2 <http://jinja.pocoo.org/docs/dev/>`_

* `Docutils <http://docutils.sourceforge.net/>`_

* `Sphinx <http://sphinx-doc.org/>`_  and the
  `Sphinx Bootstrap Theme <https://ryan-roemer.github.io/sphinx-bootstrap-theme>`_
  (for building the documentation).

* `tqdm <https://github.com/tqdm/tqdm/>`_

* `colorama <https://pypi.python.org/pypi/colorama>`_

These packages can be installed by:

.. code-block:: pyretis

    pip install -r requirements.txt

using the :download:`requirements.txt </_static/files/requirements.txt>`
file in the source code directory. This should be automatically done if you
are installing |pyretis| using ``pip``.
