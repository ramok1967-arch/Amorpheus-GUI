# -*- coding: utf-8 -*-
"""Wspolne elementy GUI: wykres matplotlib, watek roboczy, panel parametrow."""
from __future__ import annotations

import os
import traceback
from pathlib import Path

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from ..data import Params, FILE_FORMATS, load_init, save_init, file_q_range
from .. import physics as ph
from ..i18n import tr  # noqa: E402


# --------------------------------------------------------------------------------------
class PlotWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, figsize=(8, 6)):
        super().__init__(parent)
        self.fig = Figure(figsize=figsize, constrained_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.toolbar)
        lay.addWidget(self.canvas)
        self.placeholder(tr("Brak danych do wyświetlenia"))

    def placeholder(self, text):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, text, ha="center", va="center", color="#888", fontsize=12, transform=ax.transAxes)
        ax.set_axis_off()
        self.canvas.draw_idle()

    def draw(self, fn, *a, **kw):
        try:
            fn(self.fig, *a, **kw)
        except Exception as e:
            self.placeholder(tr('Błąd wykresu: {0}').format(e))
        self.canvas.draw_idle()


# --------------------------------------------------------------------------------------
class Context(QtCore.QObject):
    """Przekazywany do funkcji liczacej w watku."""
    progress = QtCore.pyqtSignal(int, int, str)
    partial = QtCore.pyqtSignal(object)
    message = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def cancelled(self):
        return self._cancel

    def report(self, i, n, txt=""):
        self.progress.emit(int(i), int(n), str(txt))

    def log(self, txt):
        self.message.emit(str(txt))


class Worker(QtCore.QThread):
    finished_ok = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn
        self.ctx = Context()

    def run(self):
        try:
            res = self.fn(self.ctx)
            self.finished_ok.emit(res)
        except Exception as e:
            self.failed.emit(f"{e}\n\n{traceback.format_exc()}")


# --------------------------------------------------------------------------------------
def dspin(lo, hi, dec, step, val=0.0, suffix=""):
    w = QtWidgets.QDoubleSpinBox()
    w.setRange(lo, hi)
    w.setDecimals(dec)
    w.setSingleStep(step)
    w.setValue(val)
    w.setKeyboardTracking(False)
    if suffix:
        w.setSuffix(" " + suffix)
    w.setAlignment(Qt.AlignRight)
    return w


def ispin(lo, hi, val):
    w = QtWidgets.QSpinBox()
    w.setRange(lo, hi)
    w.setValue(val)
    w.setAlignment(Qt.AlignRight)
    return w


class FileEdit(QtWidgets.QWidget):
    changed = QtCore.pyqtSignal()

    def __init__(self, caption, filt=None, folder=False):
        super().__init__()
        filt = filt or tr("Dane (*.dat *.xy *.txt *.chi *.csv);;Wszystkie (*)")
        self.caption, self.filt, self.folder = caption, filt, folder
        self.edit = QtWidgets.QLineEdit()
        self.btn = QtWidgets.QToolButton()
        self.btn.setText("…")
        self.btn.clicked.connect(self.browse)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.edit, 1)
        lay.addWidget(self.btn)
        self.edit.editingFinished.connect(self.changed.emit)
        self.start_dir = ""

    def browse(self):
        start = self.text() or self.start_dir
        if self.folder:
            f = QtWidgets.QFileDialog.getExistingDirectory(self, self.caption, start)
        else:
            f, _ = QtWidgets.QFileDialog.getOpenFileName(self, self.caption, start, self.filt)
        if f:
            self.edit.setText(os.path.normpath(f))
            self.changed.emit()

    def text(self):
        return self.edit.text().strip()

    def setText(self, t):
        self.edit.setText(t)


# --------------------------------------------------------------------------------------
PANEL_STYLE = """
#paramsBody QGroupBox { margin-top: 10px; padding: 8px 5px 5px 5px; border-radius: 6px; }
#paramsBody QGroupBox::title { left: 6px; padding: 0 3px; }
#paramsBody QGroupBox::indicator { width: 11px; height: 11px; }
#paramsBody QPushButton { padding: 3px 10px; border-radius: 4px; }
#paramsBody QLineEdit, #paramsBody QComboBox { padding: 1px 3px; }
#paramsBody QAbstractSpinBox { padding: 0 2px; }
#paramsBody QToolButton { padding: 0 3px; }
#paramsBody QHeaderView::section { padding: 1px 3px; }
"""


