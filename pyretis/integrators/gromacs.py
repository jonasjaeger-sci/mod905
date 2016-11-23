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
import logging
import os
import numpy as np
from pyretis.integrators import ExternalScript
from pyretis.inout.writers.traj import read_gromacs_file
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


def read_gromos96_file(filename):
    """Read a single configuration g96 file.

    Parameters
    ----------
    filename : string
        The file to read.

    Returns
    -------
    rawdata : dict of list of strings
        This is the raw data read from the file grouped into sections.
        Note that this does not include the actual positions and
        velocities as these are returned separately.
    xyz : numpy.array
        The positions.
    vel : numpy.array
        The velocities.
    """
    _len = 15
    _pos = 24
    rawdata = {'TITLE': [], 'POSITION': [], 'VELOCITY': [], 'BOX': []}
    section = None
    with open(filename, 'r') as gromosfile:
        for lines in gromosfile:
            new_section = False
            stripline = lines.strip()
            if stripline == 'END':
                continue
            for key in rawdata:
                if stripline == key:
                    new_section = True
                    section = key
                    break
            if new_section:
                continue
            rawdata[section].append(lines.rstrip())
    txtdata = {}
    xyzdata = {}
    for key in ('POSITION', 'VELOCITY'):
        txtdata[key] = []
        xyzdata[key] = []
        for line in rawdata[key]:
            txt = line[:_pos]
            txtdata[key].append(txt)
            pos = [float(line[i:i+_len]) for i in range(_pos, 4*_len, _len)]
            xyzdata[key].append(pos)
        xyzdata[key] = np.array(xyzdata[key])
    rawdata['POSITION'] = txtdata['POSITION']
    rawdata['VELOCITY'] = txtdata['VELOCITY']
    return rawdata, xyzdata['POSITION'], xyzdata['VELOCITY']


def write_gromos96_file(filename, raw, xyz, vel):
    """Write configuration in GROMACS g96 format.

    Parameters
    ----------
    filename : string
        The name of the file to create.
    raw : dict of lists of strings
        This contains the raw data read from a .g96 file.
    xyz : numpy.array
        The positions to write.
    vel : numpy.array
        The velocities to write.
    """
    _keys = ('TITLE', 'POSITION', 'VELOCITY', 'BOX')
    _fmt = '{0:}{1:15.9f}{2:15.9f}{3:15.9f}\n'
    with open(filename, 'w') as outfile:
        for key in _keys:
            outfile.write('{}\n'.format(key))
            for i, line in enumerate(raw[key]):
                if key == 'POSITION':
                    outfile.write(_fmt.format(line, *xyz[i]))
                elif key == 'VELOCITY':
                    outfile.write(_fmt.format(line, *vel[i]))
                else:
                    outfile.write('{}\n'.format(line))
            outfile.write('END\n')


class GromacsExt(ExternalScript):
    """GromacsExt(ExternalScript).

    This class defines the interface to GROMACS.

    Attributes
    ----------
    exe : string
        The command for executing GROMACS. Note that we are assuming
        that we are using version 5 of GROMACS.
    input_path : string
        The directory where the input files are stored.
    input_files : dict of strings
        The names of the input files. We expect to find the keys
        ``'configuration'``, ``'input'`` ``'topology'``.
    """

    def __init__(self, exe, input_path, input_files):
        """Initiate the script.

        Parameters
        ----------
        exe : string
            The GROMACS executable.
        input_path : string
            The path to where the input files are stored.
        input_files : dict
            This dictionary contains the names of the input files.
        """
        super(GromacsExt, self).__init__('GROMASC script')
        self.exe = exe
        self.input_path = input_path
        self.input_files = {}
        for key, val in input_files.items():
            self.input_files[key] = os.path.join(self.input_path, val)
        keys = ('configuration', 'input', 'topology')
        for key in keys:
            if key not in self.input_files:
                msg = ('Gromacs integrator is missing '
                       'input file "{}"').format(key)
                logger.error(msg)
                raise ValueError(msg)

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
        cmd = [self.exe, 'grompp', '-f', mdp, '-c', config,
               '-p', topol, '-o', tpr]
        self.execute_command(cmd)
        return tpr

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
        cmd = [self.exe, 'mdrun', '-s', tprfile, '-deffnm', deffnm]
        cpt_file = '{}.cpt'.format(deffnm)
        self.execute_command(cmd)
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
        cmd = [self.exe, 'mdrun', '-s', tprfile, '-cpi', cptfile,
               '-append', '-deffnm', deffnm]
        self.execute_command(cmd)
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
        cmd = [self.exe, 'convert-tpr', '-s', tprfile,
               '-extend', '{}'.format(time), '-o', tpxout]
        self.execute_command(cmd)
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
                cpt_file, confout = self.execute_mdrun(tpr, name)
            else:
                ext_tpr = self.extend_gromacs(tpr, ext_time)
                confout = self.execute_mdrun_continue(ext_tpr, cpt_file, name)
                # move ext_tpr to tpr so that we can extend even more:
                os.rename(ext_tpr, tpr)
            if confout is not None:
                order = self.calculate_order_parameter(orderp,
                                                       system,
                                                       confout)
                all_order.append(order)
        return all_order

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
        cmd = [self.exe, 'trjconv', '-f', trr_file, '-s', tpr_file,
               '-o', out_file, '-b', '{}'.format((idx-1) * time_step),
               '-dump', '{}'.format(idx*time_step)]
        self.execute_command(cmd, inputs=b'0')
        return None

    def read_configuration(self, filename):
        """Method to read output from GROMACS .gro files.

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

    def write_input(self, outputfile, nsteps):
        pass

    def read_output(self):
        pass
