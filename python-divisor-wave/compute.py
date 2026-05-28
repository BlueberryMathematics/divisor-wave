"""
compute.py — vectorized grid computation for all divisor-wave functions.

The key idea
────────────
The old plot_cli.py called fn(complex(x, y)) once per grid point in a nested
Python for-loop — e.g. 18 000 slow Python calls for a 180×100 grid.  Here we
replace every inner product loop with NumPy broadcasting so the entire grid is
evaluated in one shot:

    k  shape: (K, 1, 1)   — product index
    X3 shape: (1, rows, cols)   — broadcast over grid
    Z3 shape: (1, rows, cols)
    → terms shape: (K, rows, cols)  → np.prod(axis=0) → (rows, cols)

No Python loops over grid points at all.

GPU readiness
─────────────
Replace `import numpy as np` with `import cupy as cp; np = cp` and
`import scipy.special` with `import cupyx.scipy.special as scipy_special`
to run on any CUDA-compatible GPU (NVIDIA) or ROCm GPU (AMD Linux).
DirectML / AMD Windows support can be added similarly once stable.

Fallback
────────
Functions 3, 15-18, 30-32 are recursive or broken and fall back to
parallel scalar evaluation via ProcessPoolExecutor across all CPU cores.
"""

import os
import math
import warnings
import numpy as np
import scipy.special
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed


# ── Default m / beta per function ──────────────────────────────────────────
# Mirrors the hardcoded values inside special_functions.py.
# Format: {fid: {'both': (m, beta)}} or {fid: {'N': ..., 'Y': ...}}
_DEFAULTS = {
    '1':  {'both': (0.0465,  0.178)},
    '2':  {'N': (0.0125, 0.078),   'Y': (0.36,   0.1468)},
    '4':  {'both': (0.0125,  0.054)},
    '5':  {'both': (0.0125,  0.054)},
    '6':  {'both': (0.0125,  0.054)},
    '7':  {'both': (0.0125,  0.054)},
    '8':  {'N': (0.07,  1.0),      'Y': (0.27,   1.0)},
    '9':  {'N': (0.87,  1.0),      'Y': (0.87,   0.4)},
    '10': {'N': (0.007, 0.004),    'Y': (0.004,  0.004)},
    '11': {'both': (0.0125,  0.054)},
    '12': {'both': (0.0125,  0.054)},
    '13': {'both': (0.0125,  0.054)},
    '14': {'both': (0.0125,  0.054)},
    '23': {'both': (0.0125,  0.078)},
    '24': {'both': (0.0125,  0.078)},
    '25': {'both': (0.0125,  0.054)},
    '26': {'both': (0.001,   0.07)},
    '27': {'both': (0.001,   0.07)},
    '28': {'N': (0.07,  1.0),      'Y': (0.37,   0.07)},
    '29': {'both': (0.001,   0.07)},
    '30': {'both': (0.001,   0.07)},
    '31': {'both': (0.001,   0.07)},
}

def _resolve(fid, normalize, m_override, beta_override):
    """Return (m, beta) using override if provided, else function defaults."""
    entry = _DEFAULTS.get(str(fid), {})
    if 'both' in entry:
        dm, db = entry['both']
    else:
        dm, db = entry.get(normalize, entry.get('N', (0.0125, 0.054)))
    m    = m_override    if m_override    is not None else dm
    beta = beta_override if beta_override is not None else db
    return float(m), float(beta)


# ── Low-level vectorized primitives ───────────────────────────────────────

def _Z(X, Y):
    return X.astype(np.float64) + 1j * Y.astype(np.float64)

def _Nmax(X):
    return max(int(np.nanmax(X)), 2)

def _k3(N):
    """k broadcast array shape (K,1,1)."""
    return np.arange(2, N + 1, dtype=np.float64)[:, None, None]

def _valid(k, X):
    """Boolean mask (K,rows,cols): k <= floor(x)."""
    return k <= np.floor(X[None, ...])

def _prod_abs(terms, valid):
    """abs(∏ terms) with identity masking on invalid positions."""
    return np.abs(np.prod(np.where(valid, terms, 1.0 + 0j), axis=0))

def _finalize(raw_abs, m, normalize):
    with np.errstate(all='ignore'):
        W = raw_abs.real ** (-m)
    if normalize == 'Y':
        with np.errstate(all='ignore'):
            W = W / scipy.special.gamma(W)
    return np.where(np.isfinite(W), W, 0.0)


