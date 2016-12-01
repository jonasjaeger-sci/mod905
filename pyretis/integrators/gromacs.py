# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""
Example for an external pyretis interface.

In this example we will interfaces a custom made program
which performs molecular dynamics.

In order to interface an external program the following
methods are needed:
"""
import logging
import os
import shutil
import tempfile
import numpy as np
from pyretis.integrators import ExternalScript
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
    if len(rawdata['VELOCITY']) == 0:
        # No velicities were found in the input file.
        xyzdata['VELOCITY'] = np.zeros_like(xyzdata['POSITION'])
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
    time_step : float
        The time step used in the GROMACS MD simulation.
    subcycles : integer
        The number of steps each GROMACS MD run is composed of.
    """

    def __init__(self, exe, input_path, input_files, time_step, subcycles):
        """Initiate the script.

        Parameters
        ----------
        exe : string
            The GROMACS executable.
        input_path : string
            The path to where the input files are stored.
        input_files : dict
            This dictionary contains the names of the input files.
        time_step : float
            The time step used in the GROMACS MD simulation.
        subcycles : integer
            The number of steps each GROMACS MD run is composed of.
        """
        super(GromacsExt, self).__init__('GROMASC external script', exe,
                                         time_step, subcycles)
        self.input_path = os.path.join(os.getcwd(), input_path)
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

    def execute_grompp(self, mdp_file, config, deffnm, exe_dir=None):
        """Method to execute the GROMACS preprocessor.

        This step is unique to GROMACS and is included here
        as its own method.

        Parameters
        ----------
        mdp_file : string
            The path to the mdp file.
        config : string
            The path to the GROMACS config file to use as input.
        deffnm : string
            A string used to name the GROMACS files.
        exe_dir : string or None
            If different from None, this selects a working directory
            for grompp.

        Returns
        -------
        out_files : dict
            This dict contains files that were created by the GROMACS
            preprocessor.
        """
        topol = self.input_files['topology']
        tpr = '{}.tpr'.format(deffnm)
        cmd = [self.exe, 'grompp', '-f', mdp_file, '-c', config,
               '-p', topol, '-o', tpr]
        self.execute_command(cmd, cwd=exe_dir)
        out_files = {'tpr': tpr, 'mdout': 'mdout.mdp'}
        return out_files

    def execute_mdrun(self, tprfile, deffnm, exe_dir):
        """Method to execute GROMACS.

        This method is intended as the initial ``gmx mdrun`` executed.
        That is, we here assume that we do not continue a simulation.

        Parameters
        ----------
        tprfile : string
            The .tpr file to use for executing GROMACS.
        deffnm : string
            To give the GROMACS simulation a name.
        exe_dir : string or None
            If different from None, mdrun will be executed in
            this directory.

        Returns
        -------
        out_files : dict
            This dict contains the output files created by mdrun.
            Note that we here hard code the file names.
        """
        confout = '{}.g96'.format(deffnm)
        cmd = [self.exe, 'mdrun', '-s', tprfile, '-deffnm', deffnm,
               '-c', confout]
        self.execute_command(cmd, cwd=exe_dir)
        out_files = {'conf': confout}
        for key in ('cpt', 'edr', 'log', 'trr'):
            out_files[key] = '{}.{}'.format(deffnm, key)
        return out_files

    def execute_mdrun_continue(self, tprfile, cptfile, deffnm, exe_dir):
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
        exe_dir : string or None
            If different from None, mdrun will be executed in
            this directory.

        Returns
        -------
        out_files : dict
            The output files created/appended by GROMACS when we
            continue the simulation.
        """
        confout = '{}.g96'.format(deffnm)
        if os.path.isfile(confout):
            os.remove(confout)
        cmd = [self.exe, 'mdrun', '-s', tprfile, '-cpi', cptfile,
               '-append', '-deffnm', deffnm, '-c', confout]
        self.execute_command(cmd, cwd=exe_dir)
        out_files = {'conf': confout}
        for key in ('cpt', 'edr', 'log', 'trr'):
            out_files[key] = '{}.{}'.format(deffnm, key)
        return out_files

    def extend_gromacs(self, tprfile, time, exe_dir):
        """Method to extend a GROMACS simulation.

        Parameters
        ----------
        tprfile : string
            The file to read for extending.
        time : float
            The time (in ps) to extend the simulation by.
        exe_dir : string or None
            If different from None, mdrun will be executed in
            this directory.

        Returns
        -------
        out_files : dict
            The files created by GROMACS when we extend.
        """
        tpxout = 'ext_{}'.format(tprfile)
        if os.path.isfile(tpxout):
            os.remove(tpxout)
        cmd = [self.exe, 'convert-tpr', '-s', tprfile,
               '-extend', '{}'.format(time), '-o', tpxout]
        self.execute_command(cmd, cwd=exe_dir)
        out_files = {'tpr': tpxout}
        return out_files

    def execute_until(self, initial, system, settings, reverse=False,
                      exe_dir=None):
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
        reverse : boolean
            If True, we will run in the reverse direction.
        exe_dir : string or None
            The directory where we will execute GROMACS.

        Returns
        -------
        out_files : dict
            Files generated by GROMACS.
        all_order : list
            A list containing the order parameters, indexes (for
            finding configurations inside trajectory files) and
            the path to the file containing the trajectory.
        """
        if reverse:
            #EXE_DIR = 'trajb'
            name = 'trajB_new'
            basepath = os.path.dirname(initial)
            localfile = os.path.basename(initial)
            initial_conf = os.path.join(basepath, 'rev_{}'.format(localfile))
            self.reverse_velocities(initial, initial_conf)
        else:
            #EXE_DIR = 'trajf'
            name = 'trajF_new'
            initial_conf = initial


        ext_time = self.time_step * self.subcycles

        order = self.calculate_order_parameter(system,
                                               initial_conf)
        tpr_file = None
        cpt_file = None
        all_order = [order, 0, '{}.trr'.format(name)]
        for i in range(settings['steps']):
            if i == 0:
                out_grompp = self.execute_grompp(self.input_files['input'],
                                                 initial_conf,
                                                 name,
                                                 exe_dir=exe_dir)
                tpr_file = out_grompp['tpr']
                out_mdrun = self.execute_mdrun(tpr_file,
                                               name, exe_dir=exe_dir)
                cpt_file = out_mdrun['cpt']
            else:
                out_grompp = self.extend_gromacs(tpr_file, ext_time,
                                                 exe_dir=exe_dir)
                ext_tpr_file = out_grompp['tpr']
                out_mdrun = self.execute_mdrun_continue(ext_tpr_file, cpt_file, name,
                                                        exe_dir=exe_dir)
                # Move extended tpr so that we can continue extending:
                os.replace(os.path.join(exe_dir, ext_tpr_file),
                           os.path.join(exe_dir, tpr_file))
            conf_abs = os.path.join(exe_dir, out_mdrun['conf'])
            if conf_abs is not None:
                order = self.calculate_order_parameter(system,
                                                       conf_abs)
                all_order.append([order, i+1, '{}.trr'.format(name)])
                # Remove this file as it's not needed anymore:
                os.remove(conf_abs)
        # Call some kind of clean-up and remove the files we will never need:
        # Remove from the EXE-DIR:
        # for key in ('mdout.mdp', '{}.log'.format(name),
        #            '{}_prev.cpt'.format(name)):
        #    filename = os.path.join(EXE_DIR, key)
        #    #os.remove(filename)
        out_files = {}
        for key in ('trr', 'tpr', 'edr'):
            out_files[key] = '{}.{}'.format(name, key)
        return out_files, all_order

    def get_trr_frame(self, trr_file, tpr_file, idx, out_file):
        """Extract a frame from a .trr file.

        Parameters
        ----------
        trr_file : string
            The GROMACS .trr file to open.
        tpr_file : string
            The GROMACS .tpr file for the system.
        idx : integer
            The frame number we look for.
        out_file : string
            The file to dump to.

        Note
        ----
        This will only properly work in the frames in the .trr are
        separated uniformly.
        """
        time1 = (idx - 1) * self.time_step * self.subcycles
        time2 = idx * self.time_step * self.subcycles
        cmd = [self.exe, 'trjconv',
               '-f', trr_file,
               '-s', tpr_file,
               '-o', out_file,
               '-b', '{}'.format(time1),
               '-dump', '{}'.format(time2)]
        self.execute_command(cmd, inputs=b'0', cwd=None)
        return None

    def prepare_shooting_point(self, idx, input_files, output_file):
        """Method to create initial configuration for a shooting move.

        Parameters
        ----------
        idx : integer
            The index for the shooting point referring to a position
            in the input .trr file.
        input_files : dict of strings
            These are the input files we need to get the shooting point.
            Here we expect to find keys for the trajectory .trr file
            (key: ``trr``) and a .tpr file (key: ``tpr``).
        output_file : string
            Where to store the configuration to use for shooting.

        Returns
        -------
        output_file : string
            The name of the file created.
        """
        prevdir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Collect the configuration:
            tmp_config = os.path.join(tmp_dir, 'for_shooting.g96')
            self.get_trr_frame(input_files['trr'], input_files['tpr'],
                               idx, tmp_config)
            # Create output file to generate velocities:
            settings = {'gen_vel': 'yes', 'gen_seed': -1, 'nsteps': 0}
            tmp_mdp = os.path.join(tmp_dir, 'genvel.mdp')
            self.modify_input(self.input_files['input'], tmp_mdp, settings,
                              delim='=')
            # Run grompp for this input file:
            out_grompp = self.execute_grompp(tmp_mdp, tmp_config, 'genvel',
                                             exe_dir=tmp_dir)
            # Run gromacs for this tpr file:
            out_mdrun = self.execute_mdrun(out_grompp['tpr'],
                                           'genvel', exe_dir=tmp_dir)
            confout = os.path.join(tmp_dir, out_mdrun['conf'])
            # Copy back the g96 file with velocities:
            dest = os.path.join(prevdir, output_file)
            shutil.move(confout, dest)
        return output_file

    @staticmethod
    def read_configuration(filename):
        """Method to read output from GROMACS .g96 files.

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
        _, xyz, vel = read_gromos96_file(filename)
        return xyz, vel

    @staticmethod
    def reverse_velocities(filename, outfile):
        """Method to reverse velocity in a given snapshot.

        Parameters
        ----------
        filename : string
            The configuration to reverse velocities in.
        outfile : string
            The output file for storing the configuration with
            reversed velocities.
        """
        txt, xyz, vel = read_gromos96_file(filename)
        write_gromos96_file(outfile, txt, xyz, -vel)
        return None
