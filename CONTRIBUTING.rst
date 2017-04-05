Contributing to PyRETIS
=======================

There is a nice guide on github about `contributing to open source projects
<https://guides.github.com/activities/contributing-to-open-source/>`_.
In PyRETIS we largely follow this approach and the issue tracker is used
for reporting bugs and issues and requesting new features. This
section on contributing is based on 
the `description for gitlab <https://gitlab.com/gitlab-org/gitlab-ce/blob/master/CONTRIBUTING.md>`_.

Before contributing,
please read the short guidelines given below
for reporting issues_,
and for requesting new features_.
Some information on the preferred coding style_ is 
also given below.

.. _issues:

Bugs and issues
---------------

If you find a bug in PyRETIS, please `create an issue
<https://gitlab.com/pyretis/pyretis/issues>`_ using the following
template:

.. code-block:: restructuredtext

    Summary
    -------

    One sentence summary of the issue: What goes wrong, what did you
    expect to happen

    Steps to reproduce
    ------------------

    Describe how the issue can be reproduced.

    Expected behavior
    -----------------

    Describe what behavior you expected insted of what actually happens.

    Relevant logs
    -------------

    Add logs from the output.

    Output of checks
    ----------------

    Be sure that all the tests pass before filing the issue.

    Possible fixes
    --------------

    If you can, link to the line of code that might be responsible for 
    the problem.

If you wish to fix the bug yourself, please follow the approach described below.

.. _features:

New features
------------

If you are missing some functionality in PyRETIS you can create
a new issue in the issue tracker and
label it as a `feature proposal <https://gitlab.com/pyretis/pyretis/issues?label_name=feature+proposal>`_.
If you do not have rights to add the ``feature proposal`` label, you can ask one 
of the core members of the PyRETIS project to add it for you.

You can also implement the changes you want yourself as 
a merge request.
We cannot promise that we will automatically
include your work in PyRETIS but we are happy to have active users
and we will consider your contribution.
So, when you are finished with your work please make a merge request.


Merge requests
..............

The general approach for making your bug-fix or new feature available
in the PyRETIS project is as follows:

1. Fork [#]_ PyRETIS into your own personal space.

2. Create a new branch and work on your feature. 

3. Create tests for your feature. Especially, if you are fixing a bug,
   create a test that shows where the bug is causing PyRETIS to fail and
   how your code is fixing this.

4. Squash all your commits into one and push to your fork.

5. Submit a merge request to the master branch using the template given below.

6. Wait for review and the following discussion :-).

.. code-block:: restructuredtext

    Summary
    -------   

    What does this merge request do?
    
    Justification
    -------------

    Why is the merge request needed?

    Description of the new code
    ---------------------------

    A short description of the new code.
    Are there points in the code the reviewer needs to double check?

    References
    ----------

    Add references to relevant issue numbers.

After submitting a merge request the code will be reviewed [#]_ by (another)
member of the PyRETIS team.


.. _style:

Style guidelines
----------------

The guidelines can be summarized as follows:

- Check that your code follows
  `pep8 <https://www.python.org/dev/peps/pep-0008/>`_.

- Document your code using `NumPy style docstrings
  <https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt>`_

- Use a ``logger`` rather than ``print()`` in libraries.


PyRETIS follows the python
`pep8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide
(see also `pep8.org <http://pep8.org/>`_)
and new code should be checked with the
pep8 style guide `checker <https://github.com/PyCQA/pep8>`_
and `pylint <http://www.pylint.org/>`_:

.. code-block:: bash

    pep8 source_file.py
    pylint source_file.py

or other tools like `PyChecker <http://pychecker.sourceforge.net/>`_ or
`pyflakes <https://pypi.python.org/pypi/pyflakes>`_.

`NumPy's <http://www.numpy.org/>`_ imports can be a bit
tricky understand so you can help pylint by doing

.. code-block:: bash

    pylint --extension-pkg-whitelist=numpy source_file.py


The PyRETIS project is documented using the
`NumPy/SciPy documentation standard <https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt>`_
and contributors are requested to familiarize themselves with this 
style and *use it*.


References
..........

.. [#] Gitlab documentation on forking: http://doc.gitlab.com/ce/workflow/forking_workflow.html
.. [#] https://github.com/thoughtbot/guides/tree/master/code-review
