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


From this point we use :download:`this altered rst</_static/engine-examples/openmm_retis.rst>` to set up the rest of the `RETIS` simulation.

.. code-block:: python

    # Load the settings
    from pyretis.inout.settings import parse_settings_file
    from pyretis.inout.setup import create_simulation
    settings = parse_settings_file('openmm_retis.rst') 
    
    # Now we need to override some things due to pyretis internals
    def mock_potential_and_force():                                                 
        pass                                                                        
                                                                                
    system.potential_and_force = mock_potential_and_force # Not used, but legacy requirement
    engine.engine_type = 'internal' # was OpenMM                                    
                                                                                
    kwargs = {"system": system,                                                     
              "engine": engine}                                                     
    pyretis_simulation = create_simulation(settings=settings, kwargs=kwargs)        

Now that we have set up the ``pyretis_simulation``, we can setup the outputs,
initiate the ensmebles and run it. (Make sure you have write
permisions in the running directory)

.. code-block:: python

    # If the default output colors are too flamboyant you can reset the colors
    # import colorama
    # colorama.init(autoreset=True)

    # Setup the outputs                                                          
    pyretis_simulation.set_up_output(settings=settings)                             
                                                     
    # Initiate the simulation
    pyretis_simulation.initiate(settings=settings)
    
    # Run through the simulation generator to run the simulation
    for step in pyretis_simulation.run():
        pass    

