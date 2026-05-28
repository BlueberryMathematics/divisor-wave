"""
plot_cli.py — Headless CLI wrapper for divisor wave plotting.
Spawned by Electron; prints a single JSON line to stdout.

Usage:
  python plot_cli.py --function 1 --normalize N --colormap 4
                     --resolution 0.1 --xmin 2 --xmax 20
                     --ymin -5 --ymax 5 --output <dir>
                     --elev 30 --azim -70
                     [--m 0.05] [--beta 0.2]
"""
import sys
import os
import json
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.axes_grid1 import make_axes_locatable

from special_functions import Special_Functions
from compute import compute_grid

plt.style.use('dark_background')

COLORMAPS = {
    '1': cm.prism,
    '2': cm.jet,
    '3': cm.plasma,
    '4': cm.viridis,
    '5': cm.magma,
}

FUNCTION_NAMES = {
    '1':  'Product of Sin',
    '2':  'Product of Product Rep. for Sin',
    '3':  'Product of Product Rep. for Sin (Complex)',
    '4':  'Complex Playground Demo',
    '5':  'Riesz Product — Cos',
    '6':  'Riesz Product — Sin',
    '7':  'Riesz Product — Tan',
    '8':  'Viète Product — Cos',
    '9':  'Viète Product — Sin',
    '10': 'Viète Product — Tan',
    '11': 'Cos of Product of Sin',
    '12': 'Sin of Product of Sin',
    '13': 'Cos of Product Rep. of Sin',
    '14': 'Sin of Product Rep. of Sin',
    '15': 'Binary Prime Indicator H',
    '16': 'Prime Output Indicator J',
    '17': 'BOPIF Q Alternation Series',
    '18': 'Dirichlet Eta from BOPIF',
    '19': 'Basic: |loggamma(z)|',
    '20': 'Basic: 1/(1+z²)',
    '21': 'Basic: |z^z|',
    '22': 'Basic: gamma(z)',
    '23': 'Log of Product Rep. for Sin',
    '24': 'Gamma of Product Rep. for Sin',
    '25': 'Gamma Form Product Rep. for Sin',
    '26': 'Custom Riesz — Tan',
    '27': 'Custom Viète — Cos',
    '28': 'Half-Base Viète — Sin',
    '29': 'Log-Power-Base Viète — Sin',
    '30': 'Riesz Tan + Prime Indicator',
    '31': 'Nested Roots Product for 2',
    '32': 'Product Factory (Custom Formula)',
}


def _load_user_function_names():
    """Load user-defined function names from function-library/user_functions.json."""
    try:
        _ufpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '..', 'function-library', 'user_functions.json')
        if not os.path.exists(_ufpath):
            return {}
        with open(_ufpath, 'r', encoding='utf-8') as _f:
            _data = json.load(_f)
        return {str(_fn['id']): _fn['name']
                for _fn in _data.get('functions', [])
                if 'id' in _fn and 'name' in _fn}
    except Exception:
        return {}


FUNCTION_NAMES.update(_load_user_function_names())


class _SFWithOverrides(Special_Functions):
    """
    Thin subclass that intercepts self.m and self.beta assignments inside each
    special function, replacing them with user-supplied override values when set.
    This requires zero changes to special_functions.py.
    """
    def __init__(self, plot_type, m_override=None, beta_override=None):
        # Write directly to __dict__ to bypass our own __setattr__
        self.__dict__['_m_override']    = m_override
        self.__dict__['_beta_override'] = beta_override
        super().__init__(plot_type)

    def __setattr__(self, name, value):
        if name == 'm' and self.__dict__.get('_m_override') is not None:
            value = self.__dict__['_m_override']
        elif name == 'beta' and self.__dict__.get('_beta_override') is not None:
            value = self.__dict__['_beta_override']
        super().__setattr__(name, value)


