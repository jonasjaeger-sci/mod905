# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Module defining the base classes for the PyRETIS output.

Important classes defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PathStorage (:py:class:`.PathStorage`)
    A class or handling storage of external trajectories to an archive
    format (tar in this case).

"""
import logging
import tempfile
import tarfile
import os
from pyretis.inout.common import OutputBase, create_backup
from pyretis.inout.formats import (
    EnergyPathFormatter,
    OrderPathFormatter,
    PathExtFormatter,
)


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


def add_to_tar_file(tar_file, files, file_mode='a'):
    """Open a tar file and add some files.

    Parameters
    ----------
    tar_file : string
        The path to the tar file to create.
    files : list of tuples
        The path(s) to the file(s) to add with names to
        create internaly in the tar file. That is:
        ``file[i] = (source[i], target[i])`` where ``target[i]`` will be
        used as the archname for ``source[i]``.
    file_mode : string
        Determines how we try to open the tar file.

    Returns
    -------
    out : boolean
        True if we managed to write to the file.

    """
    try:
        with tarfile.open(tar_file, file_mode) as tar:
            for src, trg in files:
                tar.add(src, arcname=trg)
        return True
    except tarfile.ReadError:
        logger.warning('Could not open tar file: "%s"', tar_file)
        return False


def generate_traj_names(path, target_dir):
    """Generate new file names for moving copying paths.

    Parameters
    ----------
    path : object like :py:class:`.PathBase`
        This is the path object we are going to store.
    target_dir : string
        The location where we are moving the path to.

    Returns
    -------
    files : list of tuples of strings
        The files to add and the file names to use internally
        for storing. That is: ``file[i] = (source[i], target[i])``
        where ``target[i]`` is the internal storage name.

    """
    source = set()
    files = []
    for phasepoint in path.phasepoints:
        pos_file, _ = phasepoint.particles.get_pos()
        if pos_file not in source:
            source.add(pos_file)
            dest = os.path.join(target_dir, os.path.basename(pos_file))
            files.append((pos_file, dest))
    return files


class PathStorage(OutputBase):
    """A class for handling storage of external trajectories.

    Attributes
    ----------
    target : string
        Determines the target for this output class. Here it will
        be a file.
    tar_acc : string
        Basename for the archive with accepted trajectories.
    tar_rej : string
        Basename for the archive with rejected trajectories.
    formatters : dict
        This dict contains the formatters for writing path data,
        with default filenames used for them.
    out_dir_fmt : string
        A format to use for creating directories within the archive.

    """

    target = 'file-archive'
    tar_acc = 'traj-acc.tar'
    tar_rej = 'traj-rej.tar'
    formatters = {
        'order': {'fmt': OrderPathFormatter(), 'file': 'order.txt'},
        'energy': {'fmt': EnergyPathFormatter(), 'file': 'energy.txt'},
        'traj': {'fmt': PathExtFormatter(), 'file': 'traj.txt'},
    }
    out_dir_fmt = '{}'

    def __init__(self):
        """Set up the storage.

        Note that we here do not pass any formatters to the parent
        class. This is because this class is less flexible and
        only intended to do one thing - write path data for external
        trajectories.

        """
        super().__init__(None)

    def output_path_files(self, step, data, tempdir):
        """Write the output files for energy, path and order parameter.

        Parameters
        ----------
        step : integer
            The current simulation step.
        data : list
            Here, ``data[0]`` is assumed to be an object like
            :py:class:`.Path` and `data[1]`` a string containing the
            status of this path.
        tempdir : string
            The path to where we create the temporary file, before
            it is added to the tar file.

        Returns
        -------
        files : list of tuple of strings
            This is the list of the source files and target files on
            form ``files[i] = (source[i], target[i])``.

        """
        path, status, = data[0], data[1]
        files = []
        for key, val in self.formatters.items():
            logger.debug('Storing: %s', key)
            fmt = val['fmt']
            src = os.path.join(tempdir, val['file'])
            trg = os.path.join(self.out_dir_fmt.format(step), val['file'])
            files.append((src, trg))
            with open(src, 'w') as output:
                for line in fmt.format(step, (path, status)):
                    output.write('{}\n'.format(line))
        return files

    @staticmethod
    def _add_to_archive(archive_file, files):
        """Add some files to an archive file.

        Parameters
        ----------
        archive_file : string
            The path to the archive file to create.
        files : list of tuples
            The path(s) to the file(s) to add with names to
            create internally in the archive. That is, the form is:
            ``file[i] = (source[i], target[i])`` where ``target[i]``
            will be used as the archive name for file ``source[i]``.

        Returns
        -------
        add : boolean
            True if we added files to the archive.

        """
        add = add_to_tar_file(archive_file, files, file_mode='a')
        if not add:
            logger.info(
                ('Could not write the trajectory file.'
                 ' Will try recreating it.')
            )
            logger.info('Backing up old trajectory file first.')
            logger.info(create_backup(archive_file))
            add = add_to_tar_file(archive_file, files, file_mode='w')
        return add

    def output(self, step, data):
        """Format the path data and store the path.

        Parameters
        ----------
        step : integer
            The current simulation step.
        data : list
            Here, ``data[0]`` is assumed to be an object like
            :py:class:`.Path`, ``data[1]`` a string containing the
            status of this path and ``data[2]`` the path ensemble for
            which the path was generated.

        Returns
        -------
        files : list of tuples of strings
            The files added to the archive.

        """
        path, status, ensemble = data
        tar_file = self.tar_acc if status == 'ACC' else self.tar_rej
        tar_path = os.path.join(ensemble.directory['traj'], tar_file)
        files = []
        with tempfile.TemporaryDirectory() as tempdir:
            # Write order, energy and traj files:
            files1 = self.output_path_files(step, data, tempdir)
            if self._add_to_archive(tar_path, files1):
                files.extend(files1)
        # Write the traj files:
        target_dir = os.path.join(self.out_dir_fmt.format(step), 'traj')
        files2 = generate_traj_names(path, target_dir)
        if self._add_to_archive(tar_path, files2):
            files.extend(files2)
        return files

    def write(self, towrite, end='\n'):
        """We do not need the write method for this object."""
        raise NotImplementedError(
            '{} does not support the "write" method!'.format(
                self.__class__.__name__
            )
        )

    def formatter_info(self):
        """Return info about the formatters."""
        return [val['fmt'].__class__ for _, val in self.formatters.items()]

    def __str__(self):
        """Return basic info."""
        return '{} - archive writer.'.format(self.__class__.__name__)
