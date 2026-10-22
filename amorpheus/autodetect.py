# -*- coding: utf-8 -*-
"""
Rozpoznawanie parametrow analizy z pliku danych:
  * jednostka osi x i dlugosc fali z naglowka (pyFAI / Dioptas / Fit2D .chi),
  * korekta polaryzacji (pyFAI: "Polarization factor"),
  * zakres danych bez zer, propozycja q_min / q_max,
  * sklad z nazwy pliku (np. "Mg61Cu28Gd11" -> Mg 0.61, Cu 0.28, Gd 0.11; "wt" -> przeliczenie na at.),
  * gestosc liczbowa z gestosci masowej,
  * propozycja pliku tla w tym samym folderze.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np

from .data import Params, read_xy, tth_to_q

AVOGADRO_NM = 602.214076   # N_A * 1e-21: [at/nm^3] = 602.2 * d[g/cm^3] / M[g/mol]
BKG_WORDS = ("empty", "bkg", "background", "tlo", "tło", "gasket", "cell", "blank", "air", "pusta")


@dataclass
class Detected:
    unit: Optional[str] = None          # "q_A", "q_nm", "2th_deg", "2th_rad" albo None
    wavelength_nm: Optional[float] = None
    polarization: Optional[str] = None  # tekst z naglowka ("None", "0.99"...) albo None
    source: str = ""
    x_lo: float = np.nan                # zakres danych (bez zer) w jednostkach pliku
    x_hi: float = np.nan
    n_points: int = 0
    main_peak: float = np.nan           # pozycja 1. maksimum [nm^-1]
    warnings: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------------------
def _header_lines(path, nmax=300):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i > nmax:
                break
            s = line.strip()
            if not s:
                continue
            if s[0] in "#!%;" or not (s[0].isdigit() or s[0] in "+-."):
                out.append(s)
            elif i > 40:
                break
    return out


def sniff(path) -> Detected:
    det = Detected()
    hdr = _header_lines(path)
    text = "\n".join(hdr)
    low = text.lower()
    if "pyfai" in low:
        det.source = "pyFAI"
    if "dioptas" in low:
        det.source = "Dioptas"
    # jednostka osi (pyFAI/Dioptas: kolumna w ostatniej linii naglowka)
    for key, unit in (("q_a^-1", "q_A"), ("q_nm^-1", "q_nm"), ("2th_deg", "2th_deg"), ("2th_rad", "2th_rad")):
        if key in low:
            det.unit = unit
    if det.unit is None:   # Fit2D .chi i opisy slowne
        if re.search(r"2-?theta|two.?theta|2θ", low):
            det.unit = "2th_rad" if "rad" in low else "2th_deg"
        elif re.search(r"q\s*\(\s*(angstrom|å|a\^-1|1/a)", low) or "angstroms" in low:
            det.unit = "q_A"
        elif re.search(r"q\s*\(\s*(nm|1/nm)", low):
            det.unit = "q_nm"
    # dlugosc fali
    m = re.search(r"wavelength\s*[:=]\s*([0-9.eE+-]+)\s*(m|nm|a|å|angstrom)?\b", text, re.I)
    if m:
        val = float(m.group(1))
        u = (m.group(2) or "").lower()
        if u == "m" or (not u and val < 1e-6):
            det.wavelength_nm = val * 1e9
        elif u in ("a", "å", "angstrom"):
            det.wavelength_nm = val / 10
        elif u == "nm":
            det.wavelength_nm = val
        elif 0.05 < val < 3:          # bez jednostki: najpewniej A
            det.wavelength_nm = val / 10
    m = re.search(r"polari[sz]ation(?: factor)?\s*[:=]\s*([^\s]+)", text, re.I)
    if m:
        det.polarization = m.group(1)
    # dane
    d = read_xy(path)
    det.x_lo, det.x_hi, det.n_points = float(d[0, 0]), float(d[-1, 0]), len(d)
    full = read_xy(path, trim_zeros=False)
    if len(full) > len(d):
        det.warnings.append(f"Pominięto {len(full) - len(d)} punktów na krańcach danych "
                            f"(obszar z I = 0 – brak pokrycia detektora; dane do x = {d[-1, 0]:.4g}).")
    if det.unit is None:
        # heurystyka: Q w A^-1 rzadko > 30, 2theta zwykle 2..60, Q w nm^-1 zwykle > 30
        det.warnings.append("Nie rozpoznano jednostki osi z nagłówka – sprawdź format.")
        det.unit = "q_A" if det.x_hi < 30 else "q_nm"
    if det.unit == "2th_rad":
        det.warnings.append("Oś 2θ w radianach nie jest obsługiwana – przelicz na stopnie albo Q.")
    if det.polarization is not None and det.polarization.lower() in ("none", "0", "0.0"):
        det.warnings.append("Brak korekty polaryzacji w integracji (Polarization factor: None).")
    if det.unit.startswith("2th") and det.wavelength_nm is None:
        det.warnings.append("Dane w 2θ, a w nagłówku nie ma długości fali – podaj λ.")
    return det


# --------------------------------------------------------------------------------------
_PAIR = re.compile(r"([A-Z][a-z]?)(\d+(?:[.,]\d+)?)?")


def _is_element(sym: str) -> bool:
    import xraylib as xr
    try:
        return xr.SymbolToAtomicNumber(sym) > 0
    except Exception:
        return False


def composition_from_name(name: str):
    """Najdluzszy ciag symboli pierwiastkow z liczbami w nazwie pliku -> (elements, fractions).

    'Mg61Cu28Gd11 %at.' -> (['Mg','Cu','Gd'], [0.61,0.28,0.11]); 'wt' w nazwie -> przeliczenie z % wag.
    Zwraca ([], []) gdy nic sensownego nie znaleziono.
    """
    import xraylib as xr
    stem = Path(name).stem
    best = []
    i = 0
    while i < len(stem):
        run, j = [], i
        while j < len(stem):
            m = _PAIR.match(stem, j)
            if not m or m.end() == j:
                break
            sym, num = m.group(1), m.group(2)
            if not _is_element(sym):
                break
            run.append((sym, float(num.replace(",", ".")) if num else None))
            j = m.end()
        if len(run) >= 2 and any(n is not None for _, n in run) and len(run) > len(best):
            best = run
        i = j + 1 if j > i else i + 1
    if not best:
        return [], []
    el = [s for s, _ in best]
    x = np.array([n if n is not None else 1.0 for _, n in best], float)
    if re.search(r"wt|mas", stem, re.I) and not re.search(r"at", stem, re.I):
        w = np.array([xr.AtomicWeight(xr.SymbolToAtomicNumber(e)) for e in el])
        x = x / w
    x = x / x.sum()
    return el, [float(round(v, 6)) for v in x]


def mean_atomic_mass(elements, fractions):
    import xraylib as xr
    return float(sum(f * xr.AtomicWeight(xr.SymbolToAtomicNumber(e)) for e, f in zip(elements, fractions) if e))


def number_density(elements, fractions, mass_density):
    """Gestosc liczbowa [at/nm^3] z gestosci masowej [g/cm^3]."""
    m = mean_atomic_mass(elements, fractions)
    return AVOGADRO_NM * mass_density / m if m > 0 else np.nan


def suggest_background(path) -> List[Path]:
    path = Path(path)
    out = []
    for f in sorted(path.parent.iterdir()):
        if f == path or not f.is_file() or f.suffix.lower() not in (".xy", ".dat", ".txt", ".chi", ".csv"):
            continue
        n = f.name.lower()
        if any(w in n for w in BKG_WORDS) and "_init" not in n and not n.startswith(("norm", "minrmin", "minqmax")):
            out.append(f)
    return out


def project_path(data_path) -> Path:
    """Plik projektu obok danych: <nazwa_danych>_Init.txt"""
    p = Path(data_path)
    return p.with_name(p.stem + "_Init.txt")


def _main_peak_q(q, I):
    """Pozycja pierwszego maksimum amorficznego [nm^-1] w typowym zakresie 10-60 nm^-1."""
    m = (q >= max(q[0], 10)) & (q <= min(q[-1], 60))
    if m.sum() < 10:
        m = np.ones_like(q, bool)
    k = max(3, int(m.sum() / 100))
    Is = np.convolve(I[m], np.ones(k) / k, mode="same")
    return float(q[m][int(np.argmax(Is))])


def build_params(data_path, bkg_path=None, base: Optional[Params] = None,
                 unit: Optional[str] = None, lambd_nm: Optional[float] = None) -> (Params, Detected):
    """Parametry startowe dla pliku danych (i opcjonalnie tla).
    unit / lambd_nm - wymuszenie jednostki osi i dlugosci fali (gdy uzytkownik poprawi autodetekcje)."""
    data_path = Path(data_path)
    det = sniff(data_path)
    if unit:
        det.unit = unit
    if lambd_nm:
        det.wavelength_nm = lambd_nm
    p = (base or Params()).copy()
    p.base_dir = str(data_path.parent)
    p.filename = data_path.name
    has_bkg = bkg_path is not None and str(bkg_path).strip() != ""
    if has_bkg:
        bp = Path(bkg_path)
        p.filename_bkg = bp.name if bp.parent == data_path.parent else str(bp)
    else:
        p.filename_bkg = ""
    if det.unit and det.unit.startswith("2th"):
        p.file_format = 2 if has_bkg else 1
        if det.wavelength_nm:
            p.lambd = det.wavelength_nm
    else:
        p.file_format = 4 if has_bkg else 3
        p.q_unit = "nm" if det.unit == "q_nm" else "A"
        if det.wavelength_nm:
            p.lambd = det.wavelength_nm
    p.incoherent = 1
    p.sofq = 1
    p.normalization = 0
    p.rmin = 0.20
    p.bkfactor = 1.0
    el, x = composition_from_name(data_path.name)
    if el:
        el = (el + [""] * 6)[:max(6, len(el))]
        x = (x + [0.0] * 6)[:max(6, len(x))]
        p.elements, p.contents = el, x
    else:
        det.warnings.append("Nie odczytano składu z nazwy pliku – wpisz go ręcznie.")
        p.elements, p.contents = [""] * 6, [0.0] * 6
    # zakres q
    try:
        d = read_xy(data_path)
        q = p.x_to_q(d[:, 0])
        lo, hi = float(q[0]), float(q[-1])
        if has_bkg:
            b = read_xy(p.path(p.filename_bkg))
            qb = p.x_to_q(b[:, 0])
            lo, hi = max(lo, float(qb[0])), min(hi, float(qb[-1]))
        qp = _main_peak_q(q, d[:, 1])
        p.qmin = float(np.ceil(max(lo * 1.02, 0.55 * qp) * 2) / 2)
        p.qmax = float(np.floor(hi * 0.99))
        if p.qmax <= p.qmin:
            p.qmin, p.qmax = lo, hi
        det.main_peak = qp
    except Exception as e:
        det.warnings.append(f"Nie ustalono zakresu q: {e}")
    p.save_norm, p.save_rmin, p.save_qmax = "Norm", "MinRmin", "MinQmax"
    return p, det
