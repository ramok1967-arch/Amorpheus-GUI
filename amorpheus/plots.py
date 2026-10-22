# -*- coding: utf-8 -*-
"""Wykresy rysowane na obiekcie matplotlib Figure (bez pyplot - bezpieczne w watkach i w GUI)."""
from __future__ import annotations

import numpy as np
from matplotlib import cm
from matplotlib.figure import Figure

from .data import tth_to_q, q_to_tth, read_xy

C_DATA = "#1f4e79"
C_BKG = "#c55a11"
C_SAMPLE = "#2e7d32"
C_FIT = "#c62828"
C_MOD = "#111111"


def finish(fig: Figure):
    """tight_layout tylko dla figur bez silnika ukladu (eksport); w GUI dziala 'constrained'."""
    if hasattr(fig, "get_layout_engine"):
        if fig.get_layout_engine() is None:
            fig.tight_layout()
    elif not fig.get_constrained_layout():
        fig.tight_layout()


def iter_colors(n):
    try:
        from matplotlib import colormaps
        cmap = colormaps["viridis"]
    except ImportError:           # matplotlib < 3.5
        cmap = cm.get_cmap("viridis")
    return [cmap(0.15 + 0.7 * i / max(n - 1, 1)) for i in range(n)]


def style_ax(ax, xlabel="", ylabel="", title=""):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=8)


def plot_iterations(ax, x, Y, xlabel, ylabel, title="", lw_last=2.0):
    cols = iter_colors(len(Y))
    for i, y in enumerate(Y):
        last = i == len(Y) - 1
        ax.plot(x, y, color=cols[i], lw=lw_last if last else 0.9, alpha=1 if last else 0.75,
                label=f"iter. {i}")
    style_ax(ax, xlabel, ylabel, title)
    ax.legend(fontsize=7, ncol=2)


# --------------------------------------------------------------------------------------
def plot_raw(fig: Figure, p):
    fig.clear()
    ax = fig.add_subplot(111)
    d = read_xy(p.path(p.filename))
    ax.plot(d[:, 0], d[:, 1], color=C_DATA, lw=1.2, label=p.filename)
    if p.has_bkg:
        b = read_xy(p.path(p.filename_bkg))
        ax.plot(b[:, 0], b[:, 1], color=C_BKG, lw=1.2, label=p.filename_bkg)
    if p.is_theta:
        xl = "2θ (°)"
        fwd = (lambda x: tth_to_q(x, p.lambd), lambda q: q_to_tth(q, p.lambd))
        lo = q_to_tth(min(p.qmin, 4 * np.pi / p.lambd * 0.999), p.lambd)
        hi = q_to_tth(min(p.qmax, 4 * np.pi / p.lambd * 0.999), p.lambd)
    else:
        k = p.q_factor
        xl = "q (Å⁻¹)" if k == 10 else "q (nm⁻¹)"
        fwd = (lambda x: x * k, lambda q: q / k)
        lo, hi = p.qmin / k, p.qmax / k
    ax.axvspan(lo, hi, color="#ffd54f", alpha=0.18, label="zakres analizy")
    style_ax(ax, xl, "I (j.u.)", "Dane z pliku")
    sec = ax.secondary_xaxis("top", functions=fwd)
    sec.set_xlabel("q (nm⁻¹)")
    sec.tick_params(labelsize=8)
    ax.legend(fontsize=8)
    finish(fig)


def plot_intensity(ax, res):
    if res.Ibkg is not None:
        ax.plot(res.q_data, res.Imeas, color=C_DATA, lw=1, label="I$^{meas}$")
        ax.plot(res.q_data, res.Ibkg, color=C_BKG, lw=1, label="I$^{bkg}$")
        ax.plot(res.q_data, res.Isa, color=C_SAMPLE, lw=1.4, label=f"I$^{{sample}}$ (bk={res.bkfactor:.4f})")
    else:
        ax.plot(res.q_data, res.Isa, color=C_SAMPLE, lw=1.4, label="I$^{sample}$")
    style_ax(ax, "q (nm⁻¹)", "I (j.u.)", "Intensywność")
    ax.legend(fontsize=7)


