# -*- coding: utf-8 -*-
"""
This file contains methods and objects that handle output/input of
text files.

Objects defined here:

- TxtTable: Table of text with a header and formatted rows.

- FileWriter: Defines a simple object to output to a file.

Important functions:

- txt_energy_output: For writing the output from a energy analysis.

- txt_flux_output: For writing the output from a flux-analysis.

- txt_orderp_output: For writing the output from a order parameter
  analysis.

- txt_path_output: For writing the output from a path simulation.

- txt_save_columns: Writing a simple column-based output using numpy.
"""
import os
import warnings
import numpy as np
try:  # this will fail in python3
    from itertools import izip_longest as zip_longest
except ImportError:  # for python3
    from itertools import zip_longest as zip_longest

from retis.inout.common import (create_backup, _ENERFILES, _ENERTITLE,
                                _FLUXFILES, _ORDERFILES, _PATHFILES)


__all__ = ['TxtTable', 'FileWriter', 'txt_save_columns',
           'txt_energy_output', 'txt_flux_output', 'txt_orderp_output',
           'txt_path_output']


def txt_save_columns(outputfile, header, variables):
    """
    This will save the different variables to a text file using
    numpy's savetxt. Note that the variables are assumed to be numpy.arrays of
    equal shape. Note that the outputfile may also be a zipped gz file.

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    header : string
        String that will be written at the beginning of the file.
    variables : tuple of numpy.arrays
        These are the variables that will be save to the text file
    """
    msg = create_backup(outputfile)
    if msg:
        warnings.warn(msg)
    nvar = len(variables)
    mat = np.zeros((len(variables[0]), nvar))
    for i, vari in enumerate(variables):
        try:
            mat[:, i] = vari
        except ValueError:
            msg = 'Could not align variables, skipping (writing zeros)'
            warnings.warn(msg)
    np.savetxt(outputfile, mat, header=header)


def txt_block_error(outputfile, title, error):
    """
    This will write the output from the error analysis, to a text file.

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    title : string
        This is a identifier/title to add to the header, e.g. 'Ensemble: 001',
        'Kinetic energy', etc.
    error : list
        This is the result from the error analysis
    """
    header = '{0}, Rel.err: {1:9.6e}, Ncor: {2:9.6f}'
    header = header.format(title, error[4], error[6])
    txt_save_columns(outputfile, header, (error[0], error[3]))


def txt_histogram(outputfile, title, *histograms):
    """
    This will output histograms to a text file.

    Parameters
    ----------
    outputfile : string
        This is the name of the output file to create.
    title : string
        A descriptive title to add to the header.
    histograms : tuple
        The histograms to store.
    """
    data = []
    header = [r'{}'.format(title)]
    for hist in histograms:
        header.append(r'avg: {0:6.2f}, std: {1:6.2f}'.format(hist[2][0],
                                                             hist[2][1]))
        data.append(hist[1])
        data.append(hist[0])
    header = ', '.join(header)
    txt_save_columns(outputfile, header, data)


def txt_flux_output(results, out_fmt='txt.gz'):
    """
    Store the output from the flux analysis in text files.

    Parameters
    ----------
    results : dict
        This is the dict with the results from the flux analysis.
    out_fmt : string, optional
        This is the desired format to use for the graphs. If 'gz' is specified,
        a gzipped file will be written

    Returns
    -------
    outfiles : dict
        The output files created by this method.

    """
    outfiles = {}
    for key in _FLUXFILES:
        outfiles[key] = []
    # make running average plot and error plot:
    for i in range(len(results['flux'])):
        flux = results['flux'][i]
        runflux = results['runflux'][i]
        errflux = results['errflux'][i]
        outfile = _FLUXFILES['runflux'].format(i + 1, out_fmt)
        outfiles['runflux'].append(outfile)
        # output running average:
        txt_save_columns(outfile, 'Time, running average',
                         (flux[:, 0], runflux))
        # output block-error results:
        outfile = _FLUXFILES['block'].format(i + 1, out_fmt)
        outfiles['block'].append(outfile)
        txt_block_error(outfile, 'Block error for flux analysis',
                        errflux)
    return outfiles


