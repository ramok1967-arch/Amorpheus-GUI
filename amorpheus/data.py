# -*- coding: utf-8 -*-
"""
Parametry, plik Init.txt (zgodny z oryginalnym Amorpheus), wczytywanie danych i tabeli batch.
"""
from __future__ import annotations

import ast
import configparser
import copy
import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

import numpy as np
from scipy.interpolate import Akima1DInterpolator

from . import physics as ph

FILE_FORMATS = {
    1: "2θ, bez tła",
    2: "2θ + tło",
    3: "Q, bez tła",
    4: "Q + tło",
}
N_POINTS = 2500  # liczba punktow siatki (jak w oryginale)

# nazwy kluczy w Init.txt - dokladnie jak w oryginale (kolejnosc ma znaczenie dla batcha)
INIT_KEYS = [
    ("filename", "Filename", str),
    ("filename_bkg", "Filename background", str),
    ("file_format", "File Format", int),
    ("incoherent", "incoherent (1 on empty cell, 0 on sample)", int),
    ("lambd", "lambda (nm)", float),
    ("qmin", "qmin (nm-1)", float),
    ("qmax", "qmax (nm-1)", float),
    ("rmin", "rmin (nm)", float),
    ("bkfactor", "bkfactor", float),
    ("rho", "density (at/nm3)", float),
    ("normalization", "Normalization Type", int),
    ("sofq", "SofQ", int),
    ("qstep", "QStep", int),
    ("save_norm", "Normalization save filename", str),
    ("save_rmin", "Density rmin save filename", str),
    ("save_qmax", "Density qmax save filename", str),
]
EXTRA_SECTION = "Amorpheus-Qt"


@dataclass
class Params:
    filename: str = "Cerium.dat"
    filename_bkg: str = "background.xy"
    file_format: int = 4
    incoherent: int = 1
    lambd: float = 0.03738
    qmin: float = 15.0
    qmax: float = 78.0
    rmin: float = 0.22
    bkfactor: float = 0.927
    rho: float = 34.68
    normalization: int = 0
    sofq: int = 1
    qstep: int = 0
    save_norm: str = "Norm"
    save_rmin: str = "MinRmin"
    save_qmax: str = "MinQmax"
    elements: List[str] = field(default_factory=lambda: ["Ce", "Al", "Ni", "Cu", "Fe", "C"])
    contents: List[float] = field(default_factory=lambda: [0.7, 0.1, 0.1, 0.1, 0.0, 0.0])
    # --- opcje dodane w tej wersji (zapisywane w osobnej sekcji Init.txt) ---
    fix_norm_units: bool = True     # poprawka jednostek w normalizacji
    n_iter: int = 4                 # liczba iteracji Kaplowa
    rmax_out: float = 1.0           # zakres r dla wynikow [nm]
    dpi: int = 300
    q_unit: str = "A"               # formaty 3/4: Q w pliku w A^-1 ("A") albo nm^-1 ("nm")
    base_dir: str = ""              # folder, wzgledem ktorego liczone sa sciezki

    # ------------------------------------------------------------------------------
    def copy(self) -> "Params":
        return copy.deepcopy(self)

    @property
    def has_bkg(self) -> bool:
        return self.file_format in (2, 4)

    @property
    def is_theta(self) -> bool:
        return self.file_format in (1, 2)

    def x_to_q(self, x):
        """Os x pliku -> q [nm^-1]."""
        x = np.asarray(x, dtype=float)
        if self.is_theta:
            return tth_to_q(x, self.lambd)
        return x * 10.0 if self.q_unit != "nm" else x

    @property
    def q_factor(self) -> float:
        """Mnoznik osi x -> nm^-1 dla formatow Q."""
        return 10.0 if self.q_unit != "nm" else 1.0

    def active_composition(self):
        el, c = [], []
        for e, x in zip(self.elements, self.contents):
            if e and e.strip():
                el.append(e.strip())
                c.append(float(x))
        return el, np.array(c, dtype=float)

    def path(self, name: str) -> Path:
        p = Path(name)
        if not p.is_absolute() and self.base_dir:
            p = Path(self.base_dir) / p
        if not p.exists() and p.parent.is_dir():
            # jak na Windows: nazwa bez rozrozniania wielkosci liter
            low = p.name.lower()
            for c in p.parent.iterdir():
                if c.name.lower() == low:
                    return c
        return p

    def validate(self) -> List[str]:
        """Lista problemow (pusta = OK)."""
        err = []
        if self.file_format not in FILE_FORMATS:
            err.append("Format pliku musi byc 1-4.")
        if self.qmin <= 0 or self.qmax <= self.qmin:
            err.append("Wymagane 0 < qmin < qmax.")
        if not (0 < self.rmin <= ph.FIT_R_MAX):
            err.append(f"rmin musi byc w zakresie (0, {ph.FIT_R_MAX}] nm.")
        if self.rho <= 0:
            err.append("Gestosc musi byc dodatnia.")
        el, c = self.active_composition()
        if not el:
            err.append("Podaj sklad (co najmniej jeden pierwiastek).")
        elif abs(c.sum() - 1) > 1e-4:
            err.append(f"Suma udzialow = {c.sum():.4f}, a powinna byc 1.")
        if self.is_theta and self.lambd <= 0:
            err.append("Dla danych w 2θ podaj dlugosc fali λ > 0.")
        for e in el:
            try:
                ph.atomic_number(e)
            except Exception:
                err.append(f"Nieznany pierwiastek: {e}")
        return err


