# -*- coding: utf-8 -*-
"""Zakladki analizy."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from .. import analysis as an
from .. import export as ex
from .. import plots
from .. import physics as ph
from ..data import read_batch, read_xy, FILE_FORMATS
from ..rps import RPSSession, MODELS, smooth
from .widgets import PlotWidget, dspin, ispin
from ..i18n import tr  # noqa: E402


def num_item(v, fmt="{:.5g}"):
    it = QtWidgets.QTableWidgetItem("" if v is None or (isinstance(v, float) and np.isnan(v)) else fmt.format(v))
    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
    return it


def make_table(headers):
    t = QtWidgets.QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    t.verticalHeader().setVisible(False)
    t.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    t.setAlternatingRowColors(True)
    return t


def hint(text):
    l = QtWidgets.QLabel(text)
    l.setObjectName("hint")
    l.setWordWrap(True)
    return l


class BaseTab(QtWidgets.QWidget):
    def __init__(self, mw):
        super().__init__()
        self.mw = mw

    def run_buttons(self):
        return []


# ======================================================================================
class DataTab(BaseTab):
    def __init__(self, mw):
        super().__init__(mw)
        v = QtWidgets.QVBoxLayout(self)
        hb = QtWidgets.QHBoxLayout()
        self.btn = QtWidgets.QPushButton(tr("Pokaż dane"))
        self.btn.setObjectName("primary")
        self.btn.clicked.connect(self.show_data)
        hb.addWidget(self.btn)
        hb.addWidget(hint(tr("Surowe dane i tło w jednostkach z pliku; żółty pas = zakres q_min–q_max "
                          "używany w analizie. Górna oś: q w nm⁻¹.")), 1)
        v.addLayout(hb)
        self.plot = PlotWidget()
        v.addWidget(self.plot, 1)

    def show_data(self):
        p = self.mw.params.params()
        try:
            self.plot.draw(plots.plot_raw, p)
        except Exception as e:
            self.plot.placeholder(str(e))


# ======================================================================================
class NormTab(BaseTab):
    def __init__(self, mw):
        super().__init__(mw)
        self.res = None
        v = QtWidgets.QVBoxLayout(self)
        hb = QtWidgets.QHBoxLayout()
        self.b_norm = QtWidgets.QPushButton(tr("Normalizuj"))
        self.b_norm.setObjectName("primary")
        self.b_norm.setToolTip(tr("S(q), F(r), g(r) dla ρ i bkfactor z panelu parametrów (opcja [n] oryginału)"))
        self.b_fit = QtWidgets.QPushButton(tr("Dopasuj ρ, bk → normalizuj"))
        self.b_fit.setToolTip(tr("Najpierw minimalizacja χ² przy r_min z panelu, potem normalizacja\n"
                              "z dopasowanymi wartościami (jak pojedynczy wiersz batcha)."))
        self.b_save = QtWidgets.QPushButton(tr("Zapisz wyniki"))
        self.b_save.setEnabled(False)
        self.b_norm.clicked.connect(lambda: self.run(False))
        self.b_fit.clicked.connect(lambda: self.run(True))
        self.b_save.clicked.connect(self.save)
        for b in (self.b_norm, self.b_fit, self.b_save):
            hb.addWidget(b)
        hb.addStretch(1)
        self.ch_auto = QtWidgets.QCheckBox(tr("zapisuj automatycznie"))
        hb.addWidget(self.ch_auto)
        v.addLayout(hb)

        split = QtWidgets.QSplitter(Qt.Horizontal)
        self.plot = PlotWidget(figsize=(10, 7))
        split.addWidget(self.plot)
        side = QtWidgets.QWidget()
        sv = QtWidgets.QVBoxLayout(side)
        sv.setContentsMargins(4, 0, 0, 0)
        self.lbl = QtWidgets.QLabel("—")
        self.lbl.setObjectName("result")
        self.lbl.setWordWrap(True)
        sv.addWidget(self.lbl)
        sv.addWidget(QtWidgets.QLabel(tr("<b>Iteracje Kaplowa</b>")))
        self.table = make_table([tr("it."), tr("ρ(nachyl.)"), tr("CN1"), tr("CN2"), tr("r₁ (nm)"), tr("r_min₁")])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        sv.addWidget(self.table, 1)
        sv.addWidget(hint(tr("CN1 = 2 × całka do maksimum 1. piku (zakłada symetrię piku); "
                          "CN2 = całka do 1. minimum za pikiem. Obie przy ρ użytym w normalizacji.")))
        g = QtWidgets.QGroupBox(tr("Funkcja modyfikująca M(Q, Δ(r))"))
        f = QtWidgets.QFormLayout(g)
        self.s_a = dspin(0.01, 5, 4, 0.005, 0.3, "nm")
        self.s_b = dspin(0.0001, 5, 4, 0.005, 0.1, "nm")
        self.b_mod = QtWidgets.QPushButton(tr("Przelicz g(r) z M(Q,Δ)"))
        self.b_mod.setEnabled(False)
        self.b_mod.clicked.connect(self.apply_mod)
        self.b_moddef = QtWidgets.QPushButton(tr("Domyślne a, b"))
        self.b_moddef.setEnabled(False)
        self.b_moddef.clicked.connect(self.default_mod)
        f.addRow(tr("a (pozycja 1. piku)"), self.s_a)
        f.addRow(tr("b (szerokość)"), self.s_b)
        hb2 = QtWidgets.QHBoxLayout()
        hb2.addWidget(self.b_moddef)
        hb2.addWidget(self.b_mod)
        f.addRow(hb2)
        sv.addWidget(g)
        self.b_take = QtWidgets.QPushButton(tr("Przenieś ρ, bk do parametrów"))
        self.b_take.setEnabled(False)
        self.b_take.clicked.connect(self.take)
        sv.addWidget(self.b_take)
        split.addWidget(side)
        split.setSizes([820, 470])
        v.addWidget(split, 1)

    def run_buttons(self):
        return [self.b_norm, self.b_fit]

    def run(self, fit_first):
        p = self.mw.checked_params()
        if p is None:
            return

        def job(ctx):
            rho, bk = p.rho, p.bkfactor
            fr = None
            if fit_first:
                ctx.report(0, 2, tr("dopasowanie ρ, bk"))
                fr = an.fit_density(p)
                rho, bk = fr.rho, fr.bkfactor
                ctx.log(tr('Dopasowanie (r_min={0:g} nm): ρ = {1:.4f} at/nm³, bk = {2:.5f}, χ² = {3:.5g}  [{4} wywołań, {5:.1f} s]').format(p.rmin, rho, bk, fr.chi2, fr.nfev, fr.seconds))
            ctx.report(1, 2, tr("normalizacja"))
            return fr, an.run_normalization(p, rho=rho, bk=bk)

        self.mw.run_task(job, self.done, tr("Normalizacja"))

    def done(self, out):
        fr, res = out
        self.res = res
        self.refresh()
        self.b_save.setEnabled(True)
        self.b_mod.setEnabled(True)
        self.b_moddef.setEnabled(True)
        self.b_take.setEnabled(True)
        if np.isfinite(res.mod_a):
            self.s_a.setValue(res.mod_a)
            self.s_b.setValue(max(res.mod_b, 1e-4))
        c = res.cn[-1]
        self.mw.log(tr('Normalizacja: ρ = {0:.4f} at/nm³, bk = {1:.5f}; ρ z nachylenia F(r<rmin) = {2:.3f}').format(res.rho, res.bkfactor, res.dens_slope[-1]) + (tr('; CN1 = {0:.2f}, CN2 = {1:.2f}').format(c['CN1'], c['CN2']) if c else ""))
        if self.ch_auto.isChecked():
            self.save()

    def refresh(self):
        res = self.res
        self.plot.draw(plots.plot_norm_overview, res)
        c = res.cn[-1]
        self.lbl.setText(
            tr('<b>ρ</b> = {0:.4f} at/nm³ &nbsp; <b>bk</b> = {1:.5f}<br>ρ z nachylenia F(r&lt;r<sub>min</sub>): {2:.3f}<br>').format(res.rho, res.bkfactor, res.dens_slope[-1])
            + (tr('<b>CN1</b> = {0:.2f} &nbsp; <b>CN2</b> = {1:.2f} &nbsp; r<sub>1</sub> = {2:.4f} nm').format(c['CN1'], c['CN2'], c['r_peak']) if c else tr("CN: nie znaleziono piku")))
        self.table.setRowCount(len(res.cn))
        for i, c in enumerate(res.cn):
            vals = [i, res.dens_slope[i]] + ([c["CN1"], c["CN2"], c["r_peak"], c["r_min"]] if c else [None] * 4)
            for j, x in enumerate(vals):
                self.table.setItem(i, j, num_item(x, "{:d}" if j == 0 else "{:.3f}" if j < 4 else "{:.4f}"))

    def default_mod(self):
        if self.res is not None and np.isfinite(self.res.mod_a):
            c = self.res.cn[-1]
            self.s_a.setValue(c["r_peak"])
            self.s_b.setValue(max(c["r_peak"] - self.res.p.rmin, 1e-4))

    def apply_mod(self):
        res = self.res
        a, b = self.s_a.value(), self.s_b.value()
        self.mw.run_task(lambda ctx: (res.apply_modification(a, b), res)[1], lambda r: (self.refresh(),
                         self.mw.log(tr('g(r) z funkcją modyfikującą: a = {0:.4f} nm, b = {1:.4f} nm').format(a, b))),
                         tr("Funkcja modyfikująca"))

    def take(self):
        if self.res is None:
            return
        self.mw.params.s_rho.setValue(self.res.rho)
        if self.res.p.has_bkg:
            self.mw.params.s_bk.setValue(self.res.bkfactor)
        self.mw.log(tr("Przeniesiono ρ i bkfactor do parametrów."))

    def save(self):
        if self.res is None:
            return
        try:
            files = ex.save_normalization(self.res, self.mw.params.out_dir(), self.res.p.save_norm,
                                          overwrite=self.mw.params.ch_overwrite.isChecked())
            self.mw.log(tr('Zapisano {0} plików: {1} / {2}_*').format(len(files), Path(files[0]).parent, Path(files[0]).name.rsplit('_', 1)[0]))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, tr("Zapis"), str(e))


# ======================================================================================
class LoopTab(BaseTab):
    """Petla po rmin (kind='rmin') albo po qmax (kind='qmax')."""

    def __init__(self, mw, kind):
        super().__init__(mw)
        self.kind = kind
        self.results = []
        self.p_used = None
        v = QtWidgets.QVBoxLayout(self)
        g = QtWidgets.QGroupBox(tr("Zakres pętli i start dopasowania"))
        hb = QtWidgets.QHBoxLayout(g)
        if kind == "rmin":
            self.s_from = dspin(0.01, ph.FIT_R_MAX, 4, 0.01, 0.15, "nm")
            self.s_to = dspin(0.01, ph.FIT_R_MAX, 4, 0.01, 0.25, "nm")
            self.s_step = dspin(0.0005, 0.2, 4, 0.005, 0.01, "nm")
            txt = (tr("Dla każdego r_min: minimalizacja χ² = ∫₀^rmin [F(r)+4πρr]² dr względem ρ "
                   "(i bkfactor). Wybierz r_min z plateau ρ(r_min). χ² porównuj tylko lokalnie: "
                   "rośnie z r_min z definicji, więc jego globalne minimum nie wskazuje najlepszego r_min."))
        else:
            self.s_from = dspin(1, 1000, 3, 1, 50, "nm⁻¹")
            self.s_to = dspin(1, 1000, 3, 1, 78, "nm⁻¹")
            self.s_step = dspin(0.1, 100, 3, 1, 5, "nm⁻¹")
            txt = (tr("Dla każdego q_max dane są wczytywane w zakresie q_min–q_max i dopasowywane jest ρ "
                   "(i bkfactor) przy r_min z parametrów."))
        self.s_rho0 = dspin(1, 500, 3, 0.5, 34.68, "at/nm³")
        self.s_bk0 = dspin(ph.BK_BOUNDS[0], ph.BK_BOUNDS[1], 4, 0.01, 0.927)
        self.b_fromp = QtWidgets.QToolButton()
        self.b_fromp.setText("↺")
        self.b_fromp.setToolTip(tr("Pobierz ρ i bkfactor z panelu parametrów"))
        self.b_fromp.clicked.connect(self.sync_start)
        for lab, w in [(tr("od"), self.s_from), (tr("do"), self.s_to), (tr("krok"), self.s_step),
                       ("ρ₀", self.s_rho0), ("bk₀", self.s_bk0)]:
            hb.addWidget(QtWidgets.QLabel(lab))
            hb.addWidget(w)
        hb.addWidget(self.b_fromp)
        self.lbl_n = QtWidgets.QLabel()
        hb.addWidget(self.lbl_n)
        hb.addStretch(1)
        for w in (self.s_from, self.s_to, self.s_step):
            w.valueChanged.connect(self.count)
        v.addWidget(g)
        hb = QtWidgets.QHBoxLayout()
        self.b_run = QtWidgets.QPushButton(tr("Start"))
        self.b_run.setObjectName("primary")
        self.b_run.clicked.connect(self.run)
        self.b_save = QtWidgets.QPushButton(tr("Zapisz"))
        self.b_save.setEnabled(False)
        self.b_save.clicked.connect(self.save)
        self.b_take = QtWidgets.QPushButton(tr("Przyjmij zaznaczony wiersz do parametrów"))
        self.b_take.setEnabled(False)
        self.b_take.clicked.connect(self.take)
        self.ch_auto = QtWidgets.QCheckBox(tr("zapisz po zakończeniu"))
        self.ch_auto.setChecked(True)
        for b in (self.b_run, self.b_save, self.b_take):
            hb.addWidget(b)
        hb.addWidget(self.ch_auto)
        hb.addStretch(1)
        v.addLayout(hb)
        v.addWidget(hint(txt))
        split = QtWidgets.QSplitter(Qt.Horizontal)
        self.plot = PlotWidget()
        split.addWidget(self.plot)
        col = tr("r_min (nm)") if kind == "rmin" else tr("q_max (nm⁻¹)")
        self.table = make_table([col, tr("ρ (at/nm³)"), tr("bkfactor"), "χ²", tr("czas (s)")])
        self.table.itemSelectionChanged.connect(self.selected)
        split.addWidget(self.table)
        split.setSizes([800, 420])
        v.addWidget(split, 1)
        self.count()

    def run_buttons(self):
        return [self.b_run]

    def sync_start(self):
        p = self.mw.params.params()
        self.s_rho0.setValue(p.rho)
        self.s_bk0.setValue(min(max(p.bkfactor, ph.BK_BOUNDS[0]), ph.BK_BOUNDS[1]))
        if self.kind == "qmax":
            self.s_to.setValue(p.qmax)

    def values(self):
        return an.inclusive_range(self.s_from.value(), self.s_to.value(), self.s_step.value())

    def count(self):
        try:
            n = len(self.values())
            self.lbl_n.setText(tr('→ {0} dopasowań').format(n))
        except Exception:
            self.lbl_n.setText(tr("→ zły zakres"))

    def run(self):
        p = self.mw.checked_params()
        if p is None:
            return
        try:
            vals = self.values()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, tr("Zakres"), str(e))
            return
        if self.kind == "qmax":
            rng = self.mw.params.file_range
            if vals[0] <= p.qmin:
                QtWidgets.QMessageBox.warning(self, tr("Zakres"), tr("Początek pętli musi być większy niż q_min."))
                return
            if rng and vals[-1] > rng[1] + 1e-9:
                QtWidgets.QMessageBox.warning(self, tr("Zakres"), tr('q_max nie może przekraczać {0:.3f} nm⁻¹ (koniec danych).').format(rng[1]))
                return
        rho0, bk0 = self.s_rho0.value(), self.s_bk0.value()
        self.results = []
        self.p_used = p
        self.table.setRowCount(0)
        self.bounds = (vals[0], vals[-1])
        fn = an.loop_rmin if self.kind == "rmin" else an.loop_qmax

        def job(ctx):
            return fn(p, vals, rho0, bk0, progress=ctx.report, cancelled=ctx.cancelled,
                      on_result=ctx.partial.emit)

        self.mw.run_task(job, self.done, tr('Pętla {0}').format(self.kind), on_partial=self.add)

    def add(self, r):
        self.results.append(r)
        i = self.table.rowCount()
        self.table.insertRow(i)
        x = r.rmin if self.kind == "rmin" else r.qmax
        for j, val in enumerate([x, r.rho, r.bkfactor, r.chi2, r.seconds]):
            self.table.setItem(i, j, num_item(val, "{:.4f}" if j < 3 else "{:.4g}" if j == 3 else "{:.1f}"))
        self.table.scrollToBottom()
        self.plot.draw(plots.plot_loop, self.results, self.kind, self.p_used.has_bkg)
        self.mw.log(tr('  {0} = {1:.4f}: ρ = {2:.4f}, bk = {3:.5f}, χ² = {4:.5g}').format(self.kind, x, r.rho, r.bkfactor, r.chi2))

    def done(self, res):
        if not self.results:
            return
        self.b_save.setEnabled(True)
        self.b_take.setEnabled(True)
        # bez automatycznego wyboru: chi2 = calka 0..rmin rosnie z rmin z definicji,
        # wiec jego minimum nie wskazuje najlepszego rmin - kryterium jest plateau rho
        if self.ch_auto.isChecked():
            self.save()

    def selected(self):
        rows = self.table.selectionModel().selectedRows()
        if rows and self.results:
            self.plot.draw(plots.plot_loop, self.results, self.kind, self.p_used.has_bkg, highlight=rows[0].row())

    def take(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        r = self.results[rows[0].row()]
        pp = self.mw.params
        pp.s_rho.setValue(r.rho)
        if self.p_used.has_bkg:
            pp.s_bk.setValue(r.bkfactor)
        if self.kind == "rmin":
            pp.s_rmin.setValue(r.rmin)
        else:
            pp.s_qmax.setValue(r.qmax)
        self.mw.log(tr('Przyjęto do parametrów: {0} = {1:.4f}, ρ = {2:.4f}, bk = {3:.5f}').format(self.kind, r.rmin if self.kind == 'rmin' else r.qmax, r.rho, r.bkfactor))

    def save(self):
        if not self.results:
            return
        try:
            files = ex.save_loop(self.results, self.p_used, self.kind, self.mw.params.out_dir(),
                                 self.bounds[0], self.bounds[1], overwrite=self.mw.params.ch_overwrite.isChecked())
            self.mw.log(tr('Zapisano: {0}').format(files[0]))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, tr("Zapis"), str(e))


# ======================================================================================
class Chi2Tab(BaseTab):
    def __init__(self, mw):
        super().__init__(mw)
        self.map = None
        v = QtWidgets.QVBoxLayout(self)
        g = QtWidgets.QGroupBox(tr("Siatka (tylko formaty z tłem)"))
        grid = QtWidgets.QGridLayout(g)
        self.s_rmin = dspin(0.01, ph.FIT_R_MAX, 4, 0.005, 0.22, "nm")
        self.s_rc = dspin(1, 500, 3, 0.5, 34.68, "at/nm³")
        self.s_rw = dspin(0.01, 100, 3, 0.5, 6, "at/nm³")
        self.s_bc = dspin(0.5, 1.5, 4, 0.005, 0.927)
        self.s_bw = dspin(0.001, 1, 4, 0.01, 0.1)
        self.s_nr = ispin(2, 400, 31)
        self.s_nb = ispin(2, 400, 31)
        items = [(tr("r_min"), self.s_rmin), (tr("ρ środek"), self.s_rc), (tr("ρ szerokość"), self.s_rw),
                 (tr("punkty ρ"), self.s_nr), (tr("bk środek"), self.s_bc), (tr("bk szerokość"), self.s_bw),
                 (tr("punkty bk"), self.s_nb)]
        for k, (lab, w) in enumerate(items):
            grid.addWidget(QtWidgets.QLabel(lab), k // 4, 2 * (k % 4))
            grid.addWidget(w, k // 4, 2 * (k % 4) + 1)
        self.b_sync = QtWidgets.QPushButton(tr("Środek z parametrów"))
        self.b_sync.clicked.connect(self.sync)
        grid.addWidget(self.b_sync, 1, 7)
        v.addWidget(g)
        hb = QtWidgets.QHBoxLayout()
        self.b_run = QtWidgets.QPushButton(tr("Licz mapę"))
        self.b_run.setObjectName("primary")
        self.b_run.clicked.connect(self.run)
        self.b_save = QtWidgets.QPushButton(tr("Zapisz"))
        self.b_save.setEnabled(False)
        self.b_save.clicked.connect(self.save)
        self.b_take = QtWidgets.QPushButton(tr("Przyjmij minimum do parametrów"))
        self.b_take.setEnabled(False)
        self.b_take.clicked.connect(self.take)
        self.lbl = QtWidgets.QLabel("")
        self.lbl.setObjectName("result")
        for b in (self.b_run, self.b_save, self.b_take):
            hb.addWidget(b)
        hb.addWidget(self.lbl, 1)
        v.addLayout(hb)
        self.lbl_est = hint("")
        v.addWidget(self.lbl_est)
        for w in (self.s_nr, self.s_nb):
            w.valueChanged.connect(self.estimate)
        self.estimate()
        self.plot = PlotWidget(figsize=(12, 5))
        v.addWidget(self.plot, 1)

    def run_buttons(self):
        return [self.b_run]

    def estimate(self):
        n = self.s_nr.value() * self.s_nb.value()
        self.lbl_est.setText(tr('{0} punktów siatki, szacunkowo {1:.0f}–{2:.0f} s. Lewy panel: χ²; prawy: χ²/χ²min z konturami 1.5, 5, 10, 20, 50, 100; czerwony krzyż = środek, gwiazdka = minimum.').format(n, n * 0.012, n * 0.025))

    def sync(self):
        p = self.mw.params.params()
        self.s_rmin.setValue(p.rmin)
        self.s_rc.setValue(p.rho)
        self.s_bc.setValue(p.bkfactor)

    def run(self):
        p = self.mw.checked_params()
        if p is None:
            return
        if not p.has_bkg:
            QtWidgets.QMessageBox.information(self, tr("Mapa χ²"), tr("Mapa χ² wymaga danych z tłem (format 2 lub 4)."))
            return
        args = (self.s_rmin.value(), self.s_rc.value(), self.s_rw.value(), self.s_bc.value(),
                self.s_bw.value(), self.s_nr.value(), self.s_nb.value())
        self.p_used = p
        self.mw.run_task(lambda ctx: an.chi2_map(p, *args, progress=ctx.report, cancelled=ctx.cancelled),
                         self.done, tr("Mapa χ²"))

    def done(self, m):
        self.map = m
        if np.isfinite(m.Z).sum() < 4:
            self.plot.placeholder(tr("Za mało policzonych punktów"))
            return
        self.plot.draw(plots.plot_chi2map, m)
        r0, b0, z0 = m.minimum()
        self.lbl.setText(tr('minimum: ρ = {0:.4f} at/nm³, bk = {1:.5f}, χ² = {2:.4g}').format(r0, b0, z0)
                         + ("" if m.complete else tr("  (przerwano)")))
        self.b_save.setEnabled(True)
        self.b_take.setEnabled(True)
        self.mw.log(tr('Mapa χ²: minimum ρ = {0:.4f}, bk = {1:.5f}, χ² = {2:.4g}').format(r0, b0, z0))

    def take(self):
        r0, b0, _ = self.map.minimum()
        self.mw.params.s_rho.setValue(r0)
        self.mw.params.s_bk.setValue(b0)
        self.mw.params.s_rmin.setValue(self.map.rmin)

    def save(self):
        try:
            files = ex.save_chi2map(self.map, self.p_used, self.mw.params.out_dir(),
                                    overwrite=self.mw.params.ch_overwrite.isChecked())
            self.mw.log(tr('Zapisano: {0}').format(files[0]))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, tr("Zapis"), str(e))


# ======================================================================================
class BatchTab(BaseTab):
    COLS = ["P (GPa)", "T (K)", tr("folder"), tr("plik"), tr("tło"), tr("format"), "q_min", "q_max", "r_min", "ρ₀", "bk₀",
            "→ ρ", "→ bk", "→ χ²", "status"]

    def __init__(self, mw):
        super().__init__(mw)
        self.rows = []
        self.items = []
        v = QtWidgets.QVBoxLayout(self)
        hb = QtWidgets.QHBoxLayout()
        self.e_file = QtWidgets.QLineEdit()
        self.e_file.setPlaceholderText(tr("Tabela batch (.ods, .xlsx, .csv) w układzie Batch.ods z oryginału"))
        b_br = QtWidgets.QPushButton(tr("Wybierz…"))
        b_br.clicked.connect(self.browse)
        self.b_load = QtWidgets.QPushButton(tr("Wczytaj"))
        self.b_load.clicked.connect(self.load)
        self.b_run = QtWidgets.QPushButton(tr("Uruchom batch"))
        self.b_run.setObjectName("primary")
        self.b_run.clicked.connect(self.run)
        hb.addWidget(self.e_file, 1)
        for b in (b_br, self.b_load, self.b_run):
            hb.addWidget(b)
        v.addLayout(hb)
        v.addWidget(hint(tr("Każdy wiersz: dopasowanie ρ i bkfactor przy r_min z wiersza, następnie normalizacja "
                         "z dopasowanymi wartościami. Opcje obliczeń (poprawka jednostek, iteracje, r_max, DPI) "
                         "są brane z panelu parametrów. Wyniki: folder Batch_RRRRMMDD_HHhMM w folderze wyników.")))
        split = QtWidgets.QSplitter(Qt.Vertical)
        self.table = make_table(self.COLS)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        split.addWidget(self.table)
        self.plot = PlotWidget(figsize=(14, 4.5))
        split.addWidget(self.plot)
        split.setSizes([250, 450])
        v.addWidget(split, 1)

    def run_buttons(self):
        return [self.b_run]

    def browse(self):
        f, _ = QtWidgets.QFileDialog.getOpenFileName(self, tr("Tabela batch"), self.mw.params.base_dir,
                                                     tr("Tabele (*.ods *.xlsx *.xls *.csv);;Wszystkie (*)"))
        if f:
            self.e_file.setText(os.path.normpath(f))
            self.load()

    def template(self):
        return self.mw.params.params()

    def load(self):
        path = self.e_file.text().strip()
        if not path:
            return
        try:
            self.rows = read_batch(path, self.template())
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, tr("Batch"), tr('Nie udało się wczytać tabeli:\n{0}').format(e))
            return
        t = self.table
        t.setRowCount(len(self.rows))
        for i, r in enumerate(self.rows):
            p = r.params
            vals = [r.pressure, r.temperature, r.folder, p.filename, p.filename_bkg if p.has_bkg else "—",
                    p.file_format, p.qmin, p.qmax, p.rmin, p.rho, p.bkfactor if p.has_bkg else "—", "", "", "", ""]
            for j, x in enumerate(vals):
                it = QtWidgets.QTableWidgetItem(str(x))
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                t.setItem(i, j, it)
            errs = p.validate()
            if not p.path(p.filename).is_file():
                errs.append(tr("brak pliku danych"))
            self._status(i, "⚠ " + "; ".join(errs) if errs else tr("gotowy"), bad=bool(errs))
        self.mw.log(tr('Batch: wczytano {0} wierszy z {1}').format(len(self.rows), path))

    def _status(self, i, txt, bad=False):
        it = QtWidgets.QTableWidgetItem(txt)
        it.setForeground(QtGui.QColor("#c62828" if bad else "#2e7d32"))
        self.table.setItem(i, 14, it)

    def run(self):
        if not self.rows:
            self.load()
        if not self.rows:
            return
        tpl = self.template()
        for r in self.rows:      # opcje obliczen z panelu
            for a in ("fix_norm_units", "n_iter", "rmax_out", "dpi"):
                setattr(r.params, a, getattr(tpl, a))
        rows = self.rows
        out_dir = self.mw.params.out_dir()
        batch_path = self.e_file.text().strip()
        self.items = []

        def job(ctx):
            items = an.run_batch(rows, progress=ctx.report, cancelled=ctx.cancelled,
                                 on_item=ctx.partial.emit, log=ctx.log)
            ctx.report(len(rows), len(rows), tr("zapis wyników"))
            folder = ex.save_batch(items, batch_path, out_dir, dpi=tpl.dpi, log=ctx.log)
            return items, folder

        self.mw.run_task(job, self.done, tr("Batch"), on_partial=self.add)

    def add(self, it):
        i = len(self.items)
        self.items.append(it)
        if it.fit:
            for j, (v, f) in enumerate([(it.fit.rho, "{:.4f}"), (it.fit.bkfactor, "{:.5f}"), (it.fit.chi2, "{:.4g}")]):
                self.table.setItem(i, 11 + j, num_item(v, f))
        self._status(i, tr("BŁĄD: ") + it.error if it.error else tr("OK"), bad=bool(it.error))
        self.plot.draw(plots.plot_batch, self.items)

    def done(self, out):
        items, folder = out
        self.plot.draw(plots.plot_batch, items)
        self.mw.log(tr('Batch zakończony, wyniki w: {0}').format(folder))


# ======================================================================================
class RPSTab(BaseTab):
    def __init__(self, mw):
        super().__init__(mw)
        self.s = None
        self.path = None
        v = QtWidgets.QVBoxLayout(self)
        hb = QtWidgets.QHBoxLayout()
        b_open = QtWidgets.QPushButton(tr("Otwórz plik…"))
        b_open.clicked.connect(self.open)
        b_cur = QtWidgets.QPushButton(tr("Otwórz plik danych z parametrów"))
        b_cur.clicked.connect(self.open_current)
        self.b_save = QtWidgets.QPushButton(tr("Zapisz jako…"))
        self.b_save.clicked.connect(self.save)
        self.b_use = QtWidgets.QPushButton(tr("Zapisz i użyj jako plik danych"))
        self.b_use.clicked.connect(self.save_and_use)
        for b in (b_open, b_cur, self.b_save, self.b_use):
            hb.addWidget(b)
        hb.addStretch(1)
        v.addLayout(hb)
        v.addWidget(hint(tr("Lewy klik na górnym wykresie = początek zakresu, prawy klik = koniec. "
                         "Dopasuj pik (Lorentz/Gauss/Voigt + tło liniowe) lub zastąp zakres prostą (Replace) "
                         "albo usuń punkty (Erase), potem Zatwierdź. Wygładzanie: średnia ruchoma N punktów.")))
        ctrl = QtWidgets.QHBoxLayout()
        self.s_min = dspin(-1e6, 1e6, 4, 0.1, 0)
        self.s_max = dspin(-1e6, 1e6, 4, 0.1, 1)
        self.c_model = QtWidgets.QComboBox()
        self.c_model.addItems(MODELS)
        self.ch_fix = QtWidgets.QCheckBox(tr("stała linia bazowa"))
        self.ch_fix.setChecked(True)
        self.ch_fix.setToolTip(tr("Jak w oryginale: dane − dopasowanie + prosta przez końce zakresu.\n"
                               "Odznaczone: odejmowana tylko składowa piku."))
        self.s_deg = ispin(1, 4, 1)
        self.s_deg.setToolTip(tr("Stopień wielomianu tła w dopasowaniu (1 = liniowe)"))
        self.b_fit = QtWidgets.QPushButton(tr("Dopasuj"))
        self.b_fit.setObjectName("primary")
        self.b_acc = QtWidgets.QPushButton(tr("Zatwierdź ✔"))
        self.b_reset = QtWidgets.QPushButton(tr("Reset"))
        self.s_smooth = ispin(1, 501, 1)
        self.b_smooth = QtWidgets.QPushButton(tr("Wygładź"))
        for lab, w in [(tr("od"), self.s_min), (tr("do"), self.s_max), ("", self.c_model), ("", self.ch_fix),
                       (tr("tło st."), self.s_deg), ("", self.b_fit), ("", self.b_acc), ("", self.b_reset),
                       ("N", self.s_smooth), ("", self.b_smooth)]:
            if lab:
                ctrl.addWidget(QtWidgets.QLabel(lab))
            ctrl.addWidget(w)
        ctrl.addStretch(1)
        v.addLayout(ctrl)
        self.b_fit.clicked.connect(self.fit)
        self.b_acc.clicked.connect(self.accept)
        self.b_reset.clicked.connect(self.reset)
        self.b_smooth.clicked.connect(self.do_smooth)
        self.s_min.valueChanged.connect(self.range_changed)
        self.s_max.valueChanged.connect(self.range_changed)
        split = QtWidgets.QSplitter(Qt.Vertical)
        self.p1 = PlotWidget(figsize=(10, 4))
        self.p2 = PlotWidget(figsize=(10, 3))
        split.addWidget(self.p1)
        bottom = QtWidgets.QSplitter(Qt.Horizontal)
        bottom.addWidget(self.p2)
        self.report = QtWidgets.QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        bottom.addWidget(self.report)
        bottom.setSizes([700, 400])
        split.addWidget(bottom)
        split.setSizes([420, 330])
        v.addWidget(split, 1)
        self.p1.canvas.mpl_connect("button_press_event", self.click)
        self.p1.placeholder(tr("Otwórz plik z danymi (2 kolumny)"))
        self.p2.placeholder("")

    # ------------------------------------------------------------------------------
    def _load(self, path):
        d = read_xy(path)
        self.s = RPSSession(d[:, 0], d[:, 1])
        self.path = Path(path)
        for w, val in ((self.s_min, d[0, 0]), (self.s_max, d[-1, 0])):
            w.blockSignals(True)
            w.setValue(val)
            w.blockSignals(False)
        self.s_smooth.setValue(1)
        self.report.setPlainText(tr('{0}\n{1} punktów, x = {2:.4g} – {3:.4g}').format(path, len(d), d[0,0], d[-1,0]))
        self.redraw(reset_view=True)

    def open(self):
        f, _ = QtWidgets.QFileDialog.getOpenFileName(self, tr("Plik do obróbki"), self.mw.params.base_dir,
                                                     tr("Dane (*.dat *.xy *.txt *.chi *.csv);;Wszystkie (*)"))
        if f:
            try:
                self._load(f)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, tr("RPS"), str(e))

    def open_current(self):
        p = self.mw.params.params()
        try:
            self._load(p.path(p.filename))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, tr("RPS"), str(e))

    def click(self, ev):
        if self.s is None or ev.inaxes is None or ev.xdata is None:
            return
        if self.p1.toolbar.mode:     # nie przeszkadzaj w zoom/pan
            return
        if ev.button == 1:
            self.s_min.setValue(ev.xdata)
        elif ev.button == 3:
            self.s_max.setValue(ev.xdata)

    def range_changed(self):
        if self.s is None:
            return
        self.s.set_range(self.s_min.value(), self.s_max.value())
        self.s.fit_x = self.s.fit_y = None
        self.s.y_tmp = self.s.y_sub.copy()
        self.redraw()

    def redraw(self, reset_view=False):
        s = self.s
        f1 = self.p1.fig
        old = None
        if not reset_view and f1.axes:
            old = (f1.axes[0].get_xlim(), f1.axes[0].get_ylim())
        f1.clear()
        ax = f1.add_subplot(111)
        ax.plot(s.x, s.y_raw, color="#888", lw=1, label=tr("dane surowe"))
        ax.plot(s.x, s.y_sub, color=plots.C_BKG, lw=1.2, label=tr("po obróbce"))
        if s.smooth_n > 1:
            ax.plot(s.x, s.y_out, color=plots.C_SAMPLE, lw=1.2, label=tr('wygładzone (N={0})').format(s.smooth_n))
        ax.axvspan(*sorted((s.xmin, s.xmax)), color="#64b5f6", alpha=0.15)
        ax.axvline(s.xmin, color="#1565c0", ls=":", lw=1)
        ax.axvline(s.xmax, color="#1565c0", ls="--", lw=1)
        plots.style_ax(ax, "x", tr("I (j.u.)"), self.path.name if self.path else "")
        ax.legend(fontsize=8)
        if old:
            ax.set_xlim(old[0]); ax.set_ylim(old[1])
        self.p1.canvas.draw_idle()
        f2 = self.p2.fig
        f2.clear()
        ax2 = f2.add_subplot(111)
        m = s.mask()
        if m.sum() > 1:
            ax2.plot(s.x[m], s.y_sub[m], "o-", color="k", ms=2, lw=0.8, label=tr("zakres"))
            if s.fit_x is not None:
                ax2.plot(s.fit_x, s.fit_y, color=plots.C_FIT, lw=1.5, label=tr("dopasowanie"))
            ax2.plot(s.x[m], s.y_tmp[m], color=plots.C_BKG, lw=1.5, label=tr("wynik (przed zatw.)"))
            ax2.legend(fontsize=8)
        plots.style_ax(ax2, "x", "I", tr("Zakres"))
        self.p2.canvas.draw_idle()

    def fit(self):
        if self.s is None:
            return
        model = self.c_model.currentText()
        span = (self.s.x[-1] - self.s.x[0]) or 1.0
        frac = abs(self.s.xmax - self.s.xmin) / span
        if model in ("Lorentz", "Gauss", "Voigt") and frac > 0.25:
            r = QtWidgets.QMessageBox.question(
                self, tr("RPS"),
                tr('Zakres obejmuje {0:.0%} danych. Dopasowanie piku na tak szerokim zakresie\nodejmie sygnał amorficzny (np. główne maksimum S(q)).\n\nUstaw wąski zakres wokół piku krystalicznego (lewy/prawy klik albo pola od–do).\nMimo to dopasować?').format(frac))
            if r != QtWidgets.QMessageBox.Yes:
                return
        try:
            rep = self.s.fit(self.c_model.currentText(), self.ch_fix.isChecked(), self.s_deg.value())
            self.report.setPlainText(rep)
        except Exception as e:
            self.report.setPlainText(tr('Błąd dopasowania: {0}').format(e))
        self.redraw()

    def accept(self):
        if self.s is None:
            return
        try:
            model = self.c_model.currentText()
            self.s.accept(model)
            if model == "Erase":
                for w, val in ((self.s_min, self.s.xmin), (self.s_max, self.s.xmax)):
                    w.blockSignals(True); w.setValue(val); w.blockSignals(False)
            self.report.appendPlainText(tr("\nZatwierdzono: ") + self.s.history[-1])
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, tr("RPS"), str(e))
        self.redraw()

    def reset(self):
        if self.s:
            self.s.reset()
            self.s_smooth.setValue(1)
            self.redraw()

    def do_smooth(self):
        if self.s:
            self.s.smooth_n = self.s_smooth.value()
            self.redraw()

    def save(self):
        if self.s is None:
            return None
        start = str(self.path.with_name(self.path.stem + "_rps.txt")) if self.path else ""
        f, _ = QtWidgets.QFileDialog.getSaveFileName(self, tr("Zapisz"), start, tr("Tekst (*.txt *.dat *.xy)"))
        if f:
            self.s.save(f)
            self.mw.log(tr('RPS: zapisano {0}').format(f))
            return f
        return None

    def save_and_use(self):
        f = self.save()
        if f:
            self.mw.params.f_data.setText(f)
            self.mw.params._files_changed()
            self.mw.log(tr("RPS: plik ustawiony jako plik danych w parametrach."))
