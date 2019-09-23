.. _examples-openmm:

Running a PyRETIS simulation with OpenMM
========================================

In this example we will show the interface between ``OpenMM`` and |pyretis|. 
The implementation, so far, only exists as a library. So instead of using the
standard |pyretis| input files, this example will consist of python scripts. 
They will import |pyretis| and ``OpenMM`` objects and use them directly. 

First we will have to generate an OpenMM ``Simulation`` object. We use the online
tool `OpenMM Script Builder <http://builder.openmm.org/>`_ to generate the example
:download:`pdb</_static/engine-examples/input.pdb>` of 2 water molecules. 

.. literalinclude:: /_static/engine-examples/openmm_sim.py


With this ``Simulation`` object we can now construct the internal |pyretis| system
and ``OpenMMEngine`` objects

.. code-block:: python
    
    import simtk.unit as u
    from pyretis.core import System, Particles
    from pyretis.core.box import create_box, box_matrix_to_list
    from pyretis.engines import OpenMMEngine
    def make_pyretis_system(simulation):                                            
        """Makes PyRETIS system from OpenMM Simulation."""                          
        state = simulation.context.getState(getPositions=True, getVelocities=True)  
        box = state.getPeriodicBoxVectors(asNumpy=True).T                           
        box = create_box(cell=box_matrix_to_list(box),                              
                         periodic=[True, True, True])                               
        system = System(units='gromacs', box=box,                                   
                        temperature=simulation.integrator.getTemperature())         
        system.particles = Particles(system.get_dim())                              
        pos = state.getPositions(asNumpy=True)                                      
        vel = state.getVelocities(asNumpy=True)                                     
        for i, atom in enumerate(simulation.topology.atoms()):                      
            mass = simulation.system.getParticleMass(i)                             
            mass = mass.value_in_unit(u.grams/u.mole)                               
            name = atom.name                                                        
            system.particles.add_particle(pos=pos[i], vel=vel[i],                   
                                          force=[None, None, None],                 
                                          mass=mass, name=name)                     
        return system  
    
    # Make system and initialise the engine.
    system = make_pyretis_system(simulation=simulation)
    engine = OpenMMEngine(simulation=simulation)

From this point on we can define an order parameter, interfaces and propagate
with this ``engine`` inside the TIS ensemble.

.. code-block:: python

    from pyretis.core.random_gen import RandomGenerator
    from pyretis.core.path import Path
    from pyretis.orderparameter import Distance
    import numpy as np

    # Get a random number generator
    rgen = RandomGenerator(seed=1)
    
    # Define an empty path of a specific max length (10 in this case)
    path = Path(None, maxlen=10)
    
    # Define the order parameter, the distance between the two water oxygens
    order_parameter = Distance((0, 3), periodic=False)

    # Define state A, Interface and state B of the sampled TIS ensemble.
    ifaces = (1, 2, 3)
    
    # Modify the velocities of the shooting point 
    engine.modify_velocities(system, rgen=rgen,
                             sigma_v=None, aimless=True,
                             momentum=False, rescale=None)

    # Propegate forward
    engine.propagate(path=path, initial_system=system,
                     order_function=order_parameter,
                     interfaces=ifaces , reverse=False)


The ``path`` variable now will have the newly generated path for the user to apply
acceptance criteria on. The communication to and from the OpenMM kernel
has been reduced to a minimum, as communication can be expensive for simulations
on GPUs. Further integration with the |pyretis| application 
layer is envisioned for later |pyretis| releases.

