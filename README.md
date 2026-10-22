# Amorpheus-Qt 2.0

🇵🇱 [Wersja polska](README.pl.md)

A desktop application for analysing **X-ray scattering data of amorphous solids and liquids**: from an
integrated 1D diffraction pattern to the structure factor S(q), the reduced distribution function F(r),
the pair distribution function g(r), the atomic number density ρ and coordination numbers.

It is a complete rewrite of **Amorpheus** (S. Boccato et al., 2022), which was developed for liquids and
glasses measured, among others, in diamond anvil cells (DAC). The physics is identical to the original.
This version adds a PyQt5 interface, automatic detection of parameters from data files, faster fitting
and several bug fixes.

Original program: <https://github.com/CelluleProjet/Amorpheus>

![Main window – normalization of the example data (Ce-based glass)](docs/screenshot.png)

> The user interface is in **Polish**. The tables below give the Polish labels with their meaning.

---

## Contents

- [Features](#features)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Input data](#input-data)
- [User interface](#user-interface)
- [Practical tips](#practical-tips)
- [Output files](#output-files)
- [Changes from the original](#changes-from-the-original-v105)
- [Compatibility test](#compatibility-test)
- [Scripting](#scripting)
- [Citation and licence](#citation-and-licence)

---

## Features

- **Normalization** by the Krogh-Moe/Norman method (Morard et al. 2013, eq. 10) with the iterative
  Kaplow/Eggert correction.
- **Fit of density ρ and background scale** (bkfactor) by minimizing χ² = ∫₀^rmin [F(r) + 4πρr]² dr.
- **r_min and q_max loops** to check how the result depends on the parameters; ρ is taken from the plateau.
- **χ²(ρ, bk) map** with contours.
- **Batch mode** for measurement series (.ods, .xlsx or .csv table).
- **RPS**: removal of crystalline peaks (Lorentz, Gauss, Voigt), replacing a range with a line, smoothing.
- **Modification function M(Q, Δ(r))** to reduce Fourier termination ripples.
- **Coordination numbers** CN1 and CN2 and density from the F(r) slope for every iteration.
- **Open data with auto-detection**: axis unit, wavelength, data range, composition from the file name,
  background file.
- Project files (`Init.txt`) are **compatible with the original in both directions**.

## Installation

Requires Python ≥ 3.9 with numpy, scipy, matplotlib, PyQt5, lmfit, xraylib, pandas, odfpy and openpyxl.
Runs on Windows, Linux and macOS.

### Windows + Miniconda (recommended)

1. Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) if you do not have it.
2. Run **`instaluj.bat`** ("install"). It creates the conda environment `amorpheus` (packages from
   conda-forge) and runs the compatibility test. This takes a few minutes.
3. Start the program with **`uruchom.bat`** ("run"). You can also drag a data file or an `Init.txt` onto it.

### Manually (conda)

```bash
conda create -n amorpheus -c conda-forge python=3.11 numpy scipy matplotlib pyqt lmfit xraylib pandas odfpy openpyxl
conda activate amorpheus
python amorpheus_qt.py
```

### pip

```bash
pip install -r requirements.txt
python amorpheus_qt.py
```

`xraylib` from pip does not provide a ready-made Windows build for every Python version. If the installation
fails, use conda.

## Quick start

**Example:** on first start the program loads the example from the original (a Ce-based glass, `examples/`).
Click **Normalizacja → Normalizuj** (Normalization → Normalize). To load the example again use
**Plik → Wczytaj przykład** (File → Load example).

**Your own data:**

1. **Plik → Otwórz dane…** (File → Open data…, Ctrl+O), the "Otwórz dane…" button in the left panel, or drag
   the file onto the window.
2. A dialog shows what was read from the file. Everything can be corrected:
   - axis unit (Q in Å⁻¹ or nm⁻¹, 2θ) and wavelength from the pyFAI, Dioptas or Fit2D header;
   - data range without the edge regions with I = 0 (no detector coverage), and suggested q_min/q_max;
   - composition from the file name, e.g. `Mg61Cu28Gd11_…` → Mg 0.61 / Cu 0.28 / Gd 0.11 (if the name
     contains "wt", weight fractions are converted to atomic fractions);
   - number density ρ = 602.2·d / M̄, if you enter the mass density d [g/cm³];
   - a background file from the same folder (names containing *bkg*, *background*, *empty*, *gasket*…).
3. **Utwórz projekt** (Create project) saves `<data_name>_Init.txt` next to the data. The project is also
   saved automatically whenever a calculation starts and when the program closes. Results are written to
   the data folder.
4. When you open the same data again, the program offers to load the saved project.

Typical workflow: **Pętla r_min** (r_min loop – choose r_min from the ρ plateau) → **Pętla q_max**
(q_max loop) → **Normalizacja** → **Zapisz wyniki** (Save results).

`Init.txt` files from the original Amorpheus can be opened with **Plik → Otwórz projekt** (File → Open
project, Ctrl+Shift+O).

## Input data

- **Format:** two text columns (x, I). Separator: space, tab, semicolon or comma; decimal comma and header
  lines (`#`) are allowed. Header encoding does not matter (UTF-8, Latin-1).
- **x axis:** 2θ [°] (requires λ) or Q in Å⁻¹ or nm⁻¹.
- **Background:** an empty cell or holder measurement (recommended), or a background measured on the sample.

> **Important:** like the original, the program does **not** correct for polarization, absorption or
> multiple scattering. These corrections must be applied during data integration (e.g. in pyFAI/Dioptas:
> polarization factor ≈ 0.99 for synchrotron beams). Without a polarization correction, data at large 2θ
> lose intensity at high Q, and the fit of ρ and bkfactor becomes unstable.

## User interface

### Parameter panel (left)

| Label | Meaning |
|---|---|
| Dane / Tło | data and background files |
| Format | 1: 2θ, no background · 2: 2θ + background · 3: Q, no background · 4: Q + background |
| Jedn. Q | Q unit in the file: Å⁻¹ (as in the original) or nm⁻¹ (e.g. pyFAI `q_nm^-1`); formats 3 and 4 only |
| Incoh. | 1: empty-cell background, the sample's Compton scattering is subtracted; 0: background measured on the sample |
| λ [nm] | wavelength; 2θ data only |
| q_min, q_max [nm⁻¹] | analysis range (1 Å⁻¹ = 10 nm⁻¹) |
| r_min [nm] | cut-off radius: F(r) = −4πρr is required for r < r_min |
| ρ [at/nm³], bkfactor | values used for normalization and starting point of the fit (bounds: ρ₀ ± 50, bk 0.7–1.2) |
| Skład | composition (atomic fractions); "Do 1" fills the selected row so that the sum = 1 |
| S(q<q_min) | 1: constant = S(q_min) (recommended); 0: zero; 2: Lorentzian (unstable, diagnostics only) |
| Normalizacja | 0: standard; 1: additionally g(r) with the modification function M(Q, Δ(r)) |
| Iteracje | number of Kaplow iterations (4 as in the original) |
| r_max wyn. | r range of F(r) and g(r) in the output files |
| Poprawka jedn. | unit correction of the sum rule (recommended); unchecked = results identical to v1.0.5 |

The "Opcje obliczeń" (Calculation options) and "Zapis wyników" (Saving results) groups can be collapsed
by clicking their title. A full description of the parameters is available in **Pomoc → Pomoc – opis
parametrów** (Help → Parameter description).

### Tabs

- **Dane** (Data): raw data and background. The yellow band marks the analysed range; the top axis is q in nm⁻¹.
- **Normalizacja** (Normalization): I(q), S(q), F(r) and g(r) for every iteration. The table shows the density
  from the F(r < r_min) slope, CN1, CN2 and peak positions. "Dopasuj ρ, bk → normalizuj" (Fit ρ, bk →
  normalize) first minimizes χ², then normalizes. Parameters a and b of the modification function can be
  adjusted.
- **Pętla r_min / Pętla q_max** (r_min / q_max loop): fit of ρ (and bk) for a series of values. The table
  fills in as the calculation runs; the selected row can be transferred to the parameters.
- **Mapa χ²** (χ² map): χ²(ρ, bk) on a grid, raw and normalized. The minimum can be transferred to the
  parameters.
- **Batch**: a measurement series from a table in the layout of the original `Batch.ods` (example:
  `examples/Batch.csv`). Rows starting with `#` are skipped.
- **RPS – piki i wygładzanie** (peaks and smoothing): removal of crystalline peaks and smoothing. Select the
  range on the plot: left click = start, right click = end. The result can be set as the data file directly.

Calculations run in the background, so the window does not freeze. **Stop** interrupts a loop; partial
results are kept.

## Practical tips

- **Choose r_min from the plateau of ρ(r_min)**, not from the global χ² minimum. χ² grows with r_min because
  the integral covers a longer interval, so compare it only locally. r_min must be smaller than the shortest
  interatomic distance.
- **q_max:** the q_max loop shows where noise and high-Q errors start to change ρ. The spread of ρ over a
  reasonable q_max range is a good measure of its uncertainty.
- **bkfactor at a bound (0.7 or 1.2)** indicates a problem with the background or with the data corrections
  (most often polarization). Do not treat such a result as final.
- **CN1** is computed as 2 × the integral up to the maximum of the first peak (assumes a symmetric peak) and
  is often underestimated in multicomponent alloys. CN2 (integral up to the first minimum) is usually more
  reliable.
- **RPS:** fit peaks only in a narrow range around each peak. Fitting over the whole data range destroys the
  amorphous signal; the program warns when the range exceeds 25% of the data.

## Output files

File names and columns are the same as in the original; each file also has a header with the parameters.

| Operation | Files |
|---|---|
| Normalization | `Norm_I.txt` (q, Imeas, Ibkg, Isample), `Norm_S.txt` (q, S of iterations 0…n), `Norm_S_lastcolumn.txt`, `Norm_F.txt`, `Norm_gder.txt` (r, g of iterations), `Norm_CN.txt` (ρ from slope, CN1, CN2, peak positions), `*.png`, `Norm_overview.png`; with the modification function also `Norm_grlast.txt` and `Norm_deltaR.txt` |
| r_min loop | `MinRmin_<data>-<bkg>_<from>-<to>.txt` (rmin, ρ, bk, χ²) + `.png` |
| q_max loop | `MinQmax_<data>-<bkg>_<from>-<to>.txt` (qmax, ρ, bk, χ²) + `.png` |
| χ² map | `Norm_Chi2.txt` (rows = ρ), `Norm_Chi2_norm.txt`, `Norm_Chi2_axes.txt`, `.png` |
| Batch | folder `Batch_YYYYMMDD_HHhMM` with `S_`, `F_`, `gder_`, `grlast_` (.txt, .png) for every row, `Batch_results_*.txt`, `Batch_results.png` and a copy of the table |

Existing files are not overwritten: a number `_0`, `_1`… is appended (unless "Nadpisuj pliki" – Overwrite
files – is checked). Files are written in UTF-8.

## Changes from the original v1.0.5

- **Compatibility:** with the unit correction unchecked, results (S, F, g, CN, ρ from slope, χ², fits, loops)
  are identical to the original within ≤ 1e-13. This is verified by `tests/test_against_original.py`.
- **Unit correction in the normalization** (on by default): in the original, the Krogh-Moe sum-rule integrals
  were taken over dq in nm⁻¹ with Q² in Å⁻², which made the −2π²ρ term 10× too small. With the correction,
  ∫q²(S−1)dq = −2π²ρ holds exactly. For the Ce example ρ is unchanged and bkfactor changes from 0.9281
  to 0.9259.
- **Data loading:** the original silently skipped lines starting with "-" or ".", e.g. negative intensities
  after background subtraction. These are now read. Different separators, decimal commas and headers in any
  encoding are supported.
- **Speed:** fitting is about 4× faster because the sin(qr) matrix is computed once and only for r < r_min.
- **Works with NumPy 2.x and SciPy ≥ 1.14** (the original used the removed `np.trapz` and
  `scipy.integrate.trapz`). Batch mode no longer needs the obsolete `ezodf` package.
- **Security:** the contents of `Init.txt` are no longer executed with `exec`/`eval`.
- **New features:** graphical interface, opening data with auto-detection and automatic project creation,
  Q in nm⁻¹, skipping I = 0 regions at the data edges, `%` in file names, `Norm_CN.txt`, χ² map in the GUI.
- **Minor fixes:**
  - no NaN in the modification function at r = a;
  - correct header of the q_max loop file;
  - the ρ(q_max) plot was saved under the r_min loop prefix;
  - RPS "Erase" dropped the last point;
  - an error in one batch row no longer stops the whole batch;
  - output names no longer depend on the length of the file extension;
  - case-insensitive file names on every system (as on Windows).

The physics is unchanged: normalization by eq. 10 (Morard 2013), 4 Kaplow iterations,
χ² = ∫₀^rmin [F(r) + 4πρr]² dr, Nelder-Mead (lmfit, 500 evaluations, tol 1e-4), scattering factors
from xraylib.

## Compatibility test

```bash
python tests/test_against_original.py
```

The test computes reference results with the **original** `equations.py` (normalization for formats 1–4,
SofQ 0/1, QStep, χ², fits, r_min and q_max loops). It then computes the same with the new code in
compatibility mode and compares 43 quantities on full arrays. This takes about 2–3 minutes. A copy of the
original is stored in `tests/_original_equations.py`.

## Scripting

The calculations are separate from the interface and can be used without the GUI:

```python
from amorpheus.data import load_init
from amorpheus import analysis as an, export as ex

p = load_init("examples/Init.txt")
fit = an.fit_density(p)                              # rho, bkfactor, chi2
res = an.run_normalization(p, rho=fit.rho, bk=fit.bkfactor)
ex.save_normalization(res, "results")
```

### Project structure

```
amorpheus_qt.py          GUI entry point
amorpheus/physics.py     scattering factors (xraylib), normalization, Kaplow, χ², CN, modification function
amorpheus/data.py        parameters, Init.txt, file reading, batch table
amorpheus/autodetect.py  parameter detection from data files (header, range, composition, density)
amorpheus/analysis.py    normalization, fitting, loops, χ² map, batch
amorpheus/export.py      writing results
amorpheus/plots.py       plots
amorpheus/rps.py         peak removal and smoothing
amorpheus/gui/           PyQt5 interface
examples/                example data (Ce glass) and an example batch table
tests/                   compatibility test against the original
```

## Citation and licence

If you use this program in a publication, please cite the original work:

> S. Boccato, Y. Garino, G. Morard, B. Zhao, F. Xu, C. Sanloup, A. King, N. Guignot, A. Clark, G. Garbarino,
> *Amorpheus: a Python-based software for the treatment of X-ray scattering data of amorphous and liquid
> systems*, High Pressure Research **42**(1), 69–93 (2022),
> doi:[10.1080/08957959.2022.2032032](https://doi.org/10.1080/08957959.2022.2032032)

The normalization method is from G. Morard et al. (2013); see the article above for the full reference.

Licence: **GNU GPL v3**, the same as the original (see [LICENSE](LICENSE)).
