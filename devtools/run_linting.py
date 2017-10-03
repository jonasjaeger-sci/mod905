"""Run linting for a set of source files.

Here, we will also give some over-all evaluation of the results.
The exit code of this script will be != 0 if one or more files
have a score below a pre-set value or if the changes are "too big".
"""
import os
from operator import itemgetter
import re
import sys
import colorama
from colorama import Fore
from pylint.epylint import py_run


def look_for_source_files(rootdir):
    """Find .py files by walking the given directory."""
    files = []
    for root, _, filenames in os.walk(rootdir):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            if filename.endswith('.py'):
                files.append(filepath)
    return sorted(files)


def run_linting(files):
    """Run pylint for a set of files, individually."""
    reg = re.compile(r'-?\d+\.\d+\/\d+')
    results = {'all': [], 'below': [], 'big-change': [], 'change': []}
    print(Fore.BLUE + 'Running pylint...')
    for i, filei in enumerate(files):
        stdout, stderr = py_run(
            '{} --extension-pkg-whitelist=numpy'.format(filei),
            return_std=True
        )
        if i % 10 == 0:
            print(Fore.BLUE +
                  '{} files remaining...'.format(len(files) - i))
        result = reg.findall(stdout.read())
        score, delta = process_result(result)
        if score is None:
            print(Fore.YELLOW + 'Skipping: {}'.format(filei))
            continue
        printed = False
        if delta is not None:
            results['change'].append((filei, score, delta, abs(delta)))
            if delta < -0.5:
                results['big-change'].append((filei, score, delta))
                if not printed:
                    print(Fore.RED + '{} {} {}'.format(filei, score, delta))
                    printed = True
        if score < 9.2:
            results['below'].append((filei, score, delta))
            if not printed:
                print(Fore.RED + '{} {} {}'.format(filei, score, delta))
                printed = True
        if not printed:
            print(filei, score, delta)
            printed = True
        results['all'].append((filei, score, delta))
        stdout.close()
        stderr.close()
    return results


def process_result(result):
    """Do a simple evaluation of the scrore."""
    try:
        score = float(result[0].split('/')[0])
    except IndexError:
        return None, None
    try:
        delta = score - float(result[1].split('/')[0])
    except IndexError:
        delta = None
    return score, delta


def print_below(results):
    """Print the below results if any."""
    if results['below']:
        fmt = '    {}: {} (delta: {})'
        print()
        print(Fore.RED + 'The following files *MUST BE FIXED*:')
        for i in results['below']:
            print(fmt.format(*i))
        return 1
    return 0


def print_big_change(results):
    """Print big results if any."""
    if results['big-change']:
        fmt = '    {}: {} (delta: {})'
        print()
        print(Fore.RED +
              'The following files had a *TOO LARGE* negative change:')
        for i in results['big-change']:
            print(fmt.format(*i))
        return 1
    return 0


def evaluate_results(results):
    """Do a simple evaluation of the results."""
    fmt = '    {}: {} (delta: {})'
    # First print out 10 (if possible) files with lowest scores:
    maxlen = min(10, len(results['all']))
    txt = []
    for i in sorted(results['all'], key=itemgetter(1))[:maxlen]:
        if i[1] < 10.0:
            txt.append(fmt.format(*i))
    print()
    if txt:
        print(Fore.BLUE + 'The lowest scores:')
        for i in txt:
            print(i)
    else:
        print(Fore.GREEN + 'No scores below 10! Good job :-)')

    # Print out the 10 biggest changes:
    maxlen = min(10, len(results['change']))
    if maxlen > 0:
        txt = []
        for i in sorted(results['change'], key=itemgetter(3),
                        reverse=True)[:maxlen]:
            if abs(i[3]) > 0.0:
                txt.append(fmt.format(*i))
        print()
        if txt:
            print(Fore.BLUE + 'The biggest changes:')
            for i in txt:
                print(i)
        else:
            print()
            print(Fore.BLUE + 'No changes found.')

    fail1 = print_below(results)
    fail2 = print_big_change(results)
    return fail1 + fail2


def main(startdir='pyretis'):
    """Run the analysis."""
    print(Fore.GREEN + 'Running in: "{}"'.format(startdir))
    files = look_for_source_files(startdir)
    lint_result = run_linting(files)
    result = evaluate_results(lint_result)
    sys.exit(result)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main(startdir=sys.argv[1])
