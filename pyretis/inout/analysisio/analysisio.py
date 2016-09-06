# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the GPLV3 License. See LICENSE for more info.
"""Methods that will output results from the analysis functions.

The Methods defined here will also run the analysis and output
according to given settings.

Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

analyse_file
    Method to analyse a file. For example, it can be used as

    >>> from pyretis.inout.analysisio import analyse_file
    >>> analyse_func = analyse_file('cross', 'cross.dat')
    >>> out, fig, txt = analyse_func(settings)

    It wraps around the different analysis methods which can be called
    by

    >>> from pyretis.inout.analysisio import analyse_and_output_cross
    >>> out, fig, txt = analyse_and_output_cross(settings, rawdata)

run_analysis_files
    Methods to the analysis on a set of files. It will create some
    output that can be used for reporting.
"""
from __future__ import absolute_import
import logging
import os
# pyretis imports
from pyretis.core.units import CONVERT, create_conversion_factors
from pyretis.core.pathensemble import PATH_DIR_FMT
from pyretis.analysis import (analyse_flux, analyse_energies, analyse_orderp,
                              analyse_path_ensemble, match_probabilities,
                              retis_flux, retis_rate)
from pyretis.inout.analysisio.analysistxt import (txt_energy_output,
                                                  txt_flux_output,
                                                  txt_orderp_output,
                                                  txt_path_output,
                                                  txt_matched_probability)
from pyretis.inout.common import print_to_screen, format_number
from pyretis.inout.plotting import create_plotter
from pyretis.inout.report import generate_report
from pyretis.inout.settings.settings import KEYWORDS
from pyretis.inout.writers import get_writer, PathEnsembleFile
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['analyse_file', 'run_analysis_files']


_FILE_LOAD = {'cross': True,
              'order': True,
              'energy': True,
              'pathensemble': False}


# Input files for analysis
FILES = {'md-flux': {'cross': 'cross.dat',
                     'energy': 'energy.dat',
                     'order': 'order.dat'},
         'md-nve': {'energy': 'energy.dat'},
         'tis-single': {'pathensemble': 'pathensemble.dat'},
         'tis': {'pathensemble': 'pathensemble.dat'},
         'retis': {'pathensemble': 'pathensemble.dat'}}


def run_analysis(sim_settings):
    """Run a predefined analysis task.

    Parameters
    ----------
    sim_settings : dict
        Simulation settings and settings for the analysis.

    Returns
    -------
    out : dict
        A dictionary with the results from the analysis. This dict
        can be used to generate a report.
    """
    sim_task = sim_settings['task']
    if sim_task in set(('retis', 'tis')):
        if sim_task == 'tis':
            return run_tis_analysis(sim_settings)
        elif sim_task == 'retis':
            return run_retis_analysis(sim_settings)
    else:
        raw_data = []
        add_outdir = sim_task in set(('tis-single',))
        for file_type in FILES[sim_task]:
            filename = FILES[sim_task][file_type]
            if add_outdir:
                filename = os.path.join(sim_settings['output-dir'], filename)
            if os.path.isfile(filename):
                raw_data.append((file_type, filename))
        return run_analysis_files(sim_settings, raw_data)


def get_path_ensemble_files(ensemble, sim_settings, detect,
                            interfaces):
    """This method will return files for a single path ensemble.

    Here, we will return the files needed to analyse a single path
    ensemble and we will also return settings which can be used for
    the analysis.

    Parameters
    ----------
    ensemble : int
        This is the integer representing the ensemble.
    sim_settings : dict
        The settings to use for an analysis/simulation
    detect : float or None
        The interface use for detecting if a path is successful for not.
    interfaces : list of floats
        The interfaces used for this particular path simulation.

    Returns
    -------
    local_settings : dict
        This dict contains settings which can be used for a initial
        flux analysis.
    files : list of tuples
        The tuples in this list are the files which can be analysed
        further, using the settings in `out[0]`.
    """
    sim_task = sim_settings['task']
    local_settings = {}
    for key in sim_settings:
        local_settings[key] = sim_settings[key]
    local_settings['detect'] = detect
    local_settings['interfaces'] = interfaces
    local_settings['ensemble'] = ensemble
    files = []
    for file_type in FILES[sim_task]:
        filename = os.path.join(PATH_DIR_FMT.format(ensemble),
                                FILES[sim_task][file_type])
        if os.path.isfile(filename):
            files.append((file_type, filename))
    return local_settings, files