# --------------------------------------------------------------------------------------
# Init.txt
# --------------------------------------------------------------------------------------
def _parse_contents(text: str) -> List[float]:
    t = text.replace("[", " ").replace("]", " ").replace(",", " ")
    return [float(x) for x in t.split()]


def load_init(path) -> Params:
    path = Path(path)
    cfg = configparser.ConfigParser(interpolation=None)   # '%' w nazwach plikow
    cfg.optionxform = str
    with open(path, encoding="utf-8", errors="replace") as f:
        cfg.read_file(f)
    sec = cfg["Parameters"]
    p = Params()
    for attr, key, typ in INIT_KEYS:
        if key in sec:
            raw = sec[key].strip()
            if typ is int:
                setattr(p, attr, int(float(raw)))
            elif typ is float:
                setattr(p, attr, float(raw))
            else:
                setattr(p, attr, raw)
    if "Elements" in sec:
        p.elements = [str(e).strip() for e in ast.literal_eval(sec["Elements"])]
    if "Content" in sec:
        p.contents = _parse_contents(sec["Content"])
    n = max(len(p.elements), len(p.contents))
    p.elements += [""] * (n - len(p.elements))
    p.contents += [0.0] * (n - len(p.contents))
    if cfg.has_section(EXTRA_SECTION):
        ex = cfg[EXTRA_SECTION]
        p.fix_norm_units = ex.getboolean("fix_norm_units", p.fix_norm_units)
        p.n_iter = ex.getint("n_iter", p.n_iter)
        p.rmax_out = ex.getfloat("rmax_out", p.rmax_out)
        p.dpi = ex.getint("dpi", p.dpi)
        p.q_unit = ex.get("q_unit", p.q_unit).strip() or "A"
    else:
        # plik z oryginalu - domyslnie zachowujemy poprawke jednostek
        p.fix_norm_units = True
    p.base_dir = str(path.parent)
    return p


def save_init(p: Params, path):
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str
    cfg.add_section("Parameters")
    for attr, key, _ in INIT_KEYS:
        cfg["Parameters"][key] = str(getattr(p, attr))
    el, c = p.elements, p.contents
    cfg["Parameters"]["Elements"] = str([e for e in el])
    cfg["Parameters"]["Content"] = str(np.array(c, dtype=float))
    cfg.add_section(EXTRA_SECTION)
    cfg[EXTRA_SECTION]["fix_norm_units"] = str(p.fix_norm_units)
    cfg[EXTRA_SECTION]["n_iter"] = str(p.n_iter)
    cfg[EXTRA_SECTION]["rmax_out"] = str(p.rmax_out)
    cfg[EXTRA_SECTION]["dpi"] = str(p.dpi)
    cfg[EXTRA_SECTION]["q_unit"] = str(p.q_unit)
    with open(path, "w", encoding="utf-8") as f:
        cfg.write(f)


# --------------------------------------------------------------------------------------
# pliki danych
# --------------------------------------------------------------------------------------
_num = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eEdD][+-]?\d+)?$")


def _to_float(tok: str) -> Optional[float]:
    tok = tok.strip()
    if not tok:
        return None
    if _num.match(tok):
        return float(tok.replace("d", "e").replace("D", "e"))
    return None


