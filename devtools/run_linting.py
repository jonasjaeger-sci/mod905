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


SCORE_THRESHOLD = 9.2


def look_for_source_files(rootdir):
    """Find .py files by walking the given directory."""
    files = []
    for root, _, filenames in os.walk(rootdir):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            if filename.endswith('.py'):
                files.append(filepath)
    return sorted(files)


def lint_file(filename, reg_score, reg_warning, reg_error):
    """Run linting for a single file."""
    stdout, stderr = py_run(
        '{} --extension-pkg-whitelist=numpy'.format(filename),
        return_std=True
    )
    txt = stdout.read()
    warnings = [i for i in reg_warning.findall(txt)]
    errors = [i for i in reg_error.findall(txt)]
    result = reg_score.findall(txt)
    score, delta = process_result(result)
    stdout.close()
    stderr.close()
    return score, delta, warnings, errors


def run_linting(files):
    """Run pylint for a set of files, individually."""
    reg_score = re.compile(r'-?\d+\.\d+\/\d+')
    reg_warning = re.compile(r'.+warning \(W.+')
    reg_error = re.compile(r'.+error \(E.+')
    results = {
        'all': [],
        'below': [],
        'big-change': [],
        'change': [],
        'warnings': [],
        'errors': []
        }
    print(Fore.BLUE + 'Running pylint...')
    for i, filei in enumerate(files):
        printed = False
        if i % 10 == 0:
            print(Fore.BLUE + '{} files remaining...'.format(len(files) - i))
        score, delta, warnings, errors = lint_file(
            filei,
            reg_score,
            reg_warning,
            reg_error
        )
        if score is None:
            print(Fore.YELLOW + 'Skipping file: {}'.format(filei))
            printed = True
            continue

        if delta is not None:
            results['change'].append((filei, score, delta, abs(delta)))
            if delta < -0.5:
                results['big-change'].append((filei, score, delta))
                if not printed:
                    print(Fore.RED + '{} {} {}'.format(filei, score, delta))
                    printed = True

        if score < SCORE_THRESHOLD:
            results['below'].append((filei, score, delta))
            if not printed:
                print(Fore.RED + '{} {} {}'.format(filei, score, delta))
                printed = True

        if not printed:
            print(filei, score, delta)
            printed = True

        if warnings:
            results['warnings'].append((filei, score, delta))
            print_list(warnings, txt='warnings', color=Fore.YELLOW)
        if errors:
            results['errors'].append((filei, score, delta))
            print_list(errors, txt='errors', color=Fore.RED)

        results['all'].append((filei, score, delta))
    return results


def process_result(result):
    """Do a simple evaluation of the score."""
    try:
        score = float(result[0].split('/')[0])
    except IndexError:
        return None, None
    try:
        delta = score - float(result[1].split('/')[0])
    except IndexError:
        delta = None
    return score, delta


def print_list(list_to_print, txt='warnings', color=Fore.YELLOW):
    """Print out the contents in a list with some color and text."""
    if list_to_print:
        print(color + '    Found {}:'.format(txt))
        for i in list_to_print:
            print(color + '    {}'.format(i.strip()))


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


def print_all_warnings(results):
    """Print files with warnings if any."""
    if results['warnings']:
        fmt = '    {}'
        print()
        print(Fore.YELLOW +
              'The following files gave warnings:')
        for i in results['warnings']:
            print(fmt.format(i[0]))
        return 1
    return 0


def print_all_errors(results):
    """Print files with errors if any."""
    if results['errors']:
        fmt = '    {}'
        print()
        print(Fore.RED +
              'The following files have errors:')
        for i in results['errors']:
            print(fmt.format(i[0]))
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
    print_all_warnings(results)
    fail3 = print_all_errors(results)
    return fail1 + fail2 + fail3


def main(startdirs):
    """Run the analysis."""
    return_code = 0
    if not startdirs:
        print(Fore.RED + 'No directories given!')
        return_code += 1
    for startdir in startdirs:
        print(Fore.GREEN + '\nRunning in: "{}"'.format(startdir))
        files = look_for_source_files(startdir)
        if files:
            lint_result = run_linting(files)
            result = evaluate_results(lint_result)
            return_code += result
        else:
            print(Fore.RED + 'No files found in {}!'.format(startdir))
            return_code += 1
    sys.exit(return_code)


if __name__ == '__main__':
    colorama.init(autoreset=True)
    main(startdirs=sys.argv[1:])
