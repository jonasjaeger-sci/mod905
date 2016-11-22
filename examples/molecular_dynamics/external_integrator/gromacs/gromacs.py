# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""
Example for an external pyretis interface.

In this example we will interfaces a custom made program
which performs molecular dynamics.

In order to interface an external program the following
methods are needed:
"""
# Just to handle imports relative to this file
import sys
import os
import subprocess
import numpy as np
from pyretis.integrators import ExternalScript
from pyretis.inout.writers.traj import read_gromacs_file
# These are for the __main__.
from pyretis.core.units import create_conversion_factors
from pyretis.inout.settings import create_system
from pyretis.inout.settings import create_orderparameter

# Just so that we find the files:
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


class GromacsScript(ExternalScript):
    """GromacsScript(ExternalScript).

    This class defines the interface to GROMACS.

    Attributes
    ----------
    """

    def __init__(self):
        """Initiate the script."""
        super(GromacsScript, self).__init__('GROMASC example script')
        self.exe = 'gmx_5.1.4'
        self.input_path = 'ext_input'

        input_files = {'configuration': 'conf.gro',
                       'input': 'grompp.mdp',
                       'topology': 'topol.top'}
        self.input_files = {}
        for key, val in input_files.items():
            self.input_files[key] = os.path.join(self.input_path, val)

    def execute_grompp(self, config, deffnm):
        """Method to execute the GROMACS preprocessor.

        This step is unique to GROMACS and is included here
        as its own method.

        Parameters
        ----------
        config : string
            The path to the GROMACS gro file to use as input.
        deffnm : string
            A string used to name the GROMACS files.

        Returns
        -------
        tpr : string
            The tpr file which was created by the GROMACS preprocessor.
        """
        mdp = self.input_files['input']
        topol = self.input_files['topology']
        tpr = '{}.tpr'.format(deffnm)
        cmd = '{} grompp -f {} -c {} -p {} -o {}'.format(self.exe,
                                                         mdp,
                                                         config,
                                                         topol,
                                                         tpr)
        exe = subprocess.check_call(cmd, shell=True)
        return tpr

    def propagate(self):
        pass

    def execute_external(self):
        pass

    def execute_mdrun(self, tprfile, deffnm):
        """Method to execute GROMACS.

        This method is intended as the initial ``gmx mdrun`` executed.
        That is, we here assume that we do not continue a simulation.

        Parameters
        ----------
        tprfile : string
            The .tpr file to use for executing GROMACS.
        deffnm : string
            To give the GROMACS simulation a name.

        Returns
        -------
        cpt_file : string
            The name of the GROMACS check point file created.
        """
        confout = '{}.gro'.format(deffnm)
        cmd = '{} mdrun -s {} -deffnm {}'.format(self.exe,
                                                 tprfile,
                                                 deffnm)
        cpt_file = '{}.cpt'.format(deffnm)
        exe = subprocess.check_call(cmd, shell=True)
        return cpt_file, confout

    def execute_mdrun_continue(self, tprfile, cptfile, deffnm):
        """Method to continue the execution of GROMACS.

        Here, we assume that we have already executed ``gmx mdrun`` and
        that we are to append and continue a simulation.

        Parameters
        ----------
        tprfile : string
            The .tpr file which defines the simulation.
        cptfile : string
            The last check point file .cpt from the previous
            run.
        deffnm : string
            To give the GROMACS simulation a name.
        """
        confout = '{}.gro'.format(deffnm)
        if os.path.isfile(confout):
            os.remove(confout)
        cmd = '{} mdrun -s {} -cpi {} -append -deffnm {}'.format(self.exe,
                                                                 tprfile,
                                                                 cptfile,
                                                                 deffnm)
        exe = subprocess.check_call(cmd, shell=True)
        return confout

    def extend_gromacs(self, tprfile, time):
        """Method to extend a GROMACS simulation.

        Parameters
        ----------
        tprfile : string
            The file to read for extending.
        time : float
            The time (in ps) to extend the simulation by.

        Returns
        -------
        tpxout : string
            The tpr file created that extends the simulation.
        """
        tpxout = 'ext_{}'.format(tprfile)
        if os.path.isfile(tpxout):
            os.remove(tpxout)
        cmd = '{} convert-tpr -s {} -extend {} -o {}'.format(self.exe,
                                                             tprfile,
                                                             time,
                                                             tpxout)
        exe = subprocess.check_call(cmd, shell=True)
        return tpxout

    def execute_until(self, initial, system, settings, orderp):
        """Propagate until condition is met.

        Parameters
        ----------
        initial : string
            The initial positions.
        system : object like `pyretis.core.system`
            The object the order parameter is acting on.
        settings : dict
            This dictionary contains settings used for the
            simulation.
        orderp : object like `pyretis.orderparameter.OrderParameter`
            The object responsible for calculating the order parameter.

        Returns
        -------
        out : list
            A list containing the order parameters and the path to the
            file containing the trajectory.
        """
        name = 'test2'
        ext_time = settings['subcycles'] * settings['timestep']
        tpr = None
        cpt_file = None
        confout = None
        ext_tpr = None
        order = self.calculate_order_parameter(orderp,
                                               system,
                                               initial)
        all_order = [order]
        for i in range(settings['steps']):
            if i == 0:
                tpr = self.execute_grompp(initial, name)
                cpt_file, confout = gro.execute_mdrun(tpr, name)
            else:
                ext_tpr = gro.extend_gromacs(tpr, ext_time)
                confout = gro.execute_mdrun_continue(ext_tpr, cpt_file, name)
                # move ext_tpr to tpr so that we can extend even more:
                os.rename(ext_tpr, tpr)
            if confout is not None:
                order = self.calculate_order_parameter(orderp,
                                                       system,
                                                       confout)
                all_order.append(order)
        print(all_order)

    def get_trr_frame(self, trr_file, tpr_file, idx, time_step, out_file):
        """Extract a frame from a .trr file.

        Parameters
        ----------
        trr_file : string
            The GROMACS .trr file to open.
        tpr_file : string
            The GROMACS .tpr file for the system.
        idx : integer
            The frame number we look for.
        time_step : float
            The time step used in the simulation.
        out_file : string
            The file to dump to.

        Note
        ----
        This will only proberly work in the frames in the .trr are
        separated uniformly.
        """
        cmd = 'echo 0 | {} trjconv -f {} -s {} -o {} -b {} -dump {}'
        cmd = cmd.format(self.exe, trr_file, tpr_file, out_file,
                         (idx-1) * time_step, idx*time_step)
        exe = subprocess.check_call(cmd, shell=True)
        return exe

    def calculate_order_parameter(self, orderp, system, filename):
        """Calculate the order parameter from a given file.

        Parameters
        ----------
        orderp : object like `pyretis.orderparameter.OrderParameter`
            The object responsible for calculating the order parameter.
        system : object like `pyretis.core.system`
            The object the order parameter is acting on.
        filename : string
            The file with the configuration for which we want to
            calculate the order parameter.

        Returns
        -------
        out : float
            The order parameter.
        """ 
        snapshot = None
        for snapshot in read_gromacs_file(filename):
            pass
        xyz = np.column_stack((snapshot['x'],
                               snapshot['y'],
                               snapshot['z']))
        vel = np.column_stack((snapshot['vx'],
                               snapshot['vy'],
                               snapshot['vz']))
        system.particles.pos = xyz
        system.particles.vel = vel
        return orderp.calculate(system)

    def read_configuration(self, filename):
        """Method to read output from GROMACS.

        Parameters
        ----------
        filename : string
            The file to read the configuration from.

        Returns
        -------
        xyz : numpy.array
            The positions.
        vel : numpy.array
            The velocities.
        """
        snapshot = None
        for snapshot in read_gromacs_file(filename):
            pass
        xyz = np.column_stack((snapshot['x'],
                               snapshot['y'],
                               snapshot['z']))
        vel = np.column_stack((snapshot['vx'],
                               snapshot['vy'],
                               snapshot['vz']))
        return xyz, vel

    def write_configuration(self):
        """Method to write config for GROMACS."""
        pass

    def read_input(self):
        pass
    
    def write_input(self, outputfile, nsteps, timestep):
        infile = self.input_files['input']
        with open(outputfile, 'w') as fileout:
            with open(infile, 'r') as filein:
                for lines in filein:
                    if lines.startswith('nsteps') and lines.find('=') != -1:
                        fileout.write('nsteps = {}\n'.format(nsteps))
                    elif lines.startswith('dt') and lines.find('=') != -1:
                        fileout.write('dt = {}\n'.format(timestep))
                    else:
                        fileout.write(lines)

    def read_output(self):
        pass


if __name__ == '__main__':
    # Run a test:
    settings = {}
    
    settings['system'] = {'units': 'gromacs',
                          'temperature': 300,
                          'dimensions': 3}
    
    settings['particles'] = {'position': {'file': 'ext_input/conf.gro'}}
    
    settings['orderparameter'] = {'class': 'Position',
                                  'index': 1472,
                                  'name': 'Gromacs distance',
                                  'periodic': True,
                                  'dim': 'z'}
    create_conversion_factors(settings['system']['units'])
    
    system = create_system(settings)
    orderp = create_orderparameter(settings)

    gro = GromacsScript()
    md_settings = {'steps': 20, 'subcycles': 5, 'timestep': 0.002}
    gro.execute_until('initial.gro', system, md_settings, orderp)
    gro.get_trr_frame('test2.trr', 'test2.tpr', 10, 0.002, 'output.gro')