def txt_orderp_output(results, orderdata, out_fmt='txt.gz'):
    """
    Save the output from the order parameter analysis to text files.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the corresponding
        order parameter.
    orderdata : list of numpy.arrays
        This is the raw-data for the order parameter analysis
    out_fmt : string, optional
        This is the desired format to use for the graphs. If 'gz' is specified,
        a gzipped file will be written

    Returns
    -------
    outfiles : dict
        The output files created by this method.

    Note
    ----
    We are here only outputting results for the first order parameter.
    I.e. other order parameters or velocities are not written here. This
    will be changed when the structure of the output order parameter file
    has been fixed. Also note that, if present, the first order parameter
    will be plotted agains the second one - i.e. the second one will be
    assumed to represent the velocity here.
    """
    outfiles = {}
    for key in _ORDERFILES:
        outfiles[key] = _ORDERFILES[key].format(out_fmt)

    time = orderdata[0]
    # output running average:
    txt_save_columns(outfiles['run_order'],
                     'Time, running average',
                     (time, results[0]['running']))

    # output block-error results:
    txt_block_error(outfiles['block'], 'Block error for order param',
                    results[0]['blockerror'])
    # output distributions:
    txt_histogram(outfiles['dist'], 'Order parameter',
                  results[0]['distribution'])
    # output msd if it was calculated:
    if 'msd' in results[0]:
        msd = results[0]['msd']
        txt_save_columns(outfiles['msd'], 'Time MSD Std',
                         (time[:len(msd)], msd[:, 0], msd[:, 1]))
        # TODO: time should here be multiplied with the correct dt
    return outfiles


def txt_energy_output(results, energies, out_fmt='txt.gz'):
    """
    Save the output from the energy analysis to text files.

    Parameters
    ----------
    results : dict
        Each item in `results` contains the results for the corresponding
        energy. It is assumed to contains the keys 'vpot', 'ekin', 'etot',
        'ham', 'temp', 'elec'
    energies : numpy.array
        This is the raw-data for the energy analysis
    out_fmt : string, optional
        This is the desired format to use for the graphs. If 'gz' is specified,
        a gzipped file will be written

    Returns
    -------
    outfiles : dict
        The output files created by this method.
    """
    outfiles = {'run_energies': _ENERFILES['run_energies'].format(out_fmt),
                'temperature': _ENERFILES['temperature'].format(out_fmt),
                'run_temp': _ENERFILES['run_temp'].format(out_fmt)}
    time = energies['time']
    # 1) Store the running average:
    header = ['Running average of energy data: time']
    data = [time]
    for key in ['vpot', 'ekin', 'etot', 'ham', 'temp', 'ext']:
        if key in results:
            data.append(results[key]['running'])
            header.append(key)
    header = ' '.join(header)
    txt_save_columns(outfiles['run_energies'], header, data)
    # 2) Save block error data:
    outfile = _ENERFILES['block'].format('{}', out_fmt)
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        if key not in results:
            continue
        outfiles['{}block'.format(key)] = outfile.format(key)
        txt_block_error(outfiles['{}block'.format(key)], _ENERTITLE[key],
                        results[key]['blockerror'])
    # 3) Save histograms:
    outfile = _ENERFILES['dist'].format('{}', out_fmt)
    for key in ['vpot', 'ekin', 'etot', 'temp']:
        if key not in results:
            continue
        outfiles['{}dist'.format(key)] = outfile.format(key)
        txt_histogram(outfiles['{}dist'.format(key)],
                      r'Histogram for {}'.format(_ENERTITLE[key]),
                      results[key]['distribution'])
    return outfiles


