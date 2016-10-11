.. _user-guide-getting-started:

.. role:: header
   :class: h4


Getting started with pyretis
============================

After :ref:`installing pyretis <user-guide-install>`, you
can run simulations by:

1. Using a **text based input file**.
   This is the simplest approach. You will first have
   to learn how to create this file and this is explained in detail
   the :ref:`input description <user-guide-input>`.

2. Using **the pyretis library explicitly**. This is a more
   involved approach, but it offers more freedom in defining, running
   and interacting with the simulation. In order to make use of the
   library, you will have to read about the structure of the
   pyretis library in the 
   :ref:`introduction to the library <user-guide-intro-api>`
   and in the
   :ref:`detailed reference section <api-doc>`.

A more extensive overview can be found in
the :ref:`full user guide <user-guide-index>`.
Here, we will now rather jump into some examples showing the use of pyretis!


pyretis examples
----------------

In addition to reading the documentation we have prepared
several examples to highlight the usage and capabilities of pyretis.
The full list of examples can be found in 
the :ref:`example section <examples-index>`.

.. container:: row

    .. container:: col-sm-3
     
      .. container:: thumbnail

         .. image:: ../img/examples/thumbnails/md-nve.png
            :width: 100%
            :class: img-responsive

         .. container:: caption
         
            :header:`Molecular dynamics`

            Simple molecular dynamics


    .. container:: col-sm-3

      .. container:: thumbnail

         .. image:: ../img/examples/thumbnails/tis-1d-pot.png
            :width: 100%
            :class: img-responsive

         .. container:: caption
           
            :header:`TIS`

            This example is showing how to run a Transition Interface Sampling
            simulation.


    .. container:: col-sm-3
     
      .. container:: thumbnail

         .. image:: ../img/examples/thumbnails/placeholder.png
            :width: 100%
            :class: img-responsive

         .. container:: caption
         
            :header:`RETIS`

            This example is using Replica Exchange Transition Interface Sampling
            for calculating the rate of a simple reaction.

   
.. container:: row

    .. container:: col-sm-3

      .. container:: thumbnail

         .. image:: ../img/examples/thumbnails/placeholder.png
            :width: 100%
            :class: img-responsive

         .. container:: caption

            :header:`Custom order`

            This example demonstrates how custom order parameters
            can be added to pyretis.


    .. container:: col-sm-3
     
      .. container:: thumbnail

         .. image:: ../img/examples/thumbnails/pyretisrev.png
            :width: 100%
            :class: img-responsive

         .. container:: caption
          
            :header:`pyretis + C`

            Molecular dynamics powered by Fortran or C.

 
    .. container:: col-sm-3
     
      .. container:: thumbnail

         .. image:: ../img/examples/thumbnails/placeholder.png
            :width: 100%
            :class: img-responsive

         .. container:: caption
          
            :header:`pyretis & CP2K`

            RETIS simulations using CP2K.



