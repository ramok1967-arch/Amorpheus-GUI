# -*- coding: utf-8 -*-
"""
Fizyka: czynniki rozpraszania, normalizacja Krogh-Moe/Norman, iteracja Kaplowa,
funkcja celu chi^2, liczby koordynacyjne, funkcja modyfikujaca.

Jednostki wewnetrzne (jak w oryginalnym Amorpheus):  q [nm^-1],  r [nm],  rho [at/nm^3].

Metoda i oznaczenia za:
  S. Boccato i in., High Pressure Research 42 (2022) 69, doi:10.1080/08957959.2022.2032032
  G. Morard i in., High Pressure Research 33 (2013) 7 (rownanie 10 - normalizacja)
  A. Eggert i in., Phys. Rev. B 65 (2002) 174105 (iteracja Kaplowa)

Ten plik jest czescia przepisanej wersji Amorpheus (GPL-3.0).
"""
from __future__ import annotations

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
from .i18n import tr  # noqa: E402

# numpy >= 2.0 ma trapezoid, starsze tylko trapz
trapz = getattr(np, "trapezoid", None) or np.trapz

N_ITER_DEFAULT = 4          # "prout" w oryginale
FIT_R_STEP = 0.0005         # siatka r dla dopasowan (nm)
FIT_R_MAX = 0.4             # jak w oryginale
FIT_R0 = 1e-6
FIT_EVALS = 500
FIT_TOL = 1e-4
RHO_WINDOW = 50.0           # granice rho: [max(1, rho0-50), rho0+50]
BK_BOUNDS = (0.7, 1.2)


# --------------------------------------------------------------------------------------
# czynniki rozpraszania
# --------------------------------------------------------------------------------------
_sf_cache: dict = {}


def atomic_number(symbol: str) -> int:
    import xraylib as xr
    z = xr.SymbolToAtomicNumber(symbol.strip())
    if z <= 0:
        raise ValueError(tr("Nieznany pierwiastek: '{0}'").format(symbol))
    return int(z)


def scattering_factors(q: np.ndarray, elements, ratio, incoherent: int):
    """Zwraca (incohP, <f^2>, <f>^2) na siatce q [nm^-1] (xraylib, x = sin(theta)/lambda = q/4pi/10)."""
    import xraylib as xr
    ratio = np.asarray(ratio, dtype=float)
    key = (tuple(elements), ratio.tobytes(), int(incoherent), q.tobytes())
    if key in _sf_cache:
        return _sf_cache[key]
    zs = [atomic_number(e) for e in elements]
    ff = np.zeros((len(zs), len(q)))
    sc = np.zeros((len(zs), len(q)))
    xs = [float(i / 4 / np.pi / 10) for i in q]
    for k, z in enumerate(zs):
        ff[k] = np.array([xr.FF_Rayl(z, x) for x in xs])
        sc[k] = np.array([xr.SF_Compt(z, x) for x in xs])
    if incoherent == 0:
        incoh = 0
    else:
        incoh = (ratio[:, None] * sc).sum(axis=0)
    f2med = (ratio[:, None] * ff ** 2).sum(axis=0)
    fmed2 = ((ratio[:, None] * ff).sum(axis=0)) ** 2
    if len(_sf_cache) > 64:
        _sf_cache.clear()
    _sf_cache[key] = (incoh, f2med, fmed2)
    return incoh, f2med, fmed2


# --------------------------------------------------------------------------------------
# normalizacja
# --------------------------------------------------------------------------------------
def normalize(Isa, q, rho, incoh, f2med, fmed2, fix_units: bool = True):
    """S(q) z intensywnosci probki (rownanie 10, Morard 2013).

    fix_units=True  - calki liczone po Q w A^-1 (poprawnie, regula sum -2 pi^2 rho spelniona)
    fix_units=False - dokladnie jak oryginal v1.0.5 (dq w nm^-1, czlon gestosci 10x za slaby)
    """
    Q = q / 10.0
    x = Q if fix_units else q
    f1int = trapz(Q ** 2 * (f2med + incoh) / fmed2, x)
    f2int = trapz(Isa * Q ** 2 / fmed2, x)
    alpha = (-2 * np.pi ** 2 * rho * 1e-3 + f1int) / f2int
    return (alpha * Isa - incoh - (f2med - fmed2)) / fmed2