def plot_norm_overview(fig: Figure, res):
    fig.clear()
    axs = fig.subplots(2, 2)
    plot_intensity(axs[0, 0], res)
    plot_iterations(axs[0, 1], res.q, res.S, "q (nm⁻¹)", "S(q)", "Czynnik struktury S(q)")
    axs[0, 1].axvline(res.q_data[0], color="gray", ls=":", lw=1)
    plot_iterations(axs[1, 0], res.R, res.F, "r (nm)", "F(r)", "F(r)")
    axs[1, 0].plot(res.R, -4 * np.pi * res.rho * res.R, color="gray", ls="--", lw=1, label="−4πρr")
    axs[1, 0].axvline(res.p.rmin, color=C_FIT, ls=":", lw=1)
    lo = min(np.nanmin(res.F[-1]), -4 * np.pi * res.rho * res.p.rmin * 1.3)
    axs[1, 0].set_ylim(lo * 1.1, np.nanmax(res.F[-1]) * 1.15)
    plot_iterations(axs[1, 1], res.R, res.g, "r (nm)", "g(r)", "g(r)")
    if res.g_mod is not None:
        axs[1, 1].plot(res.R, res.g_mod, color=C_MOD, lw=1.6,
                       label=f"z M(Q,Δ(r)): a={res.mod_a:.3f}, b={res.mod_b:.3f}")
        axs[1, 1].legend(fontsize=7, ncol=2)
    axs[1, 1].axvline(res.p.rmin, color=C_FIT, ls=":", lw=1)
    axs[1, 1].set_ylim(-0.3, np.nanmax(res.g[-1][res.R > res.p.rmin]) * 1.15)
    finish(fig)


def plot_single(fig: Figure, x, Y, xlabel, ylabel, title):
    fig.clear()
    ax = fig.add_subplot(111)
    plot_iterations(ax, x, Y, xlabel, ylabel, title)
    finish(fig)
    return ax


def plot_modification(fig: Figure, res):
    fig.clear()
    ax = fig.add_subplot(111)
    ax.plot(res.R, res.g[-1], color=C_DATA, lw=1.2, label="g(r)")
    if res.g_mod is not None:
        ax.plot(res.R, res.g_mod, color=C_MOD, lw=1.6, label="g(r) z M(Q,Δ(r))")
        k = np.nanmax(res.g[-1]) / np.nanmax(res.dR)
        ax.plot(res.R, k * res.dR, "--", color=C_BKG, lw=1,
                label=f"Δ(r)·{k:.1f}: a={res.mod_a:.3f} nm, b={res.mod_b:.3f} nm")
    style_ax(ax, "r (nm)", "g(r)", "Funkcja modyfikująca")
    ax.legend(fontsize=8)
    finish(fig)


# --------------------------------------------------------------------------------------
def plot_loop(fig: Figure, results, kind="rmin", has_bkg=True, highlight=None):
    fig.clear()
    if not results:
        return
    x = np.array([r.rmin if kind == "rmin" else r.qmax for r in results])
    rho = np.array([r.rho for r in results])
    bk = np.array([r.bkfactor for r in results])
    chi = np.array([r.chi2 for r in results])
    xl = "r_min (nm)" if kind == "rmin" else "q_max (nm⁻¹)"
    axs = fig.subplots(2 if has_bkg else 1, 1, sharex=True, squeeze=False)[:, 0]
    pairs = [(rho, "ρ (at/nm³)", C_DATA)] + ([(bk, "bkfactor", C_BKG)] if has_bkg else [])
    for ax, (y, lab, col) in zip(axs, pairs):
        ax.plot(x, y, "o-", color=col, ms=4)
        ax.set_ylabel(lab, color=col)
        ax.ticklabel_format(axis="y", useOffset=False)
        ax.tick_params(axis="y", labelcolor=col, labelsize=8)
        ax.grid(True, alpha=0.3)
        a2 = ax.twinx()
        a2.plot(x, chi, "s--", color=C_FIT, ms=3, lw=1)
        a2.set_ylabel("χ²", color=C_FIT)
        a2.tick_params(axis="y", labelcolor=C_FIT, labelsize=8)
        a2.set_yscale("log" if np.all(chi > 0) and chi.max() / max(chi.min(), 1e-300) > 50 else "linear")
        if highlight is not None and 0 <= highlight < len(x):
            ax.axvline(x[highlight], color="#ffb300", lw=2, alpha=0.6)
    axs[-1].set_xlabel(xl)
    axs[0].set_title(f"Pętla po {xl.split(' ')[0]}", fontsize=10, fontweight="bold")
    finish(fig)


