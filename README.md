# MOD905 Python for Natural Sciences and Engineering

This Repository belongs to Jonas Jäger and contains the project for the MOD905 PhD course at the University of Stavanger.

<img width="815" height="734" alt="Screenshot from 2026-03-04 10-39-51" src="https://github.com/user-attachments/assets/2061bfef-eea1-4ee8-a192-9e914d430523" />


## Workflow (#1): Chemical reaction analysis from Lammps reaxFF simulation files
The purpose of this project is to develop a modular script that evaluates and analyses data from lammps reaxFF simulations to extract relevant 
information about the chemical reactions happening. The architecture is envisioned as follows:

**1. Module: Data Preparation**
The first module serves to read the different simulation files containing the discrete elements, their charges, trajectories and the systems energies to subsequently 
create adequate variables in python (dictionaries, dataframes, arrays,...). 

**2. Module: Species Analysis**
Here it should be analysed which species exist and have existed during the course of the simulation. The simulation file looks something like this:

  Timestep    No_Moles    No_Specs          Li           O           C           H
  
          0         640           4          40         180         180         240
          
  Timestep    No_Moles    No_Specs    C3H4O3Li          Li   C3H4O3Li2      C3H4O3
  
         20          89           4           7          29           2          51
         
  Timestep    No_Moles    No_Specs    C3H4O3Li          Li   C3H4O3Li2      C3H4O3
  
         40          89           4           7          29           2          51

It would make sense to first obtain a list of all unique elements/reactants. Afterwards it makes sense to create a dictionary of how often every element/reactant was
present during the simulation (absolute & %). Additionally it would be interesting to extract the development for each species individually and capture the number
of the respective element for each timestep in an array.

**3. Module: Identifying reaction pathways**
This module aims to capture the possible reaction pathways. For this, the discrete bond orders respectively bonds have to be extracted from the files: 

 Timestep 0
 
 Number of particles 640
 
 Max number of bonds per atom 4 with coarse bond order cutoff 0.300
 
 Particle connection table and bond orders
 
 id type nb id_1...id_nb mol bo_1...bo_nb abo nlp q
 
 2 3 0 0         0.088         0.001         0.453
 
 364 1 4 367 361 365 368 0         0.959         1.011         1.083         0.958         4.012         0.000         0.061
 
 101 4 2 104 106 0         1.011         1.191         2.217         1.750        -0.333
 
 102 4 2 105 106 0         1.009         1.194         2.218         1.750        -0.322
 
 103 4 1 106 0         1.951         1.954         2.000        -0.327
 
 104 1 4 101 105 107 108 0         1.011         1.084         0.959         0.958         4.012         0.000         0.034
 
 105 1 4 102 104 110 109 0         1.009         1.084         0.958         0.959         4.010         0.000         0.009

 Combined with the list of unique reactants it should be possible to check the existing reaction pathways. These could be stored in a dictionary.

 **4. Module: Calculating flux/reaction rate of chemical reactions**
Following up on module 3, this module can then trace how often each reaction occurs during the simulation to extract the reaction rates.

 **5. Module: Generating output file**
Subsequently, the key findings like number of times a species existed and chemical reaction rates should be exported in an output file

 **6. Module: Visualization (optional)**
Optionally, a function visualize different variables can be emplooyed e.g. plotting number of species and system energy can be added


## Alternative Workflow (#2): Machine learning enhancement of existing pyretis-pyvisa library
This project would aim to extend the existing pyretis-pyvisa library by adding machine learning further machine learning functionalities e.g SVM. 

 **1. Module: Access files and information produced by pyretis**
Initially it is important to read/access the relevant data of the pyretis simulation run, likely in the form of files and save them in 
adequate variables and formats.

 **2. Module: Implement function to perform ML method**
COnstruct classes or just functions that perform machine learning methods to process the output. Currently methodologies like clustering,
decision trees and principle component analysis already exist. Possible applications could be state vector machine (SVM).