# ── Single-product helper ──────────────────────────────────────────────────
def _single(X, Y, m, beta, normalize, term_fn):
    """
    W = abs( ∏_{k=2}^{floor(x)} term_fn(Z3, k, X3) ) ^ (-m)
    term_fn(Z3, k, X3) → array (K,rows,cols)
    """
    Z  = _Z(X, Y);  N = _Nmax(X)
    k  = _k3(N);    v = _valid(k, X)
    Z3 = Z[None, ...];  X3 = X[None, ...]
    return _finalize(_prod_abs(term_fn(Z3, k, X3), v), m, normalize)


# ── Double-product helper ──────────────────────────────────────────────────
def _double(X, Y, m, beta, normalize, outer_fn):
    """
    W = abs( ∏_n outer_fn(Z, X, Y, n, inner_prod_n) ) ^ (-m)
    inner_prod_n = ∏_{k=2}^{floor(x)} inner_term(Z3, k, n)
    outer_fn(Z, X, Y, n, ip) → (rows,cols)
    inner_term supplied by outer_fn via closure
    """
    Z = _Z(X, Y);  N = _Nmax(X)
    acc = np.ones_like(Z)
    for n in range(2, N + 1):
        nf      = float(n)
        n_ok    = np.floor(X) >= nf
        k       = _k3(N);  Z3 = Z[None, ...]
        inner   = 1.0 - Z3**2 / (nf**2 * k**2)
        ip      = np.prod(np.where(_valid(k, X), inner, 1.0 + 0j), axis=0)
        term    = outer_fn(Z, X, Y, nf, ip, beta)
        acc     = np.where(n_ok, acc * term, acc)
    return _finalize(np.abs(acc), m, normalize)


# ═══════════════════════════════════════════════════════════════════════════
#  Vectorized function implementations
# ═══════════════════════════════════════════════════════════════════════════

def _fn1(X, Y, m, beta, normalize):
    """1 · Product of Sin"""
    return _single(X, Y, m, beta, normalize,
                   lambda Z3, k, X3: beta * (X3 / k) * np.sin(np.pi * Z3 / k))

def _fn2(X, Y, m, beta, normalize):
    """2 · Product Rep. for Sin"""
    return _double(X, Y, m, beta, normalize,
                   lambda Z, X, Y, nf, ip, beta:
                       beta * (X / nf) * (np.pi * Z) * ip)

def _fn4(X, Y, m, beta, normalize):
    """4 · Complex Playground (Riesz Cos 3)"""
    return _single(X, Y, m, beta, normalize,
                   lambda Z3, k, X3:
                       np.power(1j * Z3.imag + (1j * Z3.imag) * np.sin(np.pi * Z3 * k),
                                1j * Z3.imag))

def _fn5(X, Y, m, beta, normalize):
    """5 · Riesz — Cos"""
    return _single(X, Y, m, beta, normalize,
                   lambda Z3, k, X3:
                       np.power(1j * Z3.imag + np.cos(np.pi * Z3 * k),
                                1j * Z3.imag))

def _fn6(X, Y, m, beta, normalize):
    """6 · Riesz — Sin"""
    return _single(X, Y, m, beta, normalize,
                   lambda Z3, k, X3: 1.0 + np.sin(np.pi * Z3 * k))

def _fn7(X, Y, m, beta, normalize):
    """7 · Riesz — Tan"""
    return _single(X, Y, m, beta, normalize,
                   lambda Z3, k, X3: 1.0 + np.tan(np.pi * Z3 * k))

def _fn8(X, Y, m, beta, normalize):
    """8 · Viète — Cos"""
    return _single(X, Y, m, beta, normalize,
                   lambda Z3, k, X3: np.cos(np.pi * Z3 / (2.0 ** k)))

def _fn9(X, Y, m, beta, normalize):
    """9 · Viète — Sin"""
    return _single(X, Y, m, beta, normalize,
                   lambda Z3, k, X3: np.sin(np.pi * Z3 / (2.0 ** k)))

def _fn10(X, Y, m, beta, normalize):
    """10 · Viète — Tan"""
    return _single(X, Y, m, beta, normalize,
                   lambda Z3, k, X3: np.tan(np.pi * Z3 / (2.0 ** k)))

