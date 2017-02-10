# -*- coding: utf-8 -*-
# Copyright (c) 2015, pyretis Development Team.
# Distributed under the LGPLv3 License. See LICENSE for more info.
"""This package contains methods for generating reports.

The reports will typically summarize the results from different
analysis and present it as a text file, pdf or web-page.

Package structure
-----------------

Modules
~~~~~~~

__init__.py
    This file, handles imports for pyretis and defines a method for
    writing a report to a file.

markup.py (:py:mod:`pyretis.inout.report.markup`)
    This module defines some methods for generating simple tables and
    formatting numbers for rst and latex.

report.py (:py:mod:`pyretis.inout.report.report`)
    General methods for generating reports.

report_md.py (:py:mod:`pyretis.inout.report.report_md`)
    This module defines the molecular dynamics reports. Specifically
    it defines the report that is made based on results from a MD Flux
    simulations.

report_path.py (:py:mod:`pyretis.inout.report.report_path`)
    This module defines the reports for path simulations like TIS and
    RETIS.


Important methods defined here
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

generate_report (:py:func:`.generate_report`)
    Method for generating reports.

Folders
~~~~~~~

templates
    A folder containing templates for generating reports:

    * :download:`report_mdflux.rst <templates/report_mdflux.rst`.
    * :download:`report_mdflux.tex <templates/report_mdflux.tex`.
    * :download:`report_mdflux.txt <templates/report_mdflux.txt`.
    * :download:`report_retis0.txt <templates/report_retis0.txt`.
    * :download:`report_retis.rst <templates/report_retis.rst`.
    * :download:`report_retis.tex <templates/report_retis.tex`.
    * :download:`report_tis.rst <templates/report_tis.rst`.
    * :download:`report_tis.tex <templates/report_tis.tex`.
    * :download:`report_tis.txt <templates/report_tis.txt`.
    * :download:`report_tis_single.rst <templates/report_tis_single.rst`.
    * :download:`report_tis_single.tex <templates/report_tis_single.tex`.
    * :download:`report_tis_single.txt <templates/report_tis_single.txt`.
"""
from .report import generate_report
