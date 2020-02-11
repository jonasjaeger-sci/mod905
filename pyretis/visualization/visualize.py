#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: skip-file
# Copyright (c) 2019, PyRETIS Development Team.
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
"""GUI application for visualizing simulation data.

This is a PyQt5 file, using a custom made ui layout, with a window which
displays different plots created by the path density tool. Window can either
display data of a pre-compiled compressed file generated with the
orderparam_density.py module, or compile on in/out files by importing
orderparam_density and executing before displaying the results.

"""
# Distributed under the LGPLv2.1+ License. See LICENSE for more info.
import colorama
import codecs
import deepdish as dd
import matplotlib as mpl
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import os
import pickle
import sys
import json
from matplotlib.backends.backend_qt5agg import (  # noqa: E402
        FigureCanvasQTAgg as FigureCanvas
        )
from matplotlib.figure import Figure  # noqa: E402
from pyretis.info import PROGRAM_NAME  # noqa: E402
from pyretis.visualization.common import try_data_shift  # noqa: E402
from pyretis.visualization.orderparam_density import (PathDensity,  # noqa: E402
                                                      PathVisualize)
from pyretis.visualization.plotting import (gen_surface,  # noqa: E402
                                            plot_regline,
                                            plot_int_plane)
from PyQt5 import QtCore, QtGui, QtWidgets, uic

# Hard-coded labels for energies and time/cycle steps
ENERGYLABELS = ['time', 'cycE', 'potE', 'kinE', 'totE']

dir_path = os.path.dirname(os.path.realpath(__file__))
VisualWindow = dir_path+'/'+'pyretisVisualizeWindow.ui'

Ui_VisualWindow, QtBaseClass = uic.loadUiType(VisualWindow)


