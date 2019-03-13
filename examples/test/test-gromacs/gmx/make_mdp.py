# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""
Update the number of steps for a GROMACS input mdp file.
"""
import sys
from pyretis.inout.settings import parse_settings_file


def main(settings_file, mdp_file, output_file):
    """Update number of steps in the gromacs input file."""
    settings = parse_settings_file(settings_file)
    steps = settings['simulation']['steps']
    subcycles = settings['engine']['subcycles']
    gmx_steps = steps * subcycles
    with open(mdp_file, 'r') as infile:
        with open(output_file, 'w') as output:
            for lines in infile:
                if lines.strip().startswith('nsteps'):
                    output.write('nsteps = {}\n'.format(gmx_steps))
                else:
                    output.write(lines)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