def get_path_simulation_files(sim_settings):
    """Set up for analysis of TIS and RETIS simulations.

    For these kinds of simulations, we expect to analyse several
    directories with raw-data. For TIS we expect to find a directory
    with raw-data for the initial flux (named ``flux``) and the
    directories for the path simulations (named ``001``, ``002`` etc.
    for ensembles [0^+], [1^+] and so on). For RETIS, we expect to
    find the same directories buth with a ``000`` (for the ``[0^-]``
    ensemble) rather than the ``flux`` directory.

    Parameters
    ----------
    sim_settings : dict
        The settings used for the (RE)TIS simulation(s). These settings
        are used to get the interfaces used and the path ensembles
        defined by these interfaces.

    Returns
    -------
    all_settings : list of dict
        This dict in this list contains settings which can be used for
        analysis.
    all_files : list of lists of tuples
        `all_files[i]` is a list of files from path ensemble
        simulation `i`. For TIS, `all_files[0]` should be the files
        obtained in the initial flux simulation. These files can be
        analysed using the settings in `all_settings[i]`.
    """
    # Check if we can do flux analysis:
    all_files, all_settings = [], []
    interfaces = sim_settings['interfaces']
    reactant = interfaces[0]
    product = interfaces[-1]
    if sim_settings['task'] == 'tis':
        all_files.append(None)
        all_settings.append(None)
    else:  # just add the 0 ensemble
        detect = None
        interface = [-float('inf'), reactant, reactant]
        setts, files = get_path_ensemble_files(0, sim_settings, detect,
                                               interface)
        all_files.append(files)
        all_settings.append(setts)
    for i, middle in enumerate(interfaces[:-1]):
        try:
            detect = interfaces[i + 1]
        except IndexError:
            detect = product
        interface = [reactant, middle, product]
        setts, files = get_path_ensemble_files(i + 1, sim_settings, detect,
                                               interface)
        all_files.append(files)
        all_settings.append(setts)
    return all_settings, all_files


def print_value_error(heading, value, rel_error):
    """Just print out matched results"""
    val = format_number(value, 0.1, 100)
    msgtxt = '{}: {}'.format(heading, val)
    print_to_screen(msgtxt.strip())
    fmt_scale = format_number(rel_error * 100, 0.1, 100)
    msgtxt = '(Relative error: {} %)'.format(fmt_scale.rstrip())
    print_to_screen(msgtxt)


def run_tis_analysis(sim_settings):
    """Run the analysis for TIS.

    Parameters
    ----------
    sim_settings : dict
        The settings to use for an analysis/simulation
    all_settings : list of dicts
        `all_settings[i]` contains information for analysing a
        specific path ensemble.
    all_files : list of lists
        `all_files[i]` contains the paths for the files to be analysed.
    """
    all_settings, all_files = get_path_simulation_files(sim_settings)
    results = {'cross': None,
               'pathensemble': [],
               'matched': None}
    nens = len(all_settings) - 1
    for i, (sett, files) in enumerate(zip(all_settings, all_files)):
        if i == 0:
            msgtxt = ('Initial flux is not calculated here.\n'
                      'Remember to calculate this separately!')
            logger.info(msgtxt)
            print_to_screen(msgtxt)
        else:
            msgtxt = 'Analysing ensemble {} of {}'.format(i, nens)
            print_to_screen(msgtxt)
            print_to_screen()
            result = run_analysis_files(sett, files)
            results['pathensemble'].append(result['pathensemble'])
            report_txt = generate_report('tis-single', result,
                                         output='txt')[0]
            print_to_screen(''.join(report_txt))
            print_to_screen()
    # match probabilities:
    out, fig, txt = analyse_and_output_matched(sim_settings,
                                               results['pathensemble'])
    results['matched'] = {'out': out, 'figures': fig, 'txtfile': txt}
    print_to_screen('Overall results')
    print_to_screen('===============')
    print_to_screen('')
    print_value_error('TIS Crossing probability',
                      out['prob'], out['relerror'])
    return results


