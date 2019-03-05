# -*- coding: utf-8 -*-
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""Check that source modules are included in the API docs.

Typical usage is: python check_api_docs.py ../../docs/api/ ../../pyretis

"""
import os
import sys


def read_api_rst(filename):
    """Yield modules documented in the given file."""
    with open(filename, 'r') as infile:
        for lines in infile:
            if lines.find('automodule') != -1:
                yield lines.strip().split()[-1]


def read_api_rst_files(dirname):
    """Read all .rst files in the given directory."""
    rst_files = [
        i for i in os.scandir(dirname) if i.is_file and i.name.endswith('rst')
    ]
    modules = set([])
    for i in rst_files:
        file_path = os.path.join(dirname, i.name)
        for mod in read_api_rst(file_path):
            modules.add(mod)
    return modules


def find_source_modules(source_dir):
    """Return source modules in the given directory."""
    source_files = set([])
    source_abs = os.path.abspath(source_dir)
    for root, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                filename_e = filename.split(os.extsep)[0]
                if filename_e == '__init__':
                    continue
                filepath_abs = os.path.abspath(os.path.join(root, filename_e))
                split = filepath_abs.split(source_abs)[-1]
                mod = 'pyretis{}'.format('.'.join(split.split(os.sep)))
                source_files.add(mod)
    return source_files


def main(docdir, source_dir):
    """Run the check."""
    modules = read_api_rst_files(docdir)
    source = find_source_modules(source_dir)
    missing = [i for i in source if i not in modules]
    if missing:
        print('Missing the following modules in the API documentation:')
        print()
        for i in sorted(missing):
            print(i)
        print()
        return 1
    print('No modules missing.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
