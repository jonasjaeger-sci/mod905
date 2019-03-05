"""Update copyright info for PyRETIS."""
import os
import re
import subprocess
import sys
import tempfile

NEW_YEAR = '2019'
COPYRIGHT = re.compile('copyright', re.IGNORECASE)
# Assume that we won't do PyRETIS after 2099 ;-)
YEAR = re.compile('20[0-9][0-9]')
FILES_TO_IGNORE = {'pyc', '.coverage', '.swp'}
# Set up environment for subprocess:
ENV = {}
for key in {'SYSTEMROOT', 'PATH'}:
    val = os.environ.get(key)
    if val is not None:
        ENV[key] = val
ENV['LANGUAGE'] = 'C'
ENV['LANG'] = 'C'
ENV['LC_ALL'] = 'C'


def is_file_in_repo(filename):
    """Test if file is part of the git repo."""
    is_in_repo = False
    try:
        out = subprocess.Popen(
            ['git', 'ls-files', '--error-unmatch', filename],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=ENV,
            shell=False,
        )
        out.communicate()
        is_in_repo = out.returncode == 0
    except OSError:
        is_in_repo = False
    return is_in_repo


def look_for_files(rootdir):
    """Locate files recursively in the given root directory."""
    for root, _, filenames in os.walk(rootdir):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            ignore = False
            for i in FILES_TO_IGNORE:
                if filepath.endswith(i):
                    ignore = True
                    break
            if not ignore:
                is_in_repo = is_file_in_repo(filepath)
                if is_in_repo:
                    yield filepath


def replace_copyright(filename):
    """Replace copyright information in the given input file."""
    replace = False
    print('Processing file: {}'.format(filename))
    with tempfile.NamedTemporaryFile() as tmp:
        with open(tmp.name, 'w') as outputfile:
            with open(filename, 'r') as inputfile:
                try:
                    for lines in inputfile:
                        copy = [i for i in COPYRIGHT.findall(lines)]
                        year = [i for i in YEAR.findall(lines)]
                        if copy and year:
                            print('\t- Found copyright & year')
                            replace = True
                            # Replace the years found with the new year:
                            for i in year:
                                lines = lines.replace(i, NEW_YEAR)
                        outputfile.write(lines)
                except UnicodeDecodeError:
                    print('\t- Skipping file due to decoding error...')
        tmp.flush()
        if replace:
            with open(tmp.name, 'r') as inputfile:
                with open(filename, 'w') as outputfile:
                    outputfile.write(inputfile.read())
    return replace


def main(rootdir):
    """Search and replace copyright information in all files found."""
    replaced = []
    for filename in look_for_files(rootdir):
        if replace_copyright(filename):
            replaced.append(filename)
    if replaced:
        print('The following files were updated:')
        for i in replaced:
            print('\t{}'.format(i))
    else:
        print('No files were updated.')


if __name__ == '__main__':
    main(sys.argv[1])