def lorentz_base(x, a, b, gamma, x0):
    return a + b / (3.14 * gamma * (1 + ((x - x0) / gamma) ** 2))


def prolong_lorentz(q, S0, diff, npts: int = 850):
    """SofQ=2: przedluzenie S(q) ponizej q_min dopasowana lorentzowka (eksperymentalne w oryginale)."""
    sl = slice(diff, min(diff + npts, len(q)))
    p, _ = curve_fit(lorentz_base, q[sl], S0[sl], [80, 20, .1, 30], maxfev=30000)
    return lorentz_base(q, *p)[0:diff]


def extend_q(q_old: np.ndarray):
    """Dolozenie punktow 0 < q < q_min z tym samym krokiem (jak w oryginale)."""
    pasq = q_old[1] - q_old[0]
    addq = np.sort(np.arange(q_old[0], 0, -pasq))[:-1]
    q = np.concatenate((addq, q_old))
    diff = int(np.abs(q - q_old[0]).argmin())
    return q, diff


def fit_r_grid(rmax: float = FIT_R_MAX):
    R = np.arange(0, rmax, FIT_R_STEP)
    R[0] = FIT_R0
    return R


def output_r_grid(rmax: float = 1.0, n: int | None = None):
    """Siatka r dla normalizacji. Dla rmax=1 identyczna z oryginalem (9001 pkt, R[0]=5e-4)."""
    if n is None:
        n = int(round(rmax * 9000)) + 1
    R = np.linspace(0, rmax, n)
    R[0] = 5e-4 if n > 1 else R[0]
    return R


# --------------------------------------------------------------------------------------
# transformaty
# --------------------------------------------------------------------------------------
def transform_F(R, q, S, chunk: int = 600):
    """F(r) = 2/pi * int q (S-1) sin(qr) dq  (liczone porcjami w r, zeby nie zajac GB pamieci)."""
    out = np.empty(len(R))
    w = q * (S - 1)
    for i in range(0, len(R), chunk):
        r = R[i:i + chunk]
        out[i:i + chunk] = 2 / np.pi * trapz(w * np.sin(r[:, None] * q), q, axis=1)
    return out


def transform_F_mod(R, q, S, a, b, chunk: int = 400):
    """F(r) z funkcja modyfikujaca M(Q, Delta(r)) (Lorch z szerokoscia zalezna od r)."""
    out = np.empty(len(R))
    w = q * (S - 1)
    for i in range(0, len(R), chunk):
        r = R[i:i + chunk]
        dR = np.pi / q[-1] * (1 - np.exp(-np.abs(r[:, None] - a) / b))
        x = q * dR
        with np.errstate(invalid="ignore", divide="ignore"):
            M = np.where(x == 0, 1.0, np.sin(x) / x)
        out[i:i + chunk] = 2 / np.pi * trapz(M * w * np.sin(r[:, None] * q), q, axis=1)
    return out


def delta_r(R, q_last, a, b):
    return np.pi / q_last * (1 - np.exp(-np.abs(R - a) / b))


