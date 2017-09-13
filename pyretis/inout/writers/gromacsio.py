# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Module for handling GROMACS input/output.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

read_gromacs_file (:py:func:`.read_gromacs_file`)
    A method for reading snapshots from a GROMACS GRO file.

read_gromacs_gro_file (:py:func:`.read_gromacs_gro_file`)
    Read a single snapshot from a GROMACS GRO file.

write_gromacs_gro_file (:py:func:`.write_gromacs_gro_file`)
    Write configuration in GROMACS GRO format.

read_gromos96_file (:py:func:`.read_gromos96_file`)
    Read a single configuration GROMACS .g96 file.

write_gromos96_file (:py:func:`.write_gromos96_file`)
    Write configuration in GROMACS g96 format.

read_xvg_file (:py:func:`.read_xvg_file`)
    For reading .xvg files from GROMACS.

read_trr_header (:py:func:`.read_trr_header`)
    Read a header from an open .trr file.

read_trr_data (:py:func:`.read_trr_data`)
    Read data from an open .trr file.

skip_trr_data (:py:func:`.skip_trr_data`)
    Skip reading data from an open .trr file and move on to the
    next header.

read_trr_file (:py:func:`.read_trr_file`)
    Yield frames from a .trr file.

trr_frame_to_g96 (:py:func:`.trr_frame_to_g96`)
    Dump a specific frame from a .trr file to a .g96 file.

write_trr_frame (:py:func:`.write_trr_frame`)
    Simple method to write to a .trr file.
"""
import logging
import struct
import io
import numpy as np
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = [
    'read_gromacs_file',
    'read_gromacs_gro_file',
    'write_gromacs_gro_file',
    'read_gromos96_file',
    'write_gromos96_file',
    'read_xvg_file',
    'read_trr_header',
    'read_trr_data',
    'skip_trr_data',
    'read_trr_file',
    'trr_frame_to_g96',
    'write_trr_frame',
]


# Define formats for the trajectory output:
_GRO_FMT = '{0:5d}{1:5s}{2:5s}{3:5d}{4:8.3f}{5:8.3f}{6:8.3f}'
_GRO_VEL_FMT = _GRO_FMT + '{7:8.4f}{8:8.4f}{9:8.4f}'
_GRO_BOX_FMT = '{:15.9f}'
_G96_FMT = '{0:}{1:15.9f}{2:15.9f}{3:15.9f}\n'
_G96_FMT_FULL = '{0:5d} {1:5s} {2:5s}{3:7d}{4:15.9f}{5:15.9f}{6:15.9f}\n'
_G96_BOX_FMT = '{:15.9f}' * 9 + '\n'

# Definitions for the .trr reader.
_GROMACS_MAGIC = 1993
_DIM = 3
_TRR_VERSION = 'GMX_trn_file'
_TRR_VERSION_B = b'GMX_trn_file'
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
        if lines_to_read == 0:  # new snapshot
            if snapshot:
                yield snapshot
            snapshot = {'header': line.strip()}
            read_natoms = True
        elif lines_to_read == 1:  # read box
            snapshot['box'] = [float(i) for i in line.strip().split()]
            lines_to_read -= 1
        else:  # read atoms
            lines_to_read -= 1
            current = 0
            for i, key, gtype in zip(gro, gro_keys, gro_type):
                val = line[current:current+i].strip()
                if not val:
                    # This typically happens if we try to read velocities
                    # and they are not present in the file.
                    break
                value = gtype(val)
                current += i
                try:
                    snapshot[key].append(value)
                except KeyError:
                    snapshot[key] = [value]
    if snapshot:
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


def read_gromacs_gro_file(filename):
    """Read a single configuration GROMACS .gro file.

    Parameters
    ----------
    filename : string
        The file to read.

    Returns
    -------
    frame : dict
        This dict contains all the data read from the file.
    xyz : numpy.array
        The positions.
    vel : numpy.array
        The velocities.
    box : numpy.array
        The box dimensions.
    """
    xyz = None
    vel = None
    frame = None
    box = None
    with open(filename, 'r') as fileh:
        for frame in read_gromacs_lines(fileh):
            xyz = np.array([[i, j, k] for i, j, k in zip(frame['x'],
                                                         frame['y'],
                                                         frame['z'])])
            try:
                vel = np.array([[i, j, k] for i, j, k in zip(frame['vx'],
                                                             frame['vy'],
                                                             frame['vz'])])
            except KeyError:
                vel = np.zeros_like(xyz)
            box = np.array(frame['box'])
            break
    return frame, xyz, vel, box


def write_gromacs_gro_file(outfile, txt, xyz, vel):
    """Write configuration in GROMACS GRO format.

    Parameters
    ----------
    outfile : string
        The name of the file to create.
    txt : dict of lists of strings
        This dict contains the information on residue-numbers, names,
        etc. required to write the GRO file.
    xyz : numpy.array
        The positions to write.
    vel : numpy.array
        The velocities to write.
    """
    resnum = txt['residunr']
    resname = txt['residuname']
    atomname = txt['atomname']
    atomnr = txt['atomnr']
    npart = len(xyz)
    with open(outfile, 'w') as output:
        output.write('{}\n'.format(txt['header']))
        output.write('{}\n'.format(npart))
        for i in range(npart):
            buff = _GRO_VEL_FMT.format(
                resnum[i],
                resname[i],
                atomname[i],
                atomnr[i],
                xyz[i, 0],
                xyz[i, 1],
                xyz[i, 2],
                vel[i, 0],
                vel[i, 1],
                vel[i, 2])
            output.write('{}\n'.format(buff))
        box = ' '.join([_GRO_BOX_FMT.format(i) for i in txt['box']])
        output.write('{}\n'.format(box))


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
    box : numpy.array
        The simulation box.
    """
    _len = 15
    _pos = 24
    rawdata = {'TITLE': [], 'POSITION': [], 'VELOCITY': [], 'BOX': []}
    section = None
    with open(filename, 'r', errors='replace') as gromosfile:
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
    if not rawdata['VELOCITY']:
        # No velocities were found in the input file.
        xyzdata['VELOCITY'] = np.zeros_like(xyzdata['POSITION'])
        logger.info('Input g96 did not contain velocities')
    if rawdata['BOX']:
        box = np.array([float(i) for i in rawdata['BOX'][0].split()])
    else:
        box = None
        logger.info('Input g96 did not contain box vectors.')
    return rawdata, xyzdata['POSITION'], xyzdata['VELOCITY'], box


