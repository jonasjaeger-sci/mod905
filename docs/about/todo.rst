.. _todo-notes:

####
Todo
####

pyretis is still in development. This is a list of work that remains to do
or could be considered:

- Finish input file format.

- Interface GROMACS, LAMMPS, CP2K, etc.

- Consider simplification of potential functions. We can for instance
  force a specific way of calling them, for instance using the system
  object.

- Consider simplification of the simulation object(s). Is it still useful
  to define them in terms of tasks or should we simplify it. Perhaps we
  can have a task-based simulation base object and a more strict simulation
  object. If we assume that the pareto principle holds, 80% of the time the
  more strict object will be used - since these define the most common
  simulation tasks.

- Add NVT capabilities. This is probably not so important, compared with
  implementing a GROMACS, LAMMPS etc. interface.

- Add restart capabilities.

- Consider if we need to do structural changes for allowing parallel
  simulations.

- Include option for storing/loading binary files

- Consider more carefully the reversing of paths: Will we need to recalculate
  order parameters here?

- Investigate where we should write c/FORTRAN code. The block error analysis
  is one example where we perhaps can speed up things? Or could this be done
  in parallel?

- Or maybe we can use Julia for something?

- Investigate if certain parts (for instance the analysis) can be made faster
  by making use of multiprocessing.

- The reports should be nicer. There should also be an option to select
  the units to output. Also, raw data should be stored so that it's easy
  to redo a report with different units for instance.
