# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test using the LAMMPS engine."""
import os
import sys
import colorama
import numpy as np
from matplotlib import pyplot as plt
from pyretis.core.path import Path
from pyretis.inout.common import make_dirs
from pyretis.engines.lammps import LAMMPSEngine
from pyretis.inout import print_to_screen
from pyretis.core.random_gen import create_random_generator
from pyretis.testing.helpers import clean_dir
from pyretis.testing.systemhelp import create_system_ext
from plotting import plot_compare, plot_xy


HERE = os.path.abspath(os.path.dirname(__file__))
STEPS = 100
SUBCYCLES = 2


def run_forward():
    """Use the LAMMPS engine to propagate a MD simulation forward in time."""
    print_to_screen(
        '\nTesting the LAMMPS engine by propagating forward & backward.',
    )
    engine = LAMMPSEngine('lmp_serial', 'lammps_input', SUBCYCLES)
    # Create a dummy system:
    system = create_system_ext(pos=('system.data', 0))
    exe_dir = os.path.join(HERE, 'run-forward-backward')
    make_dirs(exe_dir)
    clean_dir(exe_dir)
    engine.exe_dir = exe_dir
    pathf = Path(rgen=None, maxlen=STEPS)
    print_to_screen('-> Propagating forward....', level='info')
    engine.propagate(path=pathf, initial_state=system, order_function=None,
                     interfaces=[-1, 0.0, 2.0], reverse=False)
    # Propagate from the last point, but backward:
    print_to_screen(
        '-> Setting system to last point in the forward path.',
        level='info'
    )
    last = pathf.phasepoints[-1]
    pathb = Path(rgen=None, maxlen=pathf.length)
    print_to_screen('-> Propagating backward....', level='info')
    engine.propagate(path=pathb, initial_state=last, order_function=None,
                     interfaces=[-1, 0.0, 3.0], reverse=True)
    print_to_screen('-> Comparing forward & backward:', level='info')
    order_f = np.array([i.order for i in pathf.phasepoints])
    order_b = np.array([i.order for i in reversed(pathb.phasepoints)])
    data_sets = [
        [
            (range(len(order_f)), order_f[:, 0], 'Forward.'),
            (range(len(order_b)), order_b[:, 0], 'Backward.'),
        ],
        [
            (range(len(order_f)), order_f[:, 1], 'Forward.'),
            (range(len(order_b)), -1*order_b[:, 1], 'Backward.'),
        ]
    ]
    plot_compare(data_sets, ['OP1', 'OP2'])
    data_sets_xy = [
        (order_f[:, 0], order_b[:, 0], 'OP1, forward', 'OP1, backward'),
        (order_f[:, 1], -1*order_b[:, 1], 'OP2, forward', 'OP2, backward'),
    ]
    plot_xy(data_sets_xy)


def run_backward():
    """Use the LAMMPS engine to propagate a MD simulation backward in time."""
    print_to_screen(
        '\nTesting the LAMMPS engine by propagating backward & forward.',
    )
    engine = LAMMPSEngine('lmp_serial', 'lammps_input', SUBCYCLES)
    # Create a dummy system:
    system = create_system_ext(pos=('system.data', 0))
    exe_dir = os.path.join(HERE, 'run-backward-forward')
    make_dirs(exe_dir)
    clean_dir(exe_dir)
    engine.exe_dir = exe_dir
    rgen = create_random_generator({'seed': 2})
    engine.modify_velocities(system, rgen)
    pathb = Path(rgen=None, maxlen=STEPS)
    print_to_screen('-> Propagating backward....', level='info')
    engine.propagate(path=pathb, initial_state=system, order_function=None,
                     interfaces=[1.2, 5.0, 12.0], reverse=True)
    # Propagate from the last point, but forward:
    print_to_screen(
        '-> Setting system to last point in the backward path.',
        level='info'
    )
    last = pathb.phasepoints[-1]
    pathf = Path(rgen=None, maxlen=pathb.length)
    print_to_screen('-> Propagating forward....', level='info')
    engine.propagate(path=pathf, initial_state=last, order_function=None,
                     interfaces=[1.0, 5.0, 12.0], reverse=False)
    print_to_screen('-> Comparing backward & forward:', level='info')
    order_f = np.array([i.order for i in reversed(pathf.phasepoints)])
    order_b = np.array([i.order for i in pathb.phasepoints])
    data_sets = [
        [
            (range(len(order_f)), order_f[:, 0], 'Forward.'),
            (range(len(order_b)), order_b[:, 0], 'Backward.'),
        ],
        [
            (range(len(order_f)), -1*order_f[:, 1], 'Forward.'),
            (range(len(order_b)), order_b[:, 1], 'Backward.'),
        ]
    ]
    plot_compare(data_sets, ['OP1', 'OP2'])
    data_sets_xy = [
        (order_f[:, 0], order_b[:, 0], 'OP1, forward', 'OP1, backward'),
        (-1*order_f[:, 1], order_b[:, 1], 'OP2, forward', 'OP2, backward'),
    ]
    plot_xy(data_sets_xy)


def main(plot=False):
    """Run the comparisons."""
    run_forward()
    run_backward()
    if plot:
        plt.show()


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main(plot=len(sys.argv) >= 2)
