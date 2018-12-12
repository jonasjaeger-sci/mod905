.. _user-guide-getting-started:

.. role:: header
   :class: h4


Getting started with |pyretis|
==============================

After :ref:`installing PyRETIS <user-guide-install>`, you
can run simulations by using a **text based input file**
or by using **the PyRETIS library explicitly**.

The former approach is perhaps the simplest, but you will
first have to learn how to create input files and this is
explained in the :ref:`input description <user-guide-input>`.

The latter option is more involved, but you are then
given more freedom in defining, running and interacting with
a simulation. In order to make use of the
library, you will have to read about the structure of the
|pyretis| library in the
:ref:`introduction to the library <user-guide-intro-api>`
and in the :ref:`detailed reference section <api-doc>`.

A more extensive overview can be found in
the :ref:`full user guide <user-guide-index>`.
Here, we will now rather jump into some examples
showing the use of |pyretis|.


|pyretis| examples
------------------

In addition to reading the documentation we have prepared
several examples to highlight the usage and capabilities of |pyretis|.
The full list of examples can be found in
the :ref:`example section <examples-index>`.

.. container:: row

   .. container:: col-lg-3 col-md-3 col-sm-3 col-xs-6 thumbnail thumbnail2

      .. image:: /_static/img/examples/thumbnails/md-nve.png
         :width: 100%
         :class: img-responsive
         :target: ../examples/examples-md.html

      .. container:: caption

         :header:`Molecular dynamics`

         In this example, we simply run a MD
         simulation. This is just intended as an
         example of how one can make use of |pyretis|
         as a library.


   .. container:: col-lg-3 col-md-3 col-sm-3 col-xs-6 thumbnail thumbnail2

      .. image:: /_static/img/examples/thumbnails/tis-1d-pot.png
         :width: 100%
         :class: img-responsive
         :target: ../examples/examples-tis-1d.html

      .. container:: caption

         :header:`TIS`

         This example show how we can run a Transition Interface
         Sampling calculation and obtain a crossing probability.
         Here, we consider a 1D potential in which a single particle
         is moving.


   .. container:: col-lg-3 col-md-3 col-sm-3 col-xs-6 thumbnail thumbnail2

      .. image:: /_static/img/examples/thumbnails/retis-1d-pot.png
         :width: 100%
         :class: img-responsive
         :target: ../examples/examples-retis-1d.html

      .. container:: caption

         :header:`RETIS`

         This example show how we can run a Replica Exchange
         Transition Interface Sampling calculation and obtain
         a crossing probability and a rate constant.
         Here, we consider a 1D potential in which a single particle
         is moving.


   .. container:: col-lg-3 col-md-3 col-sm-3 col-xs-6 thumbnail thumbnail2

      .. image:: /_static/img/examples/thumbnails/2dpot.png
         :width: 100%
         :class: img-responsive
         :target: ../examples/examples-2d-hysteresis.html

      .. container:: caption

         :header:`RETIS 2D`

         In this example we perform a simulation of a 2D potential
         which is constructed such that the selection of the order
         parameter is not so obvious.


   .. container:: col-lg-3 col-md-3 col-sm-3 col-xs-6 thumbnail thumbnail2

      .. image:: /_static/img/examples/thumbnails/pyretisrev.png
         :width: 100%
         :class: img-responsive
         :target: ../examples/examples-md-fb.html

      .. container:: caption

         :header:`Extending with C/FORTRAN`

         This example show how we can use FORTRAN or C to speed
         up |pyretis| calculations.


   .. container:: col-lg-3 col-md-3 col-sm-3 col-xs-6 thumbnail thumbnail2

      .. image:: /_static/img/examples/thumbnails/retis-2d-wca.png
         :width: 100%
         :class: img-responsive
         :target: ../examples/examples-retis-wca.html

      .. container:: caption

         :header:`RETIS 2D WCA`

         Here we calculate the rate for the breaking of a bond between
         two particles in a fluid. We consider two cases:
         a low barrier and a high barrier case and we implement the force
         field in C.


   .. container:: col-lg-3 col-md-3 col-sm-3 col-xs-6 thumbnail thumbnail2

      .. image:: /_static/img/examples/thumbnails/hydrogen.png
         :width: 100%
         :class: img-responsive
         :target: ../examples/examples-cp2k-hydrogen.html

      .. container:: caption

         :header:`Using CP2K`

         This example demonstrates how we can make use of CP2K for
         running the dynamics for |pyretis|. Here, we are just studying
         a toy example - breakage of the bond in hydrogen.


   .. container:: col-lg-3 col-md-3 col-sm-3 col-xs-6 thumbnail thumbnail2

      .. image:: /_static/img/examples/thumbnails/hydrate.png
         :width: 100%
         :class: img-responsive
         :target: ../examples/examples-gromacs-hydrate.html

      .. container:: caption

         :header:`Using GROMACS`

         This example demonstrates how we can make use of GROMACS for
         running the dynamics for |pyretis|. In this particular example
         we study the diffusion of methane in a sI hydrate structure.


Examples of |pyretis| use
-------------------------

Below are some examples which illustrate the use of |pyretis| for realistic systems.

.. container:: row

   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/dna-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Predicting the mechanism and rate of H-NS binding to AT-rich DNA.`


   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/water-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Autoionization of water.`

         In this example, RETIS simulations were used to study the
         autoionization in pure water. More information can be found
         in the paper, please see
         `Local initiation conditions for water autoionization <https://www.pnas.org/content/115/20/E4569>`_.



   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/cyclophilin-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Conformational study of Cyclophilin - A.`

