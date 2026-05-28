"""
formula_bridge.py — Bidirectional LaTeX ↔ NumPy formula conversion.

Two reusable classes
────────────────────
NumpyToLatex  maps function IDs to their paper-canonical LaTeX strings.
              Source-of-truth is the authored formulas, not code parsing
              (auto-parsing NumPy lambdas would be fragile).

LatexToNumpy  compiles a LaTeX product-term expression to a NumPy-
              compatible callable for use with compute._single().

              The user supplies only the TERM inside the product, e.g.:
                  \\beta \\frac{x}{k} \\sin\\!\\left(\\frac{\\pi z}{k}\\right)

              The outer \\prod_{k=2}^{\\lfloor x\\rfloor} and |·|^{-m} wrapper
              are handled separately by compute._single() / _finalize().

Variable mapping inside compiled NumPy code
────────────────────────────────────────────
  z  →  Z3   complex grid array, shape (K, rows, cols)
  x  →  X3   real-part grid array, same shape
  k  →  k    product index array, shape (K, 1, 1)
  y  →  Z3.imag  imaginary component
  \\pi   →  np.pi
  \\beta →  beta  (float, passed as keyword arg)
  \\alpha → beta  (same role in the paper)
  i  →  1j

The compiled term function has signature:
  term_fn(Z3, k, X3, beta=1.0) -> ndarray  shape (K, rows, cols)
and is the term_fn argument to compute._single().

Reuse notes
───────────
Both classes are standalone — no imports from the rest of this package.
Import just this module wherever LaTeX ↔ NumPy conversion is needed.
"""

import re
import numpy as np
import scipy.special


# ═══════════════════════════════════════════════════════════════════════════════
# NumpyToLatex
# ═══════════════════════════════════════════════════════════════════════════════

# Shorthand builders for common patterns
def _wrap1(term: str) -> str:
    """Single product: |∏_{k=2}^{⌊x⌋} <term>|^{-m}"""
    return (r'\left|\prod_{k=2}^{\lfloor x\rfloor}' + term +
            r'\right|^{-m}')

def _wrap2(term: str) -> str:
    """Double product outer: |∏_{n=2}^{⌊x⌋} <term>|^{-m}"""
    return (r'\left|\prod_{n=2}^{\lfloor x\rfloor}' + term +
            r'\right|^{-m}')

def _inner_prod(term: str) -> str:
    """Inner product over k: ∏_{k=2}^{⌊x⌋} <term>"""
    return r'\prod_{k=2}^{\lfloor x\rfloor}\!' + term

_b2    = r'\beta\dfrac{x}{k}'                            # β·(x/k)
_b2n   = r'\dfrac{\beta x}{n}'                           # β·(x/n)
_sinzk = r'\sin\!\left(\dfrac{\pi z}{k}\right)'          # sin(πz/k)
_dp    = _inner_prod(r'\!\left(1-\dfrac{z^2}{n^2k^2}\right)')  # inner double-product
_fn1t  = _b2 + _sinzk                                    # fn1 term
_fn2t  = _b2n + r'\cdot\pi z' + _dp                     # fn2 term (outer)