def run_retis_analysis(sim_settings):
    """Run the analysis for RETIS.

    Parameters
    ----------
    sim_settings : dict
        The settings to use for an analysis/simulation
    all_settings : list of dicts
        `all_settings[i]` contains information for analysing a
        specific path ensemble.
    all_files : list of lists
        `all_files[i]` contains the paths for the files to be analysed.
    """
    units = sim_settings['units']
    create_conversion_factors(units, **sim_settings['units-base'])
    all_settings, all_files = get_path_simulation_files(sim_settings)
    results = {'cross': None,
               'pathensemble': [],
               'matched': None}
    nens = len(all_settings) - 1
    print_to_screen()
    for i, (sett, files) in enumerate(zip(all_settings, all_files)):
        msgtxt = 'Analysing ensemble {} of {}'.format(i, nens)
        print_to_screen(msgtxt)
        print_to_screen()
        if i == 0:
            result = run_analysis_files(sett, files)
            results['pathensemble0'] = result['pathensemble']
            report_txt = generate_report('retis0', result, output='txt')[0]
            print_to_screen(''.join(report_txt))
            print_to_screen()
        else:
            result = run_analysis_files(sett, files)
            results['pathensemble'].append(result['pathensemble'])
            report_txt = generate_report('tis-single', result,
                                         output='txt')[0]
            print_to_screen(''.join(report_txt))
            print_to_screen()
    # match probabilities:
    out, fig, txt = analyse_and_output_matched(sim_settings,
                                               results['pathensemble'])
    results['matched'] = {'out': out, 'figures': fig, 'txtfile': txt}
    flux, flux_error = retis_flux(results['pathensemble0'],
                                  results['pathensemble'][0],
                                  sim_settings['integrator']['timestep'])
    results['flux'] = {'value': flux, 'error': flux_error,
                       'unit': units}
    results['fluxc'] = {'value': flux / CONVERT['time'][units, 'ns'],
                        'error': flux_error,
                        'unit': 'ns'}
    rate, rate_error = retis_rate(out['prob'], out['relerror'],
                                  flux, flux_error)
    results['rate'] = {'value': rate, 'error': rate_error,
                       'unit': units}
    results['ratec'] = {'value': rate / CONVERT['time'][units, 'ns'],
                        'error': rate_error, 'unit': 'ns'}
    print_to_screen('Overall results')
    print_to_screen('===============')
    print_to_screen('')
    print_value_error('RETIS Crossing probability',
                      out['prob'], out['relerror'])
    print_to_screen('')
    print_value_error('Initial flux (units 1/{})'.format(units), flux,
                      flux_error)
    print_to_screen('')
    print_value_error('Rate constant (units 1/{})'.format(units), rate,
                      rate_error)
    return results


def run_analysis_files(settings, files):
    """Run the analysis on a collection of files.

    Parameters
    ----------
    settings : dict
        This dict contains settings which dictates how the
        analysis should be performed and it should also contain
        information on how the simulation was performed.
    files : list of tuples
        This list contains the raw files to be analysed. The
        tuples are on format ('filetype', 'filename').

    Returns
    -------
    The results from the analysis.
    """
    report_dir = settings.get('report-dir', None)
    plotter = create_plotter(settings['plot'], out_dir=report_dir)
    txtout = settings['txt-output']
    results = {}
    for (file_type, file_name) in files:
        analyse_func = analyse_file(file_type, file_name)
        out, figures, txtfile = analyse_func(settings, plotter=plotter,
                                             txt=txtout)
        results[file_type] = {'out': out,
                              'figures': figures,
                              'txtfile': txtfile}
    return results


