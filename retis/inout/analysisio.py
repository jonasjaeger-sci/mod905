# -*- coding: utf-8 -*-
"""
This files contains methods that will output results from the
path analysis and the energy analysis.

Important methods defined here:

- run_md_flux_analysis: Method to run the MD flux analysis on a set
  of files. It will plot the results and generate a MD-flux report.
"""
from __future__ import absolute_import
import warnings
from retis.analysis import analyse_flux, analyse_energies, analyse_orderp
from retis.inout.fileinout import CrossFile, EnergyFile, OrderFile
from retis.inout.plotting import create_plotter
from retis.inout.txtinout import (txt_energy_output, txt_flux_output,
                                  txt_orderp_output)
from retis.inout.report import generate_report_md
from retis.inout.common import _REPORTFILES


def run_md_flux_analysis(analysis_settings, simulation_settings, raw_data):
    """
    This method will analyse the output from a MD-flux simulation,
    it will determine if the data should be read from files or if it's
    passed as other structures, directly from he simulation.

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
        crossfile = raw_data['files']['cross']
        energyfile = raw_data['files']['energy']
        orderfile = raw_data['files']['order']
        results = run_md_flux_files(analysis_settings, simulation_settings,
                                    crossfile, energyfile, orderfile)
    else:
        results = None
    if results is not None:
        for report_type in analysis_settings.get('report', ['rst']):
            report, ext = generate_report_md(results, output=report_type)
            outfile = _REPORTFILES['md-flux'].format(ext)
            with open(outfile, 'w') as report_fh:
                report_fh.write(report)
    return results


def run_md_flux_files(analysis_settings, simulation_settings,
                      crossfile, energyfile, orderfile):
    """
    This method will analyse the output from a MD-flux simulation, by reading
    in raw data from output files obtained in the MD-flux simulation.
    This method will output a series of plots and generate a report based on
    the analysis. The function calls for performing the actual analysis are
    here wrapped with run_analysis_file, this is just to ensure that we are
    only analysing one block and ignoring the rest of the block in the file.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings which dictates how the
        analysis should be performed.
    simulation_settings : dict
        This dict contains information on how the simulation
        was performed.
    crossfile : string
        The file with the crossing data
    energyfile : string
        The file with the energy data
    orderfile : string
        The file with the order parameter data
    """
    plotter = create_plotter(analysis_settings.get('plotter', 'mpl'),
                             analysis_settings.get('plot-format', 'png'),
                             analysis_settings.get('plot-style', 'pytismol'))
    results = {'txtfile': {}}
    analysis = {'flux': {'func': run_flux_analysis,
                         'fileobj': CrossFile(crossfile, mode='r')},
                'order': {'func': run_order_analysis,
                          'fileobj': OrderFile(orderfile, mode='r')},
                'energy': {'func': run_energy_analysis,
                           'fileobj': EnergyFile(energyfile, mode='r')}}
    for key in analysis:
        run_func = run_analysis_file(analysis[key]['func'],
                                     analysis[key]['fileobj'])
        out, fig, txtfile = run_func(analysis_settings,
                                     simulation_settings,
                                     plotter)
        if txtfile is not None:
            results['txtfile'].update(txtfile)
        results[key] = out
        results['{}_figures'.format(key)] = fig
    return results


def run_analysis_file(analysis_func, fileobject):
    """
    This is a wrapper for analysing files, it will simply only
    consider the first block in the file and exit if more are
    found with a warning.

    Parameters
    ----------
    analysis_func : function
        This is the function to use for the analysis.
    fileobject : object of type FileWriter
        This is one of the objects derived from the FileWriter object, this is
        typically one of CrossFile, EnergyFile, OrderFile.

    Returns
    -------
    out : function
        The decorated variant of analysis_func. This function can now be used
        to analyse a file.
    """
    def wrapper(analysis_settings, simulation_settings, plotter):
        """
        This is a wrapper for the analysis from files.

        Parameters
        ----------
        analysis_settings : dict
            This dict contains settings which dictates how the
            analysis should be performed.
        simulation_settings : dict
            This dict contains information on how the simulation
            was performed.
        plotter : object as defined in plotting.py
            This is the object that handles the plotting. It is here assumed
            to define the function plot_flux(...).
        txt : string, optional
            If txt is different from None it is assumed to be the format for
            writing txt files. I.e. the text files will then be written!
        """
        first_block = True
        for block in fileobject.load():
            if not first_block:
                msg = ['Noticed a second block in the input file "{}"',
                       'This will be ignored by the flux analysis.',
                       'Are you sure you are running the correct analysis',
                       'with correct input?']
                warnings.warn(' '.join(msg).format(fileobject.filename))
                break
            return analysis_func(analysis_settings, simulation_settings,
                                 block['data'], plotter=plotter)
    return wrapper


def set_up_output(func):
    """
    This is a decorator to automatically create a plotter if it's
    not given. It will also set up txt writing based on the settings
    given as input.

    Parameters
    ----------
    func : function
        The function to wrap, typically one of the run_..._analysis
        functions.
    """
    def wrapper(analysis_settings, simulation_settings, rawdata,
                plotter=None):
        """
        This method will generate the plotter if it's needed.

        Parameters
        ----------
        analysis_settings : dict
            This dict contains settings which dictates how the
            analysis should be performed.
        simulation_settings : dict
            This dict contains information on how the simulation
            was performed.
        raw_data : list/dict etc.
            The raw data to analyse.
        plotter : object as defined in plotting.py
            This is the object that handles the plotting. It is here assumed
            to define the function plot_flux(...).
        txt : string, optional
            If txt is different from None it is assumed to be the format for
            writing txt files. I.e. the text files will then be written!
        """
        if plotter is None:
            plot = analysis_settings.get('plotter', 'mpl')
            fmt = analysis_settings.get('plot-format', 'png')
            style = analysis_settings.get('plot-style', 'pytismol')
            plotter = create_plotter(plot, fmt, style)
        txtout = analysis_settings.get('txt-format', None)
        return func(analysis_settings, simulation_settings,
                    rawdata, plotter=plotter, txt=txtout)
    return wrapper


@set_up_output
def run_flux_analysis(analysis_settings, simulation_settings,
                      crossdata, plotter=None, txt=None):
    """
    This method will just run the md flux analysis and output some
    figures.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings which dictates how the
        analysis should be performed.
    simulation_settings : dict
        This dict contains information on how the simulation
        was performed.
    crossdata : list
        The crossing data to analyse.
    plotter : object as defined in plotting.py
        This is the object that handles the plotting. It is here assumed
        to define the function plot_flux(...).
    txt : string, optional
        If txt is different from None it is assumed to be the format for
        writing txt files. I.e. the text files will then be written!

    Returns
    -------
    out[0] : dict
        This dict contains the results from the flux analysis.
    out[1] : list of dicts
        This list contains the different filenames for the figures
        created.
    out[2] : list of strings
        This list contains the different filenames for the text files
        created (if any).

    See Also
    --------
    `analyse_flux` in retis.analysis.flux_analysis.py
    """
    flux_result = analyse_flux(crossdata, analysis_settings,
                               simulation_settings)
    figname = plotter.plot_flux(flux_result)
    # restructure for report:
    figures = []
    for run, err in zip(figname['runflux'], figname['block']):
        figures.append({'runflux': run, 'errflux': err})
    outtxt = None
    if txt is not None:
        outtxt = txt_flux_output(flux_result, out_fmt=txt)
    return flux_result, figures, outtxt


@set_up_output
def run_order_analysis(analysis_settings, simulation_settings,
                       orderdata, plotter=None, txt=None):
    """
    This method will just run the order analysis and plot the results
    to files.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings which dictates how the
        analysis should be performed.
    simulation_settings : dict
        This dict contains information on how the simulation
        was performed.
    orderdata : numpy.array
        The order parameter data to analyse.
    plotter : object as defined in plotting.py
        This is the object that handles the plotting. It is here assumed
        to define the function plot_orderp(...).
    txt : string, optional
        If txt is different from None it is assumed to be the format for
        writing txt files. I.e. the text files will then be written!

    Returns
    -------
    out[0] : dict
        This dict contains the results from the flux analysis
    out[1] : list of dicts
        This list contains the different filenames for the figures
        created.
    out[2] : list of strings
        This list contains the different filenames for the text files
        created (if any).

    See Also
    --------
    `analyse_orderp` in retis.analysis.order_analysis.py
    """
    if 'units' in simulation_settings:
        warnings.warn('Change of units is not implemented yet!')
    order_result = analyse_orderp(orderdata, analysis_settings)
    figures = plotter.plot_orderp(order_result, orderdata)
    outtxt = None
    if txt is not None:
        outtxt = txt_orderp_output(order_result, orderdata, out_fmt=txt)
    return order_result, figures, outtxt


@set_up_output
def run_energy_analysis(analysis_settings, simulation_settings,
                        energydata, plotter=None, txt=None):
    """
    This method will just run the md flux analysis and output some
    figures.

    Parameters
    ----------
    analysis_settings : dict
        This dict contains settings which dictates how the
        analysis should be performed.
    simulation_settings : dict
        This dict contains information on how the simulation
        was performed.
    energydata : dict of numpy.arrays
        The energy data to analyse.
    plotter : object as defined in plotting.py
        This is the object that handles the plotting. It is here assumed
        to define the function plot_energy(...).
    txt : string, optional
        If txt is different from None it is assumed to be the format for
        writing txt files. I.e. the text files will then be written!

    Returns
    -------
    out[0] : dict
        This dict contains the results from the flux analysis.
    out[1] : list of dicts
        This list contains the different filenames for the figures
        created.
    out[2] : list of strings
        This list contains the different filenames for the text files
        created (if any).

    See Also
    --------
    `analyse_flux` in retis.analysis.flux_analysis.py
    """
    energy_result = analyse_energies(energydata, analysis_settings)
    figures = plotter.plot_energy(energy_result, energydata,
                                  sim_settings=simulation_settings)
    outtxt = None
    if txt is not None:
        outtxt = txt_energy_output(energy_result, energydata, out_fmt=txt)
    return energy_result, figures, outtxt
