.. _user-guide-getting-started:

.. role:: header
   :class: h4


Getting started with pyretis
============================

Using pyretis
-------------

After :ref:`installing pyretis <user-guide-install>`, you
can run simulations, either by using a **text-based input
file** or by making **explicit use of the pyretis library**:

The text based input file
  Using the input file is the simplest approach. You will first have
  to learn how to create this file and this is explained in
  the :ref:`input description <user-guide-input>`.

Explicit use of the pyretis library
  The second option offers more freedom in defining, running
  and interacting with the simulation. However, this approach requires
  that you study how the pyretis library is structured and build up.
  This is described in the 
  :ref:`introduction to the library <user-guide-intro-api>`
  and in the
  :ref:`detailed reference section <api-doc>`.



Learning by doing -- pyretis examples
-------------------------------------

In addition to reading the documentation we have prepared
several examples to highlight the usage and capabilities of pyretis.
The full list of examples can be found in 
the :ref:`example section <examples-index>`.

.. container:: row

   .. container:: col-sm-6 col-md-3

      .. container:: thumbnail

         .. image:: ../img/examples/thumbnails/tis-1d-pot.png
            :width: 100%
            :class: img-rounded

         .. container:: caption
            
            :header:`TIS`

            This example is showing how to run a Transition Interface Sampling
            simulation.

   .. container:: col-sm-6 col-md-3
      
      .. container:: thumbnail

         .. image:: ../img/examples/thumbnails/tis-1d-pot.png
            :width: 100%
            :class: img-rounded

         .. container:: caption
            
            :header:`RETIS`

            This example is using Replica Exchange Transition Interface Sampling
            for calculating the rate of a simple reaction.

   .. container:: col-sm-6 col-md-3
      
      .. container:: thumbnail

         .. image:: ../img/examples/thumbnails/tis-1d-pot.png
            :width: 100%
            :class: img-rounded

         .. container:: caption
            
            :header:`Custom order`

            This example shows how custom order parameters can be created.