def write_gromos96_file(filename, raw, xyz, vel):
    """Write configuration in GROMACS .g96 format.

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
    with open(filename, 'w') as outfile:
        for key in _keys:
            if key not in raw:
                continue
            outfile.write('{}\n'.format(key))
            for i, line in enumerate(raw[key]):
                if key == 'POSITION':
                    outfile.write(_G96_FMT.format(line, *xyz[i]))
                elif key == 'VELOCITY':
                    outfile.write(_G96_FMT.format(line, *vel[i]))
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
    """Unpack from a file handle with a given format.

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
        if not magic == _GROMACS_MAGIC:
            logger.critical(
                'TRR file might be inconsistent! Could find _GROMACS_MAGIC'
            )
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
    """Read box, coordinates etc. from a .trr file.

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


def read_trr_file(filename, read_data=True):
    """Yields frames from a .trr file."""
    with open(filename, 'rb') as infile:
        while True:
            try:
                header, _ = read_trr_header(infile)
                if read_data:
                    data = read_trr_data(infile, header)
                else:
                    skip_trr_data(infile, header)
                    data = None
                yield header, data
            except EOFError:
                return
            except struct.error:
                logger.warning(
                    'Could not read frame from .trr file. Stopping!'
                )
                return


def read_trr_frame(filename, index):
    """Return a given frame from a .trr file."""
    idx = 0
    with open(filename, 'rb') as infile:
        while True:
            try:
                header, _ = read_trr_header(infile)
                if idx == index:
                    data = read_trr_data(infile, header)
                    return header, data
                else:
                    skip_trr_data(infile, header)
                idx += 1
                if idx > index:
                    logger.error('Frame %i not found in %s', index, filename)
                    return None, None
            except EOFError:
                return None, None


def trr_frame_to_g96(trr_file, index, outfile):
    """Dump a .trr frame to a .g96 file.

    Parameters
    ----------
    trr_file : string
        The .trr file to read from.
    index : integer
        The index for the frame to dump from ``trr_file``.
    outfile : string
        The g96 file to write.
    """
    header, data = read_trr_frame(trr_file, index)
    with open(outfile, 'w') as output:
        output.write('TITLE\n')
        output.write(' Dump from .trr, index = {}, time = {}\n'.format(
            index,
            header['time']))
        output.write('END\n')
        output.write('POSITION\n')
        for i, posi in enumerate(data['x']):
            output.write(_G96_FMT_FULL.format(i, 'DUM', 'X', i, *posi))
        output.write('END\n')
        if 'v' in data:
            output.write('VELOCITY\n')
            for i, veli in enumerate(data['v']):
                output.write(_G96_FMT_FULL.format(i, 'DUM', 'X', i, *veli))
            output.write('END\n')
        output.write('BOX\n')
        box = data['box']
        output.write(_G96_BOX_FMT.format(box[0, 0], box[1, 1], box[2, 2],
                                         box[1, 0], box[2, 0], box[0, 1],
                                         box[2, 1], box[0, 2], box[1, 2]))
        output.write('END\n')


def _get_chunks(start, end, size):
    """Yield chunks between start and end of the given size."""
    while start < end:
        new_size = min(size, end - start)
        start += new_size
        yield start, new_size


def reverse_trr(filename, outname, print_progress=True):
    """Reverse a GROMACS .trr file.

    Parameters
    ----------
    filename : string
        The file path to the input file.
    outname : string
        The file path to the output file.
    print_progress : boolean
        This can be used to print out information about the
        progress to the screen. Might be useful if we are reading
        a large file.
    """
    # We first loop over the file until we reach the
    # last header, we skip the data and read all the headers.
    all_headers = []
    buff_size = io.DEFAULT_BUFFER_SIZE
    with open(filename, 'rb') as infile, open(outname, 'wb') as outfile:
        while True:
            try:
                header, header_size = read_trr_header(infile)
                header_loc = infile.tell()
                skip_trr_data(infile, header)
                all_headers.append((header, header_loc, header_size))
            except EOFError:
                break
        # Loop through headers in reverse and write data.
        for header, header_loc, header_size in reversed(all_headers):
            if print_progress:  # pragma: no cover
                print('Processing step {} time {}'.format(header['step'],
                                                          header['time']))
            data_size = sum([header[key] for key in TRR_DATA_ITEMS])
            start = header_loc - header_size
            infile.seek(start)
            end = start + header_size + data_size
            for _, chunk_size in _get_chunks(start, end, buff_size):
                outfile.write(infile.read(chunk_size))


def write_trr_frame(filename, data, endian=None, double=False, append=False):
    """Write data in .trr format to a file.

    Parameters
    ----------
    filename : string
        The name/path of the file to write to.
    data : dict
        The data we will write to the file.
    endian : string, optional
        Select the byte order; big-endian or little-endian. If not
        specified, the native byte order will be used.
    double : boolean, optional
        If True, we will write in double precision.
    append : boolean, optional
        If True, we will append to the file, otherwise, the file
        will be overwritten."""
    if append:
        mode = 'ab'
    else:
        mode = 'wb'

    if double:
        size = _SIZE_DOUBLE
        floatfmt = '{}d'
    else:
        floatfmt = '{}f'
        size = _SIZE_FLOAT

    if endian:
        floatfmt = endian + floatfmt

    header = {}
    for key in _HEAD_ITEMS:
        header[key] = 0

    header['natoms'] = data['natoms']
    header['step'] = data['step']
    header['box_size'] = size * _DIM * _DIM
    for i in ('x', 'v', 'f'):
        if i in data:
            header['{}_size'.format(i)] = data['natoms'] * size * _DIM
    header['endian'] = endian
    header['double'] = double
    header['time'] = data['time']
    header['lambda'] = data['lambda']

    with open(filename, mode) as outfile:
        write_trr_header(outfile, header, floatfmt, endian=endian)
        for key in TRR_DATA_ITEMS:
            if header[key] != 0:
                matrix = data[key.split('_')[0]]
                fmt = floatfmt.format(matrix.size)
                outfile.write(struct.pack(fmt, *matrix.flatten()))
    return header


def write_trr_header(outfile, header, floatfmt, endian=None):
    """Helper method to write the .trr header.

    Parameters
    ----------
    outfile : filehandle
        The file we can write to.
    header : dict
        The header data for the .trr file.
    floatfmt : string
        The string which gives the format for floats. It should indicate
        if we are writing for double or single precision.
    endian : string, optional
        Can be used to force endianess.
    """
    slen = (13, 12)
    fmt = ['1i', '2i', '{}s'.format(slen[0] - 1), '13i']
    if endian:
        fmt = [endian + i for i in fmt]
    outfile.write(struct.pack(fmt[0], _GROMACS_MAGIC))
    outfile.write(struct.pack(fmt[1], *slen))
    outfile.write(struct.pack(fmt[2], _TRR_VERSION_B))
    head = [header[key] for key in _HEAD_ITEMS[:13]]
    outfile.write(struct.pack(fmt[3], *head))
    outfile.write(struct.pack(floatfmt.format(1), header['time']))
    outfile.write(struct.pack(floatfmt.format(1), header['lambda']))
