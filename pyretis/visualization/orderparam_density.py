# -*- coding: utf-8 -*-
# Copyright (c) 2022, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Compiler of PyRETIS simulation data.

This module is part of the PyRETIS library and can be used both for compiling
the simulation data into a compressed file and/or load the data for later
visualization.
"""
import os
import pickle
import warnings
import timeit
import zipfile
import pandas as pd
from tqdm import tqdm
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.visualization.common import (get_min_max,
                                          get_startat,
                                          diff_matching)

warnings.filterwarnings('ignore', category=pd.io.pytables.PerformanceWarning)

# Hard-coded labels for energies and time/cycle steps
ENERGYLABELS = ['time', 'cycE', 'potE', 'kinE', 'totE']


def pyvisa_zip(input_file):
    """Zip compress file of simulation data.

    Parameters
    ----------
    input_file : string
        The file to compress.

    """
    with zipfile.ZipFile(input_file+'.zip', 'w') as zipped_file:
        zipped_file.write(input_file, compress_type=zipfile.ZIP_DEFLATED)

    os.remove(input_file)


def pyvisa_unzip(origin, destination=None):
    """Unzip compressed file before load in visualizer.

    Parameters
    ----------
    origin : string
        Zipped file to unzip.
    destination : string, optional
        Unzipped file name.

    """
    msg = '###################################################\n'
    msg += '# File type recognized as `.zip`, unzipping to tmp file \n'
    msg += f'# {destination} before loading.\n'
    msg += '###################################################\n'
    print_to_screen(msg, level='message')
    with zipfile.ZipFile(origin) as zipped:
        zipped.extractall(path=os.path.dirname(os.path.abspath(origin)))
        # We here assume that only a file is stored in 'zipped'.
        if destination is not None:
            os.rename(zipped.namelist()[0], destination)


def remove_nan(data_list):
    """Remove nan from data.

    The function shall remove initial nan, assuming that they are originated
    by incomplete initial conditions (e.g. no energy file). In the case that
    nan appears as last cycle, it will not be fixed and an error shall rise
    up later in the code.

    Parameters
    ----------
    data_list : list
        Input list. If nan are present, they are replaced by the following
        entry. The method accounts for multiple consecutive nan occourence.

    """
    nan = True
    inan = -1
    while nan:
        nan = False
        for idx, data_point in reversed(list(enumerate(data_list))):
            if data_point * 0 != 0:
                nan = True
                inan = idx
                break
        if nan and inan == len(data_list) - 1:
            nan = False
        if nan:
            data_list[inan] = data_list[inan + 1]


class PathDensity():
    """Perform the path density analysis.

    This class defines the path density analysis for completed simulations
    with several order parameters.

    """

    def __init__(self, iofile=None):
        """Initialize the class.

        Parameters
        ----------
        iofile : string, optional
            The input file.

        """
        self.iofile = iofile
        self.pfile = None
        try:
            testfile = open(self.iofile, 'r', encoding="utf-8")
            os.chdir(os.path.join(os.getcwd(), os.path.dirname(self.iofile)))
            testfile.close()
        except FileNotFoundError:
            line = f'Found no input file, "iofile = {self.iofile}"'
            print_to_screen(line, level='error')
            return
        # Setting up empty dictionaries for the orderP and energy values
        self.eops = {}
        self.infos = {}
        self.ops = {}
        num_op = 0
        # Getting interfaces from iofile
        settings = parse_settings_file(self.iofile)
        interfaces = settings['simulation']['interfaces']
        intnames = ['0$^{-}$', '0$^{+}$']
        for i in range(1, len(interfaces) - 1):
            intnames.append(str(i) + '$^{+}$')
        path = []
        # Getting ensembles/folders from directory
        for fol in sorted(filter(os.path.isdir, os.listdir('.'))):
            if str(fol)[0] == '0':  # Excluding folders not named '0**'
                path.append(fol)
        # Getting order parameters from order-file of first folder in path
        with open(os.path.join(path[0], 'order.txt'),
                  encoding='utf-8') as temp:
            # If implemented, use OP names as labels instead.
            tail = temp.read().split('\n')[-2]
            op_line = tail.split()
            num_op = len(op_line)-1
        op_labels = []
        for i in range(1, num_op+1):
            op_labels.append(f'op{i}')
        op_labels.append('cycO')

        self.infos['path'] = path
        self.infos['op_labels'] = op_labels
        self.infos['energy_labels'] = ENERGYLABELS
        self.infos['interfaces'] = interfaces
        self.infos['intf_names'] = intnames
        self.infos['num_op'] = num_op

    def walk_dirs(self, only_ops=False):
        """Create a lists in acc or rej dictionary for all order parameters.

        First generate list of folders/ensembles to iterate through.
        Then search for number of orderparameters(columns) in file in one
        of the folders of path, and create lists in acc/rej dictionaries
        for all order parameters.

        Lastly iterate through all folders and files, filling in correct data
        to the lists and dictionaries.

        Parameters
        ----------
        only_ops : boolean, optional
            If true, PathDensity will not collect data from energy files.

        Returns/Updates
        ---------------
        ops : dict
            Values of order params in all ensembles.
        eops : dict
            Values of order params and energies in all ensembles.

        """
        def _make_dict_lists(self, fol):
            """Generate empty lists in dictionaries.

            Parameters
            ----------
            fol : string
                Name of subfolder.

            """
            # Creating lists of statistical weigth for accepted paths
            self.ops['astatw', fol] = []
            # Creating lists of time step (from order.txt files)
            self.ops['atimo', fol], self.ops['rtimo', fol] = [], []
            if not only_ops:
                self.eops['atimo', fol], self.eops['rtimo', fol] = [], []
            # Creating empty lists in dictionaries for order params,
            # accepted and rejected
            for j in self.infos['op_labels']:
                self.ops['a'+j, fol], self.ops['r'+j, fol] = [], []
                if not only_ops:
                    self.eops['a'+j, fol], self.eops['r'+j, fol] = [], []
            # Creating empty lists in dictionary for energies and time
            if not only_ops:
                for j in ENERGYLABELS:
                    self.eops['a'+j, fol], self.eops['r'+j, fol] = [], []

        tic = [timeit.default_timer(), None]
        print_to_screen('###################################################',
                        level='message')
        print_to_screen('# PathDensity performing "walk" in \n# ' +
                        f'{os.getcwd()}/',
                        level='message')
        print_to_screen('# Number of subfolders (0**) = ' +
                        f'{len(self.infos["path"])}',
                        level='message')
        print_to_screen(f'# Found {self.infos["num_op"]} ' +
                        'order parameters in output',
                        level='message')
        print_to_screen('###################################################'
                        + '\n', level='message')
        print_to_screen('Creating empty lists for all folders', level=None)
        print_to_screen('------------------------------------')

        # Looping over folders, reading energy and orderP
        for fol in self.infos['path']:
            tic[1] = timeit.default_timer()
            _make_dict_lists(self, fol)
            files = [os.path.join(fol, 'order.txt'),
                     os.path.join(fol, 'energy.txt')]
            print_to_screen(f'Reading data from {fol}', level='message')
            file_starts = [get_startat(files[0])]
            self.get_op(files[0], fol, file_starts[0])
            if not only_ops:
                file_starts.append(get_startat(files[1]))
                self.get_eop(fol, files, file_starts)
                self.check_steps(fol)
            line = ('Done with folder, time used: '
                    f'{timeit.default_timer()-tic[1]:4.4f}s, proceeding.\n')
            print_to_screen('='*len(line) + '\n' + line, level='success')

        maxcl = '000'

        if not only_ops:
            c_e = len(self.eops['acycE', '000'] +
                      self.eops['rcycE', '000'])
            c_o = len(self.ops['acycO', '000'] +
                      self.ops['rcycO', '000'])
            for fol in self.infos['path'][1:]:
                n_e = len(self.eops['acycE', fol] +
                          self.eops['rcycE', fol])
                n_o = len(self.ops['acycO', fol] +
                          self.ops['rcycO', fol])
                if n_o > c_o and n_e > c_e:
                    maxcl = fol

        full_cycle_list = sorted(
            self.ops['acycO', maxcl] + self.ops['rcycO', maxcl])
        self.infos['long_cycle'] = [full_cycle_list[0],
                                    full_cycle_list[-1]]

        print_to_screen('###################################################',
                        level='success')
        print_to_screen('# Data successfully retrieved, in cycles:',
                        level='success')
        print_to_screen((f'# {self.infos["long_cycle"][0]} to '
                         f'{self.infos["long_cycle"][-1]}'),
                        level='success')
        print_to_screen(
            f'# Time spent: {timeit.default_timer()-tic[0]:.2f}s',
            level='success'
        )
        print_to_screen('###################################################'
                        + '\n', level='success')

    def pickle_data(self):
        """Pickles the data to a .pickle file."""
        print_to_screen('###################################################',
                        level='message')
        print_to_screen('# Pickling dictionaries to file', level='message')
        data = (self.ops, self.eops, self.infos)
        self.pfile = 'pyvisa_compressed_data.pickle'
        with open(self.pfile, 'wb') as out:
            pickle.dump(data, out, protocol=pickle.HIGHEST_PROTOCOL)
        print_to_screen(f'# {self.pfile}', level='message')
        pyvisa_zip(self.pfile)
        print_to_screen(f'# {self.pfile}.zip', level='message')
        print_to_screen('###################################################'
                        + '\n', level='message')

    def deepdish_data(self):
        """Compresses the data to a .hdf5 file."""
        print_to_screen('###################################################',
                        level='message')
        print_to_screen('# Compress dictionaries to file', level='message')
        self.pfile = 'pyvisa_compressed_data.hdf5'
        data = pd.DataFrame.from_dict({'ops': self.ops,
                                       'eops': self.eops,
                                       'infos': self.infos})
        data.to_hdf(self.pfile, key='data')
        print_to_screen(f'# {self.pfile}', level='message')
        pyvisa_zip(self.pfile)
        print_to_screen(f'# {self.pfile}.zip', level='message')
        print_to_screen('###################################################'
                        + '\n', level='message')

    def get_eop(self, fol, files, file_starts):
        """Read order and energy files, save frames only if present in both.

        Parameters
        ----------
        fol : string
            Name of folder - e.g. "000". Used in dictionaries for allocating
            values from read to correct list.
        files : list of strings
            Name of files in subfolder path.
        file_starts : list of integers
            Index of files with latest restart of simulation.

        Returns/Updates
        ---------------
        eops : [atime, rtime, apotE, rpotE, akinE, rkinE, atotE, rtotE,
                atimo, rtimo, aop{x}, rop{x}] for x in range(0, #orderP)
            Lists of floats, it contains accepted/rejected steps and energy
            from files efile and ofile in folder fol and the order param
            from file ofile in folder fol. aop{x}/rop{x} loops through the
            total number of order parameters found in the order param file.

        """
        cycle = []
        flag = ''

        # Start with energy file
        with open(files[1], 'r+', encoding='utf-8') as temp:
            for i, line in enumerate(temp):
                if i < file_starts[1]-1:
                    continue
                if '#' in line and line[0] != '#':
                    data = line[:line.index('#')].split()  # before comment
                else:
                    data = line.split()
                if not data:
                    continue
                if data[0] == '#':
                    if data[1] == 'Time':
                        continue
                    try:
                        cycle_t = int(data[2].rstrip(','))
                    except (ValueError, IndexError):
                        continue
                    if 'ACC' in data[4]:
                        flag = 'a'
                    else:
                        flag = 'r'
                    cycle.append(cycle_t)
                    continue

                self.eops[flag+'cycE', fol].append(cycle[-1])
                self.eops[flag+'time', fol].append(int(data[0]))
                self.eops[flag+'potE', fol].append(float(data[1]))
                self.eops[flag+'kinE', fol].append(float(data[2]))
                self.eops[flag+'totE', fol].append(float(data[1]) +
                                                   float(data[2]))

        for value in self.eops.values():
            remove_nan(value)

        write = False
        flag = ''
        # Continue with orderp file
        with open(files[0], 'r', encoding='utf-8') as temp:
            for i, line in enumerate(temp):
                if i < file_starts[0]-1:
                    continue
                if '#' in line and line[0] != '#':
                    data = line[:line.index('#')].split()
                else:
                    data = line.split()
                if not data:
                    continue
                if data[0] == '#':
                    if data[1] == 'Time':
                        continue
                    try:
                        cycle_t = int(data[2].rstrip(','))
                    except (ValueError, IndexError):
                        continue
                    if 'ACC' in data[4]:
                        flag = 'a'
                    else:
                        flag = 'r'
                    write = bool(cycle_t in cycle)
                    continue

                if write:
                    self.eops[flag+'cycO', fol].append(cycle_t)
                    self.eops[flag+'timo', fol].append(int(data[0]))
                    for j in range(1, self.infos['num_op']+1):
                        try:
                            x = float(data[j])
                        except IndexError:
                            x = None
                        self.eops[flag+f'op{j}', fol].append(x)

    def get_op(self, ofile, fol, ostart):
        """Read order params from file and append to the lists in dict.

        Function that reads order params from orderfile, and appends
        values to relevant lists in dictionary.

        Parameters
        ----------
        ofile : string
            Name of orderP file in subfolder path - e.g. "000/order.txt".
        fol : string
            Name of folder - e.g. "000". Used in dictionaries for allocating
            values from read to correct list.
        ostart : integer
            Index of ofile with latest restart of simulation.

        Returns/Updates
        ---------------
        ops : a/r[timo, aop{x}, cycl] for x in range(0, #orderP)
            Lists of floats. Contains accepted/rejected steps and order param
            from file ofile in folder fol. aop{x}/rop{x} loops through the
            total number of order parameters found in the order param file.

        """
        cycle = []
        statw = []
        weight = []
        flag = ''

        with open(ofile, 'r', encoding='utf-8') as orderfile:
            for i, line in enumerate(orderfile):
                if i < ostart-1:
                    continue
                if '#' in line and line[0] != '#':
                    data = line[:line.index('#')].split()
                else:
                    data = line.split()
                if not data:
                    continue
                if data[0] == '#':
                    if data[1] == 'Time':
                        continue
                    try:
                        cycle_t = int(data[2].rstrip(','))
                    except (ValueError, IndexError):
                        continue
                    cycle.append(cycle_t)
                    if 'ACC' in data[4]:
                        flag = 'a'
                        statw.append(1)
                        weight.append(1)
                    else:
                        flag = 'r'
                        if weight:
                            weight[-1] += 1
                        statw.append(0)
                    continue

                self.ops[flag+'timo', fol].append(int(data[0]))
                self.ops[flag+'cycO', fol].append(cycle[-1])
                for j in range(1, self.infos['num_op']+1):
                    try:
                        val = float(data[j])
                    except IndexError:
                        val = None
                    self.ops[flag+f'op{j}', fol].append(val)

        # Creating list of statistical weights of paths
        for val in self.ops['acycO', fol]:
            idx = cycle.index(val)
            self.ops['astatw', fol].append(statw[idx])

    def check_steps(self, fol):
        """Loop over dicts, check lengths and print energy/order lists.

        Function that loops over dictionaries, checking the length of
        lists respective to the folders they were read from. Prints length
        of energy lists, shortened order parameter lists, and full length
        order parameter lists.

        Parameters
        ----------
        fol : string
            Name of folder currently reading files from.

        Returns/Updates
        ---------------
        No returns. Checks and updates the content of orderP and energy,
        timestep and cycle, in the dictionary self.eops[]. If any differences
        are found, another function is called on all lists of that particular
        folder and acc/rej flags, which cuts the unmatched lines.

        """
        def _check_timesteps(acc, fol):
            """Check the similarities of time steps and cycles.

            Function that checks the similarities of time steps and cycles
            of the two dictionaries ops and eops for a given folder and
            acceptance.

            Parameters
            ----------
            acc : boolean
                True/False for accepted/rejected paths.
            fol : string
                Name of folder.

            Returns
            -------
            errors : boolean
                True if errors were encountered, else False.
            level : string
                The level-string for print_to_file function.
            where_err : string
                'time' or 'cycle' if error in timesteps or cycle.

            """
            errors = False
            level = None
            where_err = None
            if self.eops[acc+'timo', fol] != self.eops[acc+'time', fol]:
                errors = True
                level = 'error'
                where_err = 'time'
            elif self.eops[acc+'cycO', fol] != self.eops[acc+'cycE', fol]:
                errors = True
                level = 'error'
                where_err = 'cycle'
            return errors, level, where_err

        for acc in ['a', 'r']:
            lenep = len(self.eops[acc+'time', fol])
            lenop = len(self.eops[acc+'timo', fol])
            lentot = len(self.ops[acc+'timo', fol])
            txt = '{}: energy.txt: {}, order.txt: {}\t '
            txt += 'Total lines in order.txt: {}\t {} %'

            if lentot == 0:
                break
            prc = str('{100.*lenop/lentot:.2f}')

            errors, lev, where_err = _check_timesteps(acc, fol)
            print_to_screen((txt.format(acc.upper(), lenep, lenop, lentot, prc)
                             ), level=lev)

            if errors:
                txt = 'Found error in {}; '
                txt += 'Comparing data in folder {}, paths: {}'
                print_to_screen(txt.format(where_err, fol, acc.upper()),
                                level=lev)
                self.compare_and_cut(fol,
                                     acc,
                                     [lenep, lenop],
                                     target=where_err
                                     )

            errors, lev, where_err = _check_timesteps(acc, fol)
            if errors:
                nlenep = len(self.eops[acc+'time', fol])
                nlenop = len(self.eops[acc+'timo', fol])
                txt = 'Found error in {}; '
                txt += 'Re-checking data: E: {}, OP: {}'
                print_to_screen(txt.format(where_err, nlenep, nlenop),
                                level=lev)
                self.compare_and_cut(fol,
                                     acc,
                                     [nlenep, nlenop],
                                     target=where_err
                                     )

    def compare_and_cut(self, fol, acc, lenp, target='cycle'):
        """Compare an cut unmatched lines from dict lists.

        Function that compares step number of energy and order dictionaries,
        and deletes unmatched lines from either dictionary's lists

        Parameters
        ----------
        fol : string
            Name of folder where difference occured.
        acc : string
            'r'/'a' for accepted/rejected paths.
        lenp : list
            Length of energy time-step list in eops dictionary.
            [0] = length of E-list, [1] = length of OP-list.
        target : string
            The target lists to compare for deletion of lines.

        Returns
        -------
        Updates/removes items from lists in EOP dict and returns the
        equal length lists, with correctly matched values.

        """
        def _del_curr_op(acc, fol, idx):
            """Delete the current line in list.

            Parameters
            ----------
            fol : string
                Name of folder where difference occured.
            acc : string
                'a'/'r' for accepted/rejected paths.
            idx : integer OR tuple
                index of lines to delete, or tuple of "from-to" indeces.

            """
            for key in self.infos['op_labels']:
                del self.eops[acc+key, fol][idx]
            # 'timo' not in op_labels, include:
            del self.eops[acc+'timo', fol][idx]

        def _del_curr_en(acc, fol, idx):
            """Delete the current line in list.

            Parameters
            ----------
            fol : string
                Name of folder where difference occured.
            acc : string
                'a'/'r' for accepted/rejected paths.
            idx : integer OR tuple
                index of lines to delete, or tuple of "from-to" indices.

            """
            for key in ENERGYLABELS:
                del self.eops[acc+key, fol][idx]

        def _del_last_op(acc, fol):
            """Delete the last lines of lists in OP dict.

            Parameters
            ----------
            fol : string
                Name of folder where difference occured.

            """
            for key in self.infos['op_labels']:
                del self.eops[acc+key, fol][lenp[0]:]
            # 'timo' not in op_labels, include exception:
            del self.eops[acc+'timo', fol][lenp[0]:]

        def _del_last_en(acc, fol):
            """Delete the last lines of lists in OP dict.

            Parameters
            ----------
            fol : string
                Name of folder where difference occured.

            """
            for key in ENERGYLABELS:
                del self.eops[acc+key, fol][lenp[1]:]

        # Case: List timesteps match
        if self.eops[acc+'time', fol] == self.eops[acc+'timo', fol]:
            print_to_screen('---------------------------------',
                            level='success')
            print_to_screen('Time steps of the lists ' +
                            f'({acc.upper()}) match', level='success')

        # Case: orderP (lists) are longer than the orderP, else match
        elif (lenp[0] < lenp[1] and
              self.eops[acc+'timo', fol][0:lenp[0]] ==
              self.eops[acc+'time', fol]):
            print_to_screen(
                f'Deleting last {lenp[1]-lenp[0]} lines of orderP lists',
                level='message'
            )
            _del_last_op(acc, fol)

        # Case: energy (lists) are longer than the energy, else match
        elif (lenp[1] < lenp[0] and
              self.eops[acc+'time', fol][0:lenp[1]] ==
              self.eops[acc+'timo', fol]):
            print_to_screen(
                f'Deleting last {lenp[0]-lenp[1]} lines of energy lists',
                level='message'
            )
            _del_last_en(acc, fol)

        # Case: More differences mid-lists, heavy loop-through required
        else:
            tic = timeit.default_timer()
            print_to_screen('Matching '+target+'-lists for differences',
                            level='message')
            if target == 'cycle':
                d_e, d_o = diff_matching(self.eops[acc+'cycE', fol],
                                         self.eops[acc+'cycO', fol],
                                         lenp)
            elif target == 'time':
                d_e, d_o = diff_matching(self.eops[acc+'time', fol],
                                         self.eops[acc+'timo', fol],
                                         lenp)
            l_de, l_do = len(d_e), len(d_o)

            for i in tqdm(reversed(d_e), total=l_de, desc=' - E '):
                _del_curr_en(acc, fol, i)
            for i in tqdm(reversed(d_o), total=l_do, desc=' - OP'):
                _del_curr_op(acc, fol, i)

            toc = timeit.default_timer()
            print_to_screen('Deletion done, time used: ' +
                            f'{toc-tic:.4f}s. Proceeding',
                            level='success')


class PathVisualize():
    """Class to define the visualization of data with PathDensity.

    Class definition of the visualization of data gathered from simulation
    directory using the PathDensity class.

    """

    def __init__(self, pfile=None):
        """Initialize the PathVisualize class.

        If a supported compressed input file is present, loads the pre-compiled
        data from it. Else, must use specific functions explicitly.

        Parameters
        ----------
        pfile : string, optional
            The input file.

        """
        self.ops = None
        self.eops = None
        self.infos = None
        self.op_labels = None
        self.pfile = pfile
        if self.pfile is not None:
            self.load_whatever()

    def load_whatever(self):
        """Load all possible supported files.

        This functions directs traffic towards the real loaders.
        Essentially, it does almost nothing.

        """
        clean = False
        if self.pfile.endswith('.zip'):
            origin = self.pfile
            self.pfile = self.pfile.rstrip('.zip')
            tmp = os.path.join(os.path.dirname(os.path.abspath(origin)),
                               'tmp_'+self.pfile)
            self.pfile = tmp
            pyvisa_unzip(origin, tmp)
            clean = True
        if self.pfile.endswith('.pickle'):
            self.load_pickle()
        elif self.pfile.endswith('.hdf5'):
            self.load_dd()
        else:
            raise ValueError('Format not recognised')
        # If from zip, just keep the zip
        if clean:
            os.remove(tmp)

    def load_pickle(self):
        """Load precompiled data from pickle file.

        Function that loads precompiled data from .pickle file. Depending
        on file name, will define data as being created using fast or slow
        post-processing.

        """
        with open(self.pfile, 'rb') as pdata:
            data = pickle.load(pdata)
        # Unpacking dictionaries
        self.ops = data[0]
        self.eops = data[1]
        self.infos = data[2]
        # Unpacking lists of info from infos dict
        self.op_labels = self.infos['op_labels']

    def load_dd(self):
        """Load precompiled data from a hdf5 file.

        Function that loads precompiled data from a .hdf5 file made
        using pandas.

        """
        # Unpacking dictionaries
        data = pd.read_hdf(self.pfile, key='data')
        self.ops = data['ops']
        self.eops = data['eops']
        self.infos = data['infos']
        # Unpacking lists of info from infos dict
        self.op_labels = self.infos['op_labels']

    def get_odata(self, fol, xyacc, weight=True, min_max=(0, 0)):
        """Load relevant data from dictionaries.

        Function that loads the relevant data from the dictionaries.
        (Depending on choice of order param, folder, and whether paths
        are acc/rej/both).

        Parameters
        ----------
        fol : string
            Name of folder, 000, 001, etc.
        xyacc : list
            [0:1] : strings, names of x/y order parameter.
            [2] : bool, True/False for acc/rej paths.
        weight : boolean, optional
            If True, trajectories are
            statistically weighted when read from dict.
        min_max : list
            Minimum and maximum cycle number of simulation data.

        Returns
        -------
        x : list
            Floats with values of op2, from dict ops[op2, fol].
        y : list
            Floats with values of op1, from dict ops[op1, fol].

        """
        x, y = [], []

        if xyacc[2] == 'ACC' or xyacc[2] is True:
            acc = 'a'
        elif xyacc[2] == 'REJ' or xyacc[2] is False:
            acc = 'r'
        elif xyacc[2] == 'BOTH':
            acc = 'BOTH'

        # Default - start-to-end
        mini = {'a': 0, 'r': 0}
        maxi = {'a': len(self.ops['acycO', fol]) - 1,
                'r': len(self.ops['rcycO', fol]) - 1}

        # Deciding x,y index span using cycle number
        if acc == 'BOTH':
            for a_r in ['a', 'r']:
                get_min_max(self.ops[a_r+'cycO', fol], min_max, mini,
                            maxi, a_r)
        else:
            get_min_max(self.ops[acc+'cycO', fol], min_max, mini, maxi, acc)

        # Applying statistical weights to paths, or not
        if weight:
            weights = self.ops['astatw', fol][mini['a']:maxi['a']]
        else:
            weights = [1]*len(self.ops['a'+xyacc[0], fol][mini['a']:maxi['a']])

        if acc != 'r':
            for a, b, c in zip(
                    self.ops['a'+xyacc[0], fol][mini['a']:maxi['a']],
                    self.ops['a'+xyacc[1], fol][mini['a']:maxi['a']],
                    weights):
                for _ in range(c):
                    x.append(a)
                    y.append(b)
            if acc == 'BOTH':
                x += self.ops['r'+xyacc[0], fol][mini['r']:maxi['r']]
                y += self.ops['r'+xyacc[1], fol][mini['r']:maxi['r']]

        elif acc == 'r':
            x += self.ops['r'+xyacc[0], fol][mini['r']:maxi['r']]
            y += self.ops['r'+xyacc[1], fol][mini['r']:maxi['r']]

        # Remove item in both lists if one or both is NoneType
        del_indx = []
        for i, _ in enumerate(x):
            if x[i] is None or y[i] is None:
                del_indx.append(i)
        for i in reversed(del_indx):
            del x[i]
            del y[i]
        return x, y

    def get_edata(self, fol, xyz, acc, min_max=None):
        """Load relevant data from the dictionaries.

        Function that loads the relevant data from the dictionaries,
        depending on choice of order param and energy, whether paths
        acc/rej/both, and folder.

        Parameters
        ----------
        xyz : list
            Names of order parameter and energy labels, for x/y/z-axis.
        acc : boolean OR string
            True/False for acc/rej paths, "BOTH" for both.
        fol : string
            Name of folder, 000,001,etc.
        min_max : list
            Minimum and maximum cycle of simulation data.

        Returns
        -------
        x : list
            Floats with values of op2, from dict eops[op2, fol].
        y : list
            Floats with values of op1, from dict eops[op1, fol].
        z : list
            Floats with values of E from eops[E, fol].

        """
        x, y, z = [], [], []

        if acc == 'ACC' or acc is True:
            acc = 'a'
        elif acc == 'REJ' or acc is False:
            acc = 'r'

        # Default - start-to-end
        mini = {'a': 0, 'r': 0}
        maxi = {'a': len(self.eops['acycE', fol]) - 1,
                'r': len(self.eops['rcycE', fol]) - 1}

        # Deciding x,y,z index span using cycle number
        if min_max is not None:
            for lll in ['a', 'r']:
                get_min_max(self.eops[lll+'cycE', fol],
                            min_max, mini, maxi, lll)

        if acc == 'BOTH':
            x = (self.eops['a'+xyz[0], fol][mini['a']:maxi['a']] +
                 self.eops['r'+xyz[0], fol][mini['r']:maxi['r']])
            y = (self.eops['a'+xyz[1], fol][mini['a']:maxi['a']] +
                 self.eops['r'+xyz[1], fol][mini['r']:maxi['r']])
            if xyz[2] == 'None':
                z = [1]*len(x)
            else:
                z = (self.eops['a'+xyz[2], fol][mini['a']:maxi['a']] +
                     self.eops['r'+xyz[2], fol][mini['r']:maxi['r']])
        else:
            x = self.eops[acc+xyz[0], fol][mini[acc]:maxi[acc]]
            y = self.eops[acc+xyz[1], fol][mini[acc]:maxi[acc]]
            if len(xyz) == 2 or xyz[2] == 'None':
                z = [1]*len(x)
            else:
                z = self.eops[acc+xyz[2], fol][mini[acc]:maxi[acc]]

        # Remove item in both lists if one or both is NoneType
        del_indx = []
        for i, _ in enumerate(x):
            if x[i] is None or y[i] is None or z[i] is None:
                del_indx.append(i)
        for i in reversed(del_indx):
            del x[i]
            del y[i]
            del z[i]
        return x, y, z