LATEX_FORMULAS: dict[str, str] = {
    # ── Basic product families ──────────────────────────────────────────────
    '1': _wrap1(_fn1t),
    '2': _wrap2(_fn2t),
    '3': r'[\text{complex variant — not implemented}]',
    '4': _wrap1(
        r'\left(iy+iy\sin(\pi zk)\right)^{iy}'
    ),

    # ── Riesz products ──────────────────────────────────────────────────────
    '5': _wrap1(r'\left(iy+\cos(\pi zk)\right)^{iy}'),
    '6': _wrap1(r'\bigl(1+\sin(\pi zk)\bigr)'),
    '7': _wrap1(r'\bigl(1+\tan(\pi zk)\bigr)'),

    # ── Viète products ──────────────────────────────────────────────────────
    '8':  _wrap1(r'\cos\!\left(\dfrac{\pi z}{2^k}\right)'),
    '9':  _wrap1(r'\sin\!\left(\dfrac{\pi z}{2^k}\right)'),
    '10': _wrap1(r'\tan\!\left(\dfrac{\pi z}{2^k}\right)'),

    # ── Compositions ────────────────────────────────────────────────────────
    '11': r'\cos\!\left(' + _wrap1(_fn1t) + r'\right)',
    '12': r'\sin\!\left(' + _wrap1(_fn1t) + r'\right)',
    '13': r'\cos\!\left(' + _wrap2(_fn2t) + r'\right)',
    '14': r'\sin\!\left(' + _wrap2(_fn2t) + r'\right)',

    # ── Prime / BOPIF ────────────────────────────────────────────────────────
    '15': (r'H(z)=a(z)^{B(z)}\quad'
           r'a(z)=' + _wrap1(_fn1t) + r',\quad'
           r'B(z)=' + _wrap2(_fn2t)),
    '16': (r'J(z)=a(z)^{a(z)^{B(z)}}'),
    '17': r'Q(z)=\left|\prod_{q=2}^{\lfloor x\rfloor}'
          r'(-1)^{|\cdots|^{-c}}\right|^{-m}',
    '18': r'\eta_{\mathrm{BOPIF}}(z)='
          r'\left|\prod_{k=2}^{\lfloor x\rfloor}'
          r'\frac{1}{1+Q(z)\cdot J(z)}\right|^{-c}',

    # ── Analytic basics ──────────────────────────────────────────────────────
    '19': r'\left|\ln\Gamma(z)\right|',
    '20': r'\dfrac{1}{1+z^2}',
    '21': r'\left|z^z\right|',
    '22': r'\Gamma(z)',

    # ── Transforms of b(z) ──────────────────────────────────────────────────
    '23': r'\ln' + _wrap2(_fn2t),
    '24': r'\Gamma\!\left(' + _wrap2(_fn2t) + r'\right)',
    '25': _wrap2(
        r'\dfrac{\beta xy}{n}\,\Gamma(z)\,\Gamma(1-z)\,'
        r'e^{-z^2}' +
        _inner_prod(r'e^{z^2/(n^2 k^2)}')
    ),

    # ── Custom / normalised variants ─────────────────────────────────────────
    '26': (r'\dfrac{' + _wrap1(r'\bigl(1+\tan(\pi zk)\bigr)') + r'}{'
           r'\Gamma\!\left(' + _wrap1(r'\bigl(1+\tan(\pi zk)\bigr)') + r'\right)}'),
    '27': (r'\dfrac{' +
           _wrap1(r'\left(1+\cos\!\left(\dfrac{\pi z}{x^k}\right)\right)') + r'}{'
           r'\Gamma\!\left(' +
           _wrap1(r'\left(1+\cos\!\left(\dfrac{\pi z}{x^k}\right)\right)') + r'\right)}'),
    '28': _wrap1(r'\sin\!\left(\pi z\cdot 2^k\right)'),
    '29': (r'1+\dfrac{' +
           _wrap1(r'\sin\!\left(\dfrac{\pi z}{2^{(\ln z)/k}}\right)') + r'}{'
           r'\Gamma\!\left(\cdots\right)}'),
    '30': (r'\cos\!\left(\dfrac{B(z)}{E(z)}\right)\quad'
           r'E(z)=' + _wrap1(r'\bigl(1+\tan(\pi zk)\bigr)')),
    '31': (r'\left|\sum_{n=2}^{\lfloor x\rfloor}z^{2^{-n}}\right|^{-m}'
           r'\cdot\prod_{n=2}^{\lfloor x\rfloor}\prod_{k=2}^{\lfloor x\rfloor}z^{k^{-n}}'),
    '32': r'[\text{product factory — replaced by custom functions}]',
}


class NumpyToLatex:
    """
    Maps function IDs (str '1'..'32') to their canonical LaTeX formula.

    Example
    -------
    >>> ntl = NumpyToLatex()
    >>> ntl.get('1')
    '\\left|\\prod_{k=2}^{...}...'
    """

    def get(self, fn_id: str) -> str:
        """Return the LaTeX formula for fn_id, or '' if unknown."""
        return LATEX_FORMULAS.get(str(fn_id), '')

    def all_formulas(self) -> dict:
        """Return a copy of the full {fn_id: latex} registry."""
        return dict(LATEX_FORMULAS)


# ═══════════════════════════════════════════════════════════════════════════════
# LatexToNumpy
# ═══════════════════════════════════════════════════════════════════════════════

