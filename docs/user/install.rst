.. _user-guide-install:

Obtaining and installing |pyretis|
==================================

|pyretis| and its :ref:`requirements <user-guide-install-requirements>` can be
installed :ref:`using pip <user-guide-install-pip>`
or :ref:`using conda <user-guide-install-conda>`
as described below.
We also describe how |pyretis| can be installed in a 
:ref:`virtual environment <user-guide-install-virtual-environment>` and how it
can be installed directly from the source code :ref:`using git <user-guide-install-git>`.

.. _user-guide-prereq:

Prerequisites
-------------

|pyretis| requires **Python 3.6** or **Python 3.7**. Please make sure that you have
an updated version of Python installed on your system. |pyretis| depends on several
other Python packages, however, these should be installed automatically as part
of the installation of |pyretis|. A  list of the dependencies :ref:`can be found below <user-guide-install-requirements>`.

.. _user-guide-install-pip:

Installing via ``pip``
----------------------
|pyretis| can be installed using `pip <https://pypi.org/project/pyretis/>`_
with the following command:

.. _user-guide-prereq:

    pip install pyretis


|pyretis| requires `mdtraj <http://mdtraj.org>`_ and this has to be
installed **after** installing |pyretis|:

.. code-block:: pyretis

    pip install git+https://github.com/mdtraj/mdtraj.git

|pyretis| requires `mdtraj <http://mdtraj.org>`_ and this has to be
installed **after** installing |pyretis|:

**Note:** Please make sure that you are using a Python environment
of version 3.6 or newer. On some systems, **Python 2** may still be the default
version and ``pip`` might actually try to install for **Python 2**.
In this case, use ``pip3`` in the command above.

.. _user-guide-install-conda:

Installing via ``conda``
------------------------
|pyretis| can be installed using `conda <https://anaconda.org/conda-forge/pyretis>`_ 
with the following commands:

.. code-block:: pyretis

    conda create --name pyretis
    conda activate pyretis
    conda install pip
    pip install pyretis
    pip install git+https://github.com/mdtraj/mdtraj.git

**Note:** Since |pyretis| will **only work with Python 3.6 or newer**,
please make sure that you are using an environment with a recent version
of Python.


.. _user-guide-install-virtual-environment:

Optional: Setting up a virtual environment for pip
--------------------------------------------------

You can also install |pyretis| in a `virtual environment <https://virtualenv.pypa.io>`_.
Using a virtual environment makes it easier to maintain different
versions of |pyretis| and it's dependencies. The following steps are needed to
set up a virtual environment:

1. Install the `virtualenv package <https://virtualenv.pypa.io/en/stable/installation/>`_.
   This can be done using ``pip``:
   
   .. code-block:: pyretis

      [sudo] pip install virtualenv

   or using a package manager for your operative system, for instance ``apt`` if you are
   using a Debian-like Linux:

   .. code-block:: pyretis

      [sudo] apt-get install virtualenv

2. Create a folder dedicated to your virtual environments, for instance in your home directory:

   .. code-block:: pyretis

      mkdir ~/name-of-environment-folder
      cd ~/name-of-environment-folder

3. Install the new environment with the desired Python3 interpreter,
   using the path to the desired Python executable (usually found in ``/usr/bin/``),
   and a name for the virtual environment folder (``pyretis-env``):

   .. code-block:: pyretis

      virtualenv -p /usr/bin/python3 ~/name-of-environment-folder/pyretis-env

   Note, if you want more control over which version of Python to use, you can
   use the ``-p`` option in the command above to specify this. For instance,
   for version **3.7**:
   
   .. code-block:: pyretis

      virtualenv -p /usr/bin/python3.7 ~/name-of-environment-folder/pyretis-env


4. Activate the environment:

   .. code-block:: pyretis

      source ~/name-of-environment-folder/pyretis-env/bin/activate

5. Install |pyretis|:

   .. code-block:: pyretis

      pip install pyretis

6. Install `mdtraj <http://mdtraj.org>`_:

   .. code-block:: pyretis

    pip install git+https://github.com/mdtraj/mdtraj.git

The folder ``~/name-of-environment-folder/pyretis-env`` now contains a new Python environment
where |pyretis| has been installed. Since you have sourced the
virtual environment, ``pip`` will now refer to the version of ``pip``
installed in the environment and when you install packages, they will be
installed inside the folder ``~/name-of-environment-folder/pyretis-env``.

**Note:** that you will have to source the environment each time you want to make use of it
using the ``source`` command given above.


.. _user-guide-install-git:

Optional: Installing from the |pyretis| git repository
------------------------------------------------------

Previous versions and the latest (*possibly unstable*) sources can be
obtained using ``git``:

.. code-block:: pyretis

   git clone git@gitlab.com:pyretis/pyretis.git

or,

.. code-block:: pyretis

   git clone https://gitlab.com/pyretis/pyretis.git

After cloning the repository, |pyretis| can be
installed via ``pip`` (after navigating to the main source directory):

.. code-block:: pyretis

   pip install .

or, alternatively:

.. code-block:: pyretis

   python setup.py install

Then, install ``mdtraj``:

.. code-block:: pyretis

    pip install git+https://github.com/mdtraj/mdtraj.git

.. _user-guide-install-develop:

Optional: Installing a development version from the |pyretis| git repository
----------------------------------------------------------------------------

After cloning the repository as described above, check out the development
branch you are interested in, e.g.:

.. code-block:: pyretis

   git checkout develop 

Then install the development requirements (these are defined in the file
``requirements-dev.txt``):

.. code-block:: pyretis

   pip install -r requirements-dev.txt

install ``mdtraj``:

.. code-block:: pyretis

    pip install git+https://github.com/mdtraj/mdtraj.git

Finally, install |pyretis| using:

.. code-block:: pyretis

   pip install -e .

.. _user-guide-install-test:

Testing your installation
-------------------------

After installing from the |pyretis| source, your installation can be
tested by running the tests from the main directory:

.. code-block:: pyretis

   python -m unittest discover -v -s test

.. _user-guide-install-requirements:

Requirements for |pyretis|
--------------------------

In order to run |pyretis|, several Python libraries are needed, for instance
`SciPy <http://www.scipy.org/>`_, `NumPy <http://www.numpy.org/>`_, and `matplotlib <http://matplotlib.org/>`_
(see also the information on `installing the SciPy Stack <http://www.scipy.org/install.html>`_).
A list of the requirements can be found in the file
:download:`requirements.txt </_static/files/requirements.txt>` in the source
code directory. These packages can be installed by:

.. code-block:: pyretis

    pip install -r requirements.txt

after downloading the :download:`requirements.txt </_static/files/requirements.txt>` file.
This should be automatically done if you
are installing |pyretis| using ``pip``/``conda``. Note that the `mdtraj <http://mdtraj.org>`_
requirement may have to be installed separately as described above when using ``pip``.
