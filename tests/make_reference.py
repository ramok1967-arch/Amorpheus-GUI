"""Compute reference results with the ORIGINAL Amorpheus equations.py (v1.0.5).

Replicates exactly the code paths of Amorpheus.py menu options [n], [r], [x], [c].
Run with:  python -I make_reference.py <path-to-original-Amorpheus-dir> <data-dir> <out.npz>
<data-dir> must contain Cerium.dat, background.xy and the 2-theta versions Cerium_tth.dat,
background_tth.xy (generated as in test_against_original.py, lambda = 0.03738 nm).
"""
import sys, types, os
import numpy as np
import scipy.integrate as si
from scipy import stats
from scipy.signal import find_peaks

# oryginal uzywa np.trapz i scipy.integrate.trapz (usuniete w NumPy 2 / SciPy 1.14),
# ezodf (tylko batch) i periodictable (tylko liczby atomowe) - podstawiamy zamienniki
trapz = getattr(np, "trapezoid", None) or np.trapz
if not hasattr(np, "trapz"):
    np.trapz = trapz
if not hasattr(si, "trapz"):
    si.trapz = trapz
sys.modules['ezodf'] = types.SimpleNamespace(opendoc=None, Sheet=None)
try:
    import periodictable  # noqa: F401
except ImportError:
    import xraylib
    _pt = types.ModuleType('periodictable')
    for _z in range(1, 99):
        _s = xraylib.AtomicNumberToSymbol(_z)
        setattr(_pt, _s, types.SimpleNamespace(number=_z, name=_s))
    sys.modules['periodictable'] = _pt
import matplotlib
matplotlib.use('Agg')

orig_dir, data_dir, out_path = sys.argv[1:4]
sys.path.insert(0, orig_dir)
import equations as eq
from lmfit import Parameters, minimize

os.chdir(data_dir)
el = ['Ce', 'Al', 'Ni', 'Cu', 'Fe', 'C']
ratio = np.array([0.7, 0.1, 0.1, 0.1, 0.0, 0.0])
qmin, qmax, rmin, rho, bk, lam = 15.0, 78.0, 0.22, 34.68, 0.927, 0.03738
ref = {}


def load(ff, fn, fb, qmin_, qmax_, incoherent=1, QStep=0):
    thmin = np.arcsin(qmin_ * lam / 4 / np.pi) * 180 * 2 / np.pi
    thmax = np.arcsin(qmax_ * lam / 4 / np.pi) * 180 * 2 / np.pi
    Imeas = Ibkg = None
    if ff == 2:
        th, q, Imeas, Ibkg, inc, f2, fm2 = eq.openFiles_2(fn, fb, lam, thmin, thmax, QStep, incoherent, el, ratio)
    elif ff == 4:
        q, Imeas, Ibkg, inc, f2, fm2 = eq.openFiles_4(fn, fb, qmin_, qmax_, incoherent, el, ratio)
    elif ff == 3:
        q, Ibrut, inc, f2, fm2 = eq.openFiles_3(fn, qmin_, qmax_, incoherent, el, ratio)
    elif ff == 1:
        th, q, Ibrut, inc, f2, fm2 = eq.openFiles_1(fn, lam, thmin, thmax, QStep, incoherent, el, ratio)
    if ff in (2, 4):
        Ibrut = Imeas - bk * Ibkg
    return q, Imeas, Ibkg, Ibrut, inc, f2, fm2


def extend(q_old):
    pasq = q_old[1] - q_old[0]
    addq = np.sort(np.arange(q_old[0], 0, -pasq))[:-1]
    q = np.concatenate((addq, q_old))
    return q, np.abs(q - q_old[0]).argmin()