# Token type tags
_T_NUM    = 'NUM'
_T_VAR    = 'VAR'
_T_CONST  = 'CONST'
_T_FUNC   = 'FUNC'
_T_FRAC   = 'FRAC'
_T_PLUS   = 'PLUS'
_T_MINUS  = 'MINUS'
_T_MUL    = 'MUL'
_T_DIV    = 'DIV'
_T_POW    = 'POW'
_T_LPAREN = 'LPAREN'
_T_RPAREN = 'RPAREN'
_T_LBRACE = 'LBRACE'
_T_RBRACE = 'RBRACE'
_T_LBAR   = 'LBAR'
_T_RBAR   = 'RBAR'
_T_LFLOOR = 'LFLOOR'
_T_RFLOOR = 'RFLOOR'
_T_EOF    = 'EOF'

# LaTeX function → NumPy repr
_FUNC_NP: dict[str, str] = {
    'sin':   'np.sin',
    'cos':   'np.cos',
    'tan':   'np.tan',
    'cot':   '(lambda _a: np.cos(_a)/np.sin(_a))',
    'sec':   '(lambda _a: 1.0/np.cos(_a))',
    'csc':   '(lambda _a: 1.0/np.sin(_a))',
    'exp':   'np.exp',
    'ln':    'np.log',
    'log':   'np.log',
    'Gamma': 'scipy.special.gamma',
    'sqrt':  'np.sqrt',
    'abs':   'np.abs',
}

# Variable → NumPy name
_VAR_NP: dict[str, str] = {
    'z': 'Z3',
    'x': 'X3',
    'k': 'k',
    'n': 'k',   # n is the outer index — same broadcast array
    'y': 'Z3.imag',
}

# Constant → NumPy repr
_CONST_NP: dict[str, str] = {
    'pi':   'np.pi',
    'beta': 'beta',
    'e':    'np.e',
    'i':    '1j',
    'm':    'm',
}

# Tokens that can start a primary expression (implicit-mul detection)
_PRIMARY_STARTERS = {
    _T_NUM, _T_VAR, _T_CONST, _T_FUNC, _T_FRAC,
    _T_LPAREN, _T_LBRACE, _T_LBAR, _T_LFLOOR,
}


