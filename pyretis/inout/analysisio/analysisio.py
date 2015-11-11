# -*- coding: utf-8 -*-
"""Methods that will output results from the different analysis methods.

The methods defined here will also run the analysis and output according
to given settings.

Important functions defined here:

- run_md_flux_analysis: Method to run the MD flux analysis on a set
  of files. It will plot the results and generate a MD-flux report.
"""
from __future__ import absolute_import
import warnings
from pyretis.analysis import analyse_flux, analyse_energies, analyse_orderp
from pyretis.inout.fileinout import CrossFile, EnergyFile, OrderFile
from pyretis.inout.plotting import create_plotter
from pyretis.inout.analysisio.analysistxt import (txt_energy_output,
                                                  txt_flux_output,
                                                  txt_orderp_output)
from pyretis.inout.report import generate_report_md
from pyretis.inout.common import _REPORTFILES


__all__ = ['run_md_flux_analysis']


def run_md_flux_analysis(analysis_settings, simulation_settings, raw_data):
    """Analyse the output from a MD-flux simulation.

    This method will will determine if the data should be read from files or
    if it's passed as other structures directly from the simulation.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings which dictates how the
        analysis should be performed.
    simulation_settings : dict
        This dict contains information on how the simulation
        was performed.
    raw_data : dict
        This dict contains the raw data needed for the analysis.

    Returns
    -------
    The results from the analysis.
    """
    if 'files' in raw_data:
        results = run_md_flux_files(analysis_settings, simulation_settings,
                                    raw_data['files'])
    else:
        results = None
    if results is not None:
        for report_type in analysis_settings.get('report', ['rst']):
            report, ext = generate_report_md(results, output=report_type)
            outfile = _REPORTFILES['md-flux'].format(ext)
            with open(outfile, 'wt') as report_fh:
                try:  # will work in python 3
                    report_fh.write(report)
                except UnicodeEncodeError:  # for python 2
                    report_fh.write(report.encode('utf-8'))
    return results


def run_md_flux_files(analysis_settings, simulation_settings, raw_files):
    """Analyse the output from a MD-flux simulation from files.

    The raw data will be read from output files obtained by the MD-flux
    simulation. This method will output a series of plots and generate a
    report based on the analysis. The function calls for performing the
    actual analysis are here wrapped with run_analysis_file, this is just
    to ensure that we are only analyzing one block and ignoring the rest
    of the possible blocks in the file.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings which dictates how the
        analysis should be performed.
    simulation_settings : dict
        This dict contains information on how the simulation
        was performed.
    raw_files : dict
        The different files to open. We assume/hope that it contains
        the keys `flux`, `order` and `energy` with the file names to open.
    """
    plotter = create_plotter(analysis_settings.get('plotter', 'mpl'),
                             analysis_settings.get('plot-format', 'png'),
                             analysis_settings.get('plot-style', 'pyretis'))
    txtout = analysis_settings.get('txt-format', None)
    results = {'txtfile': {}}
    for key in raw_files:
        analyse_func = analyse_file(key, raw_files[key])
        out, fig, txtfile = analyse_func(analysis_settings,
                                         simulation_settings,
                                         plotter, txtout)

        if txtfile is not None:
            results['txtfile'].update(txtfile)
        results[key] = out
        results['{}_figures'.format(key)] = fig
    return results


def select_analyse_function(what):
    """A function to select the analyse function to use.

    Just for convenience, it will select the function to use for the analysis
    based on a given string.

    Parameters
    ----------
    what : string
        Selects the analysis function.

    Returns
    -------
    out : function
        The function to use for the analysis.
    """
    if what == 'cross':
        return analyse_and_output_cross
    elif what == 'order':
        return analyse_and_output_orderp
    elif what == 'energy':
        return analyse_and_output_energy
    else:
        return None


def get_file_instance(file_name, file_type):
    """Method to open a file with the correct file parser based on file type.

    This is a convenience function to return an instance of `FileWriter` or
    derived classes so that we are ready to read data from that file.

    Parameters
    ----------
    file_type : string
        The desired file type
    file_name : string
        The file to open

    Returns
    -------
    out : object like `FileWriter` from `pyretis.inout.fileinout`
    """
    if file_type == 'cross':
        return CrossFile(file_name, mode='r')
    elif file_type == 'order':
        return OrderFile(file_name, mode='r')
    elif file_type == 'energy':
        return EnergyFile(file_name, mode='r')
    else:
        return None


