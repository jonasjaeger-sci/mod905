# -*- coding: utf-8 -*-
# Copyright (c) 2015, PyRETIS Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""Plot results from time tests of the Lennard-Jones potential.

Here we assume that the results are available in files named
``timeings.txt``.
"""
import numpy as np
import matplotlib as mpl
from matplotlib import pylab as plt


mpl.rcParams['axes.color_cycle'] = ['4C72B0', '55A868', 'C44E52', '8172B2',
                                    'CCB974', '64B5CD']
mpl.rcParams['axes.labelsize'] = 'medium'
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = 'Times'
mpl.rcParams['font.size'] = 16
mpl.rcParams['legend.numpoints'] = 1
mpl.rcParams['legend.scatterpoints'] = 1
mpl.rcParams['legend.handlelength'] = 1.0
mpl.rcParams['legend.handleheight'] = 0.3
mpl.rcParams['text.usetex'] = True
mpl.rcParams['xtick.major.pad'] = 6
mpl.rcParams['xtick.labelsize'] = 'medium'
mpl.rcParams['ytick.major.pad'] = 6
mpl.rcParams['ytick.labelsize'] = 'medium'

results = {'c': 'c/timings.txt',
           'c (python3)': 'c-python3/timings.txt',
           'fortran': 'fortran/timings.txt',
           'fortran (pointer)': 'fortran-pointer/timings.txt',
           'numpy': 'timings-numpy.txt',
           'pure python': 'timings-python.txt'}

markers = ['o', 'v', '^', 's', '*', 'p', 'h', 'x', '+']

data = {}
for key in results:
    data[key] = np.loadtxt(results[key])

fig = plt.figure()
ax1 = fig.add_subplot(111)
for i, key in enumerate(data):
    result = data[key]
    npart, avg, std = result[:, 0], result[:, 2], result[:, 3]
    ax1.errorbar(npart, avg, yerr=std, label=key, lw=3, markersize=9,
                 marker=markers[i], alpha=0.9)
ax1.legend(ncol=2, loc='center right')
ax1.set_xlabel('System size')
ax1.set_ylabel('Time')
fig.tight_layout()

fig2 = plt.figure()
ax2 = fig2.add_subplot(111)
norm_avg = data['c'][:, 2]

for i, key in enumerate(data):
    result = data[key]
    npart, avg = result[:, 0], result[:, 2]
    nmin = min(len(norm_avg), len(avg))
    avg_n = avg[:nmin] / norm_avg[:nmin]
    ax2.plot(npart, avg_n, lw=3, label=key, markersize=9, alpha=0.9,
             marker=markers[i])
ax2.legend(ncol=2, loc='best',  bbox_to_anchor=(0.3,0.7))
ax2.set_yscale('log')
ax2.set_xlabel('System size')
ax2.set_ylabel('Time relative to python+c')
fig2.tight_layout()
plt.show()