def _txt_shoots_histogram(outputfile, histograms, scale, ensemble):
    """
    This method will write the histograms from the shoots analysis to a
    text file.

    Parameters
    ----------
    histograms : list
        These are the histograms obtained in the shoots analysis.
    scale : dict
        These are the scale factors for normalizing the histograms
        obtained in the shoots analysis.
    ensemble : string
        This is the ensemble identifier, e.g. 001, 002, etc.
    outputfile : string
        This is the name of the output file to create.
    """
    data = []
    header = ['Ensemble: {0}'.format(ensemble)]
    for key in ['ACC', 'REJ', 'BWI', 'ALL']:
        try:
            mid = histograms[key][2]
            hist = histograms[key][0]
            hist_scale = hist * scale[key]
            data.append(mid)
            data.append(hist)
            data.append(hist_scale)
            header.append('{} (mid, hist, hist*scale)'.format(key))
        except KeyError:
            continue
    header = ', '.join(header)
    txt_save_columns(outputfile, header, data)


def txt_path_output(path_ensemble, results, idetect, out_fmt='txt.gz'):
    """
    This method will output all the results obtained by the path analysis.

    Parameters
    ----------
    path_ensemble : object
        This is the path ensemble we have analysed.
    results : dict
        This dict contains the result from the analysis.
    idetect : float
        This is the interface used for the detection in the analysis.
    out_fmt : string, optional
        This is the desired format to use for the graphs. If 'gz' is specified,
        a gzipped file will be written
    """
    ens = path_ensemble.ensemble  # identify the ensemble
    outfiles = {}
    for key in _PATHFILES:
        outfiles[key] = _PATHFILES[key].format(ens, out_fmt)
    # 1) Output pcross vs lambda:
    txt_save_columns(outfiles['pcross'],
                     'Ensemble: {}, idetect: {}'.format(ens, idetect),
                     (results['pcross'][0], results['pcross'][1]))
    # 2) Output the running average of p:
    txt_save_columns(outfiles['prun'], 'Ensemble: {}'.format(ens),
                     (results['prun']))
    # 3) Block error results:
    txt_block_error(outfiles['perror'], 'Ensemble: {0}'.format(ens),
                    results['blockerror'])
    # 3) Length histograms
    txt_histogram(outfiles['pathlength'], 'Histograms for acc and all',
                  results['pathlength'][0], results['pathlength'][1])
    # 4) Shoot histograms
    _txt_shoots_histogram(outfiles['shoots'], results['shoots'][0],
                          results['shoots'][1], ens)


def txt_total_probability(path_ensembles, detect, results, matched,
                          outputfile):
    """
    This method will output the overall matched probabilities.

    Parameters
    ----------
    path_ensembles : list of PathEnsemble objects
        This is the path ensembles we have analysed.
    results : list of dicts
        This dict contains the results from the analysis.
    detect : list of floats
        These are the detect interfaces used in the analysis.
    matched : list of numpy.arrays
        These are the matched/scaled probabilities
    outputfile : string
        This is the name of the output file to create.
    """
    msg = create_backup(outputfile)
    if msg:
        warnings.warn(msg)
    with open(outputfile, 'w') as fhandle:
        for i, path_e in enumerate(path_ensembles):
            header = 'Ensemble: {}, idetect: {}'.format(path_e.ensemble,
                                                        detect[i])
            mat = np.zeros((len(matched[i]), 2))
            mat[:, 0] = results[i]['pcross'][0]
            mat[:, 1] = matched[i]
            np.savetxt(fhandle, mat, header=header)


def txt_total_matched_probability(detect, matched, outputfile):
    """
    This method will output the overall matched probability.

    Parameters
    ----------
    detect : list of floats
        These are the detect interfaces used in the analysis.
    matched : numpy.array
        The matched probability.
    outputfile : string
        This is the name of the output file to create.
    """
    header = 'Total matched probability. Interfaces: {}'
    interf = ' , '.join([str(idet) for idet in detect])
    header = header.format(interf)
    txt_save_columns(outputfile, header, (matched[:, 0], matched[:, 1]))


