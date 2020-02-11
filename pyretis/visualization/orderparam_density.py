# -*- coding: utf-8 -*-
# pylint: skip-file
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Compiler of PyRETIS simulation data.

This module is part of the PyRETIS library and can be used both for compiling
the simulation data into a compressed file and/or load the data for later
visualization.
"""
import argparse
import colorama
import deepdish as dd
import os
import pickle
import timeit
from pyretis import __version__ as VERSION
from pyretis.info import PROGRAM_NAME
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.visualization.common import (get_min_max,
                                          get_startat,
                                          diff_matching)
from tqdm import tqdm

# Hard-coded labels for energies and time/cycle steps
ENERGYLABELS = ['time', 'cycE', 'potE', 'kinE', 'totE']


def remove_nan(data):
    """Remove nan from data.

    The function shall remove initial nan, assuming that they are originated
    by incomplete initial conditions (e.g. no energy file). In the case that
    nan appears as last cycle, it will not be fixed and an error shall rise
    up later in the code.

    Parameters
    ----------
    data : list
        Input list. If nan are present, they are replaced by the following
        entry. The method accounts for multiple consecutive nan occourence.

    """
    NAN = True
    iNAN = -1
    while NAN:
        NAN = False
        for i, d in reversed(list(enumerate(data))):
            if d*0 != 0:
                NAN = True
                iNAN = i
                break
        if NAN and iNAN == len(data)-1:
            NAN = False
        if NAN:
            data[iNAN] = data[iNAN+1]


class PathDensity():
    """Perfrom the path density analysis.

    This class defines the path density analysis for completed simulations
    with several order parameters.

    """

    def __init__(self, iofile=None):
        """Initialize the class."""
        self.iofile = iofile
        self.pfile = None
        try:
            testfile = open(self.iofile, 'r')
            os.chdir(os.path.join(os.getcwd(), os.path.dirname(self.iofile)))
            testfile.close()
        except FileNotFoundError:
            line = 'Found no input file, "iofile = {}"'
            print_to_screen(line.format(self.iofile), level='error')
            # TODO pass Error to __main__?
            return
        # Setting up empty dictionaries for the orderP and energy values
        self.eops = {}
        self.infos = {}
        self.ops = {}
        num_op = 0
        # Getting interfaces from iofile
        settings = parse_settings_file(self.iofile)
        interfaces = settings['simulation']['interfaces']
        intnames = []
        intnames.append('0$^{-}$')
        intnames.append('0$^{+}$')
        for i in range(1, len(interfaces)-1):
            intnames.append(str(i)+'$^{+}$')
        path = []
        # Getting ensembles/folders from directory
        for fol in sorted(filter(os.path.isdir, os.listdir('.'))):
            if str(fol)[0] == '0':  # Excluding folders not named '0**'
                path.append(fol)
        # Getting order parameters from order-file of first folder in path
        with open(os.path.join(path[0], 'order.txt')) as temp:
            # If implemented, use OP names as labels instead.
            tail = temp.read().split('\n')[-2]
            op_line = tail.split()
            num_op = len(op_line)-1
        op_labels = []
        for i in range(1, num_op+1):
            op_labels.append('op{}'.format(i))
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
            if not (only_ops):
                self.eops['atimo', fol], self.eops['rtimo', fol] = [], []
            # Creating empty lists in dictionaries for order params,
            # accepted and rejected
            for j in self.infos['op_labels']:
                self.ops['a'+j, fol], self.ops['r'+j, fol] = [], []
                if not (only_ops):
                    self.eops['a'+j, fol], self.eops['r'+j, fol] = [], []
            # Creating empty lists in dictionary for energies and time
            if not (only_ops):
                for j in ENERGYLABELS:
                    self.eops['a'+j, fol], self.eops['r'+j, fol] = [], []

        tic = [timeit.default_timer(), None]
        print_to_screen('###################################################',
                        level='message')
        print_to_screen('# PathDensity performing "walk" in \n# ' +
                        '{}/'.format(os.getcwd()),
                        level='message')
        print_to_screen('# Number of subfolders (0**) = ' +
                        '{}'.format(len(self.infos['path'])),
                        level='message')
        print_to_screen('# Found {} '.format(self.infos['num_op']) +
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
            print_to_screen('Reading data from {}'.format(
                                fol), level='message')
            file_starts = [get_startat(files[0])]
            self.get_OP(files[0], fol, file_starts[0])
            if not (only_ops):
                file_starts.append(get_startat(files[1]))
                self.get_EOP(fol, files, file_starts)
                self.check_Steps(fol)
            line = ('Done with folder, time used: '
                    '{0:4.4f}s, proceeding.\n'
                    ''.format(timeit.default_timer()-tic[1]))
            print_to_screen('='*len(line) + '\n' + line, level='success')

        maxcl = '000'

        if not (only_ops):
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
        print_to_screen('# {} to {}'.format(self.infos['long_cycle'][0],
                                            self.infos['long_cycle'][-1]),
                        level='success')
        print_to_screen('# Time spent: {:.2f}s'.format(
                            timeit.default_timer()-tic[0]), level='success')
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
        print_to_screen('# {}'.format(self.pfile), level='message')
        print_to_screen('###################################################'
                        + '\n', level='message')

    def deepdish_data(self):
        """Compresses the data to a .hdf5 file."""
        print_to_screen('###################################################',
                        level='message')
        print_to_screen('# Compress dictionaries to file', level='message')
        data = (self.ops, self.eops, self.infos)
        self.pfile = 'pyvisa_compressed_data.hdf5'
        dd.io.save(self.pfile, data)
        print_to_screen('# {}'.format(self.pfile), level='message')
        print_to_screen('###################################################'
                        + '\n', level='message')

    def get_EOP(self, fol, files, file_starts):
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
        ACC = None
        cycle = []
        flag = ''

        # Start with energy file
        with open(files[1], 'r+') as temp:
            for i, line in enumerate(temp):
                if i < file_starts[1]-1:
                    continue
                else:
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

        for key in self.eops:
            remove_nan(self.eops[key])

        WRITE = False
        flag = ''
        # Continue with orderp file
        with open(files[0], 'r') as temp:
            for i, line in enumerate(temp):
                if i < file_starts[0]-1:
                    continue
                else:
                    if '#' in line and line[0] != '#':
                        data = line[:line.index('#')].split()
                    else:
                        data = line.split()
                    if not data:
                        continue
                    elif data[0] == '#':
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
                        WRITE = bool(cycle_t in cycle)
                        continue

                    if WRITE:
                        self.eops[flag+'cycO', fol].append(cycle_t)
                        self.eops[flag+'timo', fol].append(int(data[0]))
                        for j in range(1, self.infos['num_op']+1):
                            try:
                                x = float(data[j])
                            except IndexError:
                                x = None
                            self.eops[flag+'op{}'.format(j), fol].append(x)

    def get_OP(self, ofile, fol, ostart):
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
        ACC = None
        cycle = []
        statw = []
        weight = []
        flag = ''

        with open(ofile, 'r') as o:
            for i, line in enumerate(o):
                if i < ostart-1:
                    continue
                else:
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
                            v = float(data[j])
                        except IndexError:
                            v = None
                        self.ops[flag+'op{}'.format(j), fol].append(v)

        # Creating list of statistical weights of paths
        for t in self.ops['acycO', fol]:
            s = cycle.index(t)
            self.ops['astatw', fol].append(statw[s])

    def check_Steps(self, fol):
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
            else:
                prc = str('{0:.2f}'.format(100.*lenop/lentot))

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
                            '({}) match'.format(acc.upper()), level='success')

        # Case: orderP (lists) are longer than the orderP, else match
        elif (lenp[0] < lenp[1] and
              self.eops[acc+'timo', fol][0:lenp[0]] ==
              self.eops[acc+'time', fol]):
            print_to_screen('Deleting last {} lines of orderP lists'.format(
                            lenp[1]-lenp[0]), level='message')
            _del_last_op(acc, fol)

        # Case: energy (lists) are longer than the energy, else match
        elif (lenp[1] < lenp[0] and
              self.eops[acc+'time', fol][0:lenp[1]] ==
              self.eops[acc+'timo', fol]):
            print_to_screen('Deleting last {} lines of energy lists'.format(
                            lenp[0]-lenp[1]), level='message')
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
                            '{0:.4f}s. Proceeding'.format(toc-tic),
                            level='success')


class PathVisualize():
    """Class to define the visualization of data with PathDensity.

    Class definition of the visualization of data gathered from simulation
    directory using the PathDensity class.

    """

    def __init__(self, pfile=None):
        """Initialize the PathVisualize class.

        If an input fil .pickle or .hdf5 is present, loads the pre-compiled
        data from it. Else, must use specific functions explicitly.
        """
        self.pfile = pfile
        if self.pfile is not None:
            if 'pickle' in self.pfile:
                self.load_pickle()
            elif 'hdf5' in self.pfile:
                self.load_dd()
            else:
                raise ValueError('Format not recognised')

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
        using deepdish.

        """
        data = dd.io.load(self.pfile)
        # Unpacking dictionaries
        self.ops = data[0]
        self.eops = data[1]
        self.infos = data[2]
        # Unpacking lists of info from infos dict
        self.op_labels = self.infos['op_labels']

    def get_Odata(self, fol, XYACC, weight=True, min_max=(0, 0)):
        """Load relevant data from dictionaries.

        Function that loads the relevant data from the dictionaries.
        (Depending on choice of order param, folder, and whether paths
        are acc/rej/both).

        Parameters
        ----------
        fol : string
            Name of folder, 000, 001, etc.
        XYACC : list
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

        if XYACC[2] == 'ACC' or XYACC[2] is True:
            acc = 'a'
        elif XYACC[2] == 'REJ' or XYACC[2] is False:
            acc = 'r'
        elif XYACC[2] == 'BOTH':
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
        if (weight):
            weights = self.ops['astatw', fol][mini['a']:maxi['a']]
        else:
            weights = [1]*len(self.ops['a'+XYACC[0], fol][mini['a']:maxi['a']])

        if acc != 'r':
            for a, b, c in zip(
                    self.ops['a'+XYACC[0], fol][mini['a']:maxi['a']],
                    self.ops['a'+XYACC[1], fol][mini['a']:maxi['a']],
                    weights):
                for _ in range(c):
                    x.append(a)
                    y.append(b)
            if acc == 'BOTH':
                x += self.ops['r'+XYACC[0], fol][mini['r']:maxi['r']]
                y += self.ops['r'+XYACC[1], fol][mini['r']:maxi['r']]

        elif acc == 'r':
            x += self.ops['r'+XYACC[0], fol][mini['r']:maxi['r']]
            y += self.ops['r'+XYACC[1], fol][mini['r']:maxi['r']]

        # Remove item in both lists if one or both is NoneType
        del_indx = []
        for i in range(len(x)):
            if x[i] is None or y[i] is None:
                del_indx.append(i)
        for i in reversed(del_indx):
            del x[i]
            del y[i]
        return x, y

    def get_Edata(self, fol, XYZ, ACC, min_max=None):
        """Load relevant data from the dictionaries.

        Function that loads the relevant data from the dictionaries,
        depending on choice of order param and energy, whether paths
        acc/rej/both, and folder.

        Parameters
        ----------
        XYZ : list
            Names of order parameter and energy labels, for x/y/z-axis.
        ACC : boolean OR string
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

        if ACC == 'ACC' or ACC is True:
            acc = 'a'
        elif ACC == 'REJ' or ACC is False:
            acc = 'r'

        # Default - start-to-end
        mini = {'a': 0, 'r': 0}
        maxi = {'a': len(self.eops['acycE', fol]) - 1,
                'r': len(self.eops['rcycE', fol]) - 1}

        # Deciding x,y,z index span using cycle number
        if min_max is not None:
            for l in ['a', 'r']:
                get_min_max(self.eops[l+'cycE', fol], min_max, mini, maxi, l)

        if ACC == 'BOTH':
            x = (self.eops['a'+XYZ[0], fol][mini['a']:maxi['a']] +
                 self.eops['r'+XYZ[0], fol][mini['r']:maxi['r']])
            y = (self.eops['a'+XYZ[1], fol][mini['a']:maxi['a']] +
                 self.eops['r'+XYZ[1], fol][mini['r']:maxi['r']])
            if XYZ[2] == 'None':
                z = [1]*len(x)
            else:
                z = (self.eops['a'+XYZ[2], fol][mini['a']:maxi['a']] +
                     self.eops['r'+XYZ[2], fol][mini['r']:maxi['r']])
        else:
            x = self.eops[acc+XYZ[0], fol][mini[acc]:maxi[acc]]
            y = self.eops[acc+XYZ[1], fol][mini[acc]:maxi[acc]]
            if len(XYZ) == 2 or XYZ[2] == 'None':
                z = [1]*len(x)
            else:
                z = self.eops[acc+XYZ[2], fol][mini[acc]:maxi[acc]]

        # Remove item in both lists if one or both is NoneType
        del_indx = []
        for i in range(len(x)):
            if x[i] is None or y[i] is None or z[i] is None:
                del_indx.append(i)
        for d in reversed(del_indx):
            del x[d]
            del y[d]
            del z[d]
        return x, y, z