class VisualApp(QtWidgets.QMainWindow, Ui_VisualWindow):
    """Class definition of the path visualization window GUI for PyRETIS.

    Application opens a QMainWindow object with a QFrame for inserting
    a matplotlib figurecanvas into, and a QDropWidget with the relevant
    settings for plotting.

    Attributes
    ----------
    mainworker : A QThread object that stores (and executes) the path density
        data back-end, initialized by the VisualApp window. When
        called will update the data lists and return to VisualApp
        for plotting.

    Div. functions
    --------------
    closeEvent, action_reload, centerOnScreen, toggle_buttons :
        Functions that relate to closing of window, reloading data,
        centering the window on screen and disable key buttons while
        pdating data/figure.
    _update_canvas_{title/text} :
        Functions that update the title and label text of plot settings
        and in the figure.
    _get_settings : Gets plot settings from VisualApp dropwidget.
    _get_savename : Generate generic savename based on current settings.
    save_png : Function that store the current figure shown in VisualApp
        window as a .png image, with name generated from data settings.
    save_pickle : Function that store the current figure shown in VisualApp
        window a pickle-dump, with name generated from data settings.
    save_hdf5 : Function that store the current figure shown in VisualApp
        window a hdf5 save, with name generated from data settings.
    save_json : Function that store the current figure shown in VisualApp
        window a json save, with name generated from data settings.
    save_script : Function that generates a script to reconstruct the current
        plot from the compressed file.
    _load_file : Opens QFileDialog for choosing file to load in VisualApp.
    _load_data : Loads data from hdf5 or pickle save.
    _load_data_output : Executes a PathDensity on input/output file before
        displaying results.
    _reload : Clears old data and initializes loading new data from file.
    _change_{cmap/zoom} :
        Updates figure with different colormap, and with xlims+ylims
    toggle_{intf/regl/cbar/titles} :
        Functions that shows/hides interfaces, regression line,
        colorbar, and titles/labes, respectively.
    emit_settings : Function that is called when pressing a QPushButton labeled
        'Update' after choosing desired settings for plot.
        Sends settings to mainworker, which updates the data of
        x, y (and z) lists before sending back to VisualApp for
        plotting.

    Signals
    -------
    start_cmd : PyQt Signal
        It tells worker to start using string, cmd.
    send_settings : PyQt Signal
        It sends settings for data_get to worker thread.

    Slots
    -----
    update_cycle : A function bound to a pyqtSignal sent by the mainworker
        thread. Signal sets upper and lower bounds for max/min
        cycles used in plotting.
    update_fig : PyQt Slot, worker thread calls function by sending 3 lists
        of floats for plotting in this function.

    """

    send_settings = QtCore.pyqtSignal(dict, name='Data settings')
    start_cmd = QtCore.pyqtSignal(str)

    def closeEvent(self, event):
        """Event function, activated when attempting to close VisualApp.

        Will create a QMessage prompt asking for confirmation of exit by
        user. If confirmed, will stop Qthread of DataObject and attempt to
        clear dataobject from memory.
        """
        result = QtWidgets.QMessageBox.question(
            self, "Confirm Exit...",
            "Are you sure you want to exit ?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.Yes:
            self.statusbar.showMessage('Closing window')
            try:
                self.thread.quit()
                self.thread.wait()
                del self.dataobject
                del self.thread
            except AttributeError:
                pass
        else:
            event.ignore()

    def action_reload(self):
        """Display a QMessagebox to confirm reload action.

        Function that displays a QMessagebox for user, double confirming
        the reload data action.
        """
        load = QtWidgets.QMessageBox.question(
            self,
            "Reload data from file",
            "Are you sure to discard the current data and reload a new set ?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if load == QtWidgets.QMessageBox.Yes:
            self.statusbar.showMessage('Deleting old data')
            try:
                self.thread.quit()
                self.thread.wait()
            except AttributeError:
                # No self.thread running.
                pass
            self._reload()

    def centerOnScreen(self):
        """Centers widget/window on screen."""
        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

    def toggle_buttons(self, onoff):
        """Toggles enable-state of key buttons of VisualApp.

        avoid user-created conflicts while busy updating data and drawing
        figure.
        """
        self.updateBtn.setEnabled(onoff)
        self.intShowChkBtn.setEnabled(onoff)
        self.regLineChkBtn.setEnabled(onoff)
        self.showTitleChkBtn.setEnabled(onoff)
        self.saveFigBtn.setEnabled(onoff)
        self.previewBtn.setEnabled(onoff)

    def disable_zcombox(self):
        """Disabling combobox with z-values if plotting density."""
        if 'Density' in self.plotTypeComBox.currentText():
            self.energyComBox.setEnabled(False)
        else:
            self.energyComBox.setEnabled(True)

    def __init__(self, folder=None, iofile=None):
        """Initialize the VisualApp QMainWindow.

        Sets up ui from file, centers on screen and sets up mainworker QThread
        for data loading.
        """
        QtWidgets.QMainWindow.__init__(self)
        Ui_VisualWindow.__init__(self)
        # Delete memory on close?
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.centerOnScreen()
        self.setWindowTitle(PROGRAM_NAME +
                            ' - Path and order parameter visualization')
        self.folder = folder
        self.iofile = iofile
        self.settings, self.dataobject, self.thread = None, None, None
        # Load data in separate thread
        self._load_file()
        self._init_widget()

    def _update_canvas_font(self):
        """Change the fontsize of title/labels of figure.

        Bound to event only.
        """
        titlefont = self.titleSizeSpin.value()
        self.settings['title font'] = titlefont
        axesfont = self.axesSizeSpin.value()
        self.settings['axes font'] = axesfont
        self.myfig.title.set_fontsize(titlefont)
        self.myfig.xaxis.set_fontsize(axesfont)
        self.myfig.yaxis.set_fontsize(axesfont)
        self.myfig.zaxis.set_fontsize(axesfont)
        self.myfig.cbar.ax.tick_params(labelsize=axesfont)
        for tick in self.myfig.ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(axesfont)
        for tick in self.myfig.ax.yaxis.get_major_ticks():
            tick.label.set_fontsize(axesfont)
        # Default pyplot tick size: lenght=3.5, width=1.0
        tick_l = round(axesfont/4, 2)
        tick_w = round(axesfont/10, 2)
        self.myfig.ax.tick_params(length=tick_l, width=tick_w)
        self.myfig.fig.canvas.draw()

    def _update_canvas_text(self):
        """Create the titles and labels of figure.

        This is in VisualApp from QLineEdits current text.
        Called by update_fig() and bound to event.
        """
        self.settings['show titles'] = self.showTitleChkBtn.isChecked()
        show = self.settings['show titles']
        self.myfig.title = self.myfig.ax.set_title(
            self.titleLine.text(),
            fontsize=self.settings['title font'],
            visible=show)
        self.myfig.xaxis = self.myfig.ax.set_xlabel(
            self.xaxisLabel.text(),
            fontsize=self.settings['axes font'],
            visible=show)
        self.myfig.yaxis = self.myfig.ax.set_ylabel(
            self.yaxisLabel.text(),
            fontsize=self.settings['axes font'],
            visible=show)
        self.myfig.zaxis = self.myfig.cbar_ax.set_title(
            self.zaxisLabel.text(),
            fontsize=self.settings['axes font'],
            visible=show)
        self.myfig.fig.canvas.draw()

    def _get_titles(self):
        """Generate tiles and lables and update QLineEdits of VisualApp.

        Function that generates generic titles and labels for the figure
        axes, colorbar, etc. and updates QLineEdits of VisualApp with
        those titles/labels.
        """
        m = self.settings['method']
        n = m[0]
        ACC = self.settings['ACC']
        shift = self.settings['try_shift']
        fol = self.settings['fol']
        op1 = self.settings['op1']
        op2 = self.settings['op2']
        xyz = op1+'-'+op2
        if 'Density' not in m:
            E = self.settings['E']
            xyz += '-'+E
            self.myfig.cbar_ax.set_title(E)
        if self.settings['weight']:
            n += '(W)'
        cmin, cmax = self.settings['min_cycle'], self.settings['max_cycle']
        title = ('{}, using {} folder(s), with {} paths, '
                 'cycles: {}-{}'.format(n, fol, ACC, cmin, cmax))
        if shift:
            title += '\nData shifted'
        # Setting text in QLineEdits of VisualApp
        self.xaxisLabel.setText(op1)
        self.yaxisLabel.setText(op2)
        if self.settings['method'][0] == 'Density':
            self.zaxisLabel.setText('Density')
        else:
            self.zaxisLabel.setText(self.settings['E'])
        self.titleLine.setText(title)
        # Updating text in plot from text in QLineEdits
        self._update_canvas_text()

    def _get_savename(self):
        """Generate generic save-name.

        Function that generates a generic save-name for the current
        figure displayed in VisualApp based on settings.
        """
        m = self.settings['method']
        n = m[0]
        ACC = self.settings['ACC']
        fol = self.settings['fol']
        op1 = self.settings['op1']
        op2 = self.settings['op2']
        xyz = op1+'-'+op2
        cmin, cmax = self.settings['min_cycle'], self.settings['max_cycle']
        if 'Density' not in m and self.settings['E'] != 'None':
            xyz += '-'+self.settings['E']
        elif self.settings['weight']:
            n += '(W)'
        name = '{}_{}_ACC={}_folder={}_({}-{})'
        return name.format(n, xyz, ACC, fol, cmin, cmax)

    def _get_settings(self):
        """Update self.settings{} with the current option from the GUI.

        Function that updates the settings of dictionary
        self.settings{} with current options from GUI window.
        """
        full_method = self.plotTypeComBox.currentText()
        dim = int(full_method[0])
        method = full_method.split(' ')[1:]
        weight = bool(method[-1] == '(weight)')
        self.settings = {
            'op1': self.firstOpComBox.currentText(),
            'op2': self.secondOpComBox.currentText(),
            'E': self.energyComBox.currentText(),
            'ACC': self.accComBox.currentText(),
            'fol': self.folderComBox.currentText(),
            'min_cycle': self.minCyclSpin.value(),
            'max_cycle': self.maxCyclSpin.value(),
            'weight': weight,
            'method': method,
            'dim': dim,
            'try_shift': self.dataShiftChkBtn.isChecked(),
            'show_int': self.intShowChkBtn.isChecked(),
            'reg_line': self.regLineChkBtn.isChecked(),
            'res': self.resSpinBox.value(),
            'colormap': self.cmapComBox.currentText(),
            'colorbar': self.cbarChkBtn.isChecked(),
            'title font': self.titleSizeSpin.value(),
            'axes font': self.axesSizeSpin.value(),
            'x-limits': (float(self.xminLine.text()),
                         float(self.xmaxLine.text())),
            'y-limits': (float(self.yminLine.text()),
                         float(self.ymaxLine.text())),
            'z-limits': (float(self.zminLine.text()),
                         float(self.zmaxLine.text())),
            'show titles': self.showTitleChkBtn.isChecked()
            }

    def save_pickle(self):
        """Pickle current figure.

        Function that pickles the current pyplot.figure object of
        VisualApp and CustomFigCanvas to a .pickle file. Function creates
        title and name for file by the current settings for the plot.
        """
        if self.settings is None:
            self.statusbar.showMessage('No data selected')
            return
        name = self._get_savename()+'.pickle'
        outfile = os.path.join(self.folder, name)
        with open(outfile, 'wb') as out:
            pickle.dump(self.myfig.fig, out, protocol=pickle.HIGHEST_PROTOCOL)
        self.statusbar.showMessage('Figure pickled to file {}'.format(outfile))

    def save_hdf5(self):
        """Save in hdf5 format the current figure.

        Function that saves the current pyplot.figure object of
        VisualApp and CustomFigCanvas to a .hdf5 file. Function creates
        title and name for file by the current settings for the plot.
        """
        if self.settings is None:
            self.statusbar.showMessage('No data selected')
            return
        name = self._get_savename()+'.hdf5'
        outfile = os.path.join(self.folder, name)
        dd.io.save(outfile, self.myfig.fig)
        self.statusbar.showMessage('Figure saved as {}'.format(outfile))

    def save_json(self):
        """Save in json format the current figure.

        Function that saves the current pyplot.figure object of
        VisualApp and CustomFigCanvas to a .json file. Function creates
        title and name for file by the current settings for the plot.
        """
        if self.settings is None:
            self.statusbar.showMessage('No data selected')
            return
        name = self._get_savename()+'.json'
        outfile = os.path.join(self.folder, name)
        if self.settings['fol'] == 'All':
            x, y, z = self.dataobject._get_from_all()
        else:
            x, y, z = self.dataobject._get_from_single(self.settings['fol'])

        data = {'x': x, 'y': y, 'z': z, 'settings': self.settings}

        json.dump(data,
                  codecs.open(outfile, 'w', encoding='utf-8'),
                  separators=(',', ':'), sort_keys=True, indent=4)
        self.statusbar.showMessage('Figure saved as {}'.format(outfile))

    def save_png(self):
        """Save current figure as png.

        Function that saves the current plotted figure of VisualApp
        and CustomFigCanvas as a .png file.
        Function creates title and name for file by the current settings
        for the plot.
        """
        if self.settings is None:
            self.statusbar.showMessage('No data selected')
            return
        name = self._get_savename()+'.png'
        outfile = os.path.join(self.folder, name)
        self.myfig.fig.savefig(outfile)
        self.statusbar.showMessage('Figure saved: {}'.format(outfile))

    def save_textdata(self):
        """Save x, y, z data to file.

        Function that saves the current x, y, z data of the visualizer to
        a textfile for use in other operations, plotting, etc.
        """
        if self.settings is None:
            self.statusbar.showMessage('No data selected')
            return
        self.statusbar.showMessage('Saving figure data to file...')
        name = self._get_savename()+'.txt'
        outfile = os.path.join(self.folder, name)
        if self.settings['fol'] == 'All':
            x, y, z = self.dataobject._get_from_all()
        else:
            x, y, z = self.dataobject._get_from_single(self.settings['fol'])

        if not z:
            line = '\t{}\t\t{}\n'
            header = line.format(self.settings['op1'],
                                 self.settings['op2'])
        else:
            line = '\t{}\t\t{}\t\t{}\n'
            header = line.format(self.settings['op1'],
                                 self.settings['op2'],
                                 self.settings['E'])

        self.statusbar.showMessage('Writing file: {}'.format(outfile))
        with open(os.path.join(self.folder, outfile), 'w') as f:
            f.write(header)
            if not z:
                for i, j in zip(x, y):
                    f.write(line.format(i, j))
            else:
                for i, j, l in zip(x, y, z):
                    f.write(line.format(i, j, l))
        self.statusbar.showMessage('Figure data saved: {}!'.format(outfile))

    def save_script(self):
        """Make makefigure.py script.

        Function that generate and store the current plot from the GUI to
        a separate script file, that can re-generate a fairly similar
        figure to the GUI using stored settings.
        """
        if self.settings is None:
            self.statusbar.showMessage('No data selected')
            return
        datafile = self.iofile
        scriptfileformat = 'makefigure_{}_{}_{}_{}.py'
        self._get_settings()
        settings = self.settings
        # Text writes to makefigure.py
        txt = "# Makefigure script\n"
        if settings.get('fol') != 'All':
            if 'hdf5' in datafile:
                txt += "import deepdish\n"
            else:
                txt += "import pickle"
        txt += "import numpy as np\n"
        txt += "import matplotlib.pyplot as plt\n"
        txt += "from scipy.interpolate import griddata as scgriddata\n"
        txt += "\n"

        txt += "datafile = '{}'\n".format(datafile)
        if 'hdf5' in datafile:
            txt += "data = deepdish.io.load(datafile)\n"
        else:
            txt += "with open(datafile, 'rb') as pdata:\n"
            txt += "    data = pickle.load(pdata)\n"
        txt += "\n"

        txt += "# Dictionary with settings for data load and plotting:\n"
        txt += "settings = {}\n".format(settings)
        txt += "\n"

        if settings['fol'] == 'All':
            fol = []
            for f in next(os.walk(self.folder))[1]:
                if f[0] == '0':
                    fol.append(f)
        else:
            fol = [settings['fol']]
        txt += "fol = {}\n".format(fol)

        if settings['ACC'] == 'REJ':
            txt += "acc = 'r'\n"
        else:
            txt += "acc = 'a'\n"
        txt += "xl = '{}'\n".format(settings['op1'])
        txt += "yl = '{}'\n".format(settings['op2'])
        if settings['method'][0] == 'Density':
            index_data = 0
        else:
            index_data = 1
            txt += "zl = '{}'\n".format(settings['E'])
        txt += "\n"
        txt += "fig = plt.figure()\n"
        txt += "ax = fig.add_subplot(111)\n"
        txt += "fig.subplots_adjust(left=0.1, right=0.85, "
        txt += "bottom=0.1, top=0.9)\n"
        txt += "cbar_ax = fig.add_axes([0.86, 0.1, 0.03, 0.8])\n"
        txt += "\n"
        txt += "# Get x,y,z data\n"
        txt += "x, y, z = [], [], []\n"
        txt += "for f in fol:\n"
        txt += "    x.extend(data[{}][acc+xl, f])\n".format(index_data)
        txt += "    y.extend(data[{}][acc+yl, f])\n".format(index_data)
        res = settings['res']
        cmap = settings['colormap']
        if index_data == 1:
            txt += "    z.extend(data[{}][acc+zl, f])\n".format(index_data)
            txt += "\n"
            txt += "xi = np.linspace(min(x), max(x), {})\n".format(res)
            txt += "yi = np.linspace(min(y), max(y), {})\n".format(res)
            txt += "X, Y = np.meshgrid(xi, yi)\n"
            txt += "Z = scgriddata((x, y), np.array(z), (X, Y), "
            txt += "method='linear', fill_value=max(z))\n"
            txt += "\n"
            txt += "surf = ax.contourf(X,Y,Z, cmap='{}')\n".format(cmap)
            txt += "cbar = fig.colorbar(surf, cax=cbar_ax)\n"
        else:
            txt += "surf = ax.hist2d(x, y, bins={},".format(res)
            txt += " cmap='{}', density=True)\n".format(cmap)
            txt += "cbar = fig.colorbar(surf[3], cax=cbar_ax)\n"

        txt += "plt.show()"

        if index_data == 0:
            zl = 'Density'
        else:
            zl = settings['E']
        scriptfile = scriptfileformat.format(
            settings['op1'], settings['op2'], zl, settings['fol'])
        with open(os.path.join(self.folder, scriptfile), 'w') as f:
            f.write(txt)
        self.statusbar.showMessage('Script file saved: {}'.format(scriptfile))

    def _load_file(self):
        """Load data file.

        Function that sets up QObject, moves to QThread, and begins the
        data extract. Or, loads pre-processed data from file and
        moves to a QThread.
        """
        if self.folder is None and self.iofile is None:
            # When VisualApp is called without a directory, opens a filedialog
            iofile = QtWidgets.QFileDialog.getOpenFileName(
                parent=self,
                caption="Select input/output file in simulation directory")
            self.iofile = iofile[0]
            folder = os.path.dirname(os.path.realpath(self.iofile))
            self.folder = folder
            os.chdir(self.folder)
        # Setting name of file to QLineEdit of VisualApp
        self.filenameLine.setText(self.iofile)
        # Checking iofile type, *.rst, *hdf5 or *.pickle
        if 'rst' in self.iofile:
            self._load_data_output()
        elif any(('pickle' in self.iofile, 'hdf5' in self.iofile)):
            self._load_data(self.iofile)
        else:
            msg = 'Format Error, file {} not recognized.'.format(self.iofile)
            raise ValueError(msg)

    def _load_data_output(self):
        """Load simulation data.

        Function that loads simulation data using in/out file of simulation
        and initializes PathDensity on the directory, before showing the
        results in the VisualApp window.
        """
        self.statusbar.showMessage('Loading data from output files')
        # Set-up data object using PathDensity class and moving to thread
        self.thread = QtCore.QThread()
        self.dataobject = DataObject(iofile=self.iofile)
        # Connecting cycle print to update_cycle func
        self.dataobject.cycle_printed.connect(self.update_cycle)
        self.dataobject.return_coords.connect(self.update_fig)
        self.send_settings.connect(self.dataobject.get)
        self.start_cmd.connect(self.dataobject.walk)
        self.dataobject.moveToThread(self.thread)
        # Starting thread
        self.thread.start()
        # Starting QObject's walk_Dirs in thread
        self.start_cmd.emit('')

    def _load_data(self, pfile):
        """Load saved data.

        Function that loads simulation data from a pre-compiled
        file and initializes the VisualApp window for plotting said data.
        """
        self.statusbar.showMessage('Loading data from compressed file.')
        # Set-up data object using PathDensity class and moving to thread
        self.thread = QtCore.QThread()
        self.dataobject = VisualObject()
        # Connecting cycle print to update_cycle func
        self.dataobject.cycle_printed.connect(self.update_cycle)
        self.dataobject.return_coords.connect(self.update_fig)
        # Function takes pickle and hdf5 formats
        self.start_cmd.connect(self.dataobject.get_data)
        self.send_settings.connect(self.dataobject.get)
        self.dataobject.moveToThread(self.thread)
        # Starting thread
        self.thread.start()
        self.start_cmd.emit(pfile)

    def _reload(self):
        """Reload the data of VisualApp.

        Function that clears the old data of VisualApp and initializes
        the load of new.
        """
        self.folder, self.iofile = None, None
        self.dataobject = None
        self.toggle_buttons(False)
        self._load_file()

    def _init_widget(self):
        """Initialize QDropWidget.

        Function initializing the settings of the QDropWidget of VisualApp
        window. Adds correct items to the ComboBoxes of op1,op2 and E, and
        add the CustomFigCanvas object to the QFrame.
        If no folder or file is given when initializing VisualApp, a
        QFileDialog is opened to get file/folder.
        """
        # Actions and menubar
        self.actionExit.triggered.connect(self.close)
        # Save figure as ...
        self.action_png.triggered.connect(self.save_png)
        self.action_makefig_script.triggered.connect(self.save_script)
        self.action_pickle.triggered.connect(self.save_pickle)
        self.action_hdf5.triggered.connect(self.save_hdf5)
        self.action_json.triggered.connect(self.save_json)
        # Save figure data as ...
        self.action_datafile.triggered.connect(self.save_textdata)
        self.action_Load_data.triggered.connect(self.action_reload)
        self.statusbar.showMessage('No data loaded')
        # Connect show reg.line and interfaces, and method check
        self.intShowChkBtn.stateChanged.connect(self.toggle_intf)
        self.regLineChkBtn.stateChanged.connect(self.toggle_regl)
        self.cbarChkBtn.stateChanged.connect(self.toggle_cbar)
        self.showTitleChkBtn.stateChanged.connect(self.toggle_titles)
        self.plotTypeComBox.activated.connect(self.disable_zcombox)
        # The Frame
        self.mainFrame.setStyleSheet(
            "QWidget { background-color: %s }" % QtGui.QColor(
                210, 210, 235, 255).name()
            )
        self.layout_a = QtWidgets.QGridLayout()
        self.mainFrame.setLayout(self.layout_a)
        # The Figure
        self.myfig = CustomFigCanvas()
        self.layout_a.addWidget(self.myfig)
        # Setting up the dropwidget of VisualApp
        self.show()
        # Bind update button to function
        self.updateBtn.clicked.connect(self.emit_settings)
        self.saveFigBtn.clicked.connect(self.save_png)
        self.previewBtn.clicked.connect(self.update_preview)
        # Bind <ENTER>-press in colormap line to function
        self.cmapComBox.lineEdit().returnPressed.connect(self._change_cmap)
        # Bind changes to title and labels to functions
        self.titleSizeSpin.valueChanged.connect(self._update_canvas_font)
        self.axesSizeSpin.valueChanged.connect(self._update_canvas_font)
        self.titleLine.returnPressed.connect(self._update_canvas_text)
        self.xaxisLabel.returnPressed.connect(self._update_canvas_text)
        self.yaxisLabel.returnPressed.connect(self._update_canvas_text)
        self.zaxisLabel.returnPressed.connect(self._update_canvas_text)

    def _change_cmap(self):
        """Set colormap of surface.

        Function that tries to set the colormap of object myfig.surf (plot)
        Bound to detection of returnPress in colormap combo box.
        """
        meth = self.settings['method']
        col = self.cmapComBox.currentText()

        try:
            # Test if entered colormap is valid
            _ = plt.get_cmap(col)
            if meth[0] == 'Density':
                # Method is 2dhist-plot/list where 4th item is the plot/surf.
                self.myfig.surf[3].set_cmap(col)
            elif meth[0] == 'Scatter':
                # If scatter, replot.
                self.statusbar.showMessage(
                    'Scatter plots have to be re-drawn to update colors!')
            else:
                # Should work for most surf-objects.
                self.myfig.surf.set_cmap(col)
        except AttributeError:
            # If surf has no .set_cmap()
            self.statusbar.showMessage(
                'Could not recognize colormap, try to "Update" figure...')
        except TypeError:
            # If no surf-object, or NoneType in general
            self.statusbar.showMessage(
                'Figure not recognized, try to "Update" figure...')
        except ValueError:
            # Did not recognize 'col' in cm
            self.statusbar.showMessage(
                'Chosen colormap not recognized!')
        self.myfig.fig.canvas.draw()

    def _change_zoom(self):
        """Set the zoom/x-&y-limits of the plot."""
        self.statusbar.showMessage('Drawing figure...')
        if self.settings['dim'] == 3:
            self.myfig.ax.set_xlim3d(self.settings['x-limits'][0],
                                     self.settings['x-limits'][1])
            self.myfig.ax.set_ylim3d(self.settings['y-limits'][0],
                                     self.settings['y-limits'][1])
            self.myfig.ax.set_zlim3d(self.settings['z-limits'][0],
                                     self.settings['z-limits'][1])
        elif self.settings['dim'] == 2:
            self.myfig.ax.set_xlim(self.settings['x-limits'][0],
                                   self.settings['x-limits'][1])
            self.myfig.ax.set_ylim(self.settings['y-limits'][0],
                                   self.settings['y-limits'][1])
        # Change range on colorbar
        # Colorbar of contour plots does not scale, but color is updated
        norm = mpl.colors.Normalize(vmin=self.settings['z-limits'][0],
                                    vmax=self.settings['z-limits'][1])
        self.myfig.cbar.mappable.set_norm(norm=norm)
        self.myfig.cbar.draw_all()
        self.myfig.fig.canvas.draw()
        self.statusbar.showMessage('Plot ready!')

    def update_preview(self):
        """Update the visual of the plot.

        Button function, updates visual of plot based on all settings of
        'Plot'-tab in VisualApp.
        """
        self.statusbar.showMessage('Drawing figure...')
        self._get_settings()
        self._update_canvas_text()
        self._change_cmap()
        self._change_zoom()
        self.myfig.fig.canvas.draw()
        self.statusbar.showMessage('Plot ready!')

    # Defining button functions that toggle the visibility of:
    # interfaces, regression line, colorbar and title/axis labels.
    def toggle_intf(self):
        """Toggle interface visibility."""
        if self.intShowChkBtn.isChecked():
            for l in self.myfig.intf:
                l.set_visible(True)
        else:
            for l in self.myfig.intf:
                l.set_visible(False)
        self.myfig.fig.canvas.draw()

    def toggle_regl(self):
        """Toggle regression line and legend visibility."""
        if self.regLineChkBtn.isChecked() and self.settings['dim'] == 2:
            self.myfig.regl[0].set_visible(True)
            self.myfig.legend.set_visible(True)
        elif not self.regLineChkBtn.isChecked() and self.settings['dim'] == 2:
            self.myfig.regl[0].set_visible(False)
            self.myfig.legend.set_visible(False)
        self.myfig.fig.canvas.draw()

    def toggle_cbar(self):
        """Toggle colorbar visibility."""
        if self.cbarChkBtn.isChecked():
            self.myfig.cbar_ax.set_visible(True)
            self.myfig.fig.subplots_adjust(left=0.1, right=0.85,
                                           bottom=0.1, top=0.9)
        else:
            self.myfig.cbar_ax.set_visible(False)
            self.myfig.fig.subplots_adjust(left=0.1, right=0.90,
                                           bottom=0.1, top=0.9)
        self.myfig.fig.canvas.draw()

    def toggle_titles(self):
        """Toggle labels and titles visibility."""
        if self.showTitleChkBtn.isChecked():
            self.myfig.title.set_visible(True)
            self.myfig.xaxis.set_visible(True)
            self.myfig.yaxis.set_visible(True)
            self.myfig.zaxis.set_visible(True)
        else:
            self.myfig.title.set_visible(False)
            self.myfig.xaxis.set_visible(False)
            self.myfig.yaxis.set_visible(False)
            self.myfig.zaxis.set_visible(False)
        self.myfig.fig.canvas.draw()

    def emit_settings(self):
        """Update settings before sending to the dataobject.

        Function calls for an update of data/plot settings before sending
        dictionary to dataobject in mainworker to update the data lists
        x,y,(z).
        """
        self.toggle_buttons(False)
        # Updating statusbar of VisualApp window
        self.statusbar.showMessage('Updating data...')
        self._get_settings()

        if 'Contour' in self.settings['method'] and \
           self.settings['E'] == 'None':
            self.statusbar.showMessage('Invalid combination, '
                                       'contours need z-values')
            self.toggle_buttons(True)
        else:
            self.send_settings.emit(self.settings)

    @QtCore.pyqtSlot(list)
    def update_cycle(self, cycles):
        """Set upper and lower bound of cycles for data loading.

        Function bound to pyqtSignal from DataObject in QThread, sets upper
        and lower bound of cycles for data loading, and enables 'Update'
        QPushButton when finished.
        """
        # Adding items to ComboBoxes in VisualApp.Window
        self.firstOpComBox.clear()
        self.firstOpComBox.addItems(self.dataobject.infos['op_labels'])
        self.firstOpComBox.addItem('timo')
        self.secondOpComBox.clear()
        self.secondOpComBox.addItems(self.dataobject.infos['op_labels'])
        self.secondOpComBox.addItem('timo')
        self.secondOpComBox.insertSeparator(
            len(self.dataobject.infos['op_labels']) + 1)
        la = []
        for l in ENERGYLABELS:
            if l not in self.dataobject.infos['op_labels']:
                la.append(l)
        self.secondOpComBox.addItems(la)
        self.energyComBox.clear()
        self.energyComBox.addItems(ENERGYLABELS)
        self.energyComBox.addItems(['None'])
        self.folderComBox.clear()
        self.folderComBox.addItems(self.dataobject.infos['path'])
        self.folderComBox.insertSeparator(len(self.dataobject.infos['path'])+1)
        self.folderComBox.addItem('All')
        # Setting cycles in dropwidget
        minc, maxc = cycles[0], cycles[1]
        self.minCyclSpin.setRange(minc, maxc)
        self.maxCyclSpin.setRange(minc, maxc)
        self.minCyclSpin.setValue(minc)
        self.maxCyclSpin.setValue(maxc)
        # Enables the buttons and updates status
        self.statusbar.showMessage(
            'All {} '.format(maxc-minc) +
            'cycles loaded from files, ready to plot!')
        self.updateBtn.setEnabled(True)

    @QtCore.pyqtSlot(list, list, list)  # noqa: C901
    def update_fig(self, x, y, z):
        """Update figure by pyqtSignal.

        Function that updates figure canvas of CustomFigCanvas and the
        colorbar. Initiated by pyqtSignal from running QThread.
        Function checks method chosen in GUI and calls on built-in functions
        of orderparam_density module to generate a surface/contour/scatter/etc.
        If checked, function also plots interfaces and regression line.

        Parameters
        ----------
        x,y,z : list
            Floats, the coordinates used in plotting.

        Updates/Draws
        -------------
        self.myfig.fig : Re-draws canvas with method, data, and possible
            interfaces, reg.line and legend.
        self.myfig.ax : As above. (Axes containing plot, legend, lines, etc)
        self.myfig.cbar_ax : Axes with colorbar of plot.

        """
        self.statusbar.showMessage('Drawing figure...')

        l_x, l_y, l_z = len(x), len(y), len(z)
        if self.settings['method'][0] != 'Density' and \
                l_x == 0 or l_y == 0:
            self.statusbar.showMessage(
                'One (or more) lists are empty, plotting halted!' +
                'x: {}, y: {}'.format(l_x, l_y))
            self.updateBtn.setEnabled(True)
            return
        elif self.settings['method'][0] != 'Density' and \
                (l_x != l_z or l_y != l_z):
            self.statusbar.showMessage(
                'Lists have different lengths! ' +
                'x: {}, y: {}, z: {}'.format(l_x, l_y, l_z))
            self.updateBtn.setEnabled(True)
            return
        elif not x or not y:
            self.statusbar.showMessage(
                'One (more) OP lists empty, nothing to plot! ' +
                'x: {}, y: {}'.format(l_x, l_y))
            self.updateBtn.setEnabled(True)
            return
        elif self.settings['dim'] == 3 and not z:
            self.statusbar.showMessage('Energy list empty, nothing to plot!')
            self.updateBtn.setEnabled(True)
            return

        # Do a myfig.set_up(), in case dim/projection has changed
        self.myfig.set_up(dim=self.settings['dim'],
                          cbar=self.settings['colorbar'])
        # Setting default xlim and ylim
        xmin, xmax = min(x), max(x)
        ymin, ymax = min(y), max(y)
        if len(z) > 0:
            zmin, zmax = min(z), max(z)
        else:
            zmin, zmax = 0, 0
        self.xminLine.setText(str(xmin))
        self.xmaxLine.setText(str(xmax))
        self.yminLine.setText(str(ymin))
        self.ymaxLine.setText(str(ymax))
        self.zminLine.setText(str(zmin))
        self.zmaxLine.setText(str(zmax))

        if self.settings['dim'] == 3:
            plot = self.settings['method'][0].lower()
            if self.settings['method'][-1] == '(filled)':
                plot = plot+'f'
            else:
                pass
            self.myfig.surf, self.myfig.cbar = gen_surface(
                x, y, z,
                self.myfig.fig,
                self.myfig.ax,
                cbar_ax=self.myfig.cbar_ax,
                dim=self.settings['dim'],
                method=plot,
                resX=self.settings['res'],
                resY=self.settings['res'],
                colormap=self.settings['colormap'])
        elif self.settings['dim'] == 2:
            if self.settings['method'][0] == 'Density':
                self.myfig.surf = self.myfig.ax.hist2d(
                    x, y, (self.settings['res'], self.settings['res']),
                    cmap=self.settings['colormap'], density=True)
                self.myfig.cbar = self.myfig.fig.colorbar(
                        self.myfig.surf[3], cax=self.myfig.cbar_ax)
                # Set zmax equal to max value in histogram
                self.zmaxLine.setText(str(self.myfig.surf[0].max()))
            else:
                plot = self.settings['method'][0].lower()
                if self.settings['method'][-1] == '(filled)':
                    plot = plot+'f'
                else:
                    pass
                self.myfig.surf, self.myfig.cbar = gen_surface(
                    x, y, z,
                    self.myfig.fig,
                    self.myfig.ax,
                    cbar_ax=self.myfig.cbar_ax,
                    dim=self.settings['dim'],
                    method=plot,
                    resX=self.settings['res'],
                    resY=self.settings['res'],
                    colormap=self.settings['colormap'])
        # TODO make function "update extras" or similar of code below here
        # Showing interface planes(3D)/lines(2D)
        self.myfig.intf = []
        if self.settings['op1'] == 'op1' and self.settings['dim'] == 3:
            for i in self.dataobject.infos['interfaces']:
                if i > xmax:
                    break
                self.myfig.intf.append(
                    plot_int_plane(self.myfig.ax,
                                   i, ymin, ymax,
                                   min(z), max(z),
                                   visible=self.settings['show_int']))
        elif self.settings['op1'] == 'op1' and self.settings['dim'] == 2:
            for i in self.dataobject.infos['interfaces']:
                if i > xmax:
                    break
                self.myfig.intf.append(
                    self.myfig.ax.axvline(i, linewidth=1,
                                          color='grey', alpha=0.5,
                                          visible=self.settings['show_int']))
        # Showing regression line(2D only)
        self.myfig.regl = []
        if self.settings['dim'] == 2:
            self.myfig.regl = plot_regline(self.myfig.ax, x, y)
            self.myfig.regl[0].set_visible(self.settings['reg_line'])
            self.myfig.legend = self.myfig.ax.legend()
            self.myfig.legend.set_visible(self.settings['reg_line'])
            self.myfig.cbar_ax.set_visible(self.settings['colorbar'])
        self._get_titles()
        # Update CustomFigure canvas and status
        self.myfig.fig.canvas.draw()
        self.statusbar.showMessage('Plot ready!')
        self.toggle_buttons(True)


class CustomFigCanvas(FigureCanvas):
    """
    Class definition of the custom figure canvas used in VisualApp.

    Attributes
    ----------
    self.surf : Placeholder for object shown in main subplot of figure.
    self.cb : Placeholder for colorbar.
    self.ax : Main subplot (Axes object) of CustomFigCanvas.
    self.cbar_ax : Subplot (Axes object) of colorbar in CustomFigCanvas.
    self.intf : Placeholder for list of interface lines/planes in figure.
    self.regl : Placeholder for 2D regression line in figure.
    self.legend : Placeholder for legend in figure.
    self.title : Placeholder for the figure title.
    self.{x/y/z}axis : Placeholder for the x/y/z-axis labels.

    """

    def __init__(self,):
        """Initialize the FigureCanvas class."""
        self.fig = Figure()
        FigureCanvas.__init__(self, self.fig)
        self.surf = None
        self.cb = None
        self.cbar = None
        self.intf = None
        self.regl = None
        self.legend = None
        self.title = None
        self.xaxis, self.yaxis, self.zaxis = None, None, None
        self.set_up()

    def set_up(self, dim=2, cbar=True):
        """Define subplot projection (2D/3D).

        Function that defines the main subplot's projection (2D/3D)
        depending on chosen method from VisualApp GUI.

        Parameters
        ----------
        dim : integer, default=2
              Dimension/projection of main subplot.

        """
        # The Figure
        self.fig.clf()
        # Subplots, depending on dimension/projection
        if dim == 3:
            self.ax = self.fig.add_subplot(111, projection='3d')
        elif dim == 2:
            self.ax = self.fig.add_subplot(111)
        # Axes for colorbar
        self.cbar_ax = self.fig.add_axes([0.86, 0.1, 0.03, 0.8])
        if cbar:
            self.fig.subplots_adjust(left=0.1, right=0.85, bottom=0.1, top=0.9)
            self.cbar_ax.set_visible(True)
        else:
            self.fig.subplots_adjust(left=0.1, right=0.90, bottom=0.1, top=0.9)
            self.cbar_ax.set_visible(False)


class DataSlave(QtCore.QObject, PathVisualize):
    """QObject class definition that holds the PathDensity data.

    By pyqtSignals this object can be called upon to either do a directory
    "walk" to collect data, or get specific data into lists by specific
    settings.

    Attributes
    ----------
    Contains the same attributes as the PathDensity() class of
    orderparam_density.py in source.

    Signals
    -------
    cycle_printed : PyQt Signal, sends a list of min and max cycle number to
        the VisualApp to update the dropwidget with correct values.
    returns_coords : PyQt Signal, sends three lists of coords (or empty)
        to the VisualApp to update the figure.

    Slots
    -----
    walk : PyQt Slot connected to VisualApp. When activated with a string,
        initializes the walk_Dirs() function of DataObject/PathDensity
        class. At end of function, emits list of cycles to signal
        cycle_printed.
    get : PyQt Slot connected to VisualApp. When activated with a dictionary
        with relevant plotting settings, preforms a data fetch of either
        get_Edata or get_Odata on DataObject/PathDensity class.
        At end of function, emits lists of coords to signal return_coords.

    """

    return_coords = QtCore.pyqtSignal(list, list, list)

    def __init__(self, iofile=None):
        """Initialize the QObject class and classes inherited."""
        self.iofile = iofile
        QtCore.QObject.__init__(self)
        PathVisualize.__init__(self)
        self.settings = {}

    def _get_from_all(self):
        """Loop over all folders for data."""
        x, y, z = [], [], []
        for fol in self.infos['path']:
            xi, yi, zi = self._get_from_single(fol)
            x.extend(xi)
            y.extend(yi)
            z.extend(zi)
        return x, y, z

    def _get_from_single(self, fol):
        """Load data from folder, either OP or E data."""
        if self.settings['dim'] == 2 and \
           self.settings['op2'] not in ENERGYLABELS and \
           self.settings['method'][0] == 'Density':

            z = []
            x, y = self.get_Odata(fol,
                                  [self.settings['op1'], self.settings['op2'],
                                   self.settings['ACC']],
                                  weight=self.settings['weight'],
                                  min_max=[self.settings['min_cycle'],
                                           self.settings['max_cycle']])

        else:
            x, y, z = self.get_Edata(fol,
                                     [self.settings['op1'],
                                      self.settings['op2'],
                                      self.settings['E']],
                                     self.settings['ACC'],
                                     min_max=[self.settings['min_cycle'],
                                              self.settings['max_cycle']])
        return x, y, z

    @QtCore.pyqtSlot(dict)
    def get(self, settings):
        """Signal emission to get xyz data from settings in VisualApp."""
        self.settings = settings
        if self.settings['fol'] == 'All':
            # Loop over all folders in thread mainworkers data.path
            x, y, z = self._get_from_all()
        else:
            # Get data of folder=self.fol
            x, y, z = self._get_from_single(self.settings['fol'])

        # If allowing datashift
        if self.settings['try_shift']:
            op1 = self.settings['op1']
            x, y = try_data_shift(x, y, op1)
        self.return_coords.emit(x, y, z)


class VisualObject(DataSlave):
    """DataSlave class used by VisualApp to load data from compressed file."""

    cycle_printed = QtCore.pyqtSignal(list)

    def __init__(self, pfile=None):
        """Initialize the class and classes inherited."""
        self.pfile = pfile
        DataSlave.__init__(self)
        self.settings = {}

    @QtCore.pyqtSlot(str)
    def get_data(self, pfile):
        """Signal emission for loading data from file."""
        self.pfile = pfile
        if 'pickle' in pfile:
            self.load_pickle()
        elif 'hdf5' in pfile:
            self.load_dd()
        else:
            raise ValueError('Format not recognized')

        cycles = [int(self.infos['long_cycle'][0]),
                  int(self.infos['long_cycle'][-1])]
        self.cycle_printed.emit(cycles)


class DataObject(DataSlave, PathDensity):
    """DataSlave class used by VisualApp to load data from PyRETIS input."""

    cycle_printed = QtCore.pyqtSignal(list)

    def __init__(self, iofile=None):
        """Initialize the class and classes inherited."""
        DataSlave.__init__(self, iofile=iofile)
        PathDensity.__init__(self, iofile=iofile)

    @QtCore.pyqtSlot(str)
    def walk(self):
        """Signal emission to begin 'walk' of simulation directory."""
        self.walk_dirs()
        cycles = [int(self.infos['long_cycle'][0]),
                  int(self.infos['long_cycle'][-1])]
        self.cycle_printed.emit(cycles)


class NumpyEncoder(json.JSONEncoder):
    """Set json codecs for numpy."""

    def default(self, obj):
        """Fix ndarray."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def visualize_main(rpath, infile):
    """Run the VisualApp application."""
    app = QtWidgets.QApplication(sys.argv)
    window = VisualApp(folder=rpath, iofile=infile)
    window.show()
    sys.exit(app.exec_())