def select_analyse_function(what):
    """A function to select the analyse function to use.

    Just for convenience, it will select the function to use for the
    analysis based on a given string.

    Parameters
    ----------
    what : string
        Selects the analysis function.

    Returns
    -------
    out : function
        The function to use for the analysis.
    """
    function_map = {'cross': analyse_and_output_cross,
                    'order': analyse_and_output_orderp,
                    'energy': analyse_and_output_energy,
                    'pathensemble': analyse_and_output_path}
    return function_map.get(what, None)


def read_first_block(fileobj, file_name):
    """Helper function to read the first block of data from a file.

    Parameters
    ----------
    fileobj : object like `Writer`.
        A object that supports a `load` function to read block
        of data from a file.
    file_name : string
        The file to open.

    Returns
    -------
    out : numpy.array
        The raw data read from the file.
    """
    first_block = None
    for block in fileobj.load(file_name):
        if first_block is None:
            first_block = block
        else:
            msg = ['Noticed a second block in the input file "{}"',
                   'This will be ignored by the flux analysis.',
                   ('Are you are running the analysis with '
                    'the correct input?')]
            msgtxt = '\n'.join(msg).format(file_name)
            logger.warning(msgtxt)
            break
    if first_block is None:
        return None
    else:
        return first_block['data']


def analyse_file(file_type, file_name):
    """Run analysis on the given file.

    This function is included for convenience so that we can call an
    analysis like `analyse_file('cross', 'cross.dat')` i.e. it should
    automatically open the file and apply the correct analysis according
    to a given file type. Here we return a function to do the analysis,
    so we are basically wrapping one of the analysis functions. This is
    done in case we wish to rerun the analysis but with different
    settings for instance.


    Parameters
    ----------
    file_type : string
        This is the type of file we are to analyse.
    file_name : string
        The file name to open.

    Returns
    -------
    out : function
        A function which can be used to do the analysis.
    """
    def wrapper(settings, plotter=None, txt=None):
        """Wrapper to run analysis on first block in input file only.

        Parameters
        ----------
        settings : dict
            This dict contains settings which dictates how the
            analysis should be performed and information on how the
            simulation was performed.
        plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
            This is the object that handles the plotting.
        txt : dict
            If txt is different from None it is assumed to contain the
            format for the text files and backup settings.
        """
        function = select_analyse_function(file_type)
        if file_type in ('energy', 'order', 'cross'):
            raw_data = read_first_block(get_writer(file_type), file_name)
            return function(settings, raw_data, plotter=plotter, txt=txt)
        elif file_type == 'pathensemble':
            fileobj = PathEnsembleFile(file_name, settings['ensemble'],
                                       settings['interfaces'],
                                       detect=settings.get('detect', None))
            return function(settings, fileobj, plotter=plotter, txt=txt)
        else:
            msgtxt = 'Unknown file type "{}" requested!'.format(file_type)
            logger.error(msgtxt)
            raise ValueError(msgtxt)
    return wrapper