def compact_form(g):
    f = QtWidgets.QFormLayout(g)
    f.setContentsMargins(6, 4, 6, 4)
    f.setHorizontalSpacing(10)
    f.setVerticalSpacing(6)
    f.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    f.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
    return f


def compact_combo(c, minlen=8):
    c.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
    c.setMinimumContentsLength(minlen)
    c.view().setMinimumWidth(c.view().sizeHintForColumn(0) + 24)
    return c


class Collapsible(QtWidgets.QGroupBox):
    """Grupa zwijana kliknieciem w tytul (checkbox w naglowku)."""

    def __init__(self, title, expanded=True):
        super().__init__(title)
        self.setCheckable(True)
        self.setChecked(expanded)
        self.toggled.connect(self._toggle)

    def _toggle(self, on):
        for w in self.findChildren(QtWidgets.QWidget, options=Qt.FindDirectChildrenOnly):
            w.setVisible(on)
        self.setFlat(not on)


class ParamsPanel(QtWidgets.QScrollArea):
    """Wszystkie parametry z Init.txt + opcje dodatkowe."""
    params_changed = QtCore.pyqtSignal()
    loaded = QtCore.pyqtSignal()
    open_data_requested = QtCore.pyqtSignal()
    log = QtCore.pyqtSignal(str)

    N_EL = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QtWidgets.QWidget()
        body.setObjectName("paramsBody")
        body.setStyleSheet(PANEL_STYLE)
        self.setWidget(body)
        v = QtWidgets.QVBoxLayout(body)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(8)
        self.base_dir = ""
        self.init_path = ""

        # --- Init.txt -------------------------------------------------------------
        hb = QtWidgets.QHBoxLayout()
        self.btn_load = QtWidgets.QPushButton(tr("Otwórz dane…"))
        self.btn_load.setObjectName("primary")
        self.btn_load.setToolTip(tr("Wybierz plik danych (i tła) – parametry zostaną odczytane z pliku,\n"
                                 "a projekt <dane>_Init.txt utworzony obok danych."))
        self.btn_save = QtWidgets.QPushButton(tr("Zapisz"))
        self.btn_save.setToolTip(tr("Zapisuje parametry do pliku projektu (zapis odbywa się też automatycznie\n"
                                 "przy każdym uruchomieniu obliczeń i przy zamknięciu programu)."))
        self.btn_load.clicked.connect(self.open_data_requested.emit)
        self.btn_save.clicked.connect(lambda: self.save_project(quiet=False))
        hb.addWidget(self.btn_load)
        hb.addWidget(self.btn_save)
        v.addLayout(hb)
        self.lbl_init = QtWidgets.QLabel("—")
        self.lbl_init.setObjectName("hint")
        self.lbl_init.setWordWrap(True)
        v.addWidget(self.lbl_init)

        # --- pliki ---------------------------------------------------------------
        g = QtWidgets.QGroupBox(tr("Dane"))
        f = compact_form(g)
        self.f_data = FileEdit(tr("Plik danych"))
        self.f_bkg = FileEdit(tr("Plik tła"))
        self.c_format = QtWidgets.QComboBox()
        for k, t in FILE_FORMATS.items():
            self.c_format.addItem(f"{k}: {t}", k)
        self.c_incoh = QtWidgets.QComboBox()
        self.c_incoh.addItem(tr("1: pusta kom."), 1)
        self.c_incoh.addItem(tr("0: na próbce"), 0)
        self.c_incoh.setToolTip(tr("1: tło z pustej komórki (Compton odejmowany)\n0: tło zmierzone na próbce"))
        self.s_lambda = dspin(1e-5, 10, 6, 0.0001, 0.03738, "nm")
        self.c_qunit = QtWidgets.QComboBox()
        self.c_qunit.addItem("Å⁻¹", "A")
        self.c_qunit.addItem(tr("nm⁻¹"), "nm")
        self.c_qunit.setToolTip(tr("Jednostka osi Q w pliku danych (formaty 3 i 4)"))
        f.addRow(tr("Dane"), self.f_data)
        f.addRow(tr("Tło"), self.f_bkg)
        f.addRow(tr("Format"), self.c_format)
        f.addRow(tr("Jedn. Q"), self.c_qunit)
        f.addRow(tr("Incoh."), self.c_incoh)
        f.addRow("λ", self.s_lambda)
        self.lbl_range = QtWidgets.QLabel("")
        self.lbl_range.setObjectName("hint")
        self.lbl_range.setWordWrap(True)
        f.addRow("", self.lbl_range)
        v.addWidget(g)

        # --- zakresy -------------------------------------------------------------
        g = QtWidgets.QGroupBox(tr("Zakresy i start"))
        f = compact_form(g)
        self.s_qmin = dspin(0.01, 1000, 3, 0.5, 15, "nm⁻¹")
        self.s_qmax = dspin(0.01, 1000, 3, 1, 78, "nm⁻¹")
        self.btn_qfile = QtWidgets.QPushButton(tr("q z pliku"))
        self.btn_qfile.setToolTip(tr("Ustaw q_min i q_max na pełny zakres danych w pliku"))
        self.btn_qfile.clicked.connect(self.q_from_file)
        self.s_rmin = dspin(0.001, ph.FIT_R_MAX, 4, 0.005, 0.22, "nm")
        self.s_rho = dspin(1, 500, 4, 0.1, 34.68, "at/nm³")
        self.s_bk = dspin(ph.BK_BOUNDS[0], ph.BK_BOUNDS[1], 5, 0.001, 0.927)
        f.addRow(tr("q_min"), self.s_qmin)
        f.addRow(tr("q_max"), self.s_qmax)
        f.addRow("", self.btn_qfile)
        f.addRow(tr("r_min"), self.s_rmin)
        f.addRow("ρ", self.s_rho)
        f.addRow(tr("bkfactor"), self.s_bk)
        v.addWidget(g)

        # --- sklad ---------------------------------------------------------------
        g = QtWidgets.QGroupBox(tr("Skład (ułamki at.)"))
        lay = QtWidgets.QVBoxLayout(g)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(6)
        self.t_comp = QtWidgets.QTableWidget(self.N_EL, 2)
        self.t_comp.setHorizontalHeaderLabels([tr("Pierw."), tr("Udział")])
        hh = self.t_comp.horizontalHeader()
        hh.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        hh.resizeSection(0, 62)
        hh.resizeSection(1, 80)
        self.t_comp.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        vh = self.t_comp.verticalHeader()
        vh.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        vh.setDefaultSectionSize(19)
        vh.setMinimumSectionSize(17)
        vh.setVisible(False)
        self.t_comp.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._fit_comp_height()
        self.t_comp.itemChanged.connect(self._comp_changed)
        hb = QtWidgets.QHBoxLayout()
        hb.setSpacing(10)
        hb.addWidget(self.t_comp, 0, Qt.AlignTop)
        side = QtWidgets.QVBoxLayout()
        side.setSpacing(6)
        self.lbl_sum = QtWidgets.QLabel()
        self.btn_auto = QtWidgets.QPushButton(tr("Do 1"))
        self.btn_auto.setToolTip(tr("Ustawia udział zaznaczonego pierwiastka tak, aby suma = 1"))
        self.btn_auto.clicked.connect(self.autofill)
        side.addWidget(QtWidgets.QLabel(tr("suma:")))
        side.addWidget(self.lbl_sum)
        side.addWidget(self.btn_auto)
        side.addStretch(1)
        hb.addLayout(side)
        hb.addStretch(1)
        lay.addLayout(hb)
        v.addWidget(g)

        # --- opcje ---------------------------------------------------------------
        g = Collapsible(tr("Opcje obliczeń"), True)
        f = compact_form(g)
        self.c_sofq = QtWidgets.QComboBox()
        self.c_sofq.addItem(tr("1: = S(q_min)"), 1)
        self.c_sofq.addItem("0: = 0", 0)
        self.c_sofq.addItem(tr("2: lorentz. (niestabilne)"), 2)
        self.c_sofq.setToolTip(tr("S(q) poniżej q_min.\n1: S(q<q_min) = S(q_min)\n0: S(q<q_min) = 0\n2: lorentzówka – NIESTABILNE, tylko diagnostyka\nZalecane: 1. Opcja 2 jest ukryta w oryginale (dopasowanie lorentzowki z na sztywno\n"
                               "wpisanym startem); zwykle psuje dopasowanie gęstości."))
        self.c_sofq.currentIndexChanged.connect(self._sofq_warn)
        self.c_norm = QtWidgets.QComboBox()
        self.c_norm.addItem(tr("0: standardowa"), 0)
        self.c_norm.addItem("1: z M(Q,Δ(r))", 1)
        self.c_norm.setToolTip(tr("1: z funkcją modyfikującą M(Q,Δ(r)) (Lorch, zmienna szerokość)"))
        self.s_iter = ispin(0, 50, 4)
        self.s_rmax = dspin(0.2, 5, 2, 0.1, 1.0, "nm")
        self.ch_fix = QtWidgets.QCheckBox(tr("Poprawka jedn. (zalec.)"))
        self.ch_fix.setChecked(True)
        self.ch_fix.setToolTip(tr("Zalecane. Odznaczenie = wyniki identyczne z oryginałem v1.0.5,\n"
                               "w którym człon gęstości w regule sum był 10× za mały."))
        self.ch_qstep = QtWidgets.QCheckBox(tr("QStep (2θ)"))
        self.ch_qstep.setToolTip(tr("Stały krok dq – diagnostyka; tylko dla danych w 2θ"))
        f.addRow(tr("S(q<q_min)"), self.c_sofq)
        f.addRow(tr("Normalizacja"), self.c_norm)
        f.addRow(tr("Iteracje"), self.s_iter)
        f.addRow(tr("r_max wyn."), self.s_rmax)
        f.addRow(self.ch_fix)
        f.addRow(self.ch_qstep)
        v.addWidget(g)

        # --- zapis ---------------------------------------------------------------
        g = Collapsible(tr("Zapis wyników"), False)
        self.g_save = g
        f = compact_form(g)
        self.f_out = FileEdit(tr("Folder wyników"), folder=True)
        self.e_norm = QtWidgets.QLineEdit("Norm")
        self.e_rmin = QtWidgets.QLineEdit("MinRmin")
        self.e_qmax = QtWidgets.QLineEdit("MinQmax")
        self.s_dpi = ispin(50, 1200, 300)
        self.ch_overwrite = QtWidgets.QCheckBox(tr("Nadpisuj pliki"))
        f.addRow(tr("Folder"), self.f_out)
        f.addRow(tr("Prefiks norm."), self.e_norm)
        f.addRow(tr("Prefiks r_min"), self.e_rmin)
        f.addRow(tr("Prefiks q_max"), self.e_qmax)
        f.addRow(tr("DPI"), self.s_dpi)
        f.addRow(self.ch_overwrite)
        v.addWidget(g)
        v.addStretch(1)
        for c in (self.c_format, self.c_incoh, self.c_qunit, self.c_sofq, self.c_norm):
            compact_combo(c)
        g._toggle(False)
        for sb in body.findChildren(QtWidgets.QAbstractSpinBox):
            sb.setFixedHeight(24)
            sb.setMaximumWidth(min(sb.sizeHint().width(), 135))
            sb.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)

        for w in (self.c_format,):
            w.currentIndexChanged.connect(self._format_changed)
        for w in (self.f_data, self.f_bkg):
            w.changed.connect(self._files_changed)
        self.s_lambda.valueChanged.connect(self._files_changed)
        self.c_qunit.currentIndexChanged.connect(self._files_changed)
        self.set_params(Params())
        self._format_changed()

    # ------------------------------------------------------------------------------
    def _format_changed(self):
        ff = self.c_format.currentData()
        self.f_bkg.setEnabled(ff in (2, 4))
        self.s_lambda.setEnabled(ff in (1, 2))
        self.c_qunit.setEnabled(ff in (3, 4))
        self.s_bk.setEnabled(ff in (2, 4))
        self.ch_qstep.setEnabled(ff in (1, 2))
        self._files_changed()

    def _files_changed(self):
        try:
            p = self.params()
            lo, hi = file_q_range(p)
            self.lbl_range.setText(tr('zakres w pliku: q = {0:.3f} – {1:.3f} nm⁻¹').format(lo, hi))
            self.file_range = (lo, hi)
        except Exception as e:
            self.lbl_range.setText(f"⚠ {str(e)[:90]}")
            self.file_range = None
        self.params_changed.emit()

    def _sofq_warn(self):
        if self.c_sofq.currentData() == 2:
            self.log.emit(tr("UWAGA: SofQ = 2 (lorentzowka) jest niestabilne - dopasowanie rho moze uciec do granicy. "
                          "Zalecane SofQ = 1."))

    def q_from_file(self):
        self._files_changed()
        if self.file_range:
            lo, hi = self.file_range
            self.s_qmin.setValue(np.ceil(lo * 1000) / 1000)
            self.s_qmax.setValue(np.floor(hi * 1000) / 1000)

    def _fit_comp_height(self):
        t = self.t_comp
        for r in range(t.rowCount()):
            t.setRowHeight(r, 22)
        h = t.horizontalHeader().sizeHint().height() + sum(t.rowHeight(r) for r in range(t.rowCount()))
        t.setFixedHeight(h + 2 * t.frameWidth() + 2)
        hh = t.horizontalHeader()
        t.setFixedWidth(hh.sectionSize(0) + hh.sectionSize(1) + 2 * t.frameWidth() + 2)

    def _panel_width(self):
        return (self.widget().minimumSizeHint().width() + self.verticalScrollBar().sizeHint().width()
                + 2 * self.frameWidth() + 2)

    def minimumSizeHint(self):
        return QtCore.QSize(self._panel_width(), 200)

    def sizeHint(self):
        return QtCore.QSize(self._panel_width(), 600)

    def showEvent(self, ev):
        super().showEvent(ev)
        self._fit_comp_height()
        self.setMinimumWidth(self._panel_width())

    def _comp_changed(self, *a):
        try:
            _, c = self.params().active_composition()
            s = c.sum()
            ok = abs(s - 1) < 1e-4
            self.lbl_sum.setText(f"{s:.4f} {'✓' if ok else '✗'}")
            self.lbl_sum.setStyleSheet("color:#2e7d32;" if ok else "color:#c62828;font-weight:bold;")
        except Exception:
            self.lbl_sum.setText("?")

    def autofill(self):
        row = self.t_comp.currentRow()
        if row < 0:
            QtWidgets.QMessageBox.information(self, tr("Skład"), tr("Zaznacz wiersz pierwiastka, który ma uzupełnić sumę."))
            return
        tot = 0.0
        for r in range(self.N_EL):
            if r == row:
                continue
            tot += self._cell_float(r)
        self.t_comp.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{1 - tot:.6g}"))

    def _cell_float(self, r):
        it = self.t_comp.item(r, 1)
        try:
            return float(it.text().replace(",", ".")) if it and it.text().strip() else 0.0
        except ValueError:
            return 0.0

    # ------------------------------------------------------------------------------
    def params(self) -> Params:
        p = Params()
        p.base_dir = self.base_dir
        p.filename = self.f_data.text()
        p.filename_bkg = self.f_bkg.text()
        p.file_format = self.c_format.currentData()
        p.incoherent = self.c_incoh.currentData()
        p.lambd = self.s_lambda.value()
        p.q_unit = self.c_qunit.currentData()
        p.qmin, p.qmax = self.s_qmin.value(), self.s_qmax.value()
        p.rmin = self.s_rmin.value()
        p.rho, p.bkfactor = self.s_rho.value(), self.s_bk.value()
        p.sofq = self.c_sofq.currentData()
        p.normalization = self.c_norm.currentData()
        p.qstep = 1 if (self.ch_qstep.isChecked() and p.file_format in (1, 2)) else 0
        p.n_iter = self.s_iter.value()
        p.rmax_out = self.s_rmax.value()
        p.fix_norm_units = self.ch_fix.isChecked()
        p.save_norm = self.e_norm.text().strip() or "Norm"
        p.save_rmin = self.e_rmin.text().strip() or "MinRmin"
        p.save_qmax = self.e_qmax.text().strip() or "MinQmax"
        p.dpi = self.s_dpi.value()
        el, c = [], []
        for r in range(self.N_EL):
            it = self.t_comp.item(r, 0)
            el.append(it.text().strip() if it else "")
            c.append(self._cell_float(r))
        p.elements, p.contents = el, c
        return p

    def set_params(self, p: Params):
        self.blockSignals(True)
        self.base_dir = p.base_dir
        self.f_data.setText(p.filename)
        self.f_bkg.setText(p.filename_bkg)
        self.f_data.start_dir = self.f_bkg.start_dir = p.base_dir
        self.c_format.setCurrentIndex(max(0, self.c_format.findData(p.file_format)))
        self.c_incoh.setCurrentIndex(max(0, self.c_incoh.findData(p.incoherent)))
        if p.lambd > 0:
            self.s_lambda.setValue(p.lambd)
        self.c_qunit.setCurrentIndex(max(0, self.c_qunit.findData(p.q_unit)))
        self.s_qmin.setValue(p.qmin)
        self.s_qmax.setValue(p.qmax)
        self.s_rmin.setValue(p.rmin)
        self.s_rho.setValue(p.rho)
        self.s_bk.setValue(min(max(p.bkfactor, ph.BK_BOUNDS[0]), ph.BK_BOUNDS[1]))
        self.c_sofq.setCurrentIndex(max(0, self.c_sofq.findData(p.sofq)))
        self.c_norm.setCurrentIndex(max(0, self.c_norm.findData(p.normalization)))
        self.ch_qstep.setChecked(bool(p.qstep))
        self.s_iter.setValue(p.n_iter)
        self.s_rmax.setValue(p.rmax_out)
        self.ch_fix.setChecked(p.fix_norm_units)
        self.e_norm.setText(p.save_norm)
        self.e_rmin.setText(p.save_rmin)
        self.e_qmax.setText(p.save_qmax)
        self.s_dpi.setValue(p.dpi)
        self.t_comp.blockSignals(True)
        for r in range(self.N_EL):
            e = p.elements[r] if r < len(p.elements) else ""
            c = p.contents[r] if r < len(p.contents) else 0.0
            self.t_comp.setItem(r, 0, QtWidgets.QTableWidgetItem(e))
            self.t_comp.setItem(r, 1, QtWidgets.QTableWidgetItem(f"{c:g}"))
        self.t_comp.blockSignals(False)
        if not self.f_out.text() and p.base_dir:
            self.f_out.setText(p.base_dir)
        self.blockSignals(False)
        self._comp_changed()
        self._format_changed()

    def out_dir(self) -> Path:
        t = self.f_out.text()
        if t:
            return Path(t)
        return Path(self.base_dir or os.getcwd())

    # ------------------------------------------------------------------------------
    def load_init(self, path):
        p = load_init(path)
        self.init_path = str(path)
        self.f_out.setText(p.base_dir)
        self.set_params(p)
        self.lbl_init.setText(tr('Projekt: {0}').format(path))
        self.loaded.emit()
        self.log.emit(tr('Wczytano parametry z {0}').format(path))

    def load_dialog(self):
        f, _ = QtWidgets.QFileDialog.getOpenFileName(self, tr("Wczytaj Init.txt"), self.base_dir,
                                                     tr("Init (*.txt *.ini);;Wszystkie (*)"))
        if f:
            try:
                self.load_init(f)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, tr("Init"), tr('Nie udało się wczytać pliku:\n{0}').format(e))

    def _write(self, f):
        """Zapis parametrow do pliku f; nazwy plikow wzgledne, jesli leza w tym samym folderze."""
        p = self.params()
        d = Path(f).parent
        for attr in ("filename", "filename_bkg"):
            name = getattr(p, attr)
            if not name:
                continue
            pp = p.path(name)
            try:
                setattr(p, attr, str(pp.relative_to(d)) if pp.is_absolute() else name)
            except ValueError:
                setattr(p, attr, str(pp))
        save_init(p, f)

    def save_project(self, path=None, quiet=True):
        """Zapis do biezacego pliku projektu. Przyklad z folderu programu nie jest nadpisywany."""
        path = path or self.init_path
        if not path:
            if not quiet:
                self.save_dialog()
            return False
        from ..examples import EXAMPLES
        try:
            if Path(path).resolve() == (EXAMPLES / "Init.txt").resolve():
                if not quiet:
                    self.save_dialog()
                return False
        except Exception:
            pass
        try:
            self._write(path)
            if not quiet:
                self.log.emit(tr('Zapisano projekt: {0}').format(path))
            return True
        except Exception as e:
            self.log.emit(tr('Nie zapisano projektu {0}: {1}').format(path, e))
            return False

    def save_dialog(self):
        start = self.init_path or os.path.join(self.base_dir or "", "Init.txt")
        f, _ = QtWidgets.QFileDialog.getSaveFileName(self, tr("Zapisz Init.txt"), start, tr("Init (*.txt)"))
        if not f:
            return
        self._write(f)
        self.init_path = f
        self.lbl_init.setText(tr('Projekt: {0}').format(f))
        self.log.emit(tr('Zapisano parametry do {0}').format(f))
