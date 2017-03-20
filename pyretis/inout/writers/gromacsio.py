# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Module for handling GROMACS input/output.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

read_gromacs_file (:py:func:`.read_gromacs_file`)
    A method for reading snapshots from a GROMACS GRO file.

read_gromos96_file (:py:func:`.read_gromos96_file`)
    Read a single configuration GROMACS .g96 file.

write_gromos96_file (:py:func:`.write_gromos96_file`)
    Write configuration in GROMACS g96 format.

read_xvg_file (:py:func:`.read_xvg_file`)
    For reading .xvg files from GROMACS.

read_trr_header (:py:func:`.read_trr_header`)
    Read a header from an open .trr

read_trr_data (:py:func:`.read_trr_data`)
    Read data from an open .trr file.

skip_trr_data (:py:func:`.skip_trr_data`)
    Skip reading data from an open .trr file and move on to the
    next header.
"""
import logging
import struct
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = [
    'read_gromacs_file',
    'read_gromos96_file',
    'write_gromos96_file',
    'read_xvg_file',
    'read_trr_header',
    'read_trr_data',
    'skip_trr_data'
    ]


# Define formats for the trajectory output:
_GRO_FMT = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}'
_GRO_VEL_FMT = _GRO_FMT + '{7:8.4f}{8:8.4f}{9:8.4f}'
_GRO_BOX_FMT = '{0:12.6f} {1:12.6f} {2:12.6f}'


# Definitions for the .trr reader.
TRR_HEAD_SIZE = 74
_GROMACS_MAGIC = 1993
_DIM = 3
_TRR_VERSION = 'GMX_trn_file'
_SIZE_FLOAT = struct.calcsize('f')
_SIZE_DOUBLE = struct.calcsize('d')
_HEAD_FMT = '{}13i'
_HEAD_ITEMS = ('ir_size', 'e_size', 'box_size', 'vir_size', 'pres_size',
               'top_size', 'sym_size', 'x_size', 'v_size', 'f_size',
               'natoms', 'step', 'nre', 'time', 'lambda')
TRR_DATA_ITEMS = ('box_size', 'vir_size', 'pres_size',
                  'x_size', 'v_size', 'f_size')


def read_gromacs_lines(lines):
    """A method for reading GROMACS GRO data.

    This method will read a GROMACS file and yield the different
    snapshots found in the file.

    Parameters
    ----------
    lines : iterable
        Some lines of text data representing a GROMACS GRO file.

    Yields
    ------
    out : dict
        This dict contains the snapshot.
    """
    lines_to_read = 0
    snapshot = {}
    read_natoms = False
    gro = (5, 5, 5, 5, 8, 8, 8, 8, 8, 8)
    gro_keys = ('residunr', 'residuname', 'atomname', 'atomnr',
                'x', 'y', 'z', 'vx', 'vy', 'vz')
    gro_type = (int, str, str, int, float, float, float, float, float, float)
    for line in lines:
        if read_natoms:
            read_natoms = False
            lines_to_read = int(line.strip()) + 1
            continue  # just skip to next line
        if lines_to_read == 0:  # new shapshot
            if len(snapshot) > 0:
                yield snapshot
            snapshot = {'header': line.strip()}
            read_natoms = True
        elif lines_to_read == 1:  # read box
            snapshot['box'] = [float(boxl) for boxl in line.strip().split()]
            lines_to_read -= 1
        else:  # read atoms
            lines_to_read -= 1
            current = 0
            for i, key, gtype in zip(gro, gro_keys, gro_type):
                val = line[current:current+i].strip()
                if len(val) == 0:
                    # This typically happens if we try to read velocities
                    # and they are not present in the file.
                    break
                value = gtype(val)
                current += i
                try:
                    snapshot[key].append(value)
                except KeyError:
                    snapshot[key] = [value]
    if len(snapshot) > 1:
        yield snapshot


def read_gromacs_file(filename):
    """A method for reading GROMACS GRO files.

    This method will read a GROMACS file and yield the different
    snapshots found in the file.

    Parameters
    ----------
    filename : string
        The file to open.

    Yields
    ------
    out : dict
        This dict contains the snapshot.

    Examples
    --------
    >>> from pyretis.inout.writers.gromacsio import read_gromacs_file
    >>> for snapshot in read_gromacs_file('traj.gro'):
    ...     print(snapshot['x'][0])
    """
    with open(filename, 'r') as fileh:
        for snapshot in read_gromacs_lines(fileh):
            yield snapshot


def read_gromos96_file(filename):
    """Read a single configuration GROMACS .g96 file.

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


def swap_integer(integer):
    """Convert little/big endian."""
    return (((integer << 24) & 0xff000000) | ((integer << 8) & 0x00ff0000) |
            ((integer >> 8) & 0x0000ff00) | ((integer >> 24) & 0x000000ff))


def swap_endian(endian):
    """Just swap the string for selecting big/little."""
    if endian == '>':
        return '<'
    elif endian == '<':
        return '>'
    else:
        raise ValueError('Undefined swap!')


def read_struct_buff(fileh, fmt):
    """Unpack from a filehandle with a given format.

    Parameters
    ----------
    fileh : file object
        The file handle to unpack from.
    fmt : string
        The format to use for unpacking.

    Returns
    -------
    out : tuple
        The unpacked elements according to the given format.

    Raises
    ------
    EOFError
        We will raise an EOFError if `fileh.read()` attempts to read
        past the end of the file.
    """
    buff = fileh.read(struct.calcsize(fmt))
    if not buff:
        raise EOFError
    else:
        return struct.unpack(fmt, buff)


