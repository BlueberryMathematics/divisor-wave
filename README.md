# Divisor Wave Plotter

An Electron + Next.js desktop app for generating 3D surface plots of 32 number-theoretic and analytic functions — including Riesz products, Viète products, prime indicator functions, and compositions thereof — evaluated over the complex plane via a Python/matplotlib backend.

![Divisor Wave — Product of Product Rep. for Sin (Normalized)](assets/divisor-wave-1.png)

## Structure

```
python-divisor-wave/     # matplotlib 3D plotter & function library (CLI)
electron-divisor-wave/   # Electron shell + Next.js UI
c-sharp-plotting/        # C# alternative plotter
latex-divisor-wave-paper/# LaTeX paper
plot-outputs/            # saved PNG renders (gitignored)
```

## Running

Requires Python 3 with `numpy` and `matplotlib`, and Node.js.

```bash
# Install Python dependencies (one-time)
python -m venv venv
venv\Scripts\activate        # Windows
pip install numpy matplotlib

# Install Node dependencies (one-time)
cd electron-divisor-wave
npm install

# Launch the app
npm run dev
```

The Electron window opens automatically once Next.js is ready on `http://localhost:3000`.

## Functions

32 functions across 7 groups:

| Group | Examples |
|---|---|
| Basic | Product of Sin, Product Rep. for Sin |
| Riesz | Riesz — Cos/Sin/Tan |
| Viète | Viète — Cos/Sin/Tan |
| Compositions | Cos/Sin of Product of Sin |
| Prime | Binary Prime Indicator H, Dirichlet Eta from BOPIF |
| Analytic | \|loggamma(z)\|, gamma(z), \|z^z\| |
| Transforms / Custom / Experimental | various |

## Controls

- **Function** — select from 32 functions grouped by type
- **Normalization** — Raw or Normalized
- **Colormap** — Prism, Jet, Plasma, Viridis, Magma
- **Resolution** — grid step (smaller = finer & slower)
- **Domain** — X/Y min/max for the complex plane window
- **View Angles** — elevation and azimuth for the 3D camera
- **Coefficients** — per-function `m` (exponent) and `β` (amplitude) overrides, with an **auto** mode that fits them from sampled output variance
