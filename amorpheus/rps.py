# -*- coding: utf-8 -*-
"""
RPS - Remove Peaks and Smooth: usuwanie pikow krystalicznych i wygladzanie (odpowiednik RPS.py).

Model postepowania jak w oryginale:
  * wybierz zakres [xmin, xmax],
  * Fit: pik (Lorentz/Gauss/Voigt) + tlo liniowe (lub wielomian) w zakresie,
    wynik "na probe" = dane - dopasowanie + linia bazowa przez konce zakresu (fix_base)
    albo dane - sama skladowa piku (bez fix_base),
  * Replace: zastapienie zakresu odcinkiem prostej miedzy koncami,
  * Erase: usuniecie punktow z zakresu,
  * Accept zatwierdza zmiane, Reset wraca do danych surowych,
  * Smooth: srednia ruchoma (okno N punktow) na wyniku.
"""
from __future__ import annotations

import numpy as np
from .i18n import tr  # noqa: E402

MODELS = ["Lorentz", "Gauss", "Voigt", "Erase", "Replace"]


def smooth(y, box_pts: int):
    box_pts = int(box_pts)
    if box_pts <= 1:
        return np.array(y, dtype=float, copy=True)
    box = np.ones(box_pts) / box_pts
    ys = np.convolve(y, box, mode="same")
    h = box_pts // 2
    ys[:h] = y[:h]                       # brzegi bez artefaktow splotu
    ys[len(y) - (box_pts - 1 - h):] = y[len(y) - (box_pts - 1 - h):]
    return ys


class RPSSession:
    def __init__(self, x, y):
        self.x = np.asarray(x, float).copy()
        self.y_raw = np.asarray(y, float).copy()
        self.y_sub = self.y_raw.copy()       # wynik zatwierdzony
        self.y_tmp = self.y_raw.copy()       # wynik "na probe" (po Fit/Replace)
        self.smooth_n = 1
        self.xmin, self.xmax = float(self.x[0]), float(self.x[-1])
        self.fit_x = None
        self.fit_y = None
        self.report = ""
        self.history = []                    # opis operacji

    # ------------------------------------------------------------------------------
    @property
    def y_out(self):
        return smooth(self.y_sub, self.smooth_n)

    def mask(self):
        lo, hi = sorted((self.xmin, self.xmax))
        return (self.x >= lo) & (self.x <= hi)

    def set_range(self, xmin, xmax):
        self.xmin, self.xmax = float(xmin), float(xmax)

    def zoom(self):
        m = self.mask()
        return self.x[m], self.y_sub[m]

    # ------------------------------------------------------------------------------
    def fit(self, model="Lorentz", fix_base=True, poly_degree=1):
        from lmfit.models import LorentzianModel, GaussianModel, VoigtModel, LinearModel, PolynomialModel
        xz, yz = self.zoom()
        if len(xz) < 5:
            raise ValueError(tr("Za mało punktów w zakresie (min. 5)."))
        if model == "Replace":
            return self._replace()
        if model == "Erase":
            self.y_tmp = self.y_sub.copy()
            self.fit_x = self.fit_y = None
            self.report = tr("Erase: kliknij 'Zatwierdź', aby usunąć punkty z zakresu.")
            return self.report
        slope = (yz[0] - yz[-1]) / (xz[0] - xz[-1])
        intercept = yz[0] - slope * xz[0]
        if poly_degree > 1:
            bg = PolynomialModel(degree=int(poly_degree), prefix="line_")
            pars = bg.make_params(**{f"c{k}": 0.0 for k in range(int(poly_degree) + 1)})
            pars["line_c0"].set(value=intercept)
            pars["line_c1"].set(value=slope)
        else:
            bg = LinearModel(prefix="line_")
            pars = bg.make_params(slope=slope, intercept=intercept)
        peak = {"Lorentz": LorentzianModel, "Gauss": GaussianModel, "Voigt": VoigtModel}[model](prefix="pk_")
        center = xz[yz.argmax()]
        amp = yz.max() - (intercept + slope * center)
        width = max((xz[-1] - xz[0]) / 10, 1e-6)
        pars += peak.make_params(amplitude=amp * width * np.pi, center=center, sigma=width)
        pars["pk_center"].set(min=xz[0], max=xz[-1])
        pars["pk_sigma"].set(min=0)
        if model == "Voigt":
            pars["pk_gamma"].set(value=width, vary=True, expr="", min=0)
        if fix_base and poly_degree <= 1:
            pars["line_slope"].vary = False
        mdl = peak + bg
        out = mdl.fit(yz, pars, x=xz)
        self.fit_x = np.linspace(xz[0], xz[-1], 1000)
        self.fit_y = out.eval(x=self.fit_x)
        m = self.mask()
        res = self.y_sub.copy()
        if fix_base:
            base_line = intercept + slope * self.x
            res[m] = self.y_sub[m] - out.eval(x=self.x)[m] + base_line[m]
        else:
            comp = out.eval_components(x=self.x)["pk_"]
            res[m] = self.y_sub[m] - comp[m]
        self.y_tmp = res
        self.report = out.fit_report()
        self._pending = f"{model} [{self.xmin:.4g}, {self.xmax:.4g}]"
        return self.report

    def _replace(self):
        m = self.mask()
        idx = np.where(m)[0]
        x0, x1 = self.x[idx[0]], self.x[idx[-1]]
        y0, y1 = self.y_sub[idx[0]], self.y_sub[idx[-1]]
        res = self.y_sub.copy()
        res[m] = y0 + (y1 - y0) * (self.x[m] - x0) / (x1 - x0)
        self.y_tmp = res
        self.fit_x, self.fit_y = self.x[m], res[m]
        self.report = tr("Replace: odcinek prostej {0:.4g} – {1:.4g}").format(x0, x1)
        self._pending = f"Replace [{x0:.4g}, {x1:.4g}]"
        return self.report

    def accept(self, model):
        if model == "Erase":
            m = self.mask()
            if m.all():
                raise ValueError(tr("Nie można usunąć wszystkich punktów."))
            self.x, self.y_raw, self.y_sub = self.x[~m], self.y_raw[~m], self.y_sub[~m]
            self.y_tmp = self.y_sub.copy()
            self.history.append(f"Erase [{self.xmin:.4g}, {self.xmax:.4g}]")
            self.xmin, self.xmax = float(self.x[0]), float(self.x[-1])
        else:
            self.y_sub = self.y_tmp.copy()
            self.history.append(getattr(self, "_pending", model))
        self.fit_x = self.fit_y = None

    def reset(self):
        self.y_sub = self.y_raw.copy()
        self.y_tmp = self.y_raw.copy()
        self.fit_x = self.fit_y = None
        self.smooth_n = 1
        self.history.append("Reset")

    def save(self, path):
        hdr = "RPS (Amorpheus-Qt): " + "; ".join(self.history) + f"; smooth={self.smooth_n}"
        np.savetxt(path, np.c_[self.x, self.y_out], header=hdr, encoding="utf-8")