def read_xy(path, trim_zeros: bool = True) -> np.ndarray:
    """Czyta 2 pierwsze kolumny pliku tekstowego.

    Akceptuje separatory: spacja, tab, srednik, przecinek (gdy jedyny separator),
    przecinek dziesietny, naglowki i komentarze (ignorowane), liczby ujemne.
    Wynik posortowany rosnaco po x, bez duplikatow. trim_zeros: obcina wiersze
    z intensywnoscia dokladnie 0 na poczatku i koncu (obszar bez pokrycia detektora,
    np. w plikach z pyFAI) - nie zmienia danych, ktore zer nie maja.
    """
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s or s[0] in "#!%;":
                continue
            toks = [t for t in re.split(r"[\s;]+", s) if t]
            if len(toks) == 1 and "," in toks[0]:
                toks = toks[0].split(",")
            elif len(toks) >= 2:
                toks = [t.replace(",", ".") for t in toks]
            if len(toks) < 2:
                continue
            x, y = _to_float(toks[0]), _to_float(toks[1])
            if x is None or y is None:
                continue
            rows.append((x, y))
    if len(rows) < 4:
        raise ValueError(f"Plik {path}: za malo wierszy z danymi liczbowymi ({len(rows)}).")
    a = np.array(rows, dtype=float)
    a = a[np.argsort(a[:, 0], kind="stable")]
    keep = np.concatenate(([True], np.diff(a[:, 0]) > 0))
    a = a[keep]
    if trim_zeros:
        a = _trim_zero_edges(a)
    return a


def _trim_zero_edges(a, min_run: int = 5, edge_frac: float = 0.05):
    """Obcina obszary bez pokrycia detektora: bloki I = 0 przy koncach danych
    (razem z resztka <5% punktow za/przed blokiem, np. artefaktem na krawedzi)."""
    n = len(a)
    z = a[:, 1] == 0
    if not z.any():
        return a
    lo, hi = 0, n
    # bloki zer: (start, stop)
    edges = np.flatnonzero(np.diff(np.concatenate(([0], z.view(np.int8), [0]))))
    runs = list(zip(edges[::2], edges[1::2]))
    for s0, s1 in runs:
        if s1 - s0 < min_run and not (s0 == 0 or s1 == n):
            continue
        if n - s1 <= edge_frac * n:      # blok przy koncu
            hi = min(hi, s0)
        if s0 <= edge_frac * n:          # blok przy poczatku
            lo = max(lo, s1)
    if hi - lo < 4:
        return a
    return a[lo:hi]


def tth_to_q(tth_deg, lambd_nm):
    return 4 * np.pi * np.sin(np.pi / 180 * np.asarray(tth_deg) / 2) / lambd_nm


def q_to_tth(q_nm, lambd_nm):
    return np.arcsin(np.asarray(q_nm) * lambd_nm / 4 / np.pi) * 180 * 2 / np.pi


def file_q_range(p: Params):
    """Zakres q [nm^-1] dostepny w pliku danych (i tle)."""
    d = read_xy(p.path(p.filename))
    lo, hi = d[0, 0], d[-1, 0]
    if p.has_bkg:
        b = read_xy(p.path(p.filename_bkg))
        lo, hi = max(lo, b[0, 0]), min(hi, b[-1, 0])
    return float(p.x_to_q(lo)), float(p.x_to_q(hi))


@dataclass
class Dataset:
    q: np.ndarray                    # siatka q [nm^-1] (N punktow, qmin..qmax)
    Imeas: np.ndarray
    Ibkg: Optional[np.ndarray]
    incoh: object
    f2: np.ndarray
    fm2: np.ndarray
    th: Optional[np.ndarray] = None

    def Isa(self, bk: float) -> np.ndarray:
        if self.Ibkg is None:
            return self.Imeas
        return self.Imeas - bk * self.Ibkg


def _akima(x, y, xn, what):
    if xn[0] < x[0] - 1e-9 or xn[-1] > x[-1] + 1e-9:
        raise ValueError(f"{what}: zadany zakres wychodzi poza dane w pliku "
                         f"({x[0]:.4g} - {x[-1]:.4g}).")
    xn = np.clip(xn, x[0], x[-1])
    return Akima1DInterpolator(x, y)(xn)