def read_matrix(fileh, endian, double):
    """Read a matrix from the .trr file.

    Here, we assume that the matrix will be of
    dimensions (_DIM, _DIM).

    Parameters
    ----------
    fileh : file object
        The file handle to read from.
    endian : string
        Determines the byte order.
    double : boolean
        If true, we will assume that the numbers
        were stored in double precision.

    Returns
    -------
    mat : numpy.array
        The matrix as an numpy array.
    """
    if double:
        fmt = '{}{}d'.format(endian, _DIM * _DIM)
    else:
        fmt = '{}{}f'.format(endian, _DIM * _DIM)
    read = read_struct_buff(fileh, fmt)
    mat = np.zeros((_DIM, _DIM))
    for i in range(_DIM):
        for j in range(_DIM):
            mat[i, j] = read[i * _DIM + j]
    return mat


def read_coord(fileh, endian, double, natoms):
    """Read a coordinate section from the .trr file.

    This method will read the full coordinate section from a .trr
    file. The coordinate section may be positions, velocities or
    forces.

    Parameters
    ----------
    fileh : file object
        The file handle to read from.
    endian : string
        Determines the byte order.
    double : boolean
        If true, we will assume that the numbers
        were stored in double precision.
    natoms : int
        The number of atoms we have stored coordinates for.

    Returns
    -------
    mat : numpy.array
        The coordinates as a numpy array. It will have
        ``natoms`` rows and ``_DIM`` columns.
    """
    if double:
        fmt = '{}{}d'.format(endian, natoms * _DIM)
    else:
        fmt = '{}{}f'.format(endian, natoms * _DIM)
    read = read_struct_buff(fileh, fmt)
    mat = np.array(read)
    mat.shape = (natoms, _DIM)
    return mat


def is_double(header):
    """Determines we we should use double precision.

    This method determined the precision to use when reading
    the .trr file. This is based on the header read for a given
    frame which defines the sizes of certain "fields" like the box
    or the positions. From this size, the precision can be obtained.

    Parameters
    ----------
    header : dict
        The header read from the .trr file.

    Returns
    -------
    out : boolean
        True if we should use double precision.
    """
    key_order = ('box_size', 'x_size', 'v_size', 'f_size')
    size = 0
    for key in key_order:
        if header[key] != 0:
            if key == 'box_size':
                size = int(header[key] / _DIM**2)
                break
            else:
                size = int(header[key] / (header['natoms'] * _DIM))
                break
    if (size != _SIZE_FLOAT) and (size != _SIZE_DOUBLE):
        raise ValueError('Could not determine size!')
    else:
        return size == _SIZE_DOUBLE


def read_trr_header(fileh):
    """Read a header from a .trr file.

    Parameters
    ----------
    fileh : file object
        The file handle for the file we are reading.

    Returns
    -------
    header : dict
        The header read from the file.
    """
    start = fileh.tell()
    endian = '>'
    magic = read_struct_buff(fileh, '{}1i'.format(endian))[0]

    if magic == _GROMACS_MAGIC:
        pass
    else:
        magic = swap_integer(magic)
        endian = swap_endian(endian)
    slen = read_struct_buff(fileh, '{}2i'.format(endian))
    raw = read_struct_buff(fileh, '{}{}s'.format(endian, slen[0]-1))
    version = raw[0].split(b'\0', 1)[0].decode('utf-8')
    if not version == _TRR_VERSION:
        raise ValueError('Unknown format')

    head_fmt = _HEAD_FMT.format(endian)
    head_s = read_struct_buff(fileh, head_fmt)
    header = {}
    for i, val in enumerate(head_s):
        key = _HEAD_ITEMS[i]
        header[key] = val
    # The next are either floats or double
    double = is_double(header)
    if double:
        fmt = '{}2d'.format(endian)
    else:
        fmt = '{}2f'.format(endian)
    header_r = read_struct_buff(fileh, fmt)
    header['time'] = header_r[0]
    header['lambda'] = header_r[1]
    header['endian'] = endian
    header['double'] = double
    return header, fileh.tell() - start


def skip_trr_data(fileh, header):
    """Skip coordinates/box data etc.

    This method is used when we want to skip a data section in
    the .trr file. Rather than reading the data it will use the
    sized read in the header to skip ahead to the next frame.

    Parameters
    ----------
    fileh : file object
        The file handle for the file we are reading.
    header : dict
        The header read from the .trr file.
    """
    offset = sum([header[key] for key in TRR_DATA_ITEMS])
    fileh.seek(offset, 1)
    return None


def read_trr_data(fileh, header):
    """Read box, cooridnates etc. from a .trr file.

    Parameters
    ----------
    fileh : file object
        The file handle for the file we are reading.
    header : dict
        The header read from the file.

    Returns
    -------
    data : dict
        The data we read from the file. It may contain the following
        keys if the data was found in the frame:

        - ``box`` : the box matrix,
        - ``vir`` : the virial matrix,
        - ``pres`` : the pressure matrix,
        - ``x`` : the coordinates,
        - ``v`` : the velocities, and
        - ``f`` : the forces
    """
    data = {}
    endian = header['endian']
    double = header['double']
    for key in ('box', 'vir', 'pres'):
        header_key = '{}_size'.format(key)
        if header[header_key] != 0:
            data[key] = read_matrix(fileh, endian, double)
    for key in ('x', 'v', 'f'):
        header_key = '{}_size'.format(key)
        if header[header_key] != 0:
            data[key] = read_coord(fileh, endian, double,
                                   header['natoms'])
    return data