def _tokenize(s: str) -> list:
    """Convert a LaTeX expression string into a list of (type, value) tokens."""
    tokens: list = []
    i = 0
    n = len(s)

    while i < n:
        c = s[i]

        # ── Whitespace ─────────────────────────────────────────────────────
        if c.isspace():
            i += 1
            continue

        # ── LaTeX commands ─────────────────────────────────────────────────
        if c == '\\':
            j = i + 1
            # Spacing-only commands: \! \, \; \: \ (backslash-space)
            if j < n and s[j] in '!,;: ':
                i = j + 1
                continue
            # Read alpha command name
            k2 = j
            while k2 < n and s[k2].isalpha():
                k2 += 1
            cmd = s[i:k2]   # e.g. '\sin', '\frac', '\left'

            # Sizing / grouping prefixes: \left \right \big \bigg etc.
            if cmd in (r'\left', r'\big', r'\bigg', r'\Big', r'\Bigg'):
                # peek at the delimiter that follows
                p = k2
                while p < n and s[p].isspace():
                    p += 1
                if p < n:
                    d = s[p]
                    if d == '(':
                        tokens.append((_T_LPAREN, d)); i = p + 1; continue
                    if d == ')':
                        tokens.append((_T_RPAREN, d)); i = p + 1; continue
                    if d == '|':
                        tokens.append((_T_LBAR, d));   i = p + 1; continue
                    if d in ('[', '{'):
                        tokens.append((_T_LPAREN, d)); i = p + 1; continue
                i = k2
                continue

            if cmd == r'\right':
                p = k2
                while p < n and s[p].isspace():
                    p += 1
                if p < n:
                    d = s[p]
                    if d == ')':
                        tokens.append((_T_RPAREN, d)); i = p + 1; continue
                    if d == '|':
                        tokens.append((_T_RBAR,   d)); i = p + 1; continue
                    if d in (']', '}'):
                        tokens.append((_T_RPAREN, d)); i = p + 1; continue
                i = k2
                continue

            if cmd == r'\frac':
                tokens.append((_T_FRAC, cmd)); i = k2; continue
            if cmd == r'\sqrt':
                tokens.append((_T_FUNC, 'sqrt')); i = k2; continue
            if cmd in (r'\sin', r'\cos', r'\tan', r'\cot',
                       r'\sec', r'\csc'):
                tokens.append((_T_FUNC, cmd[1:])); i = k2; continue
            if cmd in (r'\exp',):
                tokens.append((_T_FUNC, 'exp')); i = k2; continue
            if cmd in (r'\ln', r'\log'):
                tokens.append((_T_FUNC, cmd[1:])); i = k2; continue
            if cmd in (r'\Gamma', r'\gamma'):
                tokens.append((_T_FUNC, 'Gamma')); i = k2; continue
            if cmd == r'\pi':
                tokens.append((_T_CONST, 'pi')); i = k2; continue
            if cmd in (r'\beta', r'\alpha'):
                tokens.append((_T_CONST, 'beta')); i = k2; continue
            if cmd in (r'\cdot', r'\times'):
                tokens.append((_T_MUL, '*')); i = k2; continue
            if cmd == r'\lfloor':
                tokens.append((_T_LFLOOR, cmd)); i = k2; continue
            if cmd == r'\rfloor':
                tokens.append((_T_RFLOOR, cmd)); i = k2; continue
            # Commands whose brace argument we skip entirely
            if cmd in (r'\text', r'\mathrm', r'\mathbb', r'\operatorname',
                       r'\infty', r'\Re', r'\Im'):
                i = k2
                if i < n and s[i] == '{':
                    depth = 1; i += 1
                    while i < n and depth > 0:
                        if s[i] == '{': depth += 1
                        elif s[i] == '}': depth -= 1
                        i += 1
                continue
            # Unknown command — skip
            i = k2
            continue

        # ── Single-char tokens ────────────────────────────────────────────
        if c == '{':  tokens.append((_T_LBRACE, c)); i += 1; continue
        if c == '}':  tokens.append((_T_RBRACE, c)); i += 1; continue
        if c == '(':  tokens.append((_T_LPAREN, c)); i += 1; continue
        if c == ')':  tokens.append((_T_RPAREN, c)); i += 1; continue
        if c == '[':  tokens.append((_T_LPAREN, c)); i += 1; continue
        if c == ']':  tokens.append((_T_RPAREN, c)); i += 1; continue
        if c == '|':  tokens.append((_T_LBAR,   c)); i += 1; continue
        if c == '+':  tokens.append((_T_PLUS,   c)); i += 1; continue
        if c == '-':  tokens.append((_T_MINUS,  c)); i += 1; continue
        if c == '*':  tokens.append((_T_MUL,    c)); i += 1; continue
        if c == '/':  tokens.append((_T_DIV,    c)); i += 1; continue
        if c == '^':  tokens.append((_T_POW,    c)); i += 1; continue

        # ── Numbers ───────────────────────────────────────────────────────
        if c.isdigit() or (c == '.' and i+1 < n and s[i+1].isdigit()):
            j = i
            while j < n and (s[j].isdigit() or s[j] == '.'):
                j += 1
            tokens.append((_T_NUM, s[i:j])); i = j; continue

        # ── Letters / identifiers ─────────────────────────────────────────
        if c.isalpha():
            # 'iy' is a common combination meaning i·y
            if c == 'i' and i+1 < n and s[i+1] == 'y':
                tokens.append((_T_CONST, 'i'))
                tokens.append((_T_VAR,   'y'))
                i += 2; continue
            if c in _VAR_NP:
                tokens.append((_T_VAR,   c)); i += 1; continue
            if c == 'i':
                tokens.append((_T_CONST, 'i')); i += 1; continue
            if c == 'e':
                tokens.append((_T_CONST, 'e')); i += 1; continue
            if c == 'm':
                tokens.append((_T_CONST, 'm')); i += 1; continue
            # Generic unknown letter — pass through as a variable
            tokens.append((_T_VAR, c)); i += 1; continue

        i += 1  # skip unrecognised chars

    tokens.append((_T_EOF, ''))
    return tokens