def _fn11(X, Y, m, beta, normalize):
    """11 · cos(Product of Sin)"""
    Z = _Z(X, Y);  N = _Nmax(X)
    k = _k3(N);    v = _valid(k, X)
    Z3 = Z[None, ...];  X3 = X[None, ...]
    inner = _prod_abs(beta * (X3 / k) * np.sin(np.pi * Z3 / k), v) ** (-m)
    W = np.cos(inner)
    if normalize == 'Y':
        with np.errstate(all='ignore'):
            W = W / scipy.special.gamma(W)
    return np.where(np.isfinite(W), W, 0.0)

def _fn12(X, Y, m, beta, normalize):
    """12 · sin(Product of Sin)"""
    Z = _Z(X, Y);  N = _Nmax(X)
    k = _k3(N);    v = _valid(k, X)
    Z3 = Z[None, ...];  X3 = X[None, ...]
    inner = _prod_abs(beta * (X3 / k) * np.sin(np.pi * Z3 / k), v) ** (-m)
    W = np.sin(inner)
    if normalize == 'Y':
        with np.errstate(all='ignore'):
            W = W / scipy.special.gamma(W)
    return np.where(np.isfinite(W), W, 0.0)

def _fn13(X, Y, m, beta, normalize):
    """13 · cos(Product Rep. of Sin)"""
    Z = _Z(X, Y);  N = _Nmax(X)
    acc = np.ones_like(Z)
    for n in range(2, N + 1):
        nf   = float(n);  n_ok = np.floor(X) >= nf
        k    = _k3(N);    Z3   = Z[None, ...]
        ip   = np.prod(np.where(_valid(k, X), 1.0 - Z3**2 / (nf**2 * k**2), 1.0 + 0j), axis=0)
        term = beta * (X / nf) * (np.pi * Z) * ip
        acc  = np.where(n_ok, acc * term, acc)
    with np.errstate(all='ignore'):
        W = np.cos(np.abs(acc)) ** (-m)
    if normalize == 'Y':
        with np.errstate(all='ignore'):
            W = W / scipy.special.gamma(W)
    return np.where(np.isfinite(W), W, 0.0)

def _fn14(X, Y, m, beta, normalize):
    """14 · sin(Product Rep. of Sin)"""
    Z = _Z(X, Y);  N = _Nmax(X)
    acc = np.ones_like(Z)
    for n in range(2, N + 1):
        nf   = float(n);  n_ok = np.floor(X) >= nf
        k    = _k3(N);    Z3   = Z[None, ...]
        ip   = np.prod(np.where(_valid(k, X), 1.0 - Z3**2 / (nf**2 * k**2), 1.0 + 0j), axis=0)
        term = beta * (X / nf) * (np.pi * Z) * ip
        acc  = np.where(n_ok, acc * term, acc)
    with np.errstate(all='ignore'):
        W = np.sin(np.abs(acc)) ** (-m)
    if normalize == 'Y':
        with np.errstate(all='ignore'):
            W = W / scipy.special.gamma(W)
    return np.where(np.isfinite(W), W, 0.0)

def _fn19(X, Y, m, beta, normalize):
    """19 · |loggamma(z)|"""
    Z = _Z(X, Y)
    with np.errstate(all='ignore'):
        W = np.abs(scipy.special.loggamma(Z)).real
    return np.where(np.isfinite(W), W, 0.0)

def _fn20(X, Y, m, beta, normalize):
    """20 · 1/(1+z²)"""
    Z = _Z(X, Y)
    with np.errstate(all='ignore'):
        W = np.abs(1.0 / (1.0 + Z**2)).real
    return np.where(np.isfinite(W), W, 0.0)

def _fn21(X, Y, m, beta, normalize):
    """21 · |z^z|"""
    Z = _Z(X, Y)
    with np.errstate(all='ignore'):
        W = np.abs(Z**Z).real
    return np.where(np.isfinite(W), W, 0.0)

def _fn22(X, Y, m, beta, normalize):
    """22 · gamma(z)"""
    Z = _Z(X, Y)
    with np.errstate(all='ignore'):
        W = np.abs(scipy.special.gamma(Z)).real
    return np.where(np.isfinite(W), W, 0.0)

