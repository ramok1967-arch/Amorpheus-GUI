# -*- coding: utf-8 -*-
"""Okno 'Otworz dane': parametry analizy odczytane z pliku danych, do zatwierdzenia/poprawienia."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from .. import autodetect as ad
from .. import physics as ph
from ..data import Params, read_xy
from .widgets import dspin
from ..i18n import tr  # noqa: E402

DATA_FILTER = tr("Dane (*.xy *.dat *.txt *.chi *.csv *.xye);;Wszystkie (*)")
UNITS = [(tr("Q w Å⁻¹"), "q_A"), (tr("Q w nm⁻¹"), "q_nm"), (tr("2θ w stopniach"), "2th_deg")]
N_EL = 6


class OpenDataDialog(QtWidgets.QDialog):
    def __init__(self, data_path, base: Params = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Nowa analiza – parametry z pliku danych"))
        self.resize(760, 720)
        self.data_path = Path(data_path)
        self.base = base or Params()
        v = QtWidgets.QVBoxLayout(self)

        # --- pliki ---------------------------------------------------------------
        g = QtWidgets.QGroupBox(tr("Pliki"))
        f = QtWidgets.QFormLayout(g)
        self.lbl_data = QtWidgets.QLabel(str(self.data_path))
        self.lbl_data.setWordWrap(True)
        self.lbl_data.setTextInteractionFlags(Qt.TextSelectableByMouse)
        f.addRow(tr("Dane"), self.lbl_data)
        hb = QtWidgets.QHBoxLayout()
        self.c_bkg = QtWidgets.QComboBox()
        self.c_bkg.addItem(tr("(brak tła)"), "")
        for b in ad.suggest_background(self.data_path):
            self.c_bkg.addItem(b.name, str(b))
        b_bkg = QtWidgets.QPushButton(tr("Wybierz…"))
        b_bkg.clicked.connect(self.pick_bkg)
        hb.addWidget(self.c_bkg, 1)
        hb.addWidget(b_bkg)
        f.addRow(tr("Tło (pusta komórka)"), hb)
        self.lbl_bkghint = QtWidgets.QLabel("")
        self.lbl_bkghint.setObjectName("hint")
        self.lbl_bkghint.setWordWrap(True)
        f.addRow("", self.lbl_bkghint)
        v.addWidget(g)

        # --- co wykryto ----------------------------------------------------------
        self.info = QtWidgets.QLabel()
        self.info.setWordWrap(True)
        self.info.setTextFormat(Qt.RichText)
        self.info.setObjectName("result")
        v.addWidget(self.info)

        # --- parametry -----------------------------------------------------------
        g = QtWidgets.QGroupBox(tr("Parametry (można poprawić)"))
        grid = QtWidgets.QGridLayout(g)
        self.c_unit = QtWidgets.QComboBox()
        for t, u in UNITS:
            self.c_unit.addItem(t, u)
        self.s_lam = dspin(1e-5, 10, 6, 0.0001, 0.03738, "nm")
        self.s_qmin = dspin(0.01, 1000, 2, 0.5, 15, "nm⁻¹")
        self.s_qmax = dspin(0.01, 1000, 2, 1, 78, "nm⁻¹")
        self.s_rmin = dspin(0.01, ph.FIT_R_MAX, 3, 0.005, 0.2, "nm")
        self.c_inc = QtWidgets.QComboBox()
        self.c_inc.addItem(tr("1: tło z pustej komórki"), 1)
        self.c_inc.addItem(tr("0: tło zmierzone na próbce"), 0)
        rows = [(tr("Oś x w pliku"), self.c_unit), ("λ", self.s_lam), (tr("q_min"), self.s_qmin), (tr("q_max"), self.s_qmax),
                (tr("r_min (start)"), self.s_rmin), (tr("incoherent"), self.c_inc)]
        for k, (lab, w) in enumerate(rows):
            grid.addWidget(QtWidgets.QLabel(lab), k % 3, 2 * (k // 3))
            grid.addWidget(w, k % 3, 2 * (k // 3) + 1)
        v.addWidget(g)
        self._forced_unit = None
        self._forced_lam = None
        self.p0, self.det = None, None
        self.c_unit.currentIndexChanged.connect(self._user_unit)
        self.s_lam.valueChanged.connect(self._user_lam)

        # --- sklad i gestosc -----------------------------------------------------
        g = QtWidgets.QGroupBox(tr("Skład i gęstość"))
        h = QtWidgets.QHBoxLayout(g)
        left = QtWidgets.QVBoxLayout()
        self.t = QtWidgets.QTableWidget(N_EL, 2)
        self.t.setHorizontalHeaderLabels([tr("Pierwiastek"), tr("Udział at.")])
        self.t.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        vh = self.t.verticalHeader()
        vh.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        vh.setDefaultSectionSize(24)
        self.t.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._fit_table()
        self.t.itemChanged.connect(self._update_rho)
        left.addWidget(self.t)
        self.lbl_comp = QtWidgets.QLabel("")
        self.lbl_comp.setObjectName("hint")
        left.addWidget(self.lbl_comp)
        h.addLayout(left, 1)
        right = QtWidgets.QFormLayout()
        self.s_dens = dspin(0, 30, 3, 0.05, 0.0, "g/cm³")
        self.s_dens.setSpecialValueText(tr("nieznana"))
        self.s_dens.valueChanged.connect(self._update_rho)
        self.s_rho = dspin(1, 500, 3, 0.5, 50.0, "at/nm³")
        self.lbl_rho = QtWidgets.QLabel("")
        self.lbl_rho.setObjectName("hint")
        self.lbl_rho.setWordWrap(True)
        right.addRow(tr("Gęstość masowa"), self.s_dens)
        right.addRow(tr("ρ startowe"), self.s_rho)
        right.addRow("", self.lbl_rho)
        h.addLayout(right, 1)
        v.addWidget(g)

        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.button(QtWidgets.QDialogButtonBox.Ok).setText(tr("Utwórz projekt"))
        bb.button(QtWidgets.QDialogButtonBox.Cancel).setText(tr("Anuluj"))
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)
        self.c_bkg.currentIndexChanged.connect(self.refresh)
        self.refresh(first=True)

    def _fit_table(self):
        t = self.t
        hh = max(t.horizontalHeader().height(), t.horizontalHeader().sizeHint().height())
        t.setFixedHeight(hh + sum(t.rowHeight(r) for r in range(N_EL)) + 2 * t.frameWidth() + 2)

    def showEvent(self, ev):
        super().showEvent(ev)
        self._fit_table()

    # ------------------------------------------------------------------------------
    def pick_bkg(self):
        f, _ = QtWidgets.QFileDialog.getOpenFileName(self, tr("Plik tła"), str(self.data_path.parent), DATA_FILTER)
        if f:
            i = self.c_bkg.findData(f)
            if i < 0:
                self.c_bkg.addItem(Path(f).name, f)
                i = self.c_bkg.count() - 1
            self.c_bkg.setCurrentIndex(i)

    def bkg(self):
        return self.c_bkg.currentData() or None

    def _user_unit(self):
        """Uzytkownik poprawil jednostke osi -> przelicz zakres q."""
        self._forced_unit = self.c_unit.currentData()
        self.refresh()

    def _user_lam(self):
        if self.c_unit.currentData() == "2th_deg":
            self._forced_lam = self.s_lam.value()
            self.refresh()

    def refresh(self, *a, first=False):
        try:
            p, det = ad.build_params(self.data_path, self.bkg(), self.base,
                                     unit=self._forced_unit, lambd_nm=self._forced_lam)
        except Exception as e:
            self.info.setText(tr("<b style='color:#c62828'>Nie udało się odczytać pliku:</b> {0}").format(e))
            return
        self.p0, self.det = p, det
        unit = det.unit if det.unit in dict((u, u) for _, u in UNITS) else "q_A"
        self.c_unit.blockSignals(True)
        self.c_unit.setCurrentIndex(max(0, self.c_unit.findData(unit)))
        self.c_unit.blockSignals(False)
        if det.wavelength_nm:
            self.s_lam.blockSignals(True)
            self.s_lam.setValue(det.wavelength_nm)
            self.s_lam.blockSignals(False)
        self.s_qmin.setValue(p.qmin)
        self.s_qmax.setValue(p.qmax)
        self._unit_changed()
        if first:
            self.s_rmin.setValue(p.rmin)
            self.t.blockSignals(True)
            for r in range(N_EL):
                e = p.elements[r] if r < len(p.elements) else ""
                c = p.contents[r] if r < len(p.contents) else 0.0
                self.t.setItem(r, 0, QtWidgets.QTableWidgetItem(e))
                self.t.setItem(r, 1, QtWidgets.QTableWidgetItem(f"{c:g}" if e else ""))
            self.t.blockSignals(False)
            self.lbl_comp.setText(tr("Skład odczytany z nazwy pliku.") if any(p.elements) else
                                  tr("Nie odczytano składu z nazwy – wpisz pierwiastki i udziały atomowe."))
            self._update_rho()
        self.lbl_bkghint.setText("" if self.bkg() else
                                 tr("Bez tła: format bez odejmowania tła, dopasowywana jest tylko ρ. "
                                 "Rozpraszanie od komórki/kapilary/powietrza zostaje w S(q)."))
        self._show_info()

    def _show_info(self):
        det = self.det
        unit_txt = {"q_A": "Q [Å⁻¹]", "q_nm": tr("Q [nm⁻¹]"), "2th_deg": "2θ [°]", "2th_rad": tr("2θ [rad]")}.get(det.unit, "?")
        lines = [tr('<b>Wykryto:</b> {0}, oś: {1}, {2} punktów, x = {3:.4g} – {4:.4g}').format(det.source or tr('plik tekstowy'), unit_txt, det.n_points, det.x_lo, det.x_hi)]
        if det.wavelength_nm:
            lines.append(tr('λ = {0:.6g} nm ({1:.5g} Å, {2:.2f} keV)').format(det.wavelength_nm, det.wavelength_nm * 10, 12.39842 / (det.wavelength_nm * 10)))
        if np.isfinite(det.main_peak):
            lines.append(tr('Pierwsze maksimum przy q ≈ {0:.1f} nm⁻¹ → q_min ustawione poniżej, q_max przed końcem danych.').format(det.main_peak))
        for w in det.warnings:
            lines.append(tr("<span style='color:#b45309'>⚠ {0}</span>").format(w))
        self.info.setText("<br>".join(lines))

    def _unit_changed(self):
        u = self.c_unit.currentData()
        self.s_lam.setEnabled(u == "2th_deg")

    def _composition(self):
        el, c = [], []
        for r in range(N_EL):
            e = self.t.item(r, 0)
            x = self.t.item(r, 1)
            e = e.text().strip() if e else ""
            try:
                xv = float(x.text().replace(",", ".")) if x and x.text().strip() else 0.0
            except ValueError:
                xv = 0.0
            el.append(e)
            c.append(xv)
        return el, c

    def _update_rho(self, *a):
        el, c = self._composition()
        act = [(e, x) for e, x in zip(el, c) if e]
        s = sum(x for _, x in act)
        try:
            m = ad.mean_atomic_mass([e for e, _ in act], [x / s for _, x in act]) if act and s > 0 else np.nan
        except Exception:
            m = np.nan
        txt = tr('suma udziałów = {0:.4f}').format(s) + (" ✓" if abs(s - 1) < 1e-4 else tr(" ✗ (zostanie znormalizowana)"))
        if np.isfinite(m):
            txt += f"; M̄ = {m:.2f} g/mol"
            if self.s_dens.value() > 0:
                rho = ad.AVOGADRO_NM * self.s_dens.value() / m
                self.s_rho.setValue(rho)
                txt += tr("<br>ρ = 602,2·d/M̄ = <b>{0:.2f} at/nm³</b>").format(rho)
        self.lbl_rho.setText(txt)

    # ------------------------------------------------------------------------------
    def _accept(self):
        p = self.result_params()
        errs = p.validate()
        if p.qmin >= p.qmax:
            errs.append(tr("q_min musi być mniejsze od q_max."))
        if errs:
            QtWidgets.QMessageBox.warning(self, tr("Parametry"), "\n".join(errs))
            return
        self.accept()

    def result_params(self) -> Params:
        p = self.p0.copy()
        u = self.c_unit.currentData()
        has_bkg = bool(self.bkg())
        if u == "2th_deg":
            p.file_format = 2 if has_bkg else 1
        else:
            p.file_format = 4 if has_bkg else 3
            p.q_unit = "nm" if u == "q_nm" else "A"
        p.lambd = self.s_lam.value()
        p.qmin, p.qmax = self.s_qmin.value(), self.s_qmax.value()
        p.rmin = self.s_rmin.value()
        p.incoherent = self.c_inc.currentData()
        p.rho = self.s_rho.value()
        el, c = self._composition()
        s = sum(x for e, x in zip(el, c) if e)
        if s > 0:
            c = [x / s if e else 0.0 for e, x in zip(el, c)]
        p.elements, p.contents = el, [round(x, 6) for x in c]
        return p
