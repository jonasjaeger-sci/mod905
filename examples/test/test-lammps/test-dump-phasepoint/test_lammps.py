# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""A test using the LAMMPS engine."""
from operator import itemgetter
import os
import colorama
import numpy as np
from pyretis.inout.common import make_dirs
from pyretis.engines.lammps import LAMMPSEngine
from pyretis.inout import print_to_screen
from pyretis.testing.helpers import clean_dir
from pyretis.testing.systemhelp import create_system_ext


HERE = os.path.abspath(os.path.dirname(__file__))
TRAJ = os.path.join(HERE, 'lammps_input', 'traj.lammpstrj')


def _convert_snapshot(snapshot):
    """Convert a LAMMPS text snapshot to numbers."""
    snapshot_new = {
        'timestep': int(snapshot['timestep'][0]),
        'number': int(snapshot['number'][0]),
    }
    box = []
    for line in snapshot['box']:
        box.append([float(i) for i in line.split()])
    snapshot_new['box'] = np.array(box)
    # Convert and sort atoms:
    atoms = []
    for line in snapshot['atoms']:
        atoms.append([float(i) for i in line.split()])
    snapshot_new['atoms'] = np.array(sorted(atoms, key=itemgetter(0)))
    return snapshot_new


def read_lammpstrj(filename):
    """Read frames in a LAMMPS trajectory."""
    snap = {}
    key = None
    data = []
    with open(filename) as infile:
        for lines in infile:
            strip_line = lines.strip()
            if strip_line.startswith('ITEM'):
                # This is the start of a new data block in a snapshot.
                # Add this data block to the current snapshot
                if key is not None:
                    snap[key] = data
                key = strip_line.split()[1].lower()
                data = []
                if key == 'timestep':
                    # This is the start of a new frame. Return the current
                    # snapshot, if any, and empty the data blocks:
                    if snap:
                        yield _convert_snapshot(snap)
                    snap = {}
                continue
            else:
                data.append(strip_line)
    if snap:
        if key is not None:
            snap[key] = data
        yield _convert_snapshot(snap)


def dump_phasepoint():
    """Use the LAMMPS engine to run a MD simulation forward in time."""
    print_to_screen('\nTesting that we can dump phase points.\n')
    engine = LAMMPSEngine('lmp_serial', 'lammps_input', 2,
                          extra_files=['dw-wca.in'])
    # Create a dummy system:
    system = create_system_ext(pos=(TRAJ, 0))
    exe_dir = os.path.join(HERE, 'dump')
    # Set up some directories:
    make_dirs(exe_dir)
    clean_dir(exe_dir)
    engine.exe_dir = exe_dir
    dumped_files = []
    for i in (0, 2, 4, 6, 8, 10):
        newpos = (TRAJ, i)
        print_to_screen('\t-> Dumping: {}'.format(newpos))
        system.particles.set_pos(newpos)
        engine.dump_phasepoint(system, 'dump-{:02d}'.format(i))
        pos = system.particles.get_pos()
        assert pos[1] == 0
        dumped_files.append(pos[0])
    print_to_screen('\nRunning some comparisons:\n')
    for i, frame in enumerate(read_lammpstrj(TRAJ)):
        traj = dumped_files[i]
        print_to_screen('\t-> Comparing for dumped frame: {}'.format(traj))
        frame_dump = [i for i in read_lammpstrj(traj)]
        assert len(frame_dump) == 1
        assert frame['number'] == frame_dump[0]['number']
        for key in ('box', 'atoms'):
            assert np.allclose(frame[key], frame_dump[0][key])
        assert frame_dump[0]['timestep'] == 0
        assert frame['timestep'] == engine.subcycles * i
        print_to_screen('\t\t->Frame was ok!', level='success')
    print_to_screen('\nConclusion: We can dump phase points.',
                    level='success')


def main():
    """Run the comparisons."""
    dump_phasepoint()


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main()