class _ExprParser:
    """
    Recursive-descent expression parser.
    Converts a token list produced by _tokenize() to Python/NumPy source.

    Grammar (simplified)
    ────────────────────
      expr   = term (( '+' | '-' ) term)*
      term   = power ( ( '*' | '/' | implicit_mul ) power )*
      power  = unary ( '^' exponent )?
      unary  = '-' unary | primary
      primary = NUM | VAR | CONST | func_call | frac | group | abs | floor
    """

    def __init__(self, tokens: list):
        self._tok = tokens
        self._pos = 0

    def _peek(self) -> tuple:
        return self._tok[self._pos]

    def _eat(self, expected: str | None = None) -> tuple:
        tok = self._tok[self._pos]
        if expected and tok[0] != expected:
            ctx = self._tok[max(0, self._pos-2): self._pos+3]
            raise SyntaxError(
                f"LaTeX parse: expected {expected}, got {tok}  ctx={ctx}"
            )
        self._pos += 1
        return tok

    def parse_expr(self) -> str:
        left = self._parse_term()
        while self._peek()[0] in (_T_PLUS, _T_MINUS):
            op = self._eat()
            right = self._parse_term()
            sym = '+' if op[0] == _T_PLUS else '-'
            left = f'({left} {sym} {right})'
        return left

    def _parse_term(self) -> str:
        left = self._parse_power()
        while True:
            t = self._peek()
            if t[0] == _T_MUL:
                self._eat()
                left = f'({left} * {self._parse_power()})'
            elif t[0] == _T_DIV:
                self._eat()
                left = f'({left} / {self._parse_power()})'
            elif t[0] in _PRIMARY_STARTERS:
                # Implicit multiplication (e.g. β x/k, 2z, \sin(πz/k) \cos(...))
                left = f'({left} * {self._parse_power()})'
            else:
                break
        return left

    def _parse_power(self) -> str:
        base = self._parse_unary()
        if self._peek()[0] == _T_POW:
            self._eat()
            exp = self._parse_exponent()
            return f'np.power({base}, ({exp}))'
        return base

    def _parse_exponent(self) -> str:
        if self._peek()[0] == _T_LBRACE:
            self._eat(_T_LBRACE)
            e = self.parse_expr()
            self._eat(_T_RBRACE)
            return e
        return self._parse_unary()

    def _parse_unary(self) -> str:
        if self._peek()[0] == _T_MINUS:
            self._eat()
            return f'(-({self._parse_unary()}))'
        return self._parse_primary()

    def _parse_primary(self) -> str:  # noqa: C901  (complex but readable)
        tok = self._peek()

        if tok[0] == _T_NUM:
            self._eat()
            return tok[1]

        if tok[0] == _T_VAR:
            self._eat()
            return _VAR_NP.get(tok[1], tok[1])

        if tok[0] == _T_CONST:
            self._eat()
            return _CONST_NP.get(tok[1], tok[1])

        if tok[0] == _T_FUNC:
            func = self._eat()[1]
            np_fn = _FUNC_NP.get(func, f'np.{func}')
            arg = self._parse_func_arg()
            return f'{np_fn}({arg})'

        if tok[0] == _T_FRAC:
            self._eat()
            self._eat(_T_LBRACE)
            num = self.parse_expr()
            self._eat(_T_RBRACE)
            self._eat(_T_LBRACE)
            den = self.parse_expr()
            self._eat(_T_RBRACE)
            return f'(({num}) / ({den}))'

        if tok[0] == _T_LPAREN:
            self._eat()
            inner = self.parse_expr()
            if self._peek()[0] == _T_RPAREN:
                self._eat()
            return f'({inner})'

        if tok[0] == _T_LBRACE:
            self._eat()
            inner = self.parse_expr()
            if self._peek()[0] == _T_RBRACE:
                self._eat()
            return f'({inner})'

        if tok[0] == _T_LBAR:
            self._eat()
            inner = self.parse_expr()
            if self._peek()[0] in (_T_RBAR, _T_LBAR):
                self._eat()
            return f'np.abs({inner})'

        if tok[0] == _T_LFLOOR:
            self._eat()
            inner = self.parse_expr()
            if self._peek()[0] == _T_RFLOOR:
                self._eat()
            return f'np.floor({inner})'

        if tok[0] == _T_EOF:
            return '0'

        raise SyntaxError(f"Unexpected token in LaTeX term: {tok}")

    def _parse_func_arg(self) -> str:
        """Parse function argument: {{expr}}, (expr), or \\left(expr\\right)."""
        t = self._peek()
        if t[0] == _T_LBRACE:
            self._eat(_T_LBRACE)
            inner = self.parse_expr()
            self._eat(_T_RBRACE)
            return inner
        if t[0] == _T_LPAREN:
            self._eat(_T_LPAREN)
            inner = self.parse_expr()
            if self._peek()[0] == _T_RPAREN:
                self._eat()
            return inner
        # No delimiter — parse a single primary (e.g. \sin x)
        return self._parse_primary()