def _fn23(X, Y, m, beta, normalize):
    """23 · log(Product Rep. Sin)"""
    Z = _Z(X, Y);  N = _Nmax(X)
    acc = np.ones_like(Z)
    for n in range(2, N + 1):
        nf   = float(n);  n_ok = np.floor(X) >= nf
        k    = _k3(N);    Z3   = Z[None, ...]
        ip   = np.prod(np.where(_valid(k, X), 1.0 - Z3**2 / (nf**2 * k**2), 1.0 + 0j), axis=0)
        term = beta * (X / nf) * (np.pi * Z) * ip
        acc  = np.where(n_ok, acc * term, acc)
    raw = np.abs(acc) ** (-m)
    with np.errstate(all='ignore'):
        W = np.abs(np.log(raw + 1e-300))
    return np.where(np.isfinite(W), W, 0.0)

def _fn24(X, Y, m, beta, normalize):
    """24 · gamma(Product Rep. Sin)"""
    Z = _Z(X, Y);  N = _Nmax(X)
    acc = np.ones_like(Z)
    for n in range(2, N + 1):
        nf   = float(n);  n_ok = np.floor(X) >= nf
        k    = _k3(N);    Z3   = Z[None, ...]
        ip   = np.prod(np.where(_valid(k, X), 1.0 - Z3**2 / (nf**2 * k**2), 1.0 + 0j), axis=0)
        term = beta * (X / nf) * (np.pi * Z) * ip
        acc  = np.where(n_ok, acc * term, acc)
    raw = np.abs(acc) ** (-m)
    with np.errstate(all='ignore'):
        W = scipy.special.gamma(raw)
    return np.where(np.isfinite(W), W, 0.0)

def _fn25(X, Y, m, beta, normalize):
    """25 · Gamma Form Product Rep. Sin"""
    Z = _Z(X, Y);  N = _Nmax(X)
    acc = np.ones_like(Z)
    for n in range(2, N + 1):
        nf   = float(n);  n_ok = np.floor(X) >= nf
        k    = _k3(N);    Z3   = Z[None, ...]
        exp_t = np.exp(Z3**2 / (nf**2 * k**2))
        ep   = np.prod(np.where(_valid(k, X), exp_t, 1.0 + 0j), axis=0)
        with np.errstate(all='ignore'):
            gz  = scipy.special.gamma(Z)
            g1z = scipy.special.gamma(1.0 - Z)
            term = beta * (Y * X / nf) * gz * g1z * np.exp(-Z**2) * ep
        acc = np.where(n_ok, acc * term, acc)
    return _finalize(np.abs(acc), m, normalize)

def _fn26(X, Y, m, beta, normalize):
    """26 · Custom Riesz — Tan"""
    Z = _Z(X, Y);  N = _Nmax(X)
    k = _k3(N);    v = _valid(k, X)
    p = _prod_abs(1.0 + np.tan(np.pi * Z[None, ...] * k), v) ** (-m)
    with np.errstate(all='ignore'):
        W = p / scipy.special.gamma(p)
    return np.where(np.isfinite(W), W, 0.0)

def _fn27(X, Y, m, beta, normalize):
    """27 · Custom Viète — Cos"""
    Z = _Z(X, Y);  N = _Nmax(X)
    k = _k3(N);    v = _valid(k, X)
    X3 = X[None, ...]
    with np.errstate(all='ignore'):
        terms = 1.0 + np.cos(np.pi * Z[None, ...] / (X3 ** k))
    p = _prod_abs(terms, v) ** (-m)
    with np.errstate(all='ignore'):
        W = p / scipy.special.gamma(p)
    return np.where(np.isfinite(W), W, 0.0)

def _fn28(X, Y, m, beta, normalize):
    """28 · Half-Base Viète — Sin  (base = 2^(-k))"""
    return _single(X, Y, m, beta, normalize,
                   lambda Z3, k, X3: np.sin(np.pi * Z3 * (2.0 ** k)))

def _fn29(X, Y, m, beta, normalize):
    """29 · Log-Power-Base Viète — Sin"""
    Z = _Z(X, Y);  N = _Nmax(X)
    k = _k3(N);    v = _valid(k, X)
    Z3 = Z[None, ...]
    with np.errstate(all='ignore'):
        exp = (1.0 / k) * np.log(Z3 + 1e-300)
        terms = np.sin(np.pi * Z3 / (2.0 ** exp))
    p = _prod_abs(terms, v) ** (-m)
    W = 1.0 + p
    with np.errstate(all='ignore'):
        W = W / scipy.special.gamma(W)
    return np.where(np.isfinite(W), W, 0.0)


