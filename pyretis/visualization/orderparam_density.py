# -*- coding: utf-8 -*-
# pylint: skip-file
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""orderparam_density - An application for compiling PyRETIS simulation data.

This module is part of the PyRETIS library and can be used both for compiling
the simulation data into a *.pickle dump, and load the data for later
visualization.

usage : orderparam_density.py [-h] -i INPUT [-s]

PyRETIS

optional arguments:
  -h, --help        show this help message and exit.
  -i INPUT, --input INPUT
                    Location of PyRETIS input/output file and simulation
                    directory with subfolders (ensembles).
"""
import argparse
import os
import timeit
import pickle
import colorama
from tqdm import tqdm
from pyretis.info import PROGRAM_NAME
from pyretis import __version__ as VERSION
from pyretis.inout import print_to_screen
from pyretis.inout.settings import parse_settings_file
from pyretis.visualization.common import (get_min_max,
                                          get_startat,
                                          diff_matching,
                                          hello_pathdensity_world)

# Hard-coded labels for energies and time/cycle steps
ENERGYLABELS = ['time', 'cycE', 'potE', 'kinE', 'totE']


class PathDensity():
    """Perfrom the path density analysis.

    This class defines the path density analysis for completed simulations with
    several order parameters.

    Attributes
    ----------
    walk_dirs : Function which searches through subfolders 00* for energy.txt
        and order.txt files and appends the values to dictionaries. Function is
        currently called by default during initialization of PathDensityVisual
        class.
    pickle_data : Function which dumps data of all three dictionaries
                  (ops, eops,infos)
                  to a *.pickle file for later visualization.
    get_startat : Function that return the latest restart point of a ensemble
                  file (order.txt or energy.txt).
    get_OP, get_EOP : Functions which scan order.txt and energy.txt,
                      respectively, within a given folder. Used by
                      function walk_Dirs.
    check_Steps : Function checking the lengths of all lists in dictionaries
    compare_and_cut : Function that finds indeces of lists to delete when
                      cycle number and time step values does not match.

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
            # #TODO implement new from dev, with OP names.
            tail = temp.read().split('\n')[-2]
            op_line = tail.split()
            num_op = len(op_line)-1
            """
            head = [next(temp) for x in range(3)]
            op = head[-1].rstrip('\n').split()
            self.num_op = len(op)-1
            """
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
        """Create a lists in acc/rej dictionary for all order parameters.

        First generate list of folders/ensembles to iterate through.
        Then search for number of orderparameters(columns) in file in one
        of the folders of path, and create lists in acc/rej dictionaries
        for all order parameters.

        Lastly iterate through all folders and files, filling in correct data
        to the lists and dictionaries.

        Parameters
        ----------
        only_ops : boolean, default=False
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
                  Name of subfolder (0**).

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
        uselist = 'O'  # Default OP lists

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
                    # Untestable
                    # if n_o > n_e:
                    #     uselist = 'O'
                    # else:
                    #     uselist = 'E'
        if uselist == 'O':
            full_cycle_list = sorted(
                self.ops['acycO', maxcl] + self.ops['rcycO', maxcl]
                )
            self.infos['long_cycle'] = [full_cycle_list[0],
                                        full_cycle_list[-1]]
        # Untestable
        # elif uselist == 'E':
        #     full_cycle_list = sorted(
        #         self.eops['acycO', maxcl] + self.eops['rcycO', maxcl]
        #         )
        #     self.infos['long_cycle'] = [full_cycle_list[0],
        #                                full_cycle_list[-1]]
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
        """Pickles the data to a *.pickle file."""
        print_to_screen('###################################################',
                        level='message')
        print_to_screen('# Pickling dictionaries to file', level='message')
        data = (self.ops, self.eops, self.infos)
        self.pfile = 'pathdens.pickle'
        with open(self.pfile, 'wb') as out:
            pickle.dump(data, out, protocol=pickle.HIGHEST_PROTOCOL)
        print_to_screen('# {}'.format(self.pfile), level='message')
        print_to_screen('###################################################'
                        + '\n', level='message')

    def write_lengths(self):
        """Write the lengths of the ops and eops dict to a txt file.

        Function that writes lengths of some of the data lists in
        dictionaries ops and eops to a *.txt file.

        Parameters
        ----------
        fast : Boolean, default=True
               Speed of data compile, if True is fast, else is slow.

        """
        outfile = 'pathdens.txt'
        print_to_screen('###################################################',
                        level='info')
        print_to_screen('# Writing data shape to file:', level='info')
        print_to_screen('# {}'.format(outfile), level='info')
        print_to_screen("# OP's: {}".format(self.infos['op_labels']),
                        level='info')
        print_to_screen('# E labels: {}'.format(ENERGYLABELS), level='info')
        print_to_screen('###################################################'
                        + '\n', level='info')

        with open(outfile, 'w') as out:
            out.write('###################################\n')
            out.write('# Output of path density from      \n')
            l1 = '# {}'.format(os.getcwd())
            out.write(l1+'\n')
            out.write('###################################\n\n')
            l1 = '        | {:>6}\t      \t      \t      \t| {:>6} ({})\n'
            out.write(l1.format('eops', 'ops', self.infos['num_op']))
            lp = ['cycE', 'time', 'cycO', 'timo', 'op1', 'op2']
            l1 = 'Fol acc | {:>6}\t{:>6}\t{:>6}\t{:>6}\t|'
            l1 = l1.format(lp[0], lp[1], lp[2], lp[3])
            l2 = '{:>6}\t{:>6}\t{:>6}\t{:>6}\n'
            l2 = l2.format(lp[2], lp[3], lp[4], lp[5])
            out.write(l1+l2)
            for fol in self.infos['path']:
                for acc in ['a', 'r']:
                    lp = [len(self.eops[acc+'cycE', fol]),
                          len(self.eops[acc+'time', fol]),
                          len(self.eops[acc+'cycO', fol]),
                          len(self.eops[acc+'timo', fol]),
                          len(self.ops[acc+'cycO', fol]),
                          len(self.ops[acc+'timo', fol]),
                          len(self.ops[acc+'op1', fol]),
                          len(self.ops[acc+'op2', fol])]
                    l1 = '{} {} \t| {:>6}\t{:>6}\t{:>6}\t{:>6}\t'\
                         '|'.format(fol, acc.upper(), lp[0], lp[1], lp[2],
                                    lp[3])
                    l2 = '{:>6}\t{:>6}\t{:>6}\t{:>6}\n'
                    l2 = l2.format(lp[4], lp[5], lp[6], lp[7])
                    out.write(l1+l2)

    def get_EOP(self, fol, files, file_starts):
        """Funcion that reads two files, and saves frames only if in both.

        Parameters
        ----------
        fol : string
              Name of folder - e.g. "000". Used in dictionaries for allocating
              values from read to correct list.
        files : list of strings
                Name of files in subfolder path.
        file_starts : list of integers
                      Index of files with latest restart of simulation

        Returns/Updates
        ---------------
        In:
        eops : [atime, rtime, apotE, rpotE,
             akinE, rkinE, atotE, rtotE]
             Lists of floats. Contains accepted/rejected steps and energy
             from files efile and ofile in folder fol.
        eops : [atimo, rtimo, aop{x}, rop{x}] - x in range(0,#orderP)
             Lists of floats. Contains accepted/rejected steps and order param
             from file ofile in folder fol. aop{x}/rop{x} loops through the
             total number of order parameters found in the order param file.

        """
        ACC = None
        cycle = []

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
                    if len(data) == 0:
                        continue
                    if data[0] == '#':
                        if data[1] == 'Time':
                            continue
                        try:
                            cycle_t = int(data[2].rstrip(','))
                        except ValueError:
                            ACC = 'cycle not here'
                            continue
                        if 'ACC' in data[4]:
                            cycle.append(cycle_t)
                            ACC = True
                        else:
                            ACC = False
                            cycle.append(cycle_t)
                        continue
                    if ACC is True:
                        self.eops['acycE', fol].append(cycle[-1])
                        self.eops['atime', fol].append(int(data[0]))
                        self.eops['apotE', fol].append(float(data[1]))
                        self.eops['akinE', fol].append(float(data[2]))
                        self.eops['atotE', fol].append(float(data[1]) +
                                                       float(data[2]))
                    elif ACC is False:
                        self.eops['rcycE', fol].append(cycle[-1])
                        self.eops['rtime', fol].append(int(data[0]))
                        self.eops['rpotE', fol].append(float(data[1]))
                        self.eops['rkinE', fol].append(float(data[2]))
                        self.eops['rtotE', fol].append(float(data[1]) +
                                                       float(data[2]))

        WRITE = False
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
                    if len(data) == 0:
                        continue
                    elif data[0] == '#':
                        if data[1] == 'Time':
                            continue
                        try:
                            cycle_t = int(data[2].rstrip(','))
                        except ValueError:
                            ACC = 'cycle not here'
                            continue
                        except IndexError:
                            ACC = 'Only 1 OP'
                            continue
                        if 'ACC' in data[4]:
                            ACC = True
                            WRITE = bool(cycle_t in cycle)
                        else:
                            ACC = False
                            WRITE = bool(cycle_t in cycle)

                        continue
                    if WRITE is True:
                        if ACC is True:
                            self.eops['acycO', fol].append(cycle_t)
                            self.eops['atimo', fol].append(int(data[0]))
                            for j in range(1, self.infos['num_op']+1):
                                try:
                                    x = float(data[j])
                                except IndexError:
                                    x = None
                                self.eops['aop{}'.format(j), fol].append(x)
                        elif ACC is False:
                            self.eops['rtimo', fol].append(int(data[0]))
                            self.eops['rcycO', fol].append(cycle_t)
                            for j in range(1, self.infos['num_op']+1):
                                try:
                                    x = float(data[j])
                                except IndexError:
                                    x = None
                                self.eops['rop{}'.format(j), fol].append(x)

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
                 Index of ofile with latest restart of simulation

        Returns/Updates
        ---------------
        In:
        ops : a/r[timo, aop{x}, cycl] - x in range(0,#orderP)
            Lists of floats. Contains accepted/rejected steps and order param
            from file ofile in folder fol. aop{x}/rop{x} loops through the
            total number of order parameters found in the order param file.

        """
        ACC = None
        cycle = []
        statw = []
        weight = []

        with open(ofile, 'r') as o:
            for i, line in enumerate(o):
                if i < ostart-1:
                    continue
                else:
                    if '#' in line and line[0] != '#':
                        data = line[:line.index('#')].split()
                    else:
                        data = line.split()
                    if len(data) == 0:
                        continue
                    if data[0] == '#':
                        if data[1] == 'Time':
                            continue
                        try:
                            cycle_t = int(data[2].rstrip(','))
                        except ValueError:
                            ACC = 'cycle not here'
                            continue
                        except IndexError:
                            ACC = 'Only 1 OP'
                            continue
                        if 'ACC' in data[4]:
                            ACC = True
                            cycle.append(cycle_t)
                            statw.append(1)
                            weight.append(1)
                        else:
                            ACC = False
                            cycle.append(cycle_t)
                            if len(weight) != 0:
                                weight[-1] += 1
                            statw.append(0)
                        continue
                    if ACC is True:
                        self.ops['atimo', fol].append(int(data[0]))
                        self.ops['acycO', fol].append(cycle[-1])
                        for j in range(1, self.infos['num_op']+1):
                            try:
                                v = float(data[j])
                            except IndexError:
                                v = None
                            self.ops['aop{}'.format(j), fol].append(v)
                    elif ACC is False:
                        self.ops['rtimo', fol].append(int(data[0]))
                        self.ops['rcycO', fol].append(cycle[-1])
                        for j in range(1, self.infos['num_op'] + 1):
                            try:
                                v = float(data[j])
                            except IndexError:
                                v = None
                            self.ops['rop{}'.format(j), fol].append(v)

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
            acc : Boolean
                  True/False for accepted/rejected paths.
            fol : string
                  Name of folder.

            Returns
            -------
            errors : Boolean
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

            errors, l, where_err = _check_timesteps(acc, fol)
            print_to_screen((txt.format(acc.upper(), lenep, lenop, lentot, prc)
                             ), level=l)

            if errors is True:
                txt = 'Found error in {}; '
                txt += 'Comparing data in folder {}, paths: {}'
                print_to_screen(txt.format(where_err, fol, acc.upper()),
                                level=l)
                self.compare_and_cut(fol,
                                     acc,
                                     [lenep, lenop],
                                     target=where_err
                                     )

            errors, l, where_err = _check_timesteps(acc, fol)
            if errors is True:
                nlenep = len(self.eops[acc+'time', fol])
                nlenop = len(self.eops[acc+'timo', fol])
                txt = 'Found error in {}; '
                txt += 'Re-checking data: E: {}, OP: {}'
                print_to_screen(txt.format(where_err, nlenep, nlenop), level=l)
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
        def _del_curr_op(acc, fol, i):
            """Delete the current line in list.

            Parameters
            ----------
            fol : string
                  Name of folder where difference occured.
            acc : string
                  'r'/'a' for accepted/rejected paths.
            i : integer OR tuple
                index of lines to delete, or tuple of "from-to" indeces.

            """
            for key in self.infos['op_labels']:
                del self.eops[acc+key, fol][i]
            # 'timo' not in op_labels, include:
            del self.eops[acc+'timo', fol][i]

        def _del_curr_en(acc, fol, i):
            """Delete the current line in list.

            Parameters
            ----------
            fol : string
                  Name of folder where difference occured.
            acc : string
                  'r'/'a' for accepted/rejected paths.
            i : integer OR tuple
                index of lines to delete, or tuple of "from-to" indices.

            """
            for key in ENERGYLABELS:
                del self.eops[acc+key, fol][i]

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

    Attributes
    ----------
    load_pickle : Function that loads pre-compiled simulation results from
                  a *.pickle file.
    plot_Combs : Plots the 1D and 2D density of order parameter combinations
    get_Edata : Load data (3) from eops dictionary using current settings.
    get_SingleOdata : Load data (1) from eops dictonary using curent settings
    get_Odata : Load data (2) from ops dictionary using current settings.
    plot_SingleDensity : Function that generates plot of the distribution
                         (histogram) of just one order parameter.
    plot_Density : Function that generates plot of the density of two
                   order parameters.
    plot_Surface : Function that generates different plots for combinations
                   of three order parameters/energies/other.

    """

    def __init__(self, pfile=None):
        """Initialize the PathVisualize class.

        If an input file (*.pickle) is present, loads the pre-compiled data
        from it. Else, must use func load_pickle explicitly.
        """
        self.pfile = pfile
        if self.pfile is not None:
            self.load_pickle()

    def load_pickle(self):
        """Load pre-compiled data from *.pickle file.

        Function that loads pre-compiled data from *.pickle file. Depending
        on file name, will define data as being created using fast or slow
        post-processing. Defaults to 'fast'.
        """
        with open(self.pfile, 'rb') as pdata:
            data = pickle.load(pdata)
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
              Name of folder, 000,001,etc.
        XYACC : list
                 [0:1] : strings, names of x/y order parameter.
                 [2] : bool, True/False for acc/rej paths.
        weight : boolean, default=True
                 If True, trajectories are
                 statistically weighted when read from dict.
        min_max : list
                  Minimum and maximum cycle number of simulation data.

        Returns
        -------
        x : list
            Floats with values of op2, from dict ops[op2,fol].
        y : list
            Floats with values of op1, from dict ops[op1,fol].

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
            Floats with values of op2, from dict eops[op2,fol].
        y : list
            Floats with values of op1, from dict eops[op1,fol].
        z : list
            Floats with values of E from eops[E,fol].

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


def main():
    """Run the Compressor application."""
    # Initializing colorama
    colorama.init(autoreset=True)
    # Creating argument parser
    parser = argparse.ArgumentParser(description='Path Density Analysis')
    parser.add_argument(
        '-i',
        '--input',
        help=('Location of {} input/output file'.format(PROGRAM_NAME)),
        required=True
        )
    parser.add_argument(
        '-O',
        '--only_orderp',
        action='store_true',
        help=('Use only data from order.txt files')
        )
    parser.add_argument('-V', '--version', action='version',
                        version='{} {}'.format(PROGRAM_NAME, VERSION))
    args_dict = vars(parser.parse_args())

    # TODO set up for logging..?

    inputfile = args_dict['input']
    only_ops = args_dict['only_orderp']

    hello_pathdensity_world()
    p_data = PathDensity(iofile=inputfile)
    p_data.walk_dirs(only_ops=only_ops)
    p_data.pickle_data()


if __name__ == '__main__':
    main()  # pragma: no cover
