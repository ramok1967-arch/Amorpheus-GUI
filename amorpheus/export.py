# -*- coding: utf-8 -*-
"""Zapis wynikow - nazwy i uklad kolumn jak w oryginalnym Amorpheus, plus naglowki z parametrami."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

from . import plots
from .data import FILE_FORMATS
from .i18n import tr  # noqa: E402


def _savetxt(fname, arr, **kw):
    """np.savetxt zawsze w UTF-8 (na Windows domyslnie cp1250 nie zapisze np. A^-1 w naglowku)."""
    kw.setdefault("encoding", "utf-8")
    np.savetxt(fname, arr, **kw)


def params_header(p, extra=""):
    el = ", ".join(f"{e}:{c:g}" for e, c in zip(*p.active_composition()))
    s = (f"Amorpheus-Qt | plik={p.filename} tlo={p.filename_bkg if p.has_bkg else '-'} "
         f"format={p.file_format} ({FILE_FORMATS.get(p.file_format, '?')}) incoherent={p.incoherent} "
         f"lambda={p.lambd} nm | q={p.qmin:g}-{p.qmax:g} nm^-1 rmin={p.rmin:g} nm | SofQ={p.sofq} "
         f"iteracje={p.n_iter} poprawka_jednostek={p.fix_norm_units} | sklad: {el}")
    return s + ("\n" + extra if extra else "")


def unique_base(out_dir: Path, base: str, probe_suffix: str) -> str:
    """Jak w oryginale: jesli plik istnieje, dopisz _0, _1, ..."""
    if not (out_dir / f"{base}{probe_suffix}").exists():
        return base
    k = 0
    while (out_dir / f"{base}_{k}{probe_suffix}").exists():
        k += 1
    return f"{base}_{k}"


def _savefig(draw, path, dpi, size=(8, 6), **kw):
    fig = Figure(figsize=size)
    FigureCanvasAgg(fig)
    draw(fig, **kw)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path


def save_normalization(res, out_dir, base=None, dpi=None, overwrite=False):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = res.p
    dpi = dpi or p.dpi
    base = base or p.save_norm
    if not overwrite:
        base = unique_base(out_dir, base, "_S.txt")
    hdr = params_header(p, f"rho={res.rho:.6g} at/nm^3 bkfactor={res.bkfactor:.6g}")
    files = []
    b = out_dir / base

    def st(suffix, arr, cols):
        fn = Path(f"{b}{suffix}")
        _savetxt(fn, arr, header=hdr + "\n" + cols)
        files.append(fn)

    n = len(res.S)
    it = " ".join(f"iter{i}" for i in range(n))
    if res.Ibkg is not None:
        st("_I.txt", np.vstack((res.q_data, res.Imeas, res.Ibkg, res.Isa)).T, "q(nm-1) Imeas Ibkg Isample")
    else:
        st("_I.txt", np.vstack((res.q_data, res.Isa)).T, "q(nm-1) Isample")
    st("_S.txt", np.vstack((res.q, res.S)).T, "q(nm-1) " + it)
    st("_S_lastcolumn.txt", np.vstack((res.q, res.S[-1])).T, "q(nm-1) S")
    st("_F.txt", np.vstack((res.R, res.F)).T, "r(nm) " + it)
    st("_gder.txt", np.vstack((res.R, res.g)).T, "r(nm) " + it)
    # podsumowanie: gestosc z nachylenia i liczby koordynacyjne
    rows = []
    for i, c in enumerate(res.cn):
        if c is None:
            rows.append([i, res.dens_slope[i]] + [np.nan] * 5)
        else:
            rows.append([i, res.dens_slope[i], c["CN1"], c["CN2"], c["r0"], c["r_peak"], c["r_min"]])
    st("_CN.txt", np.array(rows), "iter rho_slope(at/nm3) CN1 CN2 r0(nm) r_peak(nm) r_min(nm)")

    for suf, fn in [("_I", lambda f: _ax1(f, plots.plot_intensity, res)),
                    ("_S", lambda f: plots.plot_single(f, res.q, res.S, tr("q (nm⁻¹)"), "S(q)", "S(q)")),
                    ("_F", lambda f: plots.plot_single(f, res.R, res.F, tr("r (nm)"), "F(r)", "F(r)")),
                    ("_gder", lambda f: plots.plot_single(f, res.R, res.g, tr("r (nm)"), "g(r)", "g(r)"))]:
        files.append(_savefig(fn, f"{b}{suf}.png", dpi))
    files.append(_savefig(lambda f: plots.plot_norm_overview(f, res), f"{b}_overview.png", dpi, size=(12, 8)))
    if res.g_mod is not None:
        st("_grlast.txt", np.vstack((res.R, res.g_mod)).T,
           f"r(nm) g_mod   a={res.mod_a:.6g} nm b={res.mod_b:.6g} nm")
        st("_deltaR.txt", np.vstack((res.R, res.dR)).T, "r(nm) Delta(r)(nm)")
        files.append(_savefig(lambda f: plots.plot_modification(f, res), f"{b}ModificationFunction.png", dpi))
    return files


def _ax1(fig, fn, res):
    fig.clear()
    ax = fig.add_subplot(111)
    fn(ax, res)
    plots.finish(fig)


def save_loop(results, p, kind, out_dir, a, b, dpi=None, overwrite=False):
    """kind = 'rmin' lub 'qmax'. Plik: <prefix>_<dane>-<tlo>_<a>-<b>.txt jak w oryginale."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dpi = dpi or p.dpi
    prefix = p.save_rmin if kind == "rmin" else p.save_qmax
    stem = f"{Path(p.filename).stem}" + (f"-{Path(p.filename_bkg).stem}" if p.has_bkg else "")
    base = f"{prefix}_{stem}_{a:g}-{b:g}"
    if not overwrite:
        base = unique_base(out_dir, base, ".txt")
    col = "rmin(nm)" if kind == "rmin" else "qmax(nm-1)"
    hdr = params_header(p, f"{col} density(at/nm^3) bkfactor chisquare")
    arr = np.array([[r.rmin if kind == "rmin" else r.qmax, r.rho, r.bkfactor, r.chi2] for r in results])
    fn = out_dir / f"{base}.txt"
    _savetxt(fn, arr, header=hdr)
    png = _savefig(lambda f: plots.plot_loop(f, results, kind, p.has_bkg), out_dir / f"{base}.png", dpi)
    return [fn, png]