def plot_chi2map(fig: Figure, m, levels_norm=(1.5, 5, 10, 20, 50, 100)):
    fig.clear()
    axs = fig.subplots(1, 2)
    ext = [m.rho[0], m.rho[-1], m.bk[0], m.bk[-1]]
    Z = m.Z.T
    im = axs[0].imshow(Z, cmap="gray", origin="lower", extent=ext, aspect="auto")
    fig.colorbar(im, ax=axs[0], fraction=0.046)
    if np.isfinite(Z).sum() > 4:
        lv = np.linspace(np.nanmin(Z) * 1.5, np.nanmax(Z), 5)
        try:
            cs = axs[0].contour(m.rho, m.bk, Z, lv, colors="gold", linewidths=1.2)
            axs[0].clabel(cs, fontsize=7)
        except Exception:
            pass
    style_ax(axs[0], "ρ (at/nm³)", "bkfactor", "χ²")
    N = m.Znorm.T
    im2 = axs[1].imshow(N, cmap="RdBu_r", origin="lower", extent=ext, aspect="auto",
                        vmin=1, vmax=min(np.nanmax(N), 100))
    fig.colorbar(im2, ax=axs[1], fraction=0.046)
    if np.isfinite(N).sum() > 4:
        try:
            cs = axs[1].contour(m.rho, m.bk, N, list(levels_norm), colors="gold", linewidths=1.2)
            axs[1].clabel(cs, fontsize=7)
        except Exception:
            pass
    axs[1].axhline(m.bk_c, color="red", lw=1)
    axs[1].axvline(m.rho_c, color="red", lw=1)
    r0, b0, z0 = m.minimum()
    for ax in axs:
        ax.plot(r0, b0, "*", color="#00e676", ms=12, mec="k")
    style_ax(axs[1], "ρ (at/nm³)", "bkfactor", f"χ²/χ²min   (min: ρ={r0:.3f}, bk={b0:.4f})")
    finish(fig)


def plot_batch(fig: Figure, items, shift=0.6):
    fig.clear()
    ok = [it for it in items if it.norm is not None]
    axs = fig.subplots(1, 3)
    cols = iter_colors(max(len(ok), 2))
    for i, it in enumerate(ok):
        lab = f"{it.row.pressure} GPa, {it.row.temperature} K"
        axs[0].plot(it.norm.q, it.norm.S[-1] + i * shift, color=cols[i], lw=1, label=lab)
        g = it.norm.g_mod if it.norm.g_mod is not None else it.norm.g[-1]
        axs[1].plot(it.norm.R, g + i * shift, color=cols[i], lw=1, label=lab)
    style_ax(axs[0], "q (nm⁻¹)", "S(q) + przesunięcie", "S(q)")
    style_ax(axs[1], "r (nm)", "g(r) + przesunięcie", "g(r)")
    if ok:
        axs[0].legend(fontsize=6)
    P, rho = [], []
    for it in ok:
        try:
            P.append(float(it.row.pressure)); rho.append(it.fit.rho)
        except Exception:
            pass
    axs[2].plot(P, rho, "o-", color=C_DATA)
    style_ax(axs[2], "P (GPa)", "ρ (at/nm³)", "Gęstość")
    axs[2].ticklabel_format(useOffset=False)
    finish(fig)
