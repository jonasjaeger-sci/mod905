# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""A GROMACS external MD integrator interface.

This module defines a class for using GROMACS as an external engine.

Important classes defined here
------------------------------

GromacsEngine
    A class responsible for interfacing GROMACS.
"""
import logging
import os
import shlex
import tempfile
import numpy as np
from pyretis.engines.external import ExternalMDEngine
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


def read_xvg_file(filename):
    """Return data in xvg file as numpy array."""
    data = []
    legends = []
    with open(filename, 'r') as fileh:
        for lines in fileh:
            if lines.startswith('@ s') and lines.find('legend') != -1:
                legend = lines.split('legend')[-1].strip()
                legend = legend.replace('"', '')
                legends.append(legend.lower())
            else:
                if lines.startswith('#') or lines.startswith('@'):
                    pass
                else:
                    data.append([float(i) for i in lines.split()])
    data = np.array(data)
    data_dict = {'step': data[:, 0]}
    for i, key in enumerate(legends):
        data_dict[key] = data[:, i+1]
    return data_dict


class GromacsEngine(ExternalMDEngine):
    """A class for interfacing GROMACS.

    This class defines the interface to GROMACS.

    Attributes
    ----------
    gmx : string
        The command for executing GROMACS. Note that we are assuming
        that we are using version 5 of GROMACS.
    mdrun : string
        The command for executing GROMACS mdrun. In some cases this
        executable can be different from ``gmx mdrun``.
    input_path : string
        The directory where the input files are stored.
    input_files : dict of strings
        The names of the input files. We expect to find the keys
        ``'configuration'``, ``'input'`` ``'topology'``.
    timestep : float
        The time step used in the GROMACS MD simulation.
    subcycles : integer
        The number of steps each GROMACS MD run is composed of.
    """

    def __init__(self, gmx, mdrun, input_path, input_files, timestep,
                 subcycles):
        """Initiate the script.

        Parameters
        ----------
        gmx : string
            The GROMACS executable.
        mdrun : string
            The GROMACS mdrun executable.
        input_path : string
            The absolute path to where the input files are stored.
        input_files : dict
            This dictionary contains the names of the input files.
        timestep : float
            The time step used in the GROMACS MD simulation.
        subcycles : integer
            The number of steps each GROMACS MD run is composed of.
        """
        super().__init__('GROMASC external script', timestep,
                         subcycles, 'g96')

        self.gmx = gmx
        # define derived commands
        # For mdrun we do things a bit convolved in case the mdrun command
        # is actually several commands, e.g. ``mpirun mdrun_mpi``.
        self.mdrun = mdrun + ' -s {} -deffnm {} -c {}'
        self.mdrunc = mdrun + ' -s {} -cpi {} -append -deffnm {} -c {}'

        self.input_path = os.path.abspath(input_path)
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
        # Generate a tpr file using the input files:
        out_files = self._execute_grompp(self.input_files['input'],
                                         self.input_files['configuration'],
                                         'topol', self.input_path)
        # This will generate some noise, let's remove files we don't need:
        mdout = os.path.join(self.input_path, out_files['mdout'])
        self.removefile(mdout)
        # We also remove GROMACS backup files:
        self.remove_gromacs_backup_files(self.input_path)
        # Keep the tpr file.
        self.input_files['tpr'] = os.path.join(self.input_path,
                                               out_files['tpr'])

    def _execute_grompp(self, mdp_file, config, deffnm, exe_dir):
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
        cmd = [self.gmx, 'grompp', '-f', mdp_file, '-c', config,
               '-p', topol, '-o', tpr]
        self.execute_command(cmd, cwd=exe_dir)
        out_files = {'tpr': tpr, 'mdout': 'mdout.mdp'}
        return out_files

    def _execute_mdrun(self, tprfile, deffnm, exe_dir):
        """Method to execute GROMACS mdrun.

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
        cmd = shlex.split(self.mdrun.format(tprfile, deffnm, confout))
        self.execute_command(cmd, cwd=exe_dir)
        out_files = {'conf': confout,
                     'cpt_prev': '{}_prev.cpt'.format(deffnm)}
        for key in ('cpt', 'edr', 'log', 'trr'):
            out_files[key] = '{}.{}'.format(deffnm, key)
        return out_files

    def _execute_mdrun_continue(self, tprfile, cptfile, deffnm, exe_dir):
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
        self.removefile(confout)
        cmd = shlex.split(self.mdrunc.format(tprfile, cptfile,
                                             deffnm, confout))
        self.execute_command(cmd, cwd=exe_dir)
        out_files = {'conf': confout}
        for key in ('cpt', 'edr', 'log', 'trr'):
            out_files[key] = '{}.{}'.format(deffnm, key)
        return out_files

    def _extend_gromacs(self, tprfile, time, exe_dir):
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
        self.removefile(tpxout)
        cmd = [self.gmx, 'convert-tpr', '-s', tprfile,
               '-extend', '{}'.format(time), '-o', tpxout]
        self.execute_command(cmd, cwd=exe_dir)
        out_files = {'tpr': tpxout}
        return out_files

    def remove_gromacs_backup_files(self, dirname):
        """Remove files GROMACS has backed up.

        These are files starting with a '#'

        Parameters
        ----------
        dirname : string
            The directory where we are to remove files.
        """
        for entry in os.scandir(dirname):
            if entry.name.startswith('#') and entry.is_file():
                filename = os.path.join(dirname, entry.name)
                self.removefile(filename)

    def extract_frame(self, trr_file, idx, out_file):
        """Extract a frame from a .trr file.

        Parameters
        ----------
        trr_file : string
            The GROMACS .trr file to open.
        idx : integer
            The frame number we look for.
        out_file : string
            The file to dump to.

        Note
        ----
        This will only properly work in the frames in the .trr are
        separated uniformly.
        """
        logger.debug('Extracting .trr frame, idx = %i', idx)
        time1 = (idx - 1) * self.timestep * self.subcycles
        time2 = idx * self.timestep * self.subcycles
        cmd = [self.gmx, 'trjconv',
               '-f', trr_file,
               '-s', self.input_files['tpr'],
               '-o', out_file,
               '-b', '{}'.format(time1),
               '-dump', '{}'.format(time2)]
        self.execute_command(cmd, inputs=b'0', cwd=None)
        return None

    def get_energies(self, energy_file, exe_dir):
        """Return energies from a GROMACS run.

        Parameters
        ----------
        energy_file : string
            The file to read energies from.
        exe_dir : string
            The directory where we look for the energy file.
        """
        cmd = [self.gmx, 'energy', '-f', energy_file]
        self.execute_command(cmd, inputs=b'Potential\nKinetic-En.',
                             cwd=exe_dir)
        xvg_file = os.path.join(exe_dir, 'energy.xvg')
        energy = read_xvg_file(xvg_file)
        self.removefile(xvg_file)
        return energy

    def propagate(self, path, system, order_function, interfaces,
                  reverse=False):
        """Propagate with GROMACS."""

        status = 'Propagate w/GROMACS (reverse = {})'.format(reverse)
        logger.debug(status)
        initial_state = system.particles.get_particle_state()
        initial_file = self.dump_frame(system)
        logger.debug('Initial state: %s', initial_state)

        if reverse:
            name = 'trajB'
        else:
            name = 'trajF'
        # check if we should reverse the velocities in the dumped file:
        if reverse != initial_state['vel']:
            basepath = os.path.dirname(initial_file)
            localfile = os.path.basename(initial_file)
            initial_conf = os.path.join(basepath, 'r_{}'.format(localfile))
            logger.debug('Reversing velocities in initial config.')
            self.reverse_velocities(initial_file, initial_conf)
        else:
            initial_conf = initial_file

        success = False
        left, _, right = interfaces

        # We always start from a singe snapshot config:
        phase_point = {'pos': (initial_conf, None), 'vel': reverse,
                       'vpot': None, 'ekin': None}
        system.particles.set_particle_state(phase_point)
        order = self.calculate_order(order_function, system)
        # In some cases, we don't really have to perform a step as the
        # initial config might be left/right of the interface in
        # question. Here, we will perform a step anyway. This is to be
        # sure that we obtain energies and also a trajectory segment.
        # So, we manually perform the first step:
        out_files = {}
        out_grompp = self._execute_grompp(self.input_files['input'],
                                          initial_conf,
                                          name,
                                          self.exe_dir)
        tpr_file = out_grompp['tpr']
        for key, value in out_grompp.items():
            out_files[key] = value
        out_mdrun = self._execute_mdrun(tpr_file,
                                        name, self.exe_dir)
        for key, value in out_mdrun.items():
            out_files[key] = value
        cpt_file = out_mdrun['cpt']

        # Note: Order is calculated AT THE END of each iteration!
        for i in range(path.maxlen):
            # We first add the current phase point, and then we propagate.
            logger.debug('Current: %9.5g %9.5g %9.5g', left, order[0], right)
            phase_point = {
                'order': order,
                'pos': (os.path.join(self.exe_dir, out_files['trr']), i),
                'vel': reverse, 'vpot': None, 'ekin': None}
            add = path.append(phase_point)
            if not add:
                status = 'Could not add for unknown reason'
                success = False
                break
            if path.ordermin[0] < left:
                status = 'Crossed left interface!'
                success = True
                break
            elif path.ordermax[0] > right:
                status = 'Crossed right interface!'
                success = True
                break
            if path.length == path.maxlen:
                status = 'Max. path length exceeded!'
                success = False
                break
            if i > 0:
                out_grompp = self._extend_gromacs(tpr_file, self.ext_time,
                                                  self.exe_dir)
                ext_tpr_file = out_grompp['tpr']
                for key, value in out_grompp.items():
                    out_files[key] = value
                out_mdrun = self._execute_mdrun_continue(ext_tpr_file,
                                                         cpt_file, name,
                                                         self.exe_dir)
                for key, value in out_mdrun.items():
                    out_files[key] = value
                # Move extended tpr so that we can continue extending:
                os.replace(os.path.join(self.exe_dir, ext_tpr_file),
                           os.path.join(self.exe_dir, tpr_file))
                out_files['tpr'] = tpr_file
            # Calculate order parameter using the output config:
            conf_abs = os.path.join(self.exe_dir, out_mdrun['conf'])
            phase_point = {'pos': (conf_abs, None),
                           'vel': reverse, 'vpot': None, 'ekin': None}
            system.particles.set_particle_state(phase_point)
            order = self.calculate_order(order_function, system)
            self.removefile(conf_abs)
        logger.debug('Obtaining energies for trajectory...')
        energy = self.get_energies(out_files['edr'], self.exe_dir)
        path.vpot = np.copy(energy['potential'])
        path.ekin = np.copy(energy['kinetic en.'])
        system.particles.set_particle_state(initial_state)
        logger.debug('Removing files...')
        for key in ('log', 'mdout', 'cpt', 'cpt_prev', 'tpr', 'edr'):
            filename = os.path.join(self.exe_dir, out_files[key])
            self.removefile(filename)
        self.remove_gromacs_backup_files(self.exe_dir)
        return success, status

    def step(self, system, name, exe_dir):
        """Perform a single step with GROMACS.

        Parameters
        ----------
        system : object like :py:class:`pyretis.core.system.System`
            The system we are integrating.
        name : string
            To name the output files from the GROMACS step.
        exe_dir : string
            The path to where we will perform the GROMACS simulation.
        """
        initial_conf = self.dump_frame(system)
        # Save as a single snapshot file
        phase_point = {'pos': (initial_conf, None), 'vel': False,
                       'vpot': None, 'ekin': None}
        system.particles.set_particle_state(phase_point)
        out_grompp = self._execute_grompp(self.input_files['input'],
                                          initial_conf,
                                          name,
                                          exe_dir)
        out_mdrun = self._execute_mdrun(out_grompp['tpr'],
                                        name, exe_dir)
        conf_abs = os.path.join(exe_dir, out_mdrun['conf'])
        phase_point = {'pos': (conf_abs, None),
                       'vel': False, 'vpot': None, 'ekin': None}
        system.particles.set_particle_state(phase_point)
        out_files = {}
        for key, val in out_grompp.items():
            out_files[key] = val
        for key, val in out_mdrun.items():
            out_files[key] = val
        return out_files

    def prepare_shooting_point(self, input_file, output_file):
        """Method to create initial configuration for a shooting move.

        Parameters
        ----------
        idx : integer
            The index for the shooting point referring to a position
            in the input .trr file.
        input_file : strings
            The input configuration to generate velocities for.
        output_file : string
            Where to store the configuration to use for shooting.

        Returns
        -------
        output_file : string
            The name of the file created.
        energy : dict
            The energy terms read from the GROMACS .edr file.
        """
        prevdir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create output file to generate velocities:
            settings = {'gen_vel': 'yes', 'gen_seed': -1, 'nsteps': 0}
            tmp_mdp = os.path.join(tmp_dir, 'genvel.mdp')
            self.modify_input(self.input_files['input'], tmp_mdp, settings,
                              delim='=')
            # Run grompp for this input file:
            out_grompp = self._execute_grompp(tmp_mdp, input_file, 'genvel',
                                              exe_dir=tmp_dir)
            # Run gromacs for this tpr file:
            out_mdrun = self._execute_mdrun(out_grompp['tpr'],
                                            'genvel', exe_dir=tmp_dir)
            confout = os.path.join(tmp_dir, out_mdrun['conf'])
            energy = self.get_energies(out_mdrun['edr'], exe_dir=tmp_dir)
            # Copy back the g96 file with velocities:
            dest = os.path.join(prevdir, output_file)
            self.movefile(confout, dest)
        return output_file, energy

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

    def aimless_velocities(self, system):
        """Aimless modification of the current state.

        Parameters
        ----------
        system : object like :py:class:`core.system.System`
            System is used here since we need access to the particle
            list.

        Returns
        -------
        phase_point : dict
            The new phase point with modified velocities.
        kin_new : float
            The new kinetic energy.
        """
        pos = self.dump_frame(system)
        posvel = os.path.join(os.path.dirname(pos), 'genvel.g96')
        _, energy = self.prepare_shooting_point(pos, posvel)
        pot = energy['potential'][-1]
        kin_new = energy['kinetic en.'][-1]
        phase_point = {'pos': (posvel, None), 'vel': False,
                       'vpot': pot, 'ekin': kin_new}
        return phase_point, kin_new
