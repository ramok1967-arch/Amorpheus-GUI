# -*- coding: utf-8 -*-
"""
Test zgodnosci z oryginalnym Amorpheus v1.0.5 - porownanie na zywo.

1. Pobiera oryginalny equations.py z github.com/CelluleProjet/Amorpheus (oraz dane Ce, jesli ich brak).
2. Liczy nim wyniki referencyjne (tests/make_reference.py: opcje [n], [r], [x], dopasowania, chi^2)
   dla formatow 1-4, SofQ 0/1 i QStep 1. Dane 2θ sa generowane z danych Q (λ = 0.03738 nm).
3. Liczy to samo nowym silnikiem w trybie zgodnosci (fix_norm_units=False) i porownuje pelne tablice.

Uruchomienie:   python tests/test_against_original.py
(ok. 2-3 minuty; przy pierwszym uruchomieniu potrzebny internet)
"""
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amorpheus.data import Params  # noqa: E402
from amorpheus import analysis as an  # noqa: E402
from amorpheus.examples import ensure_examples, RAW  # noqa: E402

trapz = getattr(np, "trapezoid", None) or np.trapz
WORK = Path(tempfile.mkdtemp(prefix="amorpheus_test_"))
EX = WORK / "data"
ORIG = WORK / "original"
EX.mkdir()
ORIG.mkdir()
LAM = 0.03738

# --- dane ------------------------------------------------------------------------------
for f in ("Cerium.dat", "background.xy"):
    shutil.copy(ensure_examples() / f, EX / f)
for src, dst in (("Cerium.dat", "Cerium_tth.dat"), ("background.xy", "background_tth.xy")):
    d = np.loadtxt(EX / src)
    tth = 2 * np.degrees(np.arcsin(d[:, 0] * 10 * LAM / 4 / np.pi))
    np.savetxt(EX / dst, np.c_[tth, d[:, 1]])

# --- referencja z oryginalnego kodu ----------------------------------------------------------
cache = Path(__file__).with_name("_original_equations.py")
if not cache.exists():
    print("Pobieranie oryginalnego equations.py ...")
    with urllib.request.urlopen(RAW + "equations.py", timeout=30) as r:
        cache.write_bytes(r.read())
shutil.copy(cache, ORIG / "equations.py")
ref_file = WORK / "reference.npz"
print("Liczenie referencji ORYGINALNYM kodem (ok. 2 min) ...")
t0 = time.time()
out = subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("make_reference.py")),
                      str(ORIG), str(EX), str(ref_file)], capture_output=True, text=True)
if out.returncode != 0:
    print(out.stdout[-2000:], out.stderr[-3000:])
    sys.exit("Nie udalo sie policzyc referencji oryginalnym kodem.")
print(f"  gotowe ({time.time() - t0:.0f} s)\n")
REF = dict(np.load(ref_file))

# --- porownanie ------------------------------------------------------------------------
results = []


def check(name, a, b, rtol=1e-9, atol=1e-9):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = a.shape == b.shape and np.allclose(a, b, rtol=rtol, atol=atol, equal_nan=True)
    err = np.nanmax(np.abs(a - b)) if a.shape == b.shape else np.inf
    results.append(ok)
    print(f"  [{'OK ' if ok else 'BŁĄD'}] {name:28s} max|Δ| = {err:.3g}")


def base(ff, sofq=1, qstep=0):
    p = Params(base_dir=str(EX), fix_norm_units=False, sofq=sofq, qstep=qstep, file_format=ff,
               elements=["Ce", "Al", "Ni", "Cu", "Fe", "C"], contents=[0.7, 0.1, 0.1, 0.1, 0, 0])
    if ff in (1, 2):
        p.filename, p.filename_bkg = "Cerium_tth.dat", "background_tth.xy"
    else:
        p.filename, p.filename_bkg = "Cerium.dat", "background.xy"
    return p


print("Normalizacja (opcja [n]):")
for tag, ff, sofq, qstep in [("n4", 4, 1, 0), ("n3", 3, 1, 0), ("n2", 2, 1, 0), ("n1", 1, 1, 0),
                             ("n4s0", 4, 0, 0), ("n2qs", 2, 1, 1)]:
    t = time.time()
    r = an.run_normalization(base(ff, sofq, qstep))
    print(f" {tag}  ({time.time()-t:.1f} s)")
    check(f"{tag} S(q)", r.S, REF[f"{tag}_S"])
    check(f"{tag} F(r)", r.F, REF[f"{tag}_F"], rtol=1e-8, atol=1e-8)
    check(f"{tag} g(r)", r.g, REF[f"{tag}_g"], rtol=1e-8, atol=1e-8)
    check(f"{tag} gęstość z nachylenia", r.dens_slope, REF[f"{tag}_dens"])
    cn = np.array([[c["CN1"], c["CN2"], c["r0"], c["r_peak"], c["r_min"]] for c in r.cn])
    check(f"{tag} CN1/CN2/r", cn, REF[f"{tag}_cn"])
    r.apply_modification(*REF[f"{tag}_ab"])
    m = np.isfinite(REF[f"{tag}_grlast"])          # oryginal mial NaN w r = a
    check(f"{tag} g(r) z f. modyf.", r.g_mod[m], REF[f"{tag}_grlast"][m], rtol=1e-8, atol=1e-8)

print("Chi² w ustalonych punktach:")
pr = an.Problem(base(4))
check("chi2 (3 punkty)", [pr.chi2(30.0, 0.9), pr.chi2(34.68, 0.927), pr.chi2(38.0, 1.0)], REF["chi4_points"])

print("Dopasowania (Nelder-Mead):")
for tag, ff, rho0 in [("fit4", 4, 34.68), ("fit2", 2, 34.68), ("fit3", 3, 30.0)]:
    t = time.time()
    f = an.fit_density(base(ff), rho0=rho0, bk0=0.927)
    print(f" {tag}: rho={f.rho:.4f} bk={f.bkfactor:.4f} chi2={f.chi2:.4g} ({time.time()-t:.1f} s)")
    check(f"{tag} rho, bk", [f.rho, f.bkfactor], REF[tag][1:3], rtol=1e-6, atol=1e-6)

print("Pętle:")
lr = an.loop_rmin(base(4), [0.20, 0.22], 34.68, 0.927)
check("pętla rmin (rho, bk)", [x.row()[1:3] for x in lr], REF["loop_rmin"][:, 1:3], rtol=1e-6, atol=1e-6)
lq = an.loop_qmax(base(4), [60.0, 70.0], 34.68, 0.927)
check("pętla qmax (rho, bk)", [x.row()[1:3] for x in lq], REF["loop_qmax"][:, 1:3], rtol=1e-6, atol=1e-6)

print("Poprawka jednostek (tryb domyślny):")
p = base(4)
p.fix_norm_units = True
r = an.run_normalization(p)
m = r.q > r.q_data[0] - 1e-9
check("reguła sum ∫q²(S-1)dq", trapz(r.q[m] ** 2 * (r.S[0][m] - 1), r.q[m]), -2 * np.pi ** 2 * p.rho, rtol=1e-6)

shutil.rmtree(WORK, ignore_errors=True)
print()
print(f"{sum(results)}/{len(results)} testów zaliczonych")
sys.exit(0 if all(results) else 1)