def generate_plot_2d(function_id, normalize, colormap, resolution,
                     xmin, xmax, ymin, ymax, output_dir,
                     m_override=None, beta_override=None,
                     col_normalize=False, power_stretch=1.0):
    """Render function as a 2D heatmap over the complex plane."""
    X = np.arange(xmin, xmax, resolution)
    Y = np.arange(ymin, ymax, resolution)
    X, Y = np.meshgrid(X, Y)

    W = compute_grid(function_id, normalize, X, Y,
                     m_override=m_override, beta_override=beta_override,
                     col_normalize=col_normalize, power_stretch=power_stretch)

    # Adaptive figure size: keep the axes aspect close to the data range
    x_range  = max(float(xmax) - float(xmin), 0.001)
    y_range  = max(float(ymax) - float(ymin), 0.001)
    fig_h    = 6.5
    fig_w    = min(26.0, max(8.0, fig_h * (x_range / y_range) + 1.2))

    fig, ax  = plt.subplots(figsize=(fig_w, fig_h))
    cmap     = COLORMAPS.get(str(colormap), cm.viridis)
    mesh     = ax.pcolormesh(X, Y, W, cmap=cmap, shading='auto')

    ax.set_xlabel('Real Axis')
    ax.set_ylabel('Imaginary Axis')
    ax.set_aspect('equal', adjustable='box')

    # Colorbar exactly as tall as the axes — avoids the black-space mismatch
    divider = make_axes_locatable(ax)
    cax     = divider.append_axes('right', size='2.5%', pad=0.1)
    fig.colorbar(mesh, cax=cax, label='Value')

    fn_name  = FUNCTION_NAMES.get(str(function_id), f'Function {function_id}')
    norm_lbl = 'Normalized' if normalize == 'Y' else 'Raw'
    coeff_lbl = ''
    if m_override is not None or beta_override is not None:
        parts = []
        if m_override    is not None: parts.append(f'm={m_override}')
        if beta_override is not None: parts.append(f'β={beta_override}')
        coeff_lbl = '  [' + ', '.join(parts) + ']'
    extra_lbl = ''
    if col_normalize:                  extra_lbl += '  +col-norm'
    if power_stretch < 1.0:            extra_lbl += f'  p={power_stretch:.2f}'

    ax.set_title(f'{fn_name}  [{norm_lbl}]{coeff_lbl}{extra_lbl}')

    os.makedirs(output_dir, exist_ok=True)
    timestamp   = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename    = f'plot2d_fn{function_id}_{timestamp}.png'
    output_path = os.path.join(output_dir, filename)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return output_path, fn_name


def generate_plot(function_id, normalize, colormap, resolution,
                  xmin, xmax, ymin, ymax, output_dir, elev=30, azim=-70,
                  m_override=None, beta_override=None,
                  col_normalize=False, power_stretch=1.0):

    X = np.arange(xmin, xmax, resolution)
    Y = np.arange(ymin, ymax, resolution)
    X, Y = np.meshgrid(X, Y)

    # Vectorized grid computation — replaces the old nested Python for-loop.
    # Falls back to multiprocessing for recursive/complex functions (15-18, 30-32).
    W = compute_grid(function_id, normalize, X, Y,
                     m_override=m_override, beta_override=beta_override,
                     col_normalize=col_normalize, power_stretch=power_stretch)

    fig = plt.figure(figsize=(19, 11))
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(elev=elev, azim=azim)
    ax.dist = 10
    ax.set_box_aspect((5, 5, 1))

    cmap = COLORMAPS.get(str(colormap), cm.viridis)
    ax.plot_surface(X, Y, W, rstride=1, cstride=1, cmap=cmap)

    fn_name  = FUNCTION_NAMES.get(str(function_id), f'Function {function_id}')
    norm_lbl = 'Normalized' if normalize == 'Y' else 'Raw'
    coeff_lbl = ''
    if m_override is not None or beta_override is not None:
        parts = []
        if m_override    is not None: parts.append(f'm={m_override}')
        if beta_override is not None: parts.append(f'β={beta_override}')
        coeff_lbl = '  [' + ', '.join(parts) + ']'
    extra_lbl = ''
    if col_normalize:       extra_lbl += '  +col-norm'
    if power_stretch < 1.0: extra_lbl += f'  p={power_stretch:.2f}'

    ax.set_xlabel('Real Axis')
    ax.set_ylabel('Imaginary Axis')
    ax.set_zlabel('Value')
    ax.set_title(f'{fn_name}  [{norm_lbl}]{coeff_lbl}{extra_lbl}')

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename  = f'plot_fn{function_id}_{timestamp}.png'
    output_path = os.path.join(output_dir, filename)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return output_path, fn_name