class KaplowEngine:
    """Iteracja Kaplowa na ustalonej siatce q (rozszerzonej do 0) i r.

    Macierz sin(r q) dla r < rmin jest liczona raz - tylko ona jest potrzebna
    do poprawek i do chi^2, dlatego dopasowania sa wielokrotnie szybsze niz w oryginale,
    a wynik jest numerycznie identyczny.
    """

    def __init__(self, q, diff, R, rmin, n_iter=N_ITER_DEFAULT, sofq=1, fix_units=True):
        self.q = q
        self.diff = diff
        self.R = R
        self.rmin = rmin
        self.ind = int(np.abs(R - rmin).argmin())
        self.n_iter = n_iter
        self.sofq = sofq
        self.fix_units = fix_units
        self.Rlow = R[: self.ind]
        self.M = np.sin(self.Rlow[:, None] * q)          # (ind, Nq)

    # -- S0 z intensywnosci ------------------------------------------------------------
    def S0(self, Isa, rho, incoh, f2, fm2):
        q, diff = self.q, self.diff
        S = np.zeros(len(q))
        S[diff:] = normalize(Isa, q[diff:], rho, incoh, f2, fm2, self.fix_units)
        if self.sofq == 0:
            S[:diff] = 0
        elif self.sofq == 1:
            S[:diff] = S[diff]
        elif self.sofq == 2:
            S[:diff] = prolong_lorentz(q, S, diff)
        return S

    def _F_low(self, S):
        return 2 / np.pi * trapz(self.q * (S - 1) * self.M, self.q, axis=1)

    def _correction(self, delF_low):
        # Sinv = 1/q * int_0^rmin dF(r) sin(qr) dr
        return 1 / self.q * trapz(delF_low * self.M.T, self.Rlow, axis=1)

    def iterate(self, S0, rho):
        """Lista S_0..S_n i F(r<rmin) ostatniej iteracji."""
        Ss = [S0]
        F = self._F_low(S0)
        delF = F + 4 * np.pi * self.Rlow * rho
        for _ in range(self.n_iter):
            Sinv = self._correction(delF)
            Sn = Ss[-1] * (1 - Sinv)
            Ss.append(Sn)
            F = self._F_low(Sn)
            delF = F + 4 * np.pi * self.Rlow * rho
        return Ss, F

    def chi2(self, Isa, rho, incoh, f2, fm2):
        S0 = self.S0(Isa, rho, incoh, f2, fm2)
        _, F = self.iterate(S0, rho)
        return float(trapz((F + 4 * np.pi * self.Rlow * rho) ** 2, self.Rlow))

    def full(self, Isa, rho, incoh, f2, fm2):
        """Pelny wynik: S[k], F[k], g[k] na calej siatce R."""
        S0 = self.S0(Isa, rho, incoh, f2, fm2)
        Ss, _ = self.iterate(S0, rho)
        S = np.array(Ss)
        F = np.array([transform_F(self.R, self.q, s) for s in Ss])
        g = 1 + F / (4 * np.pi * self.R * rho)
        return S, F, g


# --------------------------------------------------------------------------------------
# analiza g(r)
# --------------------------------------------------------------------------------------
def density_from_slope(R, F, rmin):
    """Gestosc z nachylenia F(r) = -4 pi rho r dla r < rmin."""
    ind = int(np.abs(R - rmin).argmin())
    if ind < 3:
        return np.nan
    return -stats.linregress(R[:ind], F[:ind]).slope / (4 * np.pi)


def coordination_numbers(R, g, rho, rmin):
    """CN1 = 2 * calka od rmin do maksimum 1. piku (zalozenie symetrii),
    CN2 = calka od rmin do 1. minimum za pikiem.  Zwraca dict lub None."""
    i0 = int(np.abs(R - rmin).argmin())
    peaks, _ = find_peaks(g)
    after = peaks[peaks > i0]
    if len(after) == 0:
        return None
    i1 = int(after[0])
    after2 = peaks[peaks > i1 + 1]
    i_p2 = int(after2[0]) if len(after2) else len(g) - 1
    i2 = i1 + int(g[i1:i_p2].argmin()) if i_p2 > i1 else i1
    w = 4 * np.pi * rho * R ** 2 * g
    cn1 = 2 * trapz(w[i0:i1], R[i0:i1])
    cn2 = trapz(w[i0:i2], R[i0:i2])
    return dict(CN1=float(cn1), CN2=float(cn2), r0=float(R[i0]), r_peak=float(R[i1]),
                r_min=float(R[i2]), i_peak=i1)