# ── Dispatch table ─────────────────────────────────────────────────────────
_VECTORIZED = {
    '1':  _fn1,  '2':  _fn2,
    '4':  _fn4,  '5':  _fn5,  '6':  _fn6,  '7':  _fn7,
    '8':  _fn8,  '9':  _fn9,  '10': _fn10,
    '11': _fn11, '12': _fn12, '13': _fn13, '14': _fn14,
    '19': _fn19, '20': _fn20, '21': _fn21, '22': _fn22,
    '23': _fn23, '24': _fn24, '25': _fn25,
    '26': _fn26, '27': _fn27, '28': _fn28, '29': _fn29,
}

# Functions 3, 15-18, 30-32 fall back to scalar parallel evaluation.
# (3 is broken; 15-18 are deeply recursive; 30-32 are complex combinations.)


# ── Scalar parallel fallback ───────────────────────────────────────────────
def _scalar_chunk(args):
    """Worker: evaluate scalar fn over a flat slice of the grid.
    Defined at module level so ProcessPoolExecutor can pickle it on Windows.
    Avoids importing plot_cli to prevent circular imports.
    """
    fid, normalize, m_ov, beta_ov, xs, ys = args
    import sys, os, math as _math
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from special_functions import Special_Functions as _SF

    class _SFW(_SF):
        def __init__(self, plot_type, m_override=None, beta_override=None):
            self.__dict__['_m_ov']    = m_override
            self.__dict__['_beta_ov'] = beta_override
            super().__init__(plot_type)
        def __setattr__(self, name, value):
            if name == 'm'    and self.__dict__.get('_m_ov')    is not None:
                value = self.__dict__['_m_ov']
            elif name == 'beta' and self.__dict__.get('_beta_ov') is not None:
                value = self.__dict__['_beta_ov']
            super().__setattr__(name, value)

    sf  = _SFW('3D', m_override=m_ov, beta_override=beta_ov)
    fn  = sf.lamda_function_library(normalize, selection=fid)
    out = [0.0] * len(xs)
    for i, (x, y) in enumerate(zip(xs, ys)):
        try:
            w = float(fn(complex(x, y)))
            if _math.isfinite(w):
                out[i] = w
        except Exception:
            pass
    return out


def _parallel_scalar(function_id, normalize, X, Y, m_override, beta_override):
    """Evaluate a non-vectorizable function over the grid using all CPU cores."""
    n_workers = max(1, os.cpu_count() or 1)
    flat_x    = X.ravel().tolist()
    flat_y    = Y.ravel().tolist()
    n         = len(flat_x)
    chunk_sz  = max(1, math.ceil(n / n_workers))
    chunks    = [(function_id, normalize, m_override, beta_override,
                  flat_x[i:i+chunk_sz], flat_y[i:i+chunk_sz])
                 for i in range(0, n, chunk_sz)]

    result = np.zeros(n, dtype=np.float64)
    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = [pool.submit(_scalar_chunk, c) for c in chunks]
        for idx, fut in enumerate(futures):
            start = idx * chunk_sz
            vals  = fut.result()
            result[start:start + len(vals)] = vals
    return result.reshape(X.shape)


# ── Threaded vectorized execution ─────────────────────────────────────────
def _threaded_vec(vec_fn, X, Y, m, beta, normalize):
    """
    Split the grid into row-chunks and run vec_fn on each chunk in parallel
    threads.  NumPy releases the GIL during C-level operations, so threads
    genuinely run on separate CPU cores with no pickling overhead.
    """
    n_threads = max(1, os.cpu_count() or 1)
    rows      = X.shape[0]

    # No point spawning more threads than there are rows.
    n_threads = min(n_threads, rows)
    if n_threads <= 1:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return vec_fn(X, Y, m, beta, normalize)

    chunk_size = math.ceil(rows / n_threads)
    slices     = range(0, rows, chunk_size)
    results    = [None] * len(list(slices))

    def _run(idx, r_start, r_end):
        Xc = X[r_start:r_end, :]
        Yc = Y[r_start:r_end, :]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return idx, vec_fn(Xc, Yc, m, beta, normalize)

    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        futures = [
            pool.submit(_run, idx, r, min(r + chunk_size, rows))
            for idx, r in enumerate(range(0, rows, chunk_size))
        ]
        for fut in futures:
            idx, chunk_result = fut.result()
            results[idx] = chunk_result

    return np.vstack(results)


