#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
This is umbrella_sampling_mc.py with an additional movie
"""

from umbrella_sampling_mc import *
# import and execute the simulation

# we can also create a animations:
from matplotlib import animation
fig = plt.figure()
ax = plt.axes(xlim=(-1.05, 1.05), ylim=(-0.3, 0.05))

line, = ax.plot(xv, V, lw=3, color='blue') # the potential

linec = ax.axvline(x=None, lw=2, ls=':', color='black') # crossing line
axv = ax.axvspan(xmin=None, xmax=None, color="blue", alpha=0.1) # umbrella reg.
scat = ax.scatter(None, None, s=150, c='green') # the particle

umpos1 = umbrellas[0][0]
umpos2 = umbrellas[0][1]

traj_data = []
ener_data = []
umbr = [] # id of current umbrella
crossing = [] # position that must be crossed
for i, (traj, ener) in enumerate(zip(trajectory, energy)):
    r, e = traj[::50], ener[::50]
    traj_data.extend(r)
    ener_data.extend(e)
    umbr.extend([i]*len(r))
    crossing.extend([umbrellas[min(i+1, n_umb-1)][0]]*len(r))

def init():
    # function to draw a clear frame
    line.set_ydata(V)
    return line, #, axv

def update(i):
    #global umpos1, umpos2
    p = np.array([traj_data[i], ener_data[i]])
    scat.set_offsets(p)
    linec.set_xdata(crossing[i])
    umpos1 = umbrellas[umbr[i]][0]
    umpos2 = umbrellas[umbr[i]][1]
    a = np.array([[umpos1, 0.0], [umpos1, 1.0],
                 [umpos2, 1.0], [umpos2, 0.0],
                 [umpos1, 0.0]])

    b = np.array([[umpos2, 0.0], [umpos2, 1.0],
                 [1.1, 1.0], [1.1, 0.0],
                 [umpos2, 0.0]])
    #axvr.set_xy(b)
    #axvl.set_xy(a)
    axv.set_xy(a)
    return scat, axv, linec

anim = animation.FuncAnimation(fig, update, np.arange(len(traj_data)), 
        init_func=init,interval=25, blit=True)

plt.show()



