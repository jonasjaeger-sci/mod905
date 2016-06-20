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
# pyretis imports
from pyretis.analysis import (analyse_flux, analyse_energies, analyse_orderp,
                              analyse_path_ensemble)
from pyretis.inout.writers import get_file_object, PathEnsembleFile
from pyretis.inout.plotting import create_plotter
from pyretis.inout.analysisio.analysistxt import (txt_energy_output,
                                                  txt_flux_output,
                                                  txt_orderp_output,
                                                  txt_path_output)
from pyretis.inout.settings.settings import KEYWORDS
logger = logging.getLogger(__name__)  # pylint: disable=C0103
logger.addHandler(logging.NullHandler())


__all__ = ['analyse_file', 'run_analysis_files']


_FILE_LOAD = {'cross': True,
              'order': True,
              'energy': True,
              'pathensemble': False}


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
            raw_data = read_first_block(get_file_object(file_type), file_name)
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
    if idetect is None:
        idetect = settings.get('detect', None)
        if idetect is None:  # Time to panic:
            msgtxt = 'Could not determine detect interface!'
            logger.error(msgtxt)
            raise ValueError(msgtxt)
    result = analyse_path_ensemble(path_ensemble, settings, idetect)
    if plotter is not None:
        figures = plotter.plot_path(path_ensemble, result, idetect)
    if txt is not None:
        outtxt = txt_path_output(path_ensemble, result, idetect,
                                 out_fmt=txt['fmt'],
                                 backup=txt['backup'],
                                 path=settings.get('report-dir', None))
    return result, figures, outtxt