def analyse_file(file_type, file_name):
    """Run analysis on the given file.

    This function is included for convenience so that we can call a analysis
    like `analyse_file('cross', 'cross.dat')` i.e. it should automatically
    open the file and apply the correct analysis according to a given file
    type. Here we return a function to do the analysis, so we are basically
    wrapping one of the analysis functions. This is done in case we wish to
    rerun the analysis but with different settings for instance.


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
    def wrapper(analysis_settings, simulation_settings, plotter, txt):
        """Wrapper to run analysis on first block in input file only.

        Parameters
        ----------
        analysis_settings : dict
            This dict contains settings which dictates how the
            analysis should be performed.
        simulation_settings : dict
            This dict contains information on how the simulation
            was performed.
        plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
            This is the object that handles the plotting.
        txt : string, optional
            If txt is different from None it is assumed to be the format for
            writing txt files. I.e. the text files will then be written!
        """
        fileobj = get_file_instance(file_name, file_type)
        function = select_analyse_function(file_type)
        first_block = None
        for block in fileobj.load():
            if first_block is None:
                first_block = block
            else:
                msg = ['Noticed a second block in the input file "{}"',
                       'This will be ignored by the flux analysis.',
                       'Are you sure you are running the correct analysis',
                       'with correct input?']
                warnings.warn(' '.join(msg).format(fileobj.filename))
                break
        return function(analysis_settings, simulation_settings,
                        first_block['data'], plotter, txt)
    return wrapper


def check_output(function):
    """A decorator for checking outputs for the analyse functions.

    Parameters
    ----------
    func : function
        The function to decorate

    Returns
    -------
    out : function
        The decorated function which will not run if we have not
        specified any outputs.
    """
    def wrapper(analysis_settings, simulation_settings,
                rawdata, plotter, txt):
        """The actual wrapper. It will check that one of plotter/txt is given.

        Parameters
        ----------
        analysis_settings : dict
            This dict contains settings for the analysis.
        simulation_settings : dict
            This dict contains information on how the simulation was performed.
        rawdata : iterable, or similar
            This is the raw data which is processed.
        plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
            This is the object that handles the plotting.
        txt : string,
            If txt is different from None it is assumed to be the format for
            writing txt files. I.e. the text files will then be written!

        Returns
        -------
        out[0] : dict
            This dict contains the results from the analysis
        out[1] : list of dicts
            Dict with the figure files created (if any).
        out[2] : list of strings
            List with the text files created (if any).
        """
        if plotter is None and txt is None:
            msg = 'No output selected. Skipping analysis'
            warnings.warn(msg)
            return None, None, None
        return function(analysis_settings, simulation_settings,
                        rawdata, plotter, txt)
    return wrapper


@check_output
def analyse_and_output_cross(analysis_settings, simulation_settings,
                             rawdata, plotter, txt):
    """Analyse crossing data and output the results.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings for the analysis.
    simulation_settings : dict
        This dict contains information on how the simulation was performed.
    rawdata : iterable, or similar
        This is the raw data which is processed.
    plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
        This is the object that handles the plotting.
    txt : string,
        If txt is different from None it is assumed to be the format for
        writing txt files. I.e. the text files will then be written!

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
    result = analyse_flux(rawdata, analysis_settings, simulation_settings)
    if plotter is not None:
        figures = plotter.plot_flux(result)
    if txt is not None:
        outtxt = txt_flux_output(result, out_fmt=txt)
    return result, figures, outtxt


@check_output
def analyse_and_output_orderp(analysis_settings, simulation_settings,
                              rawdata, plotter, txt):
    """Analyse and output order parameter data.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings for the analysis.
    simulation_settings : dict
        This dict contains information on how the simulation was performed.
    rawdata : iterable, or similar
        This is the raw data which is processed.
    plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
        This is the object that handles the plotting.
    txt : string,
        If txt is different from None it is assumed to be the format for
        writing txt files. I.e. the text files will then be written!

    Returns
    -------
    out[0] : dict
        This dict contains the results from the analysis
    out[1] : list of dicts
        Dict with the figure files created (if any).
    out[2] : list of strings
        List with the text files created (if any).
    """
    if 'units' in simulation_settings:
        warnings.warn('Change of units is not implemented yet!')
    figures, outtxt = None, None
    result = analyse_orderp(rawdata, analysis_settings)
    if plotter is not None:
        figures = plotter.plot_orderp(result, rawdata)
    if txt is not None:
        outtxt = txt_orderp_output(result, rawdata, out_fmt=txt)
    return result, figures, outtxt


@check_output
def analyse_and_output_energy(analysis_settings, simulation_settings,
                              rawdata, plotter, txt):
    """Analyse and output energy data.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings for the analysis.
    simulation_settings : dict
        This dict contains information on how the simulation was performed.
    rawdata : iterable, or similar
        This is the raw data which is processed.
    plotter : object like `MplPlotter` from `pyretis.inout.plotting`.
        This is the object that handles the plotting.
    txt : string,
        If txt is different from None it is assumed to be the format for
        writing txt files. I.e. the text files will then be written!

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
    result = analyse_energies(rawdata, analysis_settings)
    if plotter is not None:
        figures = plotter.plot_energy(result, rawdata,
                                      sim_settings=simulation_settings)
    if txt is not None:
        outtxt = txt_energy_output(result, rawdata, out_fmt=txt)
    return result, figures, outtxt
