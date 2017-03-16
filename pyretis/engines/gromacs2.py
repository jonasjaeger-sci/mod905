# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""A GROMACS external MD integrator interface.

This module defines a class for using GROMACS as an external engine.

Important classes defined here
------------------------------

GromacsEngine2
    A class responsible for interfacing GROMACS.
"""
import logging
import os
import shlex
import subprocess
from time import sleep
import numpy as np
from pyretis.engines.gromacs import GromacsEngine
from pyretis.inout.writers.gromacsio import (read_trr_header,
                                             read_trr_data,
                                             TRR_HEAD_SIZE,
                                             TRR_DATA_ITEMS)
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


class GromacsEngine2(GromacsEngine):
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
    maxwarn : integer
        Setting for the GROMACS grompp ``maxwarn` option.
    """

    def __init__(self, gmx, mdrun, input_path, timestep, subcycles,
                 maxwarn=0):
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
        maxwarn : integer
            Setting for the GROMACS grompp ``maxwarn` option.
        """
        super().__init__(gmx, mdrun, input_path, timestep, subcycles,
                         maxwarn=maxwarn)

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
        path : object like :py:class:`pyretis.core.Path.PathBase`
            This is the path we use to fill in phase-space points.
        system : object like `System` from `pyretis.core.system`
            The system object gives the initial state.
        order_function : object like `pyretis.orderparameter.OrderParameter`
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
        # So, here we will just blast off GROMACS and check the .trr
        # output when we can.
        # 1) Create mdp_file with updated number of steps
        settings = {'gen_vel': 'no',
                    'nsteps': path.maxlen * self.subcycles,
                    'continuation': 'no'}
        mdp_file = os.path.join(self.exe_dir, '{}.mdp'.format(name))
        self._modify_input(self.input_files['input'], mdp_file, settings,
                           delim='=')
        # 2) Run GROMACS preprocessor:
        out_files = self._execute_grompp(mdp_file, initial_conf, name)
        # Generate some names that will be created by mdrun.
        confout = '{}.g96'.format(name)
        out_files['conf'] = confout
        out_files['cpt_prev'] = '{}_prev.cpt'.format(name)
        for key in ('cpt', 'edr', 'log', 'trr'):
            out_files[key] = '{}.{}'.format(name, key)
        # Remove some of these files if present (e.g. left over from a
        # crashed simulation). This is so that GromacsRunner will not
        # start reading a .trr left from a previous simulation.
        remove = [out_files[key] for key in out_files if key not in ('tpr',)]
        self._remove_files(self.exe_dir, remove)
        tpr_file = out_files['tpr']
        trr_file = os.path.join(self.exe_dir, out_files['trr'])
        edr_file = os.path.join(self.exe_dir, out_files['edr'])
        cmd = shlex.split(self.mdrun.format(tpr_file, name, confout))
        # 3) Fire off GROMACS mdrun:
        logger.debug('Executing GROMACS.')
        gro = GromacsRunner(cmd, trr_file, edr_file, self.exe_dir)
        gro.start()  # Start GROMACS run.
        for i, data in enumerate(gro.get_gromacs_frames()):
            system.particles.pos = data['x']
            system.particles.vel = data['v']
            if reverse:
                system.particles.vel *= -1
            order = order_function.calculate_all(system)
            phase_point = {'order': order,
                           'pos': (trr_file, i),
                           'vel': reverse,
                           'vpot': None,
                           'ekin': None}
            status, success, stop = self.add_to_path(path, phase_point,
                                                     left, right)
            if stop:
                logger.debug('Ending propagate at %i. Reason: %s', i, status)
                break
        # Ask GROMACS to stop and close open files
        gro.stop()
        logger.debug('GROMACS propagation done, obtaining energies!')
        energy = self.get_energies(out_files['edr'])
        if len(energy['potential']) < len(path.pos):
            logger.warning('GROMACS energies were too short!')
            path.vpot = np.zeros(len(path.pos))
            path.ekin = np.zeros(len(path.pos))
            path.vpot[:len(energy['potential'])] = energy['potential']
            path.ekin[:len(energy['kinetic en.'])] = energy['kinetic en.']
        else:
            path.vpot = energy['potential'][:len(path.pos)]
            path.ekin = energy['kinetic en.'][:len(path.pos)]
        logger.debug('Removing GROMACS output after propagate.')
        remove = [val for key, val in out_files.items() if key not in ('trr',)]
        self._remove_files(self.exe_dir, remove)
        self._remove_gromacs_backup_files(self.exe_dir)
        return success, status


def get_header(filename, fileh, idx):
    """Try to get the header from the file if we think we can

    Parameters
    ----------
    filename : string
        The name of the file.
    fileh : file object
        The file we are reading.
    idx : integer
        The current position we are at.
    """
    size = os.path.getsize(filename)
    size_h = idx + TRR_HEAD_SIZE
    if size >= size_h:
        header, header_s = read_trr_header(fileh)
        return header, size_h, header_s
    else:
        return None, idx, None


def get_data(filename, fileh, idx, header):
    """Try to get the next from the file if we think we can.

    Parameters
    ----------
    filename : string
        The name of the file.
    fileh : file object
        The file we are reading.
    idx : integer
        The current position we are at.
    header : dict
        The previously read header. Contains sizes and what to read.
    """
    size = os.path.getsize(filename)
    data_size = sum([header[key] for key in TRR_DATA_ITEMS])
    size_d = idx + data_size
    if size >= size_d:
        data = read_trr_data(fileh, header)
        return data, size_d
    else:
        return None, idx


def reopen_file(filename, fileh, inode):
    """Will reopen a file if the inode has changed.

    Parameters
    ----------
    filename : string
        The name of the file we are working with.
    fileh : file object
        The current open file object.
    inode : integer
        The current inode we are using.

    Returns
    -------
    out[0] : file object or None
        The new file object.
    out[1] : integer or None
        The new inode.
    """
    if os.stat(filename).st_ino != inode:
        new_fileh = open(filename, 'rb')
        fileh.close()
        new_inode = os.fstat(new_fileh.fileno()).st_ino
        return new_fileh, new_inode
    else:
        return None, None


def read_remaining_trr(filename, fileh, start):
    """Read remaining frames from the trr.

    Parameters
    ----------
    filename : string
        The file we are reading from.
    fileh : file object
        The file object we are reading from.
    start : integer
        The current position we are at.
    """
    stop = False
    bytes_read = start
    bytes_total = os.path.getsize(filename)
    logger.debug('Reading remaining')
    while not stop:
        if bytes_read >= bytes_total:
            stop = True
            continue
        header = None
        new_bytes = bytes_read
        try:
            logger.debug('Reading header')
            header, new_bytes, _ = get_header(filename, fileh, bytes_read)
        except EOFError:
            # Just assume that we have reached the end of the
            # file and we just stop here.
            stop = True
            logger.debug('Could not find it, aborting.')
            continue
        if header is not None:
            logger.debug('Found header')
            bytes_read = new_bytes
            try:
                logger.debug('Looking for data')
                data, new_bytes = get_data(filename, fileh, bytes_read,
                                           header)
                if data is not None:
                    logger.debug('Found some data....')
                    bytes_read = new_bytes
                    yield header, data, bytes_read
            except EOFError:
                logger.debug('Should not have looked here...')
                # Hopefully, this code should not be reached...
                stop = True
                continue


class GromacsRunner():
    """A helper class for running GROMACS.

    Attributes
    ----------
    cmd : string
        The command for executing GROMACS
    trr_file : string
        The .trr file we are going to read.
    edr_file : string
        A .edr file we are going to read.
    exe_dir : string
        Path to where we are currently running GROMACS.
    fileh : file object
        The current open file object.
    running : None or object like :py:class:`subprocess.Popen`
        The process running GROMACS.
    bytes_read : integer
        The number of bytes we have read so far from the .trr file.
    inode : integer
        The current inode we are using.
    stop_read : boolean
        If this is set to True, we will stop the reading.
    SLEEP : float
        How long we wait after an unsuccessful read before
        reading again.
    """

    SLEEP = 0.1

    def __init__(self, cmd, trr_file, edr_file, exe_dir):
        """Just set up command and files.

        Parameters
        ----------
        cmd : string
            The command for executing GROMACS
        trr_file : string
            The .trr file we are going to read.
        edr_file : string
            A .edr file we are going to read.
        exe_dir : string
            Path to where we are currently running GROMACS.
        """
        self.cmd = cmd
        self.trr_file = trr_file
        self.edr_file = edr_file
        self.exe_dir = exe_dir
        self.fileh = None
        self.running = None
        self.bytes_read = 0
        self.ino = 0
        self.stop_read = True

    def start(self):
        """Start execution of GROMACS and wait for output file creation."""
        logger.debug('Starting GROMACS execution')
        self.running = subprocess.Popen(
            self.cmd, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            cwd=self.exe_dir
        )
        # Wait for the trr/edr file to appear
        for fname in (self.trr_file, self.edr_file):
            while not os.path.isfile(fname):
                logger.debug('Waiting for GROMACS file "%s"', fname)
                sleep(self.SLEEP)
        # Prepare and open the trr file:
        self.bytes_read = 0
        self.fileh = open(self.trr_file, 'rb')
        self.ino = os.fstat(self.fileh.fileno()).st_ino
        self.stop_read = False

    def __enter__(self):
        """Start running GROMACS, for a context manager."""
        self.start()
        return self

    def get_gromacs_frames(self):
        """Read the GROMACS .trr file on-the-fly."""
        while not self.stop_read:
            poll = self.running.poll()
            if poll is not None:
                # GROMACS is done, read remaining data.
                self.stop_read = True
                if os.path.getsize(self.trr_file) - self.bytes_read > 0:
                    for _, data, _ in read_remaining_trr(self.trr_file,
                                                         self.fileh,
                                                         self.bytes_read):
                        yield data
            else:
                # Try to read next frame:
                header = None
                try:
                    header, new_bytes, _ = get_header(self.trr_file,
                                                      self.fileh,
                                                      self.bytes_read)
                except EOFError:
                    new_fileh, new_ino = reopen_file(self.trr_file,
                                                     self.fileh,
                                                     self.ino)
                    if new_fileh is not None:
                        self.fileh = new_fileh
                        self.ino = new_ino
                if header is None:
                    # Data header is not ready, we will wait before
                    # running a new cycle.
                    sleep(self.SLEEP)
                else:
                    # We have read a header, try to read the data:
                    self.bytes_read = new_bytes
                    data = None
                    while data is None:
                        try:
                            data, new_bytes = get_data(self.trr_file,
                                                       self.fileh,
                                                       self.bytes_read,
                                                       header)
                        except EOFError:
                            new_fileh, new_ino = reopen_file(self.trr_file,
                                                             self.fileh,
                                                             self.ino)
                            if new_fileh is not None:
                                self.fileh = new_fileh
                                self.ino = new_ino
                        if data is None:
                            # Data is not ready, will wait:
                            sleep(self.SLEEP)
                        else:
                            self.bytes_read = new_bytes
                    yield data

    def close(self):
        """Close the file, in case that is explicitly needed."""
        if self.fileh is not None and not self.fileh.closed:
            logger.debug('Closing GROMACS file: "%s"', self.trr_file)
            self.fileh.close()

    def stop(self):
        """Stop the current GROMACS execution."""
        if self.running is not None:
            logger.debug('Terminating GROMACS execution')
            self.running.terminate()
            logger.debug('Waiting for GROMACS termination')
            self.running.wait(timeout=60)
        self.stop_read = True
        self.close()  # close trr file.

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Just stop execution and close file for a context manager."""
        self.stop()

    def __del__(self):
        """Just stop execution and close file."""
        self.stop()
