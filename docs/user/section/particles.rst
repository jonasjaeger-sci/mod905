.. _user-section-particles:

The Particles section
=====================

Particles are added to a simulation in the ``particles`` section:

.. pyretis-input-example:: Particles

   .. code-block:: rst

       Particles
       ---------
       position = {'file': 'initial.gro'}
       velocity = {'generate': 'maxwell',
                   'temperature': 2.0,
                   'momentum': True,
                   'seed': 0}
       mass = {'Ar': 1.0}
       name = ['Ar']
       type = [0]

   In this example, the particles are read from a file
   called ``'initial.gro'`` and the velocities are set according
   to a Maxwell distribution with a temperature of ``2.0`` and the
   velocities are initiate so that the total momentum is set to zero.
   Further, the mass of particles with name ``'Ar'`` is set to ``1.0``
   and all particles are named ``'Ar'`` and assigned a particle type of ``0``.

Keywords for the Particles section
----------------------------------

The following keywords can be specified for the Particles section:

.. |part_position| replace:: :ref:`position <user-section-particles-keyword-position>`

.. |part_velocity| replace:: :ref:`velocity <user-section-particles-keyword-velocity>`

.. |part_mass| replace:: :ref:`mass <user-section-particles-keyword-mass>`

.. |part_name| replace:: :ref:`name <user-section-particles-keyword-name>`

.. |part_type| replace:: :ref:`type <user-section-particles-keyword-type>`

.. |part_npart| replace:: :ref:`npart <user-section-particles-keyword-npart>`

.. _table-keywords-particles:

.. table:: Keywords for the Particles section.
   :class: table-striped table-hover

   +-----------------+--------------------------------------------------------+
   | Keyword         | Description                                            |
   +=================+========================================================+
   | |part_position| | Defines how initial positions are set.                 |
   +-----------------+--------------------------------------------------------+
   | |part_velocity| | Defines how initial velocities are set.                |
   +-----------------+--------------------------------------------------------+
   | |part_mass|     | Defines the masses for the particles.                  |
   +-----------------+--------------------------------------------------------+
   | |part_name|     | Defines names for the particles.                       |
   +-----------------+--------------------------------------------------------+
   | |part_type|     | Defines the known particle types.                      |
   +-----------------+--------------------------------------------------------+
   | |part_npart|    | Defines the number of particles (analysis specific).   |
   +-----------------+--------------------------------------------------------+



.. _user-section-particles-keyword-position:

Keyword position
^^^^^^^^^^^^^^^^

.. pyretis-keyword:: position dictionary

   The ``position`` keyword is used to set the initial positions for a
   simulation. It is also used to define the particles we will use in the
   simulation. The initial positions can be:

   1. Generated on a lattice,

      .. code-block:: rst

         position = {'generate': 'fcc', 'repeat': [3, 3, 3], 'lcon': 1.0}

      When generating on a lattice, the following settings must be
      provided:

      * ``'generate'`` selects what kind of lattice to generate,
        valid choices are:

        - ``'sc'``: A simple cubic lattice.
        - ``'sq'``: A square lattice (2D) with one atom in the unit cell.
        - ``'sq2'``: A square lattice (2D) with two atoms in the unit cell.
        - ``'bcc'``: A body-centered cubic lattice.
        - ``'fcc'``: A face-centered cubic lattice.
        - ``'hcp'``: A hexagonal close-packed lattice.
        - ``'diamond'``: A diamond-like structure.

      * ``'repeat'`` select the number of repetitions of the unit lattice
        in the spatial directions.

      * ``'lcon'`` or ``'density'`` which specify the size of the lattice:

        - ``'lcon'``: Specifies the lattice constant.

        - ``'density'``: Specifies a particle density.

      The available lattices are further described in the
      description of the :ref:`generate_lattice <api-tools-lattice>` command from the API.

   2. Or read from a file,

      .. code-block:: rst

         position = {'file': 'initial.gro'}

      When reading initial positions from a file, the following settings
      must be provided:

      * ``'file'`` which specifies the file to open.

      If the specified file is a GROMACS GRO file, |pyretis| will also attempt to
      read velocities from the file. These can be used rather than generating
      velocities with ``particles-velocity``.

      .. NOTE::
         The specified file name is **case-sensitive**.

   More examples:

   .. code-block:: rst

      Particles
      ---------
      # Read a file from the current directory
      position = {'file': 'initial.gro'}

      # Read a file from another position:
      position = {'file': '/path/to/file/initial.gro'}

      # Generate a fcc lattice with 4 * 5**3 = 500 particles and
      # a lattice constant of 1 in reduced units:
      position = {'generate': 'fcc',
                  'repeat': [5, 5, 5],
                  'lcon': 1.0}

      # Generate a bcc lattice with 2*5**3 = 250 particles and
      # a reduced density of 0.9:
      position = {'generate': 'bcc',
                  'repeat': [5, 5, 5],
                  'density': 0.9}


