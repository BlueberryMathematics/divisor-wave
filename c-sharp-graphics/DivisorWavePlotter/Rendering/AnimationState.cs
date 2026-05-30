using OpenTK.Mathematics;

namespace DivisorWavePlotter.Rendering;

enum PlotMode { Real2D, Complex2D, Complex3D, DivisorWaveAnim }

sealed class AnimationState
{
    // ── Current plot mode ──────────────────────────────────────────────────────
    public PlotMode Mode { get; set; } = PlotMode.Real2D;

    // ── Divisor wave animation parameters ─────────────────────────────────────
    public int    KMax      { get; set; } = 12;
    public double Alpha     { get; set; } = 1.0;
    public double Speed     { get; set; } = 2.0;   // x-units per second
    public double DotRadius { get; set; } = 8.0;   // screen pixels
    public double XMin      { get; set; } = -2.0;  // left edge of initial view

    // ── Live state (updated each frame) ───────────────────────────────────────
    public bool   Playing     { get; set; } = false;
    public double CursorX     { get; private set; } = 0.0;
    public double ViewXMin    { get; private set; } = -2.0;
    public double ViewXMax    { get; private set; } = 14.0;
    public double ViewYMin    { get; private set; } = -0.5;
    public double ViewYMax    { get; private set; } = 3.0;

    const double ViewWidth   = 16.0;   // x-axis window width
    const double RightMargin = 2.0;    // when cursor is this close to right edge, pan

    public void Reset()
    {
        CursorX  = 0.0;
        ViewXMin = XMin;
        ViewXMax = XMin + ViewWidth;
        Playing  = false;
    }

    public void Advance(float dt)
    {
        if (!Playing || Mode != PlotMode.DivisorWaveAnim) return;

        CursorX += Speed * dt;

        // Pan view when cursor approaches the right edge
        double rightEdge = ViewXMax - RightMargin;
        if (CursorX > rightEdge)
        {
            double shift = CursorX - rightEdge;
            ViewXMin += shift;
            ViewXMax += shift;
        }
    }

    // Normalized screen coordinate for the cursor x position
    public float CursorNDC => (float)((CursorX - ViewXMin) / (ViewXMax - ViewXMin) * 2.0 - 1.0);

    // Convert a world (x, y) → NDC vec2 given current view
    public Vector2 ToNDC(double wx, double wy) => new(
        (float)((wx - ViewXMin)  / (ViewXMax - ViewXMin)  * 2.0 - 1.0),
        (float)((wy - ViewYMin) / (ViewYMax - ViewYMin) * 2.0 - 1.0)
    );

    public void SetYRange(double yMin, double yMax)
    {
        ViewYMin = yMin;
        ViewYMax = yMax;
    }
}