def create_and_format_row(row, width, header=False, spacing=1, fmt_str=None):
    """
    This will format a row according to the given width(s).
    The specified width can either be a fixed number which will be
    applied to all cells, or it can be an iterable.

    Parameters
    ----------
    row : list
        The data to format.
    width : int or iterable
        This is the width of the cells in the table. If it's given as an
        iterable it will be applied to headers untill it's exhausted. In that
        case the last entry will be repeated and used for the remaining items.
    header : boolean, optional
        To tell if we are formatting for a header or not.
        The header will include a '#' to indicate that it's a header.
    spacing : int, optional
        This is the white space for separating columns.
    fmt_str : string, optional
        This is the format to apply, if it's not given, it will be created.

    Returns
    -------
    out[0] : strings
        The format string for the row
    out[1] : string
        This is the formatted row

    Note
    ----
    If the field-width is too large, the value will be truncated here!
    """
    row_str = []
    # first check if width is iterable:
    try:
        for _ in width:
            break
    except TypeError:
        width = [width]
    if fmt_str is None:
        fmt = None
        for (col, wid) in zip_longest(row, width,
                                      fillvalue=width[-1]):
            if header:
                # if this is the header, just assume that all will be strings:
                if fmt is None:  # first item includes a "# " in front.
                    fmt = ['# {{:>{}s}}'.format(wid - 2)]
                else:
                    fmt.append('{{:>{}s}}'.format(wid))
            else:
                # this is not the header, use 'g'
                if fmt is None:
                    fmt = []
                fmt.append('{{:> {}.{}g}}'.format(wid, wid - 6))
                try:
                    fmt[-1].format(col)
                except ValueError:
                    fmt[-1] = '{{:> {}}}'.format(wid)
            rowi = fmt[-1].format(col)
            row_str.append(rowi)
        str_white = (' ') * spacing
        return str_white.join(fmt), str_white.join(row_str)
    else:
        row_str = fmt_str.format(*row)
        return fmt_str, row_str


def _simple_line_parser(line):
    """
    This is just a simple line parser. It will simply return floats from
    columns from a file. It is here created as a def to avoid assigning
    using a lambda expression (see pep8).

    Parameters
    ----------
    line : string
        This string represents a line that we will parse.

    Returns
    -------
    out : list
        This list contains a float for each item in line.split().
    """
    return [float(col) for col in line.split()]


def read_some_lines(filename, line_parser=_simple_line_parser,
                    block_label='#'):
    """
    This function fill open a file and try to read as many lines as
    possible - it the given line_parser can not be used on a line in a
    file the function will stop here. The function will read data in blocks
    and yield the block when a new block is found. A special string is assumed
    to idenity the blocks.

    Parameter
    ---------
    filename : string
        This is the filename to open and read
    line_parser : function, optional
        This is a function which knows how to translate a given line
        to a desired internal format. If not given, a simple float
        will be used.
    block_label : string
        This string is used to identify blocks.

    Yields
    -------
    data : list
        The data read from the file, arranged in dicts
    """
    nblock = len(block_label)
    ncol = -1  # The number of columns
    new_block = None
    with open(filename, 'r') as fileh:
        for line in fileh:
            stripline = line.strip()
            if stripline[:nblock] == block_label:
                # this is a comment = a new block follows
                # store the current block:
                if new_block is not None:
                    yield new_block
                new_block = {'comment': stripline, 'data': []}
                ncol = -1
            else:
                linedata = line_parser(stripline)
                newcol = len(linedata)
                if ncol == -1:  # first item
                    ncol = newcol
                    if new_block is None:
                        new_block = {'comment': None, 'data': []}
                if newcol == ncol:
                    new_block['data'].append(linedata)
                else:
                    break
    if new_block is not None:
        yield new_block