def compute_auto_coeffs(function_id, normalize, xmin, xmax, ymin, ymax, n_samples=15):
    """
    Sample the function with m=1, beta=1 on a coarse grid and compute Lyapunov-derived
    coefficient estimates:
      m_opt    = 1 / std(log|output|)   — variance normalization
      beta_opt = exp(mean(log|output|) / N_avg)  — geometric mean centering
    Returns (m_opt, beta_opt, n_valid, note) or (None, None, n_valid, reason) on failure.
    """
    sf = _SFWithOverrides('3D', m_override=1.0, beta_override=1.0)
    fn = sf.lamda_function_library(normalize, selection=function_id)

    xs = np.linspace(max(float(xmin) + 0.5, 2.5), float(xmax) - 0.5, n_samples)
    ys = np.linspace(float(ymin) + 0.5, float(ymax) - 0.5, n_samples)

    log_vals, n_terms_list = [], []
    for x in xs:
        for y in ys:
            try:
                raw = float(fn(complex(x, y)))
                if raw > 0 and np.isfinite(raw):
                    log_vals.append(np.log(raw))
                    n_terms_list.append(max(int(x) - 1, 1))
            except Exception:
                pass

    n_valid = len(log_vals)
    if n_valid < 10:
        return None, None, n_valid, f'only {n_valid}/{n_samples**2} valid samples — cannot fit'

    log_arr = np.array(log_vals)
    mu      = float(np.mean(log_arr))
    sigma   = float(np.std(log_arr))
    n_avg   = float(np.mean(n_terms_list))

    if sigma < 1e-6:
        return None, None, n_valid, 'near-zero variance — function appears constant'

    m_opt    = float(np.clip(1.0 / sigma, 0.0001, 2.0))
    beta_opt = float(np.clip(np.exp(mu / max(n_avg, 1.0)), 0.0001, 2.0))
    note = f'{n_valid}/{n_samples**2} pts · log μ={mu:.3f} σ={sigma:.3f} N̄={n_avg:.0f}'
    return m_opt, beta_opt, n_valid, note


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Divisor wave headless plotter')
    parser.add_argument('--function',    required=True)
    parser.add_argument('--normalize',   default='N')
    parser.add_argument('--colormap',    default='4')
    parser.add_argument('--resolution',  type=float, default=0.15)
    parser.add_argument('--xmin',        type=float, default=2.0)
    parser.add_argument('--xmax',        type=float, default=20.0)
    parser.add_argument('--ymin',        type=float, default=-5.0)
    parser.add_argument('--ymax',        type=float, default=5.0)
    parser.add_argument('--elev',        type=float, default=30.0)
    parser.add_argument('--azim',        type=float, default=-70.0)
    parser.add_argument('--mode',        default='3d', choices=['2d', '3d'])
    parser.add_argument('--output',      default=None)
    parser.add_argument('--auto-coeffs', action='store_true', help='Compute auto coefficients and exit without plotting')
    parser.add_argument('--col-normalize', action='store_true', default=False,
                        help='Per-column (x-slice) normalization to equalize imaginary-axis hilliness')
    parser.add_argument('--power-stretch', type=float, default=1.0,
                        help='W^p power stretch (0<p<=1); 1.0=off, ~0.4=moderate, ~0.2=aggressive')
    # Optional coefficient overrides (omit to use each function's built-in defaults)
    parser.add_argument('--m',    type=float, default=None, help='Override m exponent coeff')
    parser.add_argument('--beta', type=float, default=None, help='Override beta lead coeff')

    args = parser.parse_args()

    if args.auto_coeffs:
        try:
            m, beta, n, note = compute_auto_coeffs(
                args.function, args.normalize,
                args.xmin, args.xmax, args.ymin, args.ymax,
            )
            if m is None:
                print(json.dumps({'success': False, 'error': note, 'samples': n}))
            else:
                print(json.dumps({'success': True, 'm': m, 'beta': beta, 'samples': n, 'note': note}))
        except Exception as e:
            import traceback
            print(json.dumps({'success': False, 'error': str(e), 'trace': traceback.format_exc()}))
            sys.exit(1)
        sys.exit(0)

    if args.output is None:
        print(json.dumps({'success': False, 'error': '--output is required for plot generation'}))
        sys.exit(1)

    try:
        if args.mode == '2d':
            path, name = generate_plot_2d(
                args.function, args.normalize, args.colormap,
                args.resolution,
                args.xmin, args.xmax, args.ymin, args.ymax,
                args.output,
                m_override=args.m, beta_override=args.beta,
                col_normalize=args.col_normalize,
                power_stretch=args.power_stretch,
            )
        else:
            path, name = generate_plot(
                args.function, args.normalize, args.colormap,
                args.resolution,
                args.xmin, args.xmax, args.ymin, args.ymax,
                args.output, args.elev, args.azim,
                m_override=args.m, beta_override=args.beta,
                col_normalize=args.col_normalize,
                power_stretch=args.power_stretch,
            )
        print(json.dumps({'success': True, 'path': path, 'name': name}))
    except Exception as e:
        import traceback
        print(json.dumps({'success': False, 'error': str(e), 'trace': traceback.format_exc()}))
        sys.exit(1)
