# -*- coding: utf-8 -*-
"""
This file contains methods and objects that handle output/input of
text files.

Objects defined here:

- OrderFile: Writing/reading of order parameter data
"""
import numpy as np
from .txtinout import FileWriter, read_some_lines

__all__ = ['OrderFile']

# format for order files, here as a tuple since we don't know how many
# parameters we will write:
ORDER_FMT = ['{:>10d}', '{:>12.6f}']


class OrderFile(FileWriter):
    """
    OrderFile(FileWriter)

    This class handles writing/reading of order parameter data.

    Attributes
    ----------
    Same as for the FileWriter object.
    """
    def __init__(self, filename, mode='w', oldfile='backup'):
        """
        Initialize the OrderFile object

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
        header = {'text': ['Time', 'Orderp', 'Orderv'],
                  'width': [10, 12]}
        super(OrderFile, self).__init__(filename, 'orderparameter',
                                        mode=mode, oldfile=oldfile,
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
        The format is `time` `orderp0` `orderv0` `orderp1` `orderv1` etc...

        Yields
        -------
        data_dict : dict
            Data read from the order parameter file.

        See Also
        --------
        read_some_lines
        """
        for blocks in read_some_lines(self.filename):
            data = np.array(blocks['data'])
            _, col = data.shape
            data_dict = {'comment': blocks['comment']}
            data_dict['data'] = []
            for i in range(col):
                data_dict['data'].append(data[:, i])
            yield data_dict

    def write(self, step, orderdata):
        """
        This will write the order parameter data to the file.

        Parameters
        ----------
        step : int
            This is the current step number.
        orderdata : list of floats
            This is the raw order parameter data.

        Returns
        -------
        out : boolean
            True if line could be written, False otherwise.
        """
        towrite = [ORDER_FMT[0].format(step)]
        for orderp in orderdata:
            towrite.append(ORDER_FMT[1].format(orderp))
        towrite = ' '.join(towrite)
        return self.write_line(towrite)

    def __str__(self):
        """
        Return a string with some info about this object
        """
        msg = 'Order parameter file: {} (mode: {})'.format(self.filename,
                                                           self.mode)
        return msg