# ── Per-column (imaginary-axis) normalization ──────────────────────────────
def _normalize_per_column(W):
    """
    For each fixed real value (column in the meshgrid), scale the imaginary-axis
    profile so its maximum = 1.  This keeps the waves equally 'hilly' at all x
    regardless of how many product terms have accumulated — without distorting
    the relative shape (zeros and valleys remain near zero within each column).
    """
    col_max = W.max(axis=0, keepdims=True)
    return np.where(col_max > 0, W / np.maximum(col_max, 1e-300), W)


# ── Power stretch ──────────────────────────────────────────────────────────
def _power_stretch(W, p):
    """
    Apply W^p  (0 < p < 1) to expand low values upward.

    Since W = |product|^(-m), applying W^p gives |product|^(-m·p), which is
    exactly equivalent to plotting the same function with a smaller effective m.
    The shape of every feature is preserved — poles stay poles, valleys stay
    valleys — but the flanks are stretched so that off-axis structure (waves in
    the imaginary direction) gains more height and colour contrast.

    p = 1.0  → no change (identity)
    p = 0.4  → moderate stretch, equivalent to ~40 % of the original m
    p = 0.2  → aggressive stretch
    """
    with np.errstate(all='ignore'):
        out = np.power(W, p)
    return np.where(np.isfinite(out), out, 0.0)


# ── Load user-defined functions from JSON ─────────────────────────────────
def _load_user_functions():
    """
    Read user_functions.json from the repo root, compile each LaTeX term
    with LatexToNumpy, and register the result in _VECTORIZED / _DEFAULTS.

    Safe to call at import time — failures are silently skipped.
    """
    import json as _json
    _ufpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'function-library', 'user_functions.json')
    if not os.path.exists(_ufpath):
        return

    try:
        with open(_ufpath, 'r', encoding='utf-8') as _f:
            _data = _json.load(_f)
    except Exception:
        return

    try:
        from formula_bridge import LatexToNumpy
        _ltn = LatexToNumpy()
    except Exception:
        return

    for _fn in _data.get('functions', []):
        _fid   = str(_fn.get('id', ''))
        _latex = _fn.get('latex', '')
        _defs  = _fn.get('defaults', {})
        _m_d   = float(_defs.get('m',    0.0125))
        _b_d   = float(_defs.get('beta', 0.054))

        if not _fid or not _latex:
            continue

        try:
            _term = _ltn.make_term_fn(_latex)
        except Exception as _e:
            import warnings as _w
            _w.warn(f'compute: skip user fn {_fid!r}: {_e}')
            continue

        # Capture loop variables in closure
        def _make_vec_fn(_tf, _md, _bd):
            def _user_vec(X, Y, m, beta, normalize):
                return _single(X, Y, m, beta, normalize,
                               lambda Z3, k, X3: _tf(Z3, k, X3, beta=beta))
            return _user_vec

        _VECTORIZED[_fid] = _make_vec_fn(_term, _m_d, _b_d)
        _DEFAULTS[_fid]   = {'both': (_m_d, _b_d)}


_load_user_functions()


# ── Public entry point ─────────────────────────────────────────────────────
def compute_grid(function_id, normalize, X, Y, m_override=None, beta_override=None,
                 col_normalize=False, power_stretch=1.0):
    """
    Compute the plot surface W over the grid (X, Y).

    Parameters
    ----------
    function_id   : str or int
    normalize     : 'Y' or 'N'
    X, Y          : 2-D float ndarray (meshgrid)
    m_override    : float or None
    beta_override : float or None
    col_normalize : bool  — per-column max normalisation (equal hilliness in y)
    power_stretch : float — W^p stretch; 1.0 = off, <1.0 expands low values

    Returns
    -------
    W : 2-D float ndarray, same shape as X/Y
    """
    fid = str(function_id)
    m, beta = _resolve(fid, normalize, m_override, beta_override)

    vec_fn = _VECTORIZED.get(fid)
    if vec_fn is not None:
        W = _threaded_vec(vec_fn, X, Y, m, beta, normalize)
    else:
        # Scalar parallel fallback via processes (fn 3, 15-18, 30-32)
        W = _parallel_scalar(fid, normalize, X, Y, m_override, beta_override)

    if col_normalize:
        W = _normalize_per_column(W)
    if power_stretch < 1.0:
        W = _power_stretch(W, power_stretch)
    return W
