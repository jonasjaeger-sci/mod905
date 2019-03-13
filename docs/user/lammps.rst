.. _user-guide-lammps:

Running LAMMPS with PyRETIS
===========================

We have prepared some extra documentation for instructions on how to use the `LAMMPS Molecular Dynamics Simulator <https://lammps.sandia.gov/doc/Manual.html>`_ with |pyretis|.

Standard LAMMPS input
---------------------

The LAMMPS – |pyretis| interface is constructing to take advantage of LAMMPS internal ability to perform on-the-fly calculations. |pyretis| expects a `LAMMPS input file <https://lammps.sandia.gov/doc/Commands_input.html>`_ to be present in the folder from which it is executed. This input file should refer to all the information LAMMPS needs to run a simulation on your system, including but not limited to:

* Initial coordinates, molecular topology  (optional: force field coefficients) in a `LAMMPS data file <https://lammps.sandia.gov/doc/2001/data_format.html>`_. This file can be read into LAMMPS using the `read_data <https://lammps.sandia.gov/doc/read_data.html>`_ command.

- Information about units, bonded and non-bonded force field coefficients, (if applicable) long-range electrostatics methods.

* A `LAMMPS fix <https://lammps.sandia.gov/doc/fix.html>`_ that will integrate the motion of the atoms in the system.

The LAMMPS input file should contain everything that is needed to run a normal MD simulation except for the `run <https://lammps.sandia.gov/doc/run.html>`_ command.

PyRETIS requirements for LAMMPS input
-------------------------------------

In addition to the standard input requirements for a LAMMPS simulation, there are additional requirements for running LAMMPS with |pyretis|.

- **Mandatory Format:** The target temperature for the RETIS simulations must be set to a `LAMMPS equal-style variable <https://lammps.sandia.gov/doc/variable.html>`_ called SET_TEMP. An example is shown below:

  .. code-block:: pyretis

     variable SET_TEMP equal 300.0

In the above example, the system temperature is set to 300.0 K (assuming real LAMMPS units).

* **Mandatory Format:** The order parameter(s) that |pyretis| will keep track of should be declared as `LAMMPS equal-style variable(s) <https://lammps.sandia.gov/doc/variable.html>`_. Multiple order parameters can be defined, but the first order parameter (op_1) will be used by |pyretis| to determine interface crossing.

  .. code-block:: pyretis

     variable op_1 equal c_1
     variable op_2 equal c_2

  In the above example, two order parameters will be tracked and output by LAMMPS to a file called order.txt. The first column of order.txt will be the LAMMPS step, the second column will be op_1, the third column will be op_2. Only op_1 will be used by LAMMPS to determine the crossing of the first or last interface and stop the simulation.

  The above example refers to `LAMMPS compute <https://lammps.sandia.gov/doc/compute.html>`_, referenced by c_1 and c_2, that return *scalar* values. Using combination of `LAMMPS compute <https://lammps.sandia.gov/doc/compute.html>`_ and `LAMMPS variable <https://lammps.sandia.gov/doc/variable.html>`_ commands, a large number of calculations can be performed internally by LAMMPS. `LAMMPS can also call Python <https://lammps.sandia.gov/doc/Python_call.html>`_ scripts to facilitate more calculations. For best coding practices, the order parameter calculations can be scripted in a separate file (order.in) and included in the main LAMMPS input script as follows:

  .. code-block:: pyretis

     include order.in

Restrictions
------------

There are some restrictions for the LAMMPS-|pyretis| interface.

- Motion should be propagated using NVE dynamics, as NVT/NPT dynamics have not been shown to be accurately time-reversible in practice.

* We recommend that the `SHAKE <https://lammps.sandia.gov/doc/fix_shake.html>`_ algorithm not be used, because in practice it produces non-time reversible results due to the iterative nature of the algorithm.

- Order Parameters must **NOT** depend on the direction of velocity components.

Notes
-----

The subcycle length, defined in the |pyretis| input file, refers to how often LAMMPS will print to the log file and the order.txt file.
