.. _user-section-forcefield:

The Forcefield section
======================

The force field section defines the force field
to use for the simulation.

.. pyretis-input-example:: Forcefield

   .. code-block:: rst

      Forcefield settings
      --------------------

      description = Lennard Jones test

The actual potential functions to use are explicitly
defined using the :ref:`potential section <user-section-potential>`.


Keywords for the Forcefield section
-----------------------------------

For the Forcefield section the following keywords can be set:

.. |ff_description| replace:: :ref:`description <user-section-forcefield-keyword-description>`

.. _table-keywords-forcefield:

.. table:: Keywords for the Forcefield section.
   :class: table-striped

   +------------------+-------------------------------------------------------+
   | Keyword          | Description                                           |
   +==================+=======================================================+
   | |ff_description| | Text that labels the force field.                     |
   +------------------+-------------------------------------------------------+


.. _user-section-forcefield-keyword-description:

Keyword description
^^^^^^^^^^^^^^^^^^^

.. pyretis-keyword:: description string

   description
   The ``description`` keyword is a text that labels the force field.
   This is only used when printing out information about the
   force field.

   .. code-block:: rst

       Forcefield
       ----------
       description = my new force field

   Default:
       The default value for the description is the
       text: ``'Generic force field'``