def normalize(tag, ff, fn, fb, SofQ=1, rho_=rho, QStep=0):
    q, Imeas, Ibkg, Ibrut, inc, f2, fm2 = load(ff, fn, fb, qmin, qmax, QStep=QStep)
    rmax = 1
    R = np.linspace(0, rmax, 9001); R[0] = 5e-4
    q_old = q
    q, diff = extend(q_old)
    S = np.zeros((eq.prout + 1, len(q))); gr = np.zeros((eq.prout + 1, len(R))); F = np.zeros((eq.prout + 1, len(R)))
    S, F, g = eq.getSandF3(q, S, F, gr, Ibrut, rho_, R, rmin, rmax, diff, inc, ratio, f2, fm2, SofQ, None, None)
    indrmin = np.abs(R - rmin).argmin()
    dens = np.array([-stats.linregress(R[0:indrmin], F[i][0:indrmin]).slope / (4 * np.pi) for i in range(eq.prout + 1)])
    intMin = np.abs(R - rmin).argmin()
    cn = []
    for index in range(len(g)):
        peaks, _ = find_peaks(g[index])
        intMax = peaks[np.argmax(peaks > intMin)]
        CN1 = 2 * trapz(4 * np.pi * rho_ * R[intMin:intMax] ** 2 * g[index][intMin:intMax], R[intMin:intMax])
        peak_2 = peaks[np.argmax(peaks > intMax + 1)]
        intMax2 = intMax + g[index][intMax:peak_2].argmin()
        CN2 = trapz(4 * np.pi * rho_ * R[intMin:intMax2] ** 2 * g[index][intMin:intMax2], R[intMin:intMax2])
        cn.append([CN1, CN2, R[intMin], R[intMax], R[intMax2]])
    a, b = R[intMax], R[intMax] - rmin
    Flast = eq.calcF_speed_ModificationFunction(R, q, S[-1], a, b)
    grlast = 1 + Flast / (4 * np.pi * R * rho_)
    ref.update({f'{tag}_q': q, f'{tag}_S': S, f'{tag}_R': R, f'{tag}_F': F, f'{tag}_g': g,
                f'{tag}_dens': dens, f'{tag}_cn': np.array(cn), f'{tag}_grlast': grlast, f'{tag}_ab': np.array([a, b]),
                f'{tag}_Ibrut': Ibrut})
    print(tag, 'done; CN last', cn[-1][:2], 'dens', dens[-2])


def fit(ff, fn, fb, rmin_, qmax_=qmax, rho0=rho, bk0=bk, rmaxR=0.4):
    q, Imeas, Ibkg, Ibrut, inc, f2, fm2 = load(ff, fn, fb, qmin, qmax_)
    R = np.arange(0, rmaxR, 0.0005); R[0] = 1e-6
    q, diff = extend(q)
    S = np.zeros((eq.prout + 1, len(q))); gr = np.zeros((eq.prout + 1, len(R))); F = np.zeros((eq.prout + 1, len(R)))
    ind = np.abs(R - rmin_).argmin()
    p = Parameters(); p.add('rhomi', value=rho0, min=max(1, rho0 - 50), max=rho0 + 50)
    if ff in (2, 4):
        p.add('bkfactor', value=bk0, min=0.7, max=1.2)
        args = (q, S, F, gr, Imeas, Ibkg, R, rmin_, rmaxR, diff, inc, ratio, f2, fm2, 1, ind, None, None)
        fn_ = eq.chisquare_DAC_LMFIT
    else:
        args = (q, S, F, gr, Ibrut, R, rmin_, rmaxR, diff, inc, ratio, f2, fm2, 1, ind, None, None)
        fn_ = eq.chisquare_LV_LMFIT
    out = minimize(fn_, p, args=args, method='nelder', options={'maxfev': 500, 'fatol': 0.0001, 'xatol': 0.0001})
    bkv = out.params['bkfactor'].value if ff in (2, 4) else 0
    return [rmin_, out.params['rhomi'].value, bkv, out.residual[0]], (fn_, args)


normalize('n4', 4, 'Cerium.dat', 'background.xy')
normalize('n3', 3, 'Cerium.dat', None)
normalize('n2', 2, 'Cerium_tth.dat', 'background_tth.xy')
normalize('n1', 1, 'Cerium_tth.dat', None)
normalize('n4s0', 4, 'Cerium.dat', 'background.xy', SofQ=0)
normalize('n2qs', 2, 'Cerium_tth.dat', 'background_tth.xy', QStep=1)

res, (fn_, args) = fit(4, 'Cerium.dat', 'background.xy', rmin)
ref['fit4'] = np.array(res); print('fit4', res)
# single chi2 evaluations at fixed parameters (deterministic, no optimizer)
chis = []
for r_, b_ in [(30.0, 0.9), (34.68, 0.927), (38.0, 1.0)]:
    p = Parameters(); p.add('rhomi', value=r_); p.add('bkfactor', value=b_)
    chis.append(fn_(p, *args))
ref['chi4_points'] = np.array(chis); print('chi', chis)
res, (fn3, args3) = fit(3, 'Cerium.dat', None, rmin, rho0=30)
ref['fit3'] = np.array(res); print('fit3', res)
res, _ = fit(2, 'Cerium_tth.dat', 'background_tth.xy', rmin)
ref['fit2'] = np.array(res); print('fit2', res)
ref['loop_rmin'] = np.array([fit(4, 'Cerium.dat', 'background.xy', r)[0] for r in eq.arange(0.20, 0.24, 0.02)])
print('loop rmin', ref['loop_rmin'])
lq = []
for qm in eq.arange(60, 70, 10):
    r_ = fit(4, 'Cerium.dat', 'background.xy', rmin, qmax_=qm)[0]; r_[0] = qm; lq.append(r_)
ref['loop_qmax'] = np.array(lq); print('loop qmax', ref['loop_qmax'])
np.savez_compressed(out_path, **ref)
print('saved', out_path)