def check_output(function):
    """A decorator for checking outputs for the analyse functions.

    Outputs can either be specified explicitly or implicitly by the
    analysis settings. Here we create a decorator that will set up
    output if nothing is specified. We handle plotters and txt output
    slightly differently since the plotter needs to have objects
    created and the txt output is just a string specifying the file
    extension.

    For plotters:

    - If a plotter is explicitly given with the `plotter` keyword then
      we use that one.

    - If not explicitly given, we try to create a plotter from given
      analysis settings. If the analysis settings specify that no
      plotter should be created we leave `plotter` equal to None.

    For text output:

    - Text output is specified with a dictionary. if the text output
      is not explicitly specified here, we check if it is defined by the
      analysis settings by looking for the keyword `txt-output`.
      If this is given we just look for the keys `fmt` which specifies
      the format and 'backup' which determines if we should do backups
      or not.

    Parameters
    ----------
    function : A callable function
        The function to decorate

    Returns
    -------
    out : A callable function
        The decorated function which will not run if we have not
        specified any outputs.
    """
    def wrapper(settings, rawdata, plotter=None, txt=None):
        """The actual wrapper. It will check that one of plotter/txt is given.

        Parameters
        ----------
        settings : dict
            This dict contains settings for the analysis and it should
            also contain information on how the simulation was performed.
        rawdata : iterable, or similar
            This is the raw data which is processed.
        plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
            This is the object that handles the plotting.
        txt : dict
            If `txt` is different from None it is assumed to contain
            the format for the text files and backup settings.

        Returns
        -------
        out[0] : dict
            This dict contains the results from the analysis
        out[1] : list of dicts
            Dict with the figure files created (if any).
        out[2] : list of strings
            List with the text files created (if any).
        """
        txtout = None
        if plotter is None:
            plotter = create_plotter(settings['plot'],
                                     out_dir=settings.get('report-dir', None))
        txt = settings['txt-output']
        if plotter is None and txt is None:
            msg = 'No output selected. Skipping analysis!'
            logger.warning(msg)
            return None, None, None
        if txt is not None:  # just make sure we specify the things we need:
            default = KEYWORDS['txt-output']['default']
            try:
                txtout = {'fmt': txt.get('fmt', default['fmt']),
                          'backup': txt.get('backup', default['backup'])}
            except AttributeError:
                txtout = default
                msgtxt = ('Malformed "txt-output" setting: "{}".'
                          ' Assuming "{}"')
                msgtxt = msgtxt.format(txt, txtout)
                logger.critical(msgtxt)
        return function(settings, rawdata, plotter=plotter, txt=txtout)
    return wrapper


@check_output
def analyse_and_output_cross(settings, rawdata, plotter=None, txt=None):
    """Analyse crossing data and output the results.

    Parameters
    ----------
    settings : dict
        This dict contains settings for the analysis and it should
        also contain information on how the simulation was performed.
    rawdata : iterable
        This is the raw data which is processed.
    plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
        This is the object that handles the plotting.
    txt : dict
        If `txt` is different from None it is assumed to contain the
        format for the text files and backup settings.

    Returns
    -------
    out[0] : dict
        This dict contains the results from the analysis
    out[1] : list of dicts
        Dict with the figure files created (if any).
    out[2] : list of strings
        List with the text files created (if any).
    """
    figures, outtxt = None, None
    result = analyse_flux(rawdata, settings)
    if plotter is not None:
        figures = plotter.plot_flux(result)
    if txt is not None:
        outtxt = txt_flux_output(result, out_fmt=txt['fmt'],
                                 backup=txt['backup'],
                                 path=settings.get('report-dir', None))
    return result, figures, outtxt


@check_output
def analyse_and_output_orderp(settings, rawdata, plotter=None, txt=None):
    """Analyse and output order parameter data.

    Parameters
    ----------
    settings : dict
        This dict contains settings for the analysis and should also
        contain information on how the simulation was performed.
    rawdata : iterable, or similar
        This is the raw data which is processed.
    plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
        This is the object that handles the plotting.
    txt : dict
        If txt is different from None it is assumed to contain the
        format for the text files and backup settings.

    Returns
    -------
    out[0] : dict
        This dict contains the results from the analysis
    out[1] : list of dicts
        Dict with the figure files created (if any).
    out[2] : list of strings
        List with the text files created (if any).
    """
    if 'units-out' in settings:
        logger.warning('Change of units is not implemented yet!')
    figures, outtxt = None, None
    result = analyse_orderp(rawdata, settings)
    if plotter is not None:
        figures = plotter.plot_orderp(result, rawdata)
    if txt is not None:
        outtxt = txt_orderp_output(result, rawdata, out_fmt=txt['fmt'],
                                   backup=txt['backup'],
                                   path=settings.get('report-dir', None))
    return result, figures, outtxt


