.. _our-results:

.. role:: header
   :class: h4


Main studies performed with |pyretis|
-------------------------------------

.. container:: row

   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/dna-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Predicting the mechanism and rate of H-NS binding to AT-rich DNA.`

         The adsorption of H-NS on DNA is studied at atomistic resolution
         with GROMACS. Local minima have been located by metadynamics
         and the transition rates computed by RETIS.

         Paper:
         `Predicting the mechanism and rate of H-NS binding to AT-rich DNA
         <https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006845>`_
         
         `Source Files <http://pyretis.org/source_files/H-NS_2019>`__


   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/water-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Autoionization of water.`

         BO-DFT simulations, via the RETIS approach, were used to study water
         autoionization. The mechanism(s) have been highlighted and their rate(s)
         quantified. Machine learning was applied to test the quality of 
         the order parameters.

         Paper: `Local initiation conditions for water autoionization <https://www.pnas.org/content/115/20/E4569>`_
         
         `Source Files <http://pyretis.org/source_files/Water_2019>`__


   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/cyclophilin-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Conformational study of Cyclophilin - A.`

         Full atomistic simulations with GROMACS have been performed to sample
         and quantify the rate of the structural rearrangements of CyP-A and
         its muted confomer.
        
         Paper in preparation.

         `Source Files <http://pyretis.org/source_files/CyP-A_2019>`__


   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/trimer-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Proton transfer in a water trimer.`

         A study on the proton transfer reaction with a polarizable potential
         is included. The various features of |pyvisa| can be tested
         on the simulation outputs.
        
         Paper: `PyVisA: Visualization and Analysis of path sampling
         trajectories
         <https://onlinelibrary.wiley.com/doi/full/10.1002/jcc.26467>`_

         `Source Files <http://pyretis.org/source_files/Water_trimer_2020>`__


   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/formic-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Formic acid catalysed formation of sulfuric acid`. 

         A study on the formic acid catalysed conversion of
         sulfur trioxide and water to sulfuric acid.
         The mechanism(s) have been highlighted and their rate(s) estimated
         as a function of the temperature.

         Paper: `Path sampling for atmospheric reactions: formic acid catalysed
         conversion <https://doi.org/10.7717/peerj-pchem.7>`_

         `Source Files <http://pyretis.org/source_files/Formic_acid_2020>`__


   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/wirefence-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Enhanced path sampling using subtrajectory Monte Carlo moves`. 

         A study on the effect of using the subtrajectory Wire Fencing move
         compared to the standard shooting move. Systems studied are the
         1D potential double-well, thin film breaking and a ruthenium redox
         reaction.

         Paper: `Enhanced path sampling using subtrajectory Monte Carlo moves
         <https://doi.org/10.1063/5.0127249>`_

         `Source Files <http://pyretis.org/source_files/Submoves_2022>`__

   .. container:: col-lg-4 col-md-4 col-sm-4 col-xs-6 thumbnail thumbnail3

      .. image:: /_static/img/examples/thumbnails/repptis-400x400.png
         :width: 100%
         :class: img-responsive

      .. container:: caption

         :header:`Memory reduction using partial path ensembles`. 

         A study on how the path ensemble definitions can be changed when 
         long-lived metastable states are present in the reaction.

         Paper: `Path sampling with memory reduction and replica exchange to
         reach long permeation timescales 
         <https://doi.org/10.1016/j.bpj.2023.02.021>`_

         `Source Files <https://github.com/WouterWV/pathsampling_toymodels>`__