def save_chi2map(m, p, out_dir, base=None, dpi=None, overwrite=False):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = base or p.save_norm
    if not overwrite:
        base = unique_base(out_dir, base, "_Chi2.txt")
    r0, b0, z0 = m.minimum()
    hdr = params_header(p, f"rmin={m.rmin:g} nm; wiersze: rho {m.rho[0]:g}..{m.rho[-1]:g} ({len(m.rho)}), "
                           f"kolumny: bkfactor {m.bk[0]:g}..{m.bk[-1]:g} ({len(m.bk)}); "
                           f"minimum: rho={r0:.6g} bk={b0:.6g} chi2={z0:.6g}")
    f1 = out_dir / f"{base}_Chi2.txt"
    f2 = out_dir / f"{base}_Chi2_norm.txt"
    _savetxt(f1, m.Z, header=hdr)
    _savetxt(f2, m.Znorm.T, header=hdr + "\n(transponowana: wiersze = bkfactor, jak w oryginale)")
    with open(out_dir / f"{base}_Chi2_axes.txt", "w", encoding="utf-8") as f:
        f.write("# os rho (at/nm3) - wiersze Z\n" + " ".join(f"{v:.8g}" for v in m.rho) + "\n")
        f.write("# os bkfactor - kolumny Z\n" + " ".join(f"{v:.8g}" for v in m.bk) + "\n")
    png = _savefig(lambda f: plots.plot_chi2map(f, m), out_dir / f"{base}_Chi2.png", dpi or p.dpi, size=(12, 5))
    return [f1, f2, png]


def save_batch(items, batch_path, out_dir=None, dpi=300, log=None):
    """Folder Batch_RRRRMMDD_HHhMM z plikami jak w oryginale + kopia tabeli batch."""
    log = log or (lambda s: None)
    stamp = time.strftime("%Y%m%d_%Hh%M")
    batch_path = Path(batch_path)
    root = Path(out_dir) if out_dir else batch_path.parent
    folder = root / f"Batch_{stamp}"
    folder.mkdir(parents=True, exist_ok=True)
    summary = []
    for it in items:
        if it.norm is None:
            continue
        res = it.norm
        tag = f"{Path(it.row.params.filename).stem}_{it.row.pressure}".replace(".", "p")
        hdr = params_header(res.p, f"P={it.row.pressure} T={it.row.temperature} rho={res.rho:.6g} bk={res.bkfactor:.6g}")
        _savetxt(folder / f"S_{tag}.txt", np.vstack([res.q, res.S]).T, header=hdr)
        _savetxt(folder / f"F_{tag}.txt", np.vstack([res.R, res.F]).T, header=hdr)
        _savetxt(folder / f"gder_{tag}.txt", np.vstack([res.R, res.g]).T, header=hdr)
        _savefig(lambda f: _ax1(f, plots.plot_intensity, res), folder / f"I_{tag}.png", dpi)
        _savefig(lambda f: plots.plot_single(f, res.q, res.S, tr("q (nm⁻¹)"), "S(q)", f"S(q) {tag}"), folder / f"S_{tag}.png", dpi)
        _savefig(lambda f: plots.plot_single(f, res.R, res.F, tr("r (nm)"), "F(r)", f"F(r) {tag}"), folder / f"F_{tag}.png", dpi)
        _savefig(lambda f: plots.plot_single(f, res.R, res.g, tr("r (nm)"), "g(r)", f"g(r) {tag}"), folder / f"gder_{tag}.png", dpi)
        if res.g_mod is not None:
            _savetxt(folder / f"grlast_{tag}.txt", np.array([res.R, res.g_mod]).T, header=hdr)
            _savefig(lambda f: plots.plot_modification(f, res), folder / f"grlast_{tag}.png", dpi)
        summary.append([it.row.pressure, it.row.temperature, it.fit.rmin, it.fit.rho, it.fit.bkfactor, it.fit.chi2])
    if summary:
        with open(folder / f"Batch_results_{stamp}.txt", "w", encoding="utf-8") as f:
            f.write("pressure, temperature, rmin, density, bkfactor, chisquare \n")
            for r in summary:
                f.write(" ".join(str(x) for x in r) + "\n")
        _savefig(lambda f: plots.plot_batch(f, items), folder / "Batch_results.png", dpi, size=(15, 5))
    try:
        shutil.copy2(batch_path, folder / f"Batch_{stamp}{batch_path.suffix}")
    except Exception as e:
        log(tr('Nie skopiowano tabeli batch: {0}').format(e))
    return folder
