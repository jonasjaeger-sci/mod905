RETIS with Stone Skipping and Web Throwing methods
--------------------------------------------------

Simulation example and test on a 1D particle in a double well potential. 

The present input settings are mainly for computational checks and tutorial purposes.

For detailed balance check a much larger number of cycles would be required. 
The larger the merrier, we indicate a minimum number of cycles of about 10000
(In retis.rst, change the Simulation section 'steps = 100' to 'steps = 10000').
The detailed balance check can be produced by comparing the P cross for EACH 
ensemble produced with the different methods. Ideally they should converge
to the same number. 

Note that in PyRETIS~2, the number of n_jumps and the position of the
SOUR interface can be defined only once and it is the same for all the ensemble.
This settings is, instead, changeable in PyRETIS~3 in the Ensemble sections.