@check_output
def analyse_and_output_energy(settings, rawdata, plotter=None, txt=None):
    """Analyse and output energy data.

    Parameters
    ----------
    settings : dict
        This dict contains settings for the analysis and information
        on how the simulation was performed.
    rawdata : iterable, or similar
        This is the raw data which is processed.
    plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
        This is the object that handles the plotting.
    txt : dict
        If txt is different from None it is assumed to contain the
        format for the text files and backup settings.

    Returns
    -------
    out[0] : dict
        This dict contains the results from the analysis
    out[1] : list of dicts
        Dict with the figure files created (if any).
    out[2] : list of strings
        List with the text files created (if any).
    """
    figures, outtxt = None, None
    result = analyse_energies(rawdata, settings)
    if plotter is not None:
        figures = plotter.plot_energy(result, rawdata)
    if txt is not None:
        outtxt = txt_energy_output(result, rawdata, out_fmt=txt['fmt'],
                                   backup=txt['backup'],
                                   path=settings.get('report-dir', None))
    return result, figures, outtxt


@check_output
def analyse_and_output_path(settings, path_ensemble, plotter=None, txt=None):
    """Analyse and output path data.

    This will run the path analysis and output the results.

    Parameters
    ----------
    settings : dict
        This dict contains settings for the analysis and information
        on how the simulation was performed.
    path_ensemble : object like `PathEnsemble` from `pyretis.core.path`
        This is the path ensemble we will analyse. This can also be a
        object like `PathEnsembleFile` from `pyretis.inout.writers`.
    plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
        This is the object that handles the plotting.
    txt : dict
        If txt is different from None it is assumed to contain the
        format for the text files and backup settings.

    Returns
    -------
    out[0] : dict
        This dict contains the results from the analysis
    out[1] : list of dicts
        Dict with the figure files created (if any).
    out[2] : list of strings
        List with the text files created (if any).
    """
    if 'units-out' in settings:
        logger.warning('Change of units is not implemented yet!')
    figures, outtxt = None, None
    idetect = path_ensemble.detect
    result = analyse_path_ensemble(path_ensemble, settings, idetect)
    if plotter is not None:
        figures = plotter.plot_path(path_ensemble, result, idetect)
    if txt is not None:
        outtxt = txt_path_output(path_ensemble, result, idetect,
                                 out_fmt=txt['fmt'],
                                 backup=txt['backup'],
                                 path=settings.get('report-dir', None))
    return result, figures, outtxt


@check_output
def analyse_and_output_matched(settings, raw_data, plotter=None, txt=None):
    """Analyse and output matched probability,

    This will calculate the over-all crossing probability by combining
    results from many path simulations.

    Parameters
    ----------
    settings : dict
        This dict contains settings for the analysis and information
        on how the simulation was performed.
    plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
        This is the object that handles the plotting.
    txt : dict
        If txt is different from None it is assumed to contain the
        format for the text files and backup settings.

    Returns
    -------
    out[0] : dict
        This dict contains the results from the analysis
    out[1] : list of dicts
        A dictionary with the figure files created (if any).
    out[2] : list of strings
        A list with the text files created (if any).
    """
    figures, outtxt = None, None
    path_results, path_ensembles_name, detect = [], [], []
    for ensemble in raw_data:
        path_results.append(ensemble['out'])
        path_ensembles_name.append(ensemble['out']['ensemble'])
        detect.append(ensemble['out']['detect'])
    result = match_probabilities(path_results, detect)
    if plotter is not None:
        figures = plotter.plot_total_probability(path_ensembles_name, detect,
                                                 result)
    if txt is not None:
        outtxt = txt_matched_probability(path_ensembles_name, detect, result,
                                         out_fmt=txt['fmt'],
                                         backup=txt['backup'],
                                         path=settings.get('report-dir', None))
    return result, figures, outtxt