.. _user-section-particles-keyword-velocity:

Keyword velocity
^^^^^^^^^^^^^^^^

.. pyretis-keyword:: velocity dictionary

   The ``velocity`` keyword is used to set initial velocities
   for the particles according to a specified temperature.

   Example:

   .. code-block:: rst

      velocity = {'generate': 'maxwell',
                  'temperature': 2.0,
                  'momentum': True,
                  'seed': 0}

   The following settings must be provided:

   * ``'generate'`` which specifies the distribution to draw random
     velocities from. Currently, the only recognised distribution is
     a Maxwell distribution, which is selected by setting the value
     ``'maxwell'``, as shown in the example above.

   * ``'temperature'`` which specifies the desired temperature in
     internal units. If this is not provided, the value set by the
     input keyword ``temperature`` is used.

   * ``'momentum'`` which specifies if the resulting momentum should be
     zero or not. The default value is ``True`` which will generate velocities
     so that the total momentum is zero.

   * ``'seed'`` which can be used to specify a seed for the random number
     generator. If this value is not given a ``0`` will be used.

.. _user-section-particles-keyword-mass:

Keyword mass
^^^^^^^^^^^^

.. pyretis-keyword:: mass dictionary of floats

   The ``mass`` keyword sets the masses for different particles.
   The provided values are assumed to be in **internal units**. If masses are not
   set, |pyretis| will try to guess them from the periodic system, however, this
   might fail unless the names you have used for the particles correspond to
   names used in the periodic system.

   Example 1:

   .. code-block:: rst

       # define masses for particles with name 'Ar'
       mass = {'Ar': 1.0}

   Example 2:

   .. code-block:: rst

       # define masses for particles with name 'Ar', 'Kr' and 'big'
       mass = {'Ar': 1.0, 'Kr': 2.098, 'big': 10.0}

.. _user-section-particles-keyword-name:

Keyword name
^^^^^^^^^^^^

.. pyretis-keyword:: name list of strings

   The ``name`` keyword is used give particles a name.
   This can, for instance, be used to label specific particles and, when
   used together with the ``mass`` keyword, it can be
   used to control the masses assigned to the different particles.
   The particle names are also used when writing output configurations.

   Example:

   .. code-block:: rst

      name = ['Ar']

   The input value is a list with the particle names in the order
   they have been generated/read from a file by the
   :ref:`position <user-section-particles-keyword-position>` keyword.
   If the ``name`` list is too short,
   the **last** item in the list will be repeated.

   This means that,

   .. code-block:: rst

      name = ['Ar', 'Kr']

   will name one particle (the first) ``'Ar'`` and the rest
   of the particles will be named ``'Kr'``.


.. _user-section-particles-keyword-type:

Keyword type
^^^^^^^^^^^^

.. pyretis-keyword:: type list of integers

   The ``type`` keyword is used to specify the particle types for the
   different particles. The particle type is used to distinguish particles, for
   instance when calculating pair interactions.

   The input value is a list with the particle types in the order
   they have been generated/read from a file by the
   :ref:`position <user-section-particles-keyword-position>` keyword.
   If the ``type`` list is too short, the **last** item in the list will be
   repeated.

   Example 1:

   .. code-block:: rst

       type = [0, 1]
       name= ['Ar', 'Kr']

   This can be used to define a simulation where we have particles of
   two different types with different masses.

   Example 2:

   .. code-block:: rst

       type = [0]
       name= ['Ar', 'Ar2', 'Ar']

   This can be used to define a simulation where we have only particles
   of the same type, however, one of the particles have a different
   name than the others and can, for instance, be assigned a different
   mass.

.. _user-section-particles-keyword-npart:

Keyword npart
^^^^^^^^^^^^^

.. pyretis-keyword:: npart integer

   The ``npart`` keyword specifies the number of particles in total in
   the simulation. This keyword is used by the analysis application, and
   does **not** need to be set in the input. The |pyretis| application
   will automatically update this keyword.

   Default
      None, the |pyretis| application will automatically update this keyword.
