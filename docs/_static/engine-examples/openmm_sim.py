from openmm import app
import openmm as mm
from openmm import unit

pdb = app.PDBFile('input.pdb')
forcefield = app.ForceField('amber99sbildn.xml', 'tip3p.xml')

system = forcefield.createSystem(pdb.topology, nonbondedMethod=app.PME,
                                 nonbondedCutoff=1.0*unit.nanometers,
                                 constraints=app.HBonds, rigidWater=True,
                                 ewaldErrorTolerance=0.0005)
integrator = mm.LangevinIntegrator(300*unit.kelvin,
                                   1.0/unit.picoseconds,
                                   2.0*unit.femtoseconds)
integrator.setConstraintTolerance(0.00001)

# Check with "python -m simtk.testInstallation" which platforms are available
# Here I use CUDA, but CPU is more commonly available
# platform = mm.Platform.getPlatformByName('CPU')
platform = mm.Platform.getPlatformByName('CUDA')
simulation = app.Simulation(pdb.topology, system, integrator, platform)
simulation.context.setPositions(pdb.positions)
