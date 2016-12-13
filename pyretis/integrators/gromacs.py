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


class GromacsExt(ExternalScript):
    """A class for interfacing GROMACS.

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
            The absolute path to where the input files are stored.
        input_files : dict
            This dictionary contains the names of the input files.
        time_step : float
            The time step used in the GROMACS MD simulation.
        subcycles : integer
            The number of steps each GROMACS MD run is composed of.
        """
        super().__init__('GROMASC external script', exe,
                         time_step, subcycles)
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
        # Generate a tpr file using the input files:
        out_files = self.execute_grompp(self.input_files['input'],
                                        self.input_files['configuration'],
                                        'topol',
                                        exe_dir=self.input_path)

        self.input_files['tpr'] = os.path.join(self.input_path,
                                               out_files['tpr'])

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

    def propagate(self, path, system, order_function, interfaces,
                  reverse=False, exe_dir=None):
        """Propagate with GROMACS."""
        initial_state = system.particles.get_particle_state()
        print('Start propagate')
        print(system.particles.config)
        print(initial_state)
        initial_file = self.dump_frame(system)
        if reverse:
            name = 'trajB_new'
            basepath = os.path.dirname(initial_file)
            localfile = os.path.basename(initial_file)
            initial_conf = os.path.join(basepath, 'rev_{}'.format(localfile))
            self.reverse_velocities(initial_file, initial_conf)
        else:
            name = 'trajF_new'
            initial_conf = initial_file

        success = False
        left, _, right = interfaces

        # Save as a single snapshot file
        phase_point = {'pos': (initial_conf, None), 'vel': reverse,
                       'vpot': None, 'ekin': None}
        system.particles.set_particle_state(phase_point)
        ext_time = self.time_step * self.subcycles
        
        out_files = {}
        for key in ('trr', 'tpr', 'edr'):
            out_files[key] = '{}.{}'.format(name, key)

        tpr_file = None
        cpt_file = None
        # Note: Order is calculated after end of each iteration!
        order = self.calculate_order(order_function, system)
        for i in range(path.maxlen):
            phase_point = {
                'order': order,
                'pos': (os.path.join(exe_dir, out_files['trr']), i),
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
                out_mdrun = self.execute_mdrun_continue(ext_tpr_file,
                                                        cpt_file, name,
                                                        exe_dir=exe_dir)
                # Move extended tpr so that we can continue extending:
                os.replace(os.path.join(exe_dir, ext_tpr_file),
                           os.path.join(exe_dir, tpr_file))
            # Calculate order parameter using the output config:
            conf_abs = os.path.join(exe_dir, out_mdrun['conf'])
            phase_point = {'pos': (conf_abs, None),
                           'vel': reverse, 'vpot': None, 'ekin': None}
            system.particles.set_particle_state(phase_point)
            order = self.calculate_order(order_function, system)
            os.remove(conf_abs)
            print(order, system.particles.config)
            print(path)
            print('***')
        energy = self.get_energies(out_files['edr'], exe_dir=exe_dir)
        path.vpot = np.copy(energy['potential'])
        path.ekin = np.copy(energy['kinetic en.'])
        print(len(energy['potential']))
        system.particles.set_particle_state(initial_state)
        print(system.particles.config)

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

    def get_energies(self, energy_file, exe_dir=None):
        """Return energies from a GROMACS run.

        Parameters
        ----------
        energy_file : string
            The file to read energies from.
        """
        cmd = [self.exe, 'energy', '-f', energy_file]
        self.execute_command(cmd, inputs=b'Potential\nKinetic-En.',
                             cwd=exe_dir)
        xvg_file = os.path.join(exe_dir, 'energy.xvg')
        energy = read_xvg_file(xvg_file)
        os.remove(xvg_file)
        return energy

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
            out_grompp = self.execute_grompp(tmp_mdp, input_file, 'genvel',
                                             exe_dir=tmp_dir)
            # Run gromacs for this tpr file:
            out_mdrun = self.execute_mdrun(out_grompp['tpr'],
                                           'genvel', exe_dir=tmp_dir)
            confout = os.path.join(tmp_dir, out_mdrun['conf'])
            energy = self.get_energies(out_mdrun['edr'], exe_dir=tmp_dir)
            # Copy back the g96 file with velocities:
            dest = os.path.join(prevdir, output_file)
            shutil.move(confout, dest)
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

    def dump_frame(self, system):
        """Extract configuration frame from a system if needed.
        
        Parameters
        ----------
        system : object like :py:class:`core.system.System`
            System is used here since we need access to the particle
            list.

        Returns
        -------
        out : string
            The file name we dumped to. If we did not in fact dump, this is
            because the system contains a single frame and we can use it
            directly. Then we return simply this file name.

        Note
        ----
        We assume here that we won't be using the velocities in the
        configuration and we do not reverse the velocities.
        """
        pos_file, idx = system.particles.config
        if idx is None:
            return pos_file
        else:
            basepath = os.path.dirname(pos_file)
            out_file = os.path.join(basepath, 'conf.g96')
            self.get_trr_frame(pos_file, self.input_files['tpr'],
                               idx, out_file)
            return out_file

    def modify_velocities(self, system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        """Modify the velocities of the current state.

        This method will modify the velocities of a time slice.
        And it is part of the integrator since it, conceptually,
        fits here:  we are acting on the system and modifying it.

        Parameters
        ----------
        system : object like :py:class:`core.system.System`
            System is used here since we need access to the particle
            list.
        rgen : object like :py:class:`core.random_gen.RandomGenerator`
            This is the random generator that will be used.
        sigma_v : numpy.array, optional
            These values can be used to set a standard deviation (one
            for each particle) for the generated velocities.
        aimless : boolean, optional
            Determines if we should do aimless shooting or not.
        momentum : boolean, optional
            If True, we reset the linear momentum to zero after generating.
        rescale : float, optional
            In some NVE simulations, we may wish to rescale the energy to
            a fixed value. If `rescale` is a float > 0, we will rescale
            the energy (after modification of the velocities) to match the
            given float.

        Returns
        -------
        dek : float
            The change in the kinetic energy.
        kin_new : float
            The new kinetic energy.
        """
        dek = None
        kin_old = None
        kin_new = None
        if rescale is not None and rescale is not False and rescale > 0:
            msgtxt = 'GROMACS integrator does not support energy rescale!'
            raise NotImplementedError(msgtxt)
        else:
            kin_old = system.particles.ekin
        if aimless:
            # Do GROMACS update
            pos = self.dump_frame(system)
            posvel = os.path.join(os.path.dirname(pos), 'genvel.g96')
            _, energy = self.prepare_shooting_point(pos, posvel)
            pot = energy['potential'][-1]
            kin_new = energy['kinetic en.'][-1]
            phase_point = {'pos': (posvel, None), 'vel': False,
                           'vpot': pot, 'ekin': kin_new}
            system.particles.set_particle_state(phase_point)
        else:  # soft velocity change, add from Gaussian dist
            msgtxt = 'GROMACS integrator only support aimless shooting!'
            raise NotImplementedError(msgtxt)
        if not momentum:
            pass
        if kin_old is None or kin_new is None:
            dek = float('inf')
            msgtxt = 'External kinetic energy not set!'
            logger.warning(msgtxt)
        else:
            dek = kin_new - kin_old
        return dek, kin_new

