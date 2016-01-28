# -*- coding: utf-8 -*-
"""This module handles input and output for energy files.

The energy file will just write out the energy of the system as a
function of time.

Important classes defined here:

- EnergyFile: Writing/reading of energy data to a file.
"""
import numpy as np
# pyretis imports
from pyretis.inout.fileio.fileinout import FileIO, read_some_lines


__all__ = ['EnergyFile']


# format for the energy files, here also as a tuple since this makes
# convenient for outputting in a specific order:
ENERGY_FMT = ['{:>10d}'] + 5*['{:>12.6f}']


class EnergyFile(FileIO):
    """EnergyFile(FileIO) - Handle energy data for pyretis.

    This class handles writing/reading of energy data. The data is written in
    7 columns:

    1) Time, i.e. the step number.

    2) Potential energy.

    3) Kinetic energy.

    4) Total energy, should equal the sum of the two previous columns.

    5) Hamiltonian energy, i.e. the conserved quantity for
       Nose-Hoover dynamics.

    6) Temperature.
    """
    filetype = 'EnergyFile'

    def __init__(self, filename, mode='w', oldfile='backup'):
        """Initialize the `EnergyFile` class.

        Parameters
        ----------
        filename : string
            Name of file to read/write.
        mode : string
            Mode can be used to select if we should write to the file
            (if mode is equal to `'w'`) or read from the file (mode equal
            to `'r'`). The default is mode equal to `'w'`.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only useful when the mode is
            set to `'w'`.
        """
        header = {'text': ['Time', 'Potential', 'Kinetic', 'Total',
                           'Hamiltonian', 'Temperature'],
                  'width': [10, 12]}
        super(EnergyFile, self).__init__(filename,
                                         mode=mode,
                                         oldfile=oldfile,
                                         header=header)

    def load(self):
        """Load entire energy blocks into memory.

        (Quote of the day: 'memory is cheap, function calls are expensive'.)
        In the future, a more intelligent way of handling files like this
        may be in order, but for now the entire file is read as it's very
        convenient for the subsequent analysis.

        Yields
        ------
        data_dict : dict
            This is the energy data read from the file, stored in
            a dict. This is for convenience, so that each energy term
            can be accessed by data[key].

        See Also
        --------
        `read_some_lines` in `pyretis.inout.fileio.fileinout`.
        """
        for blocks in read_some_lines(self.filename):
            data = np.array(blocks['data'])
            data_dict = {'comment': blocks['comment'],
                         'data': {'time': data[:, 0],
                                  'vpot': data[:, 1],
                                  'ekin': data[:, 2],
                                  'etot': data[:, 3],
                                  'ham': data[:, 4],
                                  'temp': data[:, 5]}}
            yield data_dict

    def write(self, step, energy):
        """Write the energy data to the file.

        Parameters
        ----------
        step : int
            This is the current step number.
        energy : dict
            This is the energy data stored as a dictionary.

        Returns
        -------
        out : boolean
            True if line could be written, False otherwise.
        """
        towrite = [ENERGY_FMT[0].format(step)]
        for i, key in enumerate(['vpot', 'ekin', 'etot', 'ham',
                                 'temp']):
            value = energy.get(key, 0.0)
            towrite.append(ENERGY_FMT[i + 1].format(value))
        return self.write_line(' '.join(towrite))