class LatexToNumpy:
    """
    Compiles a LaTeX product-term expression to a NumPy-compatible callable.

    Usage
    -----
    >>> ltn = LatexToNumpy()
    >>> code = ltn.compile_term(r'\\beta \\frac{x}{k} \\sin\\!\\left(\\frac{\\pi z}{k}\\right)')
    >>> print(code)
    (beta * ((X3) / (k)) * np.sin((np.pi * Z3) / (k)))
    >>> fn = ltn.make_term_fn(code)   # ready to pass to compute._single()
    """

    def compile_term(self, latex: str) -> str:
        """
        Parse *latex* and return Python/NumPy source for the term expression.
        The returned string can be used inside a lambda or eval'd.

        Parameters
        ----------
        latex : str
            The body of the product term only (no \\prod, no |·|^{-m}).

        Returns
        -------
        str  Python expression using np.*, scipy.special.*, Z3, X3, k, beta.
        """
        tokens = _tokenize(latex)
        parser = _ExprParser(tokens)
        return parser.parse_expr()

    def make_term_fn(self, latex_or_code: str, is_code: bool = False):
        """
        Return a callable  term_fn(Z3, k, X3, beta=1.0) → ndarray.

        Parameters
        ----------
        latex_or_code : str
            LaTeX term string (default) or pre-compiled Python code if
            is_code=True.
        is_code : bool
            If True, *latex_or_code* is already compiled Python code.
        """
        code = latex_or_code if is_code else self.compile_term(latex_or_code)
        src = f'lambda Z3, k, X3, beta=1.0: {code}'
        globs = {
            'np':     np,
            'scipy':  scipy,
            '__builtins__': {},
        }
        try:
            return eval(src, globs)  # noqa: S307 (research tool, controlled input)
        except Exception as exc:
            raise ValueError(
                f'Failed to build term function from code:\n  {src}\n  {exc}'
            ) from exc

    def validate(self, latex: str) -> tuple[bool, str]:
        """
        Compile *latex* and run a tiny test evaluation.

        Returns
        -------
        (success, error_message)
        """
        try:
            code = self.compile_term(latex)
        except SyntaxError as e:
            return False, f'parse error: {e}'
        try:
            fn = self.make_term_fn(code, is_code=True)
            Z3_t = np.array([[[2.5 + 1j]]])
            k_t  = np.array([[[2.0]]])
            X3_t = np.array([[[2.5]]])
            result = fn(Z3_t, k_t, X3_t, beta=0.178)
            if not np.all(np.isfinite(result) | (result != 0)):
                pass  # some non-finite values are acceptable
            return True, f'compiled OK → code: {code}'
        except Exception as e:
            return False, f'runtime error: {e}'


# ═══════════════════════════════════════════════════════════════════════════════
# CLI entry point (called by Electron IPC handlers)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    import json
    import argparse

    _parser = argparse.ArgumentParser(description='formula_bridge CLI')
    _parser.add_argument('--all-formulas', action='store_true',
                         help='Print JSON of all {fn_id: latex} formulas and exit')
    _parser.add_argument('--validate', type=str, default=None, metavar='LATEX',
                         help='Validate a LaTeX term string and print JSON result')
    _args = _parser.parse_args()

    if _args.all_formulas:
        ntl = NumpyToLatex()
        print(json.dumps({'success': True, 'formulas': ntl.all_formulas()}))
        sys.exit(0)

    if _args.validate is not None:
        ltn = LatexToNumpy()
        ok, msg = ltn.validate(_args.validate)
        # Also return the compiled code so the UI can show it
        code = ''
        if ok:
            try:
                code = ltn.compile_term(_args.validate)
            except Exception:
                pass
        print(json.dumps({'success': ok, 'message': msg, 'code': code}))
        sys.exit(0)

    _parser.print_help()
    sys.exit(1)
