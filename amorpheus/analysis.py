# -*- coding: utf-8 -*-
"""
Operacje wysokiego poziomu - odpowiedniki opcji menu oryginalnego Amorpheus:
  [n] normalizacja, [r] petla po rmin, [x] petla po qmax, [c] mapa chi^2, [b] batch.

Funkcje nie maja zadnych input()/print() - przyjmuja opcjonalne callbacki
progress(i, n, tekst) i cancelled() -> bool, wiec dzialaja zarowno w GUI (watek), jak i w skryptach.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import numpy as np
from lmfit import Parameters, minimize

from . import physics as ph
from .data import Params, Dataset, prepare

Progress = Optional[Callable[[int, int, str], None]]
Cancelled = Optional[Callable[[], bool]]


def _noprog(*a):
    pass


def _never():
    return False


def inclusive_range(start, stop, step):
    """Zakres z krokiem, wlacznie z koncem (odporny na bledy zaokraglen)."""
    if step <= 0:
        raise ValueError("Krok musi byc dodatni.")
    n = int(np.floor((stop - start) / step + 1e-9)) + 1
    if n < 1:
        raise ValueError("Pusty zakres.")
    return start + step * np.arange(n)


# --------------------------------------------------------------------------------------
# dopasowanie rho (i bkfactor)
# --------------------------------------------------------------------------------------
@dataclass
class FitResult:
    rmin: float
    rho: float
    bkfactor: float
    chi2: float
    nfev: int
    seconds: float
    qmax: float = np.nan

    def row(self):
        return [self.rmin, self.rho, self.bkfactor, self.chi2]


class Problem:
    """Dane + siatki przygotowane do wielokrotnego liczenia chi^2."""

    def __init__(self, p: Params, ds: Optional[Dataset] = None, rmin: Optional[float] = None,
                 R: Optional[np.ndarray] = None, qmax: Optional[float] = None):
        self.p = p
        self.ds = ds if ds is not None else prepare(p, qmax=qmax)
        self.q, self.diff = ph.extend_q(self.ds.q)
        self.rmin = p.rmin if rmin is None else rmin
        self.R = ph.fit_r_grid() if R is None else R
        self.engine = ph.KaplowEngine(self.q, self.diff, self.R, self.rmin, n_iter=p.n_iter,
                                      sofq=p.sofq, fix_units=p.fix_norm_units)

    def chi2(self, rho, bk):
        ds = self.ds
        return self.engine.chi2(ds.Isa(bk), rho, ds.incoh, ds.f2, ds.fm2)

    def fit(self, rho0, bk0) -> FitResult:
        t0 = time.time()
        pars = Parameters()
        pars.add("rhomi", value=rho0, min=max(1, rho0 - ph.RHO_WINDOW), max=rho0 + ph.RHO_WINDOW)
        if self.p.has_bkg:
            pars.add("bkfactor", value=bk0, min=ph.BK_BOUNDS[0], max=ph.BK_BOUNDS[1])

        def objective(pp):
            v = pp.valuesdict()
            return self.chi2(v["rhomi"], v.get("bkfactor", 0.0))

        out = minimize(objective, pars, method="nelder",
                       options={"maxfev": ph.FIT_EVALS, "fatol": ph.FIT_TOL, "xatol": ph.FIT_TOL})
        rho = out.params["rhomi"].value
        bk = out.params["bkfactor"].value if self.p.has_bkg else 0.0
        return FitResult(self.rmin, rho, bk, self.chi2(rho, bk), out.nfev, time.time() - t0)


def fit_density(p: Params, rho0=None, bk0=None, rmin=None, qmax=None) -> FitResult:
    pr = Problem(p, rmin=rmin, qmax=qmax)
    r = pr.fit(p.rho if rho0 is None else rho0, p.bkfactor if bk0 is None else bk0)
    r.qmax = p.qmax if qmax is None else qmax
    return r


# --------------------------------------------------------------------------------------
# [n] normalizacja
# --------------------------------------------------------------------------------------
@dataclass
class NormResult:
    p: Params
    rho: float
    bkfactor: float
    q_data: np.ndarray            # siatka danych (qmin..qmax)
    Imeas: np.ndarray
    Ibkg: Optional[np.ndarray]
    Isa: np.ndarray
    q: np.ndarray                 # siatka rozszerzona do 0
    S: np.ndarray                 # (n_iter+1, Nq)
    R: np.ndarray
    F: np.ndarray                 # (n_iter+1, NR)
    g: np.ndarray
    dens_slope: np.ndarray        # gestosc z nachylenia F(r<rmin) dla kazdej iteracji
    cn: List[Optional[dict]]
    mod_a: float = np.nan         # funkcja modyfikujaca - domyslne parametry
    mod_b: float = np.nan
    g_mod: Optional[np.ndarray] = None
    F_mod: Optional[np.ndarray] = None
    dR: Optional[np.ndarray] = None

    def apply_modification(self, a, b):
        self.mod_a, self.mod_b = float(a), float(b)
        self.F_mod = ph.transform_F_mod(self.R, self.q, self.S[-1], a, b)
        self.g_mod = 1 + self.F_mod / (4 * np.pi * self.R * self.rho)
        self.dR = ph.delta_r(self.R, self.q[-1], a, b)


def run_normalization(p: Params, rho=None, bk=None, ds: Optional[Dataset] = None) -> NormResult:
    rho = p.rho if rho is None else rho
    bk = p.bkfactor if bk is None else bk
    ds = ds if ds is not None else prepare(p)
    R = ph.output_r_grid(p.rmax_out)
    q, diff = ph.extend_q(ds.q)
    eng = ph.KaplowEngine(q, diff, R, p.rmin, n_iter=p.n_iter, sofq=p.sofq, fix_units=p.fix_norm_units)
    Isa = ds.Isa(bk) if p.has_bkg else ds.Imeas
    S, F, g = eng.full(Isa, rho, ds.incoh, ds.f2, ds.fm2)
    dens = np.array([ph.density_from_slope(R, F[i], p.rmin) for i in range(len(F))])
    cn = [ph.coordination_numbers(R, g[i], rho, p.rmin) for i in range(len(g))]
    res = NormResult(p=p.copy(), rho=rho, bkfactor=bk if p.has_bkg else 0.0, q_data=ds.q,
                     Imeas=ds.Imeas, Ibkg=ds.Ibkg, Isa=Isa, q=q, S=S, R=R, F=F, g=g,
                     dens_slope=dens, cn=cn)
    last = cn[-1]
    if last is not None:
        res.mod_a = last["r_peak"]
        res.mod_b = last["r_peak"] - p.rmin
    if p.normalization == 1 and last is not None and res.mod_b > 0:
        res.apply_modification(res.mod_a, res.mod_b)
    return res


# --------------------------------------------------------------------------------------
# [r] petla rmin, [x] petla qmax
# --------------------------------------------------------------------------------------
def loop_rmin(p: Params, values, rho0, bk0, progress: Progress = None,
              cancelled: Cancelled = None, on_result=None) -> List[FitResult]:
    progress = progress or _noprog
    cancelled = cancelled or _never
    ds = prepare(p)
    out = []
    for i, r in enumerate(values):
        if cancelled():
            break
        progress(i, len(values), f"rmin = {r:.4f} nm")
        res = Problem(p, ds=ds, rmin=float(r)).fit(rho0, bk0)
        out.append(res)
        if on_result:
            on_result(res)
    progress(len(out), len(values), "gotowe")
    return out


def loop_qmax(p: Params, values, rho0, bk0, progress: Progress = None,
              cancelled: Cancelled = None, on_result=None) -> List[FitResult]:
    progress = progress or _noprog
    cancelled = cancelled or _never
    out = []
    for i, qm in enumerate(values):
        if cancelled():
            break
        progress(i, len(values), f"qmax = {qm:.3f} nm⁻¹")
        res = Problem(p, qmax=float(qm)).fit(rho0, bk0)
        res.qmax = float(qm)
        out.append(res)
        if on_result:
            on_result(res)
    progress(len(out), len(values), "gotowe")
    return out


# --------------------------------------------------------------------------------------
# [c] mapa chi^2
# --------------------------------------------------------------------------------------
@dataclass
class Chi2Map:
    rho: np.ndarray
    bk: np.ndarray
    Z: np.ndarray                 # Z[i_rho, j_bk]
    rmin: float
    rho_c: float
    bk_c: float
    complete: bool = True

    @property
    def Znorm(self):
        return self.Z / np.nanmin(self.Z)

    def minimum(self):
        i, j = np.unravel_index(np.nanargmin(self.Z), self.Z.shape)
        return self.rho[i], self.bk[j], self.Z[i, j]


def chi2_map(p: Params, rmin, rho_c, rho_width, bk_c, bk_width, n_rho, n_bk,
             progress: Progress = None, cancelled: Cancelled = None) -> Chi2Map:
    if not p.has_bkg:
        raise ValueError("Mapa chi² wymaga danych z tlem (format 2 lub 4).")
    progress = progress or _noprog
    cancelled = cancelled or _never
    pr = Problem(p, rmin=rmin)
    x = np.linspace(rho_c - rho_width / 2, rho_c + rho_width / 2, int(n_rho))
    y = np.linspace(bk_c - bk_width / 2, bk_c + bk_width / 2, int(n_bk))
    Z = np.full((len(x), len(y)), np.nan)
    tot = len(x) * len(y)
    done = True
    for i, xv in enumerate(x):
        for j, yv in enumerate(y):
            if cancelled():
                done = False
                break
            Z[i, j] = pr.chi2(xv, yv)
            k = i * len(y) + j + 1
            if k % 5 == 0 or k == tot:
                progress(k, tot, f"{k}/{tot}")
        if not done:
            break
    return Chi2Map(x, y, Z, rmin, rho_c, bk_c, done)


# --------------------------------------------------------------------------------------
# [b] batch
# --------------------------------------------------------------------------------------
@dataclass
class BatchItem:
    row: object
    fit: Optional[FitResult] = None
    norm: Optional[NormResult] = None
    error: str = ""


def run_batch(rows, progress: Progress = None, cancelled: Cancelled = None,
              on_item=None, log=None) -> List[BatchItem]:
    """Dla kazdego wiersza: dopasowanie rho/bk przy rmin z wiersza, potem normalizacja."""
    progress = progress or _noprog
    cancelled = cancelled or _never
    log = log or (lambda s: None)
    items = []
    for i, row in enumerate(rows):
        if cancelled():
            break
        p = row.params
        progress(i, len(rows), f"{row.label}: dopasowanie")
        it = BatchItem(row)
        try:
            errs = p.validate()
            if errs:
                raise ValueError("; ".join(errs))
            ds = prepare(p)
            fr = Problem(p, ds=ds).fit(p.rho, p.bkfactor)
            it.fit = fr
            log(f"[{i+1}/{len(rows)}] {row.label}: rho = {fr.rho:.3f} at/nm³, "
                f"bk = {fr.bkfactor:.4f}, χ² = {fr.chi2:.4g}  ({fr.seconds:.1f} s)")
            progress(i, len(rows), f"{row.label}: normalizacja")
            it.norm = run_normalization(p, rho=fr.rho, bk=fr.bkfactor, ds=ds)
        except Exception as e:  # jeden zly wiersz nie przerywa calosci
            it.error = str(e)
            log(f"[{i+1}/{len(rows)}] {row.label}: BLAD - {e}")
        items.append(it)
        if on_item:
            on_item(it)
    progress(len(items), len(rows), "gotowe")
    return items
