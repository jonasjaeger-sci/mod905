# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""A GROMACS external MD integrator interface.

This module defines a class for using GROMACS as an external engine.

Important classes defined here
------------------------------

GromacsEngine (:py:class:`.GromacsEngine`)
    A class responsible for interfacing GROMACS.
"""
import logging
import os
import shlex
import numpy as np
from pyretis.engines.external import ExternalMDEngine
from pyretis.inout.writers.gromacsio import (read_gromos96_file,
                                             write_gromos96_file)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


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
    mdrun_c : string
        The command for executing GROMACS mdrun when continuing a
        simulation. This is derived from the ``mdrun`` command.
    input_path : string
        The directory where the input files are stored.
    input_files : dict of strings
        The names of the input files. We expect to find the keys
        ``'conf'``, ``'input'`` ``'topology'``.
    ext_time : float
        The time to extend simulations by. It is equal to
        ``timestep * subcycles``.
    """

    def __init__(self, gmx, mdrun, input_path, timestep, subcycles):
        """Initiate the script.

        Parameters
        ----------
        gmx : string
            The GROMACS executable.
        mdrun : string
            The GROMACS mdrun executable.
        input_path : string
            The absolute path to where the input files are stored.
        timestep : float
            The time step used in the GROMACS MD simulation.
        subcycles : integer
            The number of steps each GROMACS MD run is composed of.
        """
        super().__init__('GROMASC engine', timestep, subcycles, 'g96')
        # Define the gmx command:
        self.gmx = gmx
        # For mdrun, set up for first execution and continuation:
        self.mdrun = mdrun + ' -s {} -deffnm {} -c {}'
        self.mdrun_c = mdrun + ' -s {} -cpi {} -append -deffnm {} -c {}'
        self.ext_time = self.timestep * self.subcycles

        # Add input path and the input files:
        self.input_path = os.path.abspath(input_path)
        input_files = {'conf': 'conf.g96',
                       'input_o': 'grompp.mdp',  # "o" = original input file
                       'topology': 'topol.top'}
        self.input_files = {}
        for key, val in input_files.items():
            self.input_files[key] = os.path.join(self.input_path, val)
            if not os.path.isfile(self.input_files[key]):
                msg = 'GROMACS engine is missing input file "{}"'.format(val)
                logger.error(msg)
                raise ValueError(msg)
        # Check the input file and create a pyretis version with consistent
        # settings:
        settings = {'dt': self.timestep, 'nstxout-compressed': 0,
                    'gen_vel': 'no'}
        for key in ('nsteps', 'nstxout', 'nstvout', 'nstfout', 'nstlog',
                    'nstcalcenergy', 'nstenergy'):
            settings[key] = self.subcycles
        self.input_files['input'] = os.path.join(self.input_path,
                                                 'pyretis.mdp')
        self._modify_input(self.input_files['input_o'],
                           self.input_files['input'], settings, delim='=')
        logger.info(('Created GROMACS mdp input from %s. You might '
                     'want to check the input file: %s'),
                    self.input_files['input_o'], self.input_files['input'])
        # Generate a tpr file using the input files:
        logger.info('Creating ".tpr" for GROMACS in %s', self.input_path)
        self.exe_dir = self.input_path
        out_files = self._execute_grompp(self.input_files['input'],
                                         self.input_files['conf'], 'topol')
        # This will generate some noise, let's remove files we don't need:
        mdout = os.path.join(self.input_path, out_files['mdout'])
        self._removefile(mdout)
        # We also remove GROMACS backup files after creating the tpr:
        self._remove_gromacs_backup_files(self.input_path)
        # Keep the tpr file.
        self.input_files['tpr'] = os.path.join(self.input_path,
                                               out_files['tpr'])
        logger.info('GROMACS ".tpr" created: %s', self.input_files['tpr'])

    def _execute_grompp(self, mdp_file, config, deffnm):
        """Method to execute the GROMACS preprocessor.

        Parameters
        ----------
        mdp_file : string
            The path to the mdp file.
        config : string
            The path to the GROMACS config file to use as input.
        deffnm : string
            A string used to name the GROMACS files.

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
        self.execute_command(cmd, cwd=self.exe_dir)
        out_files = {'tpr': tpr, 'mdout': 'mdout.mdp'}
        return out_files

    def _execute_mdrun(self, tprfile, deffnm):
        """Method to execute GROMACS mdrun.

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
        out_files : dict
            This dict contains the output files created by mdrun.
            Note that we here hard code the file names.
        """
        confout = '{}.g96'.format(deffnm)
        cmd = shlex.split(self.mdrun.format(tprfile, deffnm, confout))
        self.execute_command(cmd, cwd=self.exe_dir)
        out_files = {'conf': confout,
                     'cpt_prev': '{}_prev.cpt'.format(deffnm)}
        for key in ('cpt', 'edr', 'log', 'trr'):
            out_files[key] = '{}.{}'.format(deffnm, key)
        self._remove_gromacs_backup_files(self.exe_dir)
        return out_files

    def _execute_grompp_and_mdrun(self, config, deffnm):
        """Run grompp and mdrun.

        Here we use the input file given in the input directory.

        Parameters
        ----------
        config : string
            The path to the GROMACS config file to use as input.
        deffnm : string
            A string used to name the GROMACS files.

        Returns
        -------
        out_files : dict of strings
            The files created by this command.
        """
        out_files = {}
        out_grompp = self._execute_grompp(self.input_files['input'],
                                          config, deffnm)
        tpr_file = out_grompp['tpr']
        for key, value in out_grompp.items():
            out_files[key] = value
        out_mdrun = self._execute_mdrun(tpr_file,
                                        deffnm)
        for key, value in out_mdrun.items():
            out_files[key] = value
        return out_files

    def _execute_mdrun_continue(self, tprfile, cptfile, deffnm):
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

        Returns
        -------
        out_files : dict
            The output files created/appended by GROMACS when we
            continue the simulation.
        """
        confout = '{}.g96'.format(deffnm)
        self._removefile(confout)
        cmd = shlex.split(self.mdrun_c.format(tprfile, cptfile,
                                              deffnm, confout))
        self.execute_command(cmd, cwd=self.exe_dir)
        out_files = {'conf': confout}
        for key in ('cpt', 'edr', 'log', 'trr'):
            out_files[key] = '{}.{}'.format(deffnm, key)
        self._remove_gromacs_backup_files(self.exe_dir)
        return out_files

    def _extend_gromacs(self, tprfile, time):
        """Method to extend a GROMACS simulation.

        Parameters
        ----------
        tprfile : string
            The file to read for extending.
        time : float
            The time (in ps) to extend the simulation by.

        Returns
        -------
        out_files : dict
            The files created by GROMACS when we extend.
        """
        tpxout = 'ext_{}'.format(tprfile)
        self._removefile(tpxout)
        cmd = [self.gmx, 'convert-tpr', '-s', tprfile,
               '-extend', '{}'.format(time), '-o', tpxout]
        self.execute_command(cmd, cwd=self.exe_dir)
        out_files = {'tpr': tpxout}
        return out_files

    def _extend_and_execute_mdrun(self, tpr_file, cpt_file, deffnm):
        """Extend GROMACS and execute mdrun.

        Parameters
        ----------
        tpr_file : string
            The location of the "current" .tpr file.
        cpt_file : string
            The last check point file .cpt from the previous
            run.
        deffnm : string
            To give the GROMACS simulation a name.

        Returns
        -------
        out_files : dict
            The files created by GROMACS when we extend.
        """
        out_files = {}
        out_grompp = self._extend_gromacs(tpr_file, self.ext_time)
        ext_tpr_file = out_grompp['tpr']
        for key, value in out_grompp.items():
            out_files[key] = value
        out_mdrun = self._execute_mdrun_continue(ext_tpr_file, cpt_file,
                                                 deffnm)
        for key, value in out_mdrun.items():
            out_files[key] = value
        # Move extended tpr so that we can continue extending:
        source = os.path.join(self.exe_dir, ext_tpr_file)
        dest = os.path.join(self.exe_dir, tpr_file)
        self._movefile(source, dest)
        out_files['tpr'] = tpr_file
        return out_files

    def _remove_gromacs_backup_files(self, dirname):
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
                self._removefile(filename)

    def _extract_frame(self, trr_file, idx, out_file):
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

    def get_energies(self, energy_file):
        """Return energies from a GROMACS run.

        Parameters
        ----------
        energy_file : string
            The file to read energies from.
        """
        cmd = [self.gmx, 'energy', '-f', energy_file]
        self.execute_command(cmd, inputs=b'Potential\nKinetic-En.',
                             cwd=self.exe_dir)
        xvg_file = os.path.join(self.exe_dir, 'energy.xvg')
        energy = read_xvg_file(xvg_file)
        self._removefile(xvg_file)
        return energy

    def _propagate_from(self, name, path, system, order_function, interfaces,
                        reverse=False):
        """Propagate with GROMACS from the current system configuration.

        Here, we assume that this method is called after the propagate()
        has been called in the parent. The parent is then responsible
        for reversing the velocities and also for setting the initial
        state of the system.

        Parameters
        ----------
        name : string
            A name to use for the trajectory we are generating.
        path : object like :py:class:`.PathBase`
            This is the path we use to fill in phase-space points.
        system : object like :py:class:`.System`
            The system object gives the initial state.
        order_function : object like :py:class:`.OrderParameter`
            The object used for calculating the order parameter.
        interfaces : list of floats
            These interfaces define the stopping criterion.
        reverse : boolean
            If True, the system will be propagated backwards in time.

        Returns
        -------
        success : boolean
            This is True if we generated an acceptable path.
        status : string
            A text description of the current status of the propagation.
        """
        status = 'propagating with GROMACS (reverse = {})'.format(reverse)
        logger.debug(status)
        success = False
        left, _, right = interfaces
        # Dumping of the initial config were done by the parent, here
        # we will just use it:
        initial_conf = system.particles.get_pos()[0]
        # Get current order parameter
        order = self.calculate_order(order_function, system)
        # In some cases, we don't really have to perform a step as the
        # initial config might be left/right of the interface in
        # question. Here, we will perform a step anyway. This is to be
        # sure that we obtain energies and also a trajectory segment.
        # Note that all the energies are obtained after we are done
        # with the integration from the .edr file of the trajectory.
        out_files = self._execute_grompp_and_mdrun(initial_conf, name)
        # Define name of some files:
        tpr_file = out_files['tpr']
        cpt_file = out_files['cpt']
        traj_file = os.path.join(self.exe_dir, out_files['trr'])
        conf_abs = os.path.join(self.exe_dir, out_files['conf'])
        # Note: Order is calculated AT THE END of each iteration!
        for i in range(path.maxlen):
            logger.debug('Current: %9.5g %9.5g %9.5g', left, order[0], right)
            # We first add the previous phase point, and then we propagate.
            phase_point = {'order': order,
                           'pos': (traj_file, i),
                           'vel': reverse,
                           'vpot': None,
                           'ekin': None}
            status, success, stop = self.add_to_path(path, phase_point,
                                                     left, right)
            if stop:
                logger.debug('Ending propagate at %i. Reason: %s', i, status)
                break
            if i == 0:
                # This step was performed before entering the main loop
                pass
            elif i > 0:
                out_extnd = self._extend_and_execute_mdrun(tpr_file, cpt_file,
                                                           name)
                out_files.update(out_extnd)
            # Calculate the order parameter using the current system:
            system.particles.set_vel(reverse)
            system.particles.set_pos((conf_abs, None))
            order = self.calculate_order(order_function, system)
            # We now have the order parameter, for GROMACS just remove the
            # config file to avoid the GROMACS #conf_abs# backup clutter:
            self._removefile(conf_abs)
        logger.debug('GROMACS propagation done, obtaining energies')
        energy = self.get_energies(out_files['edr'])
        path.vpot = np.copy(energy['potential'])
        path.ekin = np.copy(energy['kinetic en.'])

        logger.debug('Removing GROMACS output after propagate.')
        remove = [val for key, val in out_files.items() if key not in ('trr',)]
        self._remove_files(self.exe_dir, remove)
        self._remove_gromacs_backup_files(self.exe_dir)
        return success, status

    def step(self, system, name):
        """Perform a single step with GROMACS.

        Parameters
        ----------
        system : object like :py:class:`.System`
            The system we are integrating.
        name : string
            To name the output files from the GROMACS step.

        Returns
        -------
        out : string
            The name of the output configuration, obtained after
            completing the step.
        """
        initial_conf = self.dump_frame(system)
        # Save as a single snapshot file
        phase_point = {'pos': (initial_conf, None), 'vel': False,
                       'vpot': None, 'ekin': None}
        system.particles.set_particle_state(phase_point)
        out_grompp = self._execute_grompp(self.input_files['input'],
                                          initial_conf,
                                          name)
        out_mdrun = self._execute_mdrun(out_grompp['tpr'],
                                        name)
        conf_abs = os.path.join(self.exe_dir, out_mdrun['conf'])
        logger.debug('Obtaining GROMACS energies after single step.')
        energy = self.get_energies(out_mdrun['edr'])
        phase_point = {'pos': (conf_abs, None),
                       'vel': False,
                       'vpot': energy['potential'][-1],
                       'ekin': energy['kinetic en.'][-1]}
        system.particles.set_particle_state(phase_point)
        logger.debug('Removing GROMACS output after single step.')
        remove = [val for _, val in out_grompp.items()]
        remove += [val for key, val in out_mdrun.items() if key != 'conf']
        self._remove_files(self.exe_dir, remove)
        return out_mdrun['conf']

    def _prepare_shooting_point(self, input_file):
        """Method to create initial configuration for a shooting move.

        Parameters
        ----------
        input_file : string
            The input configuration to generate velocities for.

        Returns
        -------
        output_file : string
            The name of the file created.
        energy : dict
            The energy terms read from the GROMACS .edr file.
        """
        gen_mdp = os.path.join(self.exe_dir, 'genvel.mdp')
        if os.path.isfile(gen_mdp):
            logger.debug('%s found. Re-using it!', gen_mdp)
        else:
            # Create output file to generate velocities:
            settings = {'gen_vel': 'yes', 'gen_seed': -1, 'nsteps': 0,
                        'continuation': 'no'}
            self._modify_input(self.input_files['input'], gen_mdp, settings,
                               delim='=')
        # Run grompp for this input file:
        out_grompp = self._execute_grompp(gen_mdp, input_file, 'genvel')
        remove = [val for _, val in out_grompp.items()]
        # Run gromacs for this tpr file:
        out_mdrun = self._execute_mdrun(out_grompp['tpr'], 'genvel')
        remove += [val for key, val in out_mdrun.items() if key != 'conf']
        confout = os.path.join(self.exe_dir, out_mdrun['conf'])
        energy = self.get_energies(out_mdrun['edr'])
        # remove run-files:
        logger.debug('Removing GROMACS output after velocity generation.')
        self._remove_files(self.exe_dir, remove)
        return confout, energy

    @staticmethod
    def _read_configuration(filename):
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
    def _reverse_velocities(filename, outfile):
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

    def modify_velocities(self, system, rgen, sigma_v=None, aimless=True,
                          momentum=False, rescale=None):
        """Modify the velocities of the current state.

        This method will modify the velocities of a time slice.

        Parameters
        ----------
        system : object like :py:class:`.System`
            System is used here since we need access to the particle
            list.
        rgen : object like :py:class:`.RandomGenerator`
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
            msgtxt = 'GROMACS engine does not support energy rescale.'
            logger.error(msgtxt)
            raise NotImplementedError(msgtxt)
        else:
            kin_old = system.particles.ekin
        if aimless:
            pos = self.dump_frame(system)
            posvel, energy = self._prepare_shooting_point(pos)
            kin_new = energy['kinetic en.'][-1]
            phase_point = {'pos': (posvel, None), 'vel': False,
                           'ekin': kin_new,
                           'vpot': energy['potential'][-1]}
            system.particles.set_particle_state(phase_point)
        else:  # soft velocity change, add from Gaussian dist
            msgtxt = 'GROMACS engine only support aimless shooting!'
            logger.error(msgtxt)
            raise NotImplementedError(msgtxt)
        if momentum:
            pass
        if kin_old is None or kin_new is None:
            dek = float('inf')
            logger.warning(('Kinetic energy not found for previous point.'
                            '\n(This happens when the initial configuration '
                            'does not contain energies.)'))
        else:
            dek = kin_new - kin_old
        return dek, kin_new
