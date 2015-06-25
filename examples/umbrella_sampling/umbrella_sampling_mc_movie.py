# -*- coding: utf-8 -*-
"""
This is an simple example of how we can create a simple animation.
It will run the umbrella sampling defined in umbrella_samplin_mc.py and
draw the frames as a very simple animation.
"""
from __future__ import print_function
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation
# import and execute the simulation
from umbrella_sampling_mc import (trajectory, energy, umbrellas, n_umb, VPOT,
                                  XPOT)

# Create very simple animation:
fig = plt.figure()
axs = plt.axes(xlim=(-1.05, 1.05), ylim=(-0.3, 0.05))
# replot the potential:
line, = axs.plot(XPOT, VPOT, lw=3, color='blue')
# plot the line we have to cross:
linec = axs.axvline(x=-10, lw=2, ls=':', color='black')
# plot the umbrella region
axv = axs.axvspan(xmin=-10, xmax=-10, color="blue", alpha=0.1)
# plot the particle:
scat = axs.scatter(-10, -10, s=150, c='green')

traj_data = []
ener_data = []
umbr = []  # id of current umbrella
crossing = []  # position that must be crossed
for i, (traj, ener) in enumerate(zip(trajectory, energy)):
    pos, ene = traj[::50], ener[::50]
    traj_data.extend(pos)
    ener_data.extend(ene)
    umbr.extend([i] * len(pos))
    crossing.extend([umbrellas[min(i + 1, n_umb - 1)][0]] * len(pos))


def init():
    """
    Function to clear the frame
    """
    line.set_ydata(VPOT)
    return line,


def update(frame):
    """
    Function to update animation
    """
    pos_ener = np.array([traj_data[frame], ener_data[frame]])
    scat.set_offsets(pos_ener)
    linec.set_xdata(crossing[frame])
    umpos1 = umbrellas[umbr[frame]][0]
    umpos2 = umbrellas[umbr[frame]][1]
    region = np.array([[umpos1, 0.0], [umpos1, 1.0],
                       [umpos2, 1.0], [umpos2, 0.0],
                       [umpos1, 0.0]])
    axv.set_xy(region)
    return scat, axv, linec

anim = animation.FuncAnimation(fig, update, np.arange(len(traj_data)),
                               init_func=init, interval=25, blit=True,
                               repeat=False)
# for making a movie:
#anim.save('simple.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
plt.show()