class TxtTable(object):
    """
    TxtTable(object)

    This object will return a table of text with a header and
    with formatted rows.

    Attributes
    ----------
    variables : list of strings
        This is used to choose the variables to write out
    headers : list of strings
        These can be used as headers for the table. If they are
        not given, the strings in variables will be used.
    header : string
        This is the formatted header for the table.
    width : int or iterable
        This defines the maximum width of one cell.
    spacing : int
        This defines the white space between columns.
        A spacing less than 0 will be interpreted as a 0.
    row_fmt : string
        This is a format string which can be used to format the rows of the
        table.
    """
    def __init__(self, variables, width=12, headers=None, spacing=1):
        """
        Initialize the table. Here we can specify default formats for
        floats and for integers.

        Parameters
        ----------
        variables : list of strings
            This is the variables to output to the table.
        width : int or iterable, optional
            This defines the maximum width of one cell.
        headers : list of strings, optional
            These can be used as headers for the table. If they are
            not given, the strings in variables will be used.
        spacing : int, optional
            This is the white space to include between columns.
        """
        self.width = width
        self.variables = variables
        self.spacing = spacing  # zeros are correctly handled by get_header
        self.headers, self.header = self.make_header(headers=headers)
        self.row_fmt = None

    def make_header(self, headers=None):
        """
        This is just a function to return the header. It will also
        create it if needed.

        Parameters
        ----------
        headers : list of strings, optional
            These can be used as headers for the table. If they are
            not given, the strings in variables will be used.

        Returns
        -------
        out[0] : list of strings
            The created headers.
        out[1] : string
            The header as a string.
        """
        if headers is None:
            new_headers = [var.title() for var in self.variables]
        else:
            new_headers = [var.title() for var in headers]
        _, header = create_and_format_row(new_headers, width=self.width,
                                          header=True, spacing=self.spacing)
        return new_headers, header

    def get_header(self):
        """Function to just return the current header."""
        return self.header

    def get_row(self, row_dict, header=False):
        """
        This method will write a row.

        Parameters
        ----------
        row_dict : dict
            This is the row values (columns) to write. Variables will
            be selected according to self.variables. This is just so that
            we can enforce a ordering.
        header : boolean, optional
            If this is true, we are creating the header.
        """
        row = [row_dict.get(var, None) for var in self.variables]
        row_fmt, str_row = create_and_format_row(row,
                                                 width=self.width,
                                                 header=header,
                                                 spacing=self.spacing,
                                                 fmt_str=self.row_fmt)
        if self.row_fmt is None:  # store the row format for re-usage
            self.row_fmt = row_fmt
        return str_row

    def __call__(self, row, header=False):
        """
        This method is just for convenience. It will just
        call self.get_row() with the parameters.

        Parameters
        ----------
        row : dict
            This is the row values (columns) to write. Variables will
            be selected according to self.variables. This is just so that
            we can enforce a ordering.
        header : boolean, optional
            If this is true, we are creating the header.
        """
        return self.get_row(row, header=header)