def prepare(p: Params, qmax: Optional[float] = None, qmin: Optional[float] = None) -> Dataset:
    """Wczytanie danych i interpolacja na siatke 2500 punktow (jak openFiles_1..4 w oryginale)."""
    qmin = p.qmin if qmin is None else qmin
    qmax = p.qmax if qmax is None else qmax
    el, ratio = p.active_composition()
    d = read_xy(p.path(p.filename))
    b = read_xy(p.path(p.filename_bkg)) if p.has_bkg else None
    th = None
    if p.is_theta:
        s_lo, s_hi = qmin * p.lambd / 4 / np.pi, qmax * p.lambd / 4 / np.pi
        if s_hi >= 1:
            raise ValueError("qmax niedostepne dla tej dlugosci fali (q·λ/4π ≥ 1).")
        thmin, thmax = np.arcsin(s_lo) * 360 / np.pi, np.arcsin(s_hi) * 360 / np.pi
        th = np.linspace(thmin, thmax, N_POINTS)
        Imeas = _akima(d[:, 0], d[:, 1], th, "Dane")
        Ibkg = _akima(b[:, 0], b[:, 1], th, "Tlo") if b is not None else None
        if p.qstep == 0:
            q = 4 * np.pi * np.sin(np.pi / 180 * th / 2) / p.lambd
        else:   # przyblizenie stalego kroku dq (opcja diagnostyczna z oryginalu)
            q1 = 4 * np.pi * np.sin(np.pi / 180 * th[0] / 2) / p.lambd
            qm = 4 * np.pi * np.sin(np.pi / 180 * th[-1] / 2) / p.lambd
            pas = (qm - q1) / len(th)
            q = q1 + pas * np.arange(len(th))
    else:
        q = np.linspace(qmin, qmax, N_POINTS)
        k = p.q_factor
        Imeas = _akima(d[:, 0] * k, d[:, 1], q, "Dane")
        Ibkg = _akima(b[:, 0] * k, b[:, 1], q, "Tlo") if b is not None else None
    incoh, f2, fm2 = ph.scattering_factors(q, el, ratio, p.incoherent)
    return Dataset(q=q, Imeas=Imeas, Ibkg=Ibkg, incoh=incoh, f2=f2, fm2=fm2, th=th)


# --------------------------------------------------------------------------------------
# batch
# --------------------------------------------------------------------------------------
@dataclass
class BatchRow:
    pressure: object
    temperature: object
    folder: str
    params: Params
    label: str


def read_batch(path, template: Optional[Params] = None) -> List[BatchRow]:
    """Tabela batch w ukladzie oryginalnego Batch.ods (.ods, .xlsx, .xls, .csv).

    Kolumny: P, T, folder, 13 parametrow w kolejnosci Init.txt (Filename..QStep),
    potem pary (pierwiastek, udzial) x 6. Pierwszy wiersz = naglowek.
    Wiersze zaczynajace sie od '#' i puste sa pomijane.
    """
    import pandas as pd
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".ods":
        df = pd.read_excel(path, engine="odf", header=None, dtype=object)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path, header=None, dtype=object)
    else:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            first = f.readline()
        sep = ";" if first.count(";") > first.count(",") else ("\t" if "\t" in first else ",")
        df = pd.read_csv(path, header=None, dtype=object, sep=sep, encoding="utf-8-sig",
                         skip_blank_lines=True, keep_default_na=False, na_values=[""])
    rows = []
    base = path.parent
    for _, r in df.iloc[1:].iterrows():
        vals = list(r.values)
        first = vals[0]
        if first is None or (isinstance(first, float) and np.isnan(first)) or str(first).strip() == "":
            continue
        if str(first).strip().startswith("#"):
            continue
        p = (template or Params()).copy()
        for k, (attr, _, typ) in enumerate(INIT_KEYS[:13]):
            v = vals[3 + k]
            if v is None or (isinstance(v, float) and np.isnan(v)):
                continue
            setattr(p, attr, typ(float(v)) if typ is int else typ(v))
        el, ct = [], []
        for j in range(16, len(vals) - 1, 2):
            e, c = vals[j], vals[j + 1]
            if e is None or (isinstance(e, float) and np.isnan(e)) or str(e).strip() == "":
                continue
            el.append(str(e).strip())
            ct.append(float(c) if c is not None and not (isinstance(c, float) and np.isnan(c)) else 0.0)
        if el:
            p.elements, p.contents = el, ct
        folder = vals[2]
        folder = "" if folder is None or (isinstance(folder, float) and np.isnan(folder)) else str(folder).strip()
        fdir = (base / folder) if folder else base
        if folder and (fdir / p.filename).is_file():
            p.base_dir = str(fdir)
        else:
            p.base_dir = str(base)
        label = f"{Path(p.filename).stem}_{_fmt(vals[0])}"
        rows.append(BatchRow(vals[0], vals[1], folder, p, label))
    return rows


def _fmt(v):
    try:
        f = float(v)
        return str(int(f)) if f.is_integer() else str(f)
    except Exception:
        return str(v)
