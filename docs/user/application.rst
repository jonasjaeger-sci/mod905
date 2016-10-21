.. _user-guide-application:

The pyretis application
=======================

The pyretis application, ``pyretisrun``, is used to
execute simulations defined in input files:

.. code-block:: bash

    $ pyretisrun.py [-h] -i INPUT [-V] [-f LOG_FILE] [-l LOG_LEVEL] [-p] 

The arguments are:

+-------------------------------------+--------------------------------------------------+
| Argument                            | Description                                      |
+=====================================+==================================================+
| -h, --help                          | Show the help message and exit                   |
+-------------------------------------+--------------------------------------------------+
| -i INPUT, --input INPUT             | Location of the input file.                      |
+-------------------------------------+--------------------------------------------------+
| -V, --version                       | Show the version number and exit.                |
+-------------------------------------+--------------------------------------------------+
| -log_file LOG_FILE                  | Specify location of log file to write.           |
+-------------------------------------+--------------------------------------------------+
| -l LOG_LEVEL, --log_level LOG_LEVEL | Specify log level for the log file.              |
+-------------------------------------+--------------------------------------------------+
| -p, --progress                      | Display a progress meter instead of text output. |
+-------------------------------------+--------------------------------------------------+

The ``LOG_LEVEL`` can be set as:

+-----------+---------------------------------------------------------+
| LOG_LEVEL | Description                                             |
+===========+=========================================================+
| CRITICAL  | Only display critical messages.                         |
+-----------+---------------------------------------------------------+
| ERROR     | Display critical and error messages.                    |
+-----------+---------------------------------------------------------+
| WARNING   | Display critical and error messages and warnings        |
+-----------+---------------------------------------------------------+
| INFO      | Display all of the above and some info messages.        |
+-----------+---------------------------------------------------------+
| DEBUG     | Display all of the above and additional debug messages. |
+-----------+---------------------------------------------------------+

Some examples: 

To run the simulation defined in a file named ``retis.rst``, make a log file
for output named ``retis.log`` and display a progress bar:

.. code-block:: bash

    $ pyretisrun.py -i retis.rst -f retis.log -p

To run the simulation defined in a file named ``test.rst`` and display debug messages:

.. code-block:: bash

    $ pyretisrun.py -i test.rst -l DEBUG
 
