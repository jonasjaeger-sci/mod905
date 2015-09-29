# -*- coding: utf-8 -*-
"""
This file contains methods and objects that handle output/input of
text files.

Objects defined here:

- EnergyFile: Writing/reading of energy data to a file.

"""
import numpy as np
from .txtinout import FileWriter, read_some_lines

__all__ = ['EnergyFile']

# format for the energy files, here also as a tuple since this makes
# convenient for outputting in a specific order:
ENERGY_FMT = ['{:>10d}'] + 6*['{:>12.6f}']


class EnergyFile(FileWriter):
    """
    EnergyFile(FileWriter)

    This class handles writing/reading of energy data.

    Attributes
    ----------
    Same as for the FileWriter object.
    """
    def __init__(self, filename, mode='w', oldfile='backup'):
        """
        Initialize the EnergyFile object

        Parameters
        ----------
        filename : string
            Name of file to read/write.
        mode : string
            Mode can be used to select if we should write to the file
            (if mode is equal to 'w') or read from the file (mode equal
            to 'r'). The default is mode equal to 'w'.
        oldfile : string
            Defines how we handle existing files with the same name as given
            in `filename`. Note that this is only usefull when the mode is
            set to 'w'.
        """
        header = {'text': ['Time', 'Potential', 'Kinetic', 'Total',
                           'Hamiltonian', 'Temperature', 'External'],
                  'width': [10, 12]}
        super(EnergyFile, self).__init__(filename, 'energyfile',
                                         mode=mode,
                                         oldfile=oldfile,
                                         header=header)

    def load(self):
        """
        This method will attempt to load the entire energy file into memory.
        (Quote of the day: 'memory is cheap, function calls are expensive'.)
        In the future, a more intelligent way of handling files like this
        may be in order, but for now the entire file is read as it's very
        convenient for the subsequent analysis. In case blocks are found in
        the file, they will be yielded, this is just to reduce the memory
        usage.

        Yields
        -------
        data_dict : dict
            This is the energy data read from the file, stored in
            a dict. This is for convenience, so that each energy term
            can be accessed by data[key]

        See Also
        --------
        read_some_lines
        """
        for blocks in read_some_lines(self.filename):
            data = np.array(blocks['data'])
            data_dict = {'comment': blocks['comment'],
                         'data': {'time': data[:, 0],
                                  'vpot': data[:, 1],
                                  'ekin': data[:, 2],
                                  'etot': data[:, 3],
                                  'ham': data[:, 4],
                                  'temp': data[:, 5],
                                  'ext': data[:, 6]}}
            yield data_dict

    def write(self, step, energy):
        """
        This function will write the energy data to the file.

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
                                 'temp', 'ext']):
            value = energy.get(key, 0.0)
            towrite.append(ENERGY_FMT[i + 1].format(value))
        towrite = ' '.join(towrite)
        return self.write_line(towrite)

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = 'Energy file: {} (mode: {})'.format(self.filename, self.mode)
        return msg