class FileWriter(object):
    """
    FileWriter(object)

    This class defines a simple object to output to a file.
    Actual formatting are handled by derived objects such as the trajectory
    writers and other writers. This object handles creation/opening of the
    file with backup/overwriting etc.

    Attributes
    ----------
    filename : string
        Name of file to write.
    filetype : string
        Identifies the filetype to write - the "format".
    mode : string
        Mode can be used to select if we should write to the file
        (if mode is equal to 'w') or read from the file (mode equal to 'r').
        The default is mode equal to 'w'.
    oldfile : string
        Defines how we handle existing files with the same
        name as given in `filename`. Note that this is only usefull when the
        mode is set to 'w'.
    count : int
        This is just a counter of how many times write has been called.
    fileh : file
        This is the file handle which can be used for writing etc.
    header : string
        A header (comment) for the first line of the file.
    """
    def __init__(self, filename, filetype, mode='w', oldfile='backup',
                 count=0, header=None):
        """
        Initiates the file writer object. This will just define and
        set some variables

        Paramters
        ---------
        filename : string
            Name of the file to write.
        filetype : string
            Identifies the filetype to write (i.e. the format).
        mode : string, optional
            This determines if we write (= 'w') or read (='r') the file.
        oldfile : string, optional
            Behavior if the `filename` is an existing file.
        frame : int
            Counts the number of frames written
        header : dict, optional
            This determines if we should create a header for the file. For some
            text files this can help for the readability.
        """
        self.count = count
        self.filename = filename
        self.filetype = filetype
        self.mode = mode.lower()
        self.fileh = None
        self.header = None
        if header is not None:
            if 'width' in header:
                _, self.header = create_and_format_row(header['text'],
                                                       header['width'],
                                                       header=True,
                                                       spacing=1,
                                                       fmt_str=None)
            else:
                self.header = header['text']
        if self.mode == 'w':
            self.fileopen(oldfile=oldfile)
            if oldfile != 'append' and self.header is not None:
                self.write_line(self.header)

    def fileopen(self, oldfile='bakcup'):
        """
        Method to open a file, to make it ready for reading/writing.
        This function is separated from the __init__ in case some derived
        classes will open the file at a later stage. Default is to run
        open if the mode it set to 'w'.

        Parameters
        ----------
        oldfile : string, optional
            Behavior if the `filename` is an existing file, i.e. it is only
            usfull when self.mode = 'w'

        Returns
        -------
        None, but self.fileh is set to the open file.
        """
        if self.mode == 'r':  # Read data
            try:
                self.fileh = open(self.filename, 'r')
            except IOError as error:
                msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
                warnings.warn(msg)
        elif self.mode == 'w':  # Write data to file + handle backup:
            try:
                if os.path.isfile(self.filename):
                    msg = 'File {} exist'.format(self.filename)
                    if oldfile == 'overwrite':
                        msg = '{}: Will overwrite!'.format(msg)
                        self.fileh = open(self.filename, 'w')
                    elif oldfile == 'append':
                        msg = '{}: Will append to file'.format(msg)
                        self.fileh = open(self.filename, 'a')
                    else:
                        msg_back = create_backup(self.filename)
                        msg = '{}: {}'.format(msg, msg_back)
                        self.fileh = open(self.filename, 'w')
                    warnings.warn(msg)
                else:
                    self.fileh = open(self.filename, 'w')
            except IOError as error:
                msg = 'I/O error ({}): {}'.format(error.errno, error.strerror)
                warnings.warn(msg)
            except Exception as error:
                msg = 'Error: {}'.format(error)
                warnings.warn(msg)
                raise
        else:
            msg = 'Unknown file mode "{}"'.format(self.mode)
            warnings.warn(msg)

        if self.fileh is None:
            msg = 'Could not open file!'
            warnings.warn(msg)
            raise

    def close(self):
        """
        Method to close the file, in case that is explicitly needed.
        """
        if self.fileh is not None and not self.fileh.closed:
            self.fileh.close()

    def get_mode(self):
        """
        Method to return mode of the file.
        """
        try:
            return self.fileh.mode
        except AttributeError:
            return None

    def write_string(self, towrite):
        """
        Method to write a string to the file.

        Parameters
        ----------
        towrite : string
            This is the string to output to the file
        """
        if towrite is None:
            return False
        if self.fileh is not None and not self.fileh.closed:
            try:
                self.fileh.write(towrite)
                self.count += 1
                return True
            except IOError as error:
                msg = 'Write I/O error ({}): {}'.format(error.errno,
                                                        error.strerror)
                warnings.warn(msg)
            except Exception as error:
                msg = 'Write error: {}'.format(error)
                warnings.warn(msg)
                raise
        else:
            return False

    def write_line(self, towrite):
        """
        This method calls `write_string` adding a new-line to the given
        string.

        Parameters
        ----------
        towrite : string
            This is the string to output to the file
        """
        return self.write_string('{}\n'.format(towrite))

    def __del__(self):
        """
        This method in just to close the file in case the program
        crashes. It is used here as it's not so nice to add a
        with statement to the main script running the simulation.
        """
        if self.fileh is not None and not self.fileh.closed:
            self.fileh.close()
