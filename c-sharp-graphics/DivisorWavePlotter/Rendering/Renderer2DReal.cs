using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using DivisorWavePlotter.Core;

namespace DivisorWavePlotter.Rendering;

// Renders 2D real-valued function plots and divisor wave animations.
// GPU path: compute shader evaluates all sample points on the GPU.
// The resulting SSBO is then consumed directly by the line vertex shader
// so no CPU readback is needed for the normal plot path.
// For animation, we do per-frame compute dispatch + draw.
sealed class Renderer2DReal : IDisposable
{
    // ── Shaders ────────────────────────────────────────────────────────────────
    ShaderProgram _computeWaves;   // divisor wave compute  (compute_waves.glsl)
    ShaderProgram _computeReal;    // single-function compute (compute_real.glsl)
    ShaderProgram _lineShader;     // line strip vertex+frag
    ShaderProgram _dotShader;      // dot billboard vertex+frag
    ShaderProgram _axisShader;     // axis lines vertex+frag

    // ── GPU buffers ────────────────────────────────────────────────────────────
    int _waveSSBO;     // wave data from compute shader: float[kCount * numPoints]
    int _lineVAO, _lineVBO;  // static plot: interleaved (x, y) NDC pairs
    int _dotVAO,  _dotVBO;   // one quad per dot (6 verts each)

    // ── State ──────────────────────────────────────────────────────────────────
    int    _viewW, _viewH;
    string _funcId   = "1";
    double _alpha    = 1.0;
    double _beta     = 1.0;
    double _m        = 0.0465;
    double _xMin     = 2.0;
    double _xMax     = 20.0;
    int    _numPoints = 2048;    // samples per wave (GPU parallel)

    // Animation state cache (set by PrepareWaves)
    int    _kMin, _kMax;
    float  _animAlpha;

    const int MaxWaves = 60;     // max k supported

    // Wave colors (HSV-spaced, precomputed)
    static readonly Vector3[] WaveColors = GenerateColors(MaxWaves);

    public Renderer2DReal(int w, int h)
    {
        _viewW = w; _viewH = h;

        _computeWaves = ShaderProgram.ComputeFromFile("compute_waves.glsl");
        _computeReal  = ShaderProgram.ComputeFromFile("compute_real.glsl");
        _lineShader   = ShaderProgram.FromFiles("line2d.vert.glsl", "line2d.frag.glsl");
        _dotShader    = ShaderProgram.FromFiles("dot.vert.glsl",  "dot.frag.glsl");
        _axisShader   = ShaderProgram.FromFiles("axis.vert.glsl", "axis.frag.glsl");

        // SSBO for compute output
        _waveSSBO = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ShaderStorageBuffer, _waveSSBO);
        GL.BufferData(BufferTarget.ShaderStorageBuffer,
            MaxWaves * _numPoints * sizeof(float),
            IntPtr.Zero, BufferUsageHint.DynamicDraw);

        // Line VAO (positions are filled from SSBO on CPU for static plots)
        _lineVAO = GL.GenVertexArray();
        _lineVBO = GL.GenBuffer();
        GL.BindVertexArray(_lineVAO);
        GL.BindBuffer(BufferTarget.ArrayBuffer, _lineVBO);
        GL.BufferData(BufferTarget.ArrayBuffer, _numPoints * 2 * sizeof(float),
            IntPtr.Zero, BufferUsageHint.DynamicDraw);
        GL.VertexAttribPointer(0, 2, VertexAttribPointerType.Float, false, 2 * sizeof(float), 0);
        GL.EnableVertexAttribArray(0);

        // Dot VAO (6 verts per dot = 1 quad; max MaxWaves dots)
        _dotVAO = GL.GenVertexArray();
        _dotVBO = GL.GenBuffer();
        GL.BindVertexArray(_dotVAO);
        GL.BindBuffer(BufferTarget.ArrayBuffer, _dotVBO);
        GL.BufferData(BufferTarget.ArrayBuffer, MaxWaves * 6 * 4 * sizeof(float),
            IntPtr.Zero, BufferUsageHint.DynamicDraw);
        // layout: vec2 pos, vec2 uv
        GL.VertexAttribPointer(0, 2, VertexAttribPointerType.Float, false, 4 * sizeof(float), 0);
        GL.EnableVertexAttribArray(0);
        GL.VertexAttribPointer(1, 2, VertexAttribPointerType.Float, false, 4 * sizeof(float), 2 * sizeof(float));
        GL.EnableVertexAttribArray(1);

        GL.BindVertexArray(0);
    }

    // Called by MainWindow when Electron sends a "plot" command for real mode
    public void SetFunction(string funcId, Dictionary<string, System.Text.Json.JsonElement>? p)
    {
        _funcId = funcId;
        _alpha  = p?.TryGetValue("alpha",  out var ae) == true ? ae.GetDouble() : 1.0;
        _beta   = p?.TryGetValue("beta",   out var be) == true ? be.GetDouble() : 1.0;
        _m      = p?.TryGetValue("m",      out var me) == true ? me.GetDouble() : 0.0465;
        _xMin   = p?.TryGetValue("xMin",   out var xmine) == true ? xmine.GetDouble() : 2.0;
        _xMax   = p?.TryGetValue("xMax",   out var xmaxe) == true ? xmaxe.GetDouble() : 20.0;

        ComputeAndUploadRealFunction();
    }

    // Called once before animation starts
    public void PrepareWaves(AnimationState anim)
    {
        _kMin       = 2;
        _kMax       = anim.KMax;
        _animAlpha  = (float)anim.Alpha;
    }

    // ── Drawing ────────────────────────────────────────────────────────────────

    // Draw static real function (non-animation)
    public void Draw()
    {
        DrawAxes(_xMin, _xMax);

        _lineShader.Use();
        _lineShader.Set("color", new Vector3(0.7f, 0.63f, 1.0f)); // accent purple

        GL.BindVertexArray(_lineVAO);
        GL.LineWidth(1.8f);
        GL.DrawArrays(PrimitiveType.LineStrip, 0, _numPoints);
        GL.BindVertexArray(0);
    }

    // Draw divisor wave animation: compute on GPU, draw lines + dots
    public void DrawAnimation(AnimationState anim)
    {
        // ── 1. Dispatch compute shader ─────────────────────────────────────────
        int kCount  = _kMax - _kMin + 1;
        double visibleXMin = anim.ViewXMin;
        double visibleXMax = anim.CursorX;   // only draw up to cursor
        if (visibleXMax <= visibleXMin) visibleXMax = visibleXMin + 0.001;

        _computeWaves.Use();
        _computeWaves.Set("xMin",      (float)visibleXMin);
        _computeWaves.Set("xMax",      (float)visibleXMax);
        _computeWaves.Set("numPoints", _numPoints);
        _computeWaves.Set("kMin",      _kMin);
        _computeWaves.Set("kMax",      _kMax);
        _computeWaves.Set("alpha",     _animAlpha);

        GL.BindBufferBase(BufferRangeTarget.ShaderStorageBuffer, 0, _waveSSBO);
        // ensure buffer is big enough
        GL.BindBuffer(BufferTarget.ShaderStorageBuffer, _waveSSBO);
        int needed = kCount * _numPoints * sizeof(float);
        GL.BufferData(BufferTarget.ShaderStorageBuffer, needed, IntPtr.Zero, BufferUsageHint.DynamicDraw);

        int groupsX = (_numPoints + 63) / 64;
        GL.DispatchCompute(groupsX, kCount, 1);
        GL.MemoryBarrier(MemoryBarrierFlags.ShaderStorageBarrierBit);

        // ── 2. Read back GPU data for line drawing ─────────────────────────────
        // (GL 4.3-compatible readback — no DSA required)
        float[] gpuData = new float[kCount * _numPoints];
        GL.BindBuffer(BufferTarget.ShaderStorageBuffer, _waveSSBO);
        GL.GetBufferSubData(BufferTarget.ShaderStorageBuffer, IntPtr.Zero, needed, gpuData);
        GL.BindBuffer(BufferTarget.ShaderStorageBuffer, 0);

        // Auto-scale Y to the peak visible value this frame
        float yPeak = 0.01f;
        for (int i = 0; i < gpuData.Length; i++)
            if (float.IsFinite(gpuData[i])) yPeak = Math.Max(yPeak, gpuData[i]);
        anim.SetYRange(-yPeak * 0.12, yPeak * 1.15);

        // ── 3. Draw axes ───────────────────────────────────────────────────────
        DrawAxes(anim.ViewXMin, anim.ViewXMax, anim.ViewYMin, anim.ViewYMax);

        // ── 4. Draw wave lines ─────────────────────────────────────────────────
        _lineShader.Use();
        GL.LineWidth(1.6f);

        float[] lineVerts = new float[_numPoints * 2];
        for (int ki = 0; ki < kCount; ki++)
        {
            Vector3 col = WaveColors[ki % WaveColors.Length];
            _lineShader.Set("color", col);

            int offset = ki * _numPoints;
            for (int xi = 0; xi < _numPoints; xi++)
            {
                double wx = visibleXMin + (visibleXMax - visibleXMin) * xi / (_numPoints - 1);
                double wy = gpuData[offset + xi];
                Vector2 ndc = anim.ToNDC(wx, wy);
                lineVerts[xi * 2]     = ndc.X;
                lineVerts[xi * 2 + 1] = ndc.Y;
            }

            GL.BindBuffer(BufferTarget.ArrayBuffer, _lineVBO);
            GL.BufferData(BufferTarget.ArrayBuffer, lineVerts.Length * sizeof(float),
                lineVerts, BufferUsageHint.StreamDraw);
            GL.BindVertexArray(_lineVAO);
            GL.DrawArrays(PrimitiveType.LineStrip, 0, _numPoints);
        }
        GL.BindVertexArray(0);

        // ── 5. Draw cursor line ────────────────────────────────────────────────
        DrawCursorLine(anim);

        // ── 6. Draw dots at cursor position ────────────────────────────────────
        DrawDots(anim, gpuData, kCount, visibleXMin, visibleXMax);
    }

    void DrawCursorLine(AnimationState anim)
    {
        float cx = anim.CursorNDC;
        float[] verts = [ cx, -1f, cx, 1f ];

        _lineShader.Use();
        _lineShader.Set("color", new Vector3(1f, 1f, 1f));
        GL.LineWidth(1.0f);

        GL.BindBuffer(BufferTarget.ArrayBuffer, _lineVBO);
        GL.BufferData(BufferTarget.ArrayBuffer, verts.Length * sizeof(float), verts, BufferUsageHint.StreamDraw);
        GL.BindVertexArray(_lineVAO);
        GL.DrawArrays(PrimitiveType.Lines, 0, 2);
        GL.BindVertexArray(0);
    }

    void DrawDots(AnimationState anim, float[] gpuData, int kCount, double visXMin, double visXMax)
    {
        if (_numPoints < 2) return;

        // For each wave, sample the value at cursor_x by interpolating the last computed point
        _dotShader.Use();
        float dotR = (float)(anim.DotRadius / _viewW * 2.0); // dot radius in NDC

        float[] quadVerts = new float[kCount * 6 * 4]; // 6 verts × (x,y,u,v)
        int qIdx = 0;

        for (int ki = 0; ki < kCount; ki++)
        {
            // Last sample is at cursor_x
            float wy = gpuData[ki * _numPoints + (_numPoints - 1)];
            if (!float.IsFinite(wy)) wy = 0;

            Vector2 center = anim.ToNDC(anim.CursorX, wy);
            Vector3 col    = WaveColors[ki % WaveColors.Length];

            _dotShader.Set("dotColor", col);
            _dotShader.Set("center",   center);
            _dotShader.Set("radius",   dotR);

            // Full-screen quad — let fragment shader do the circle masking
            // (we draw one dot at a time to pass the center uniform)
            float x0 = center.X - dotR * 1.5f, x1 = center.X + dotR * 1.5f;
            float y0 = center.Y - dotR * 1.5f, y1 = center.Y + dotR * 1.5f;

            quadVerts[qIdx++] = x0; quadVerts[qIdx++] = y0; quadVerts[qIdx++] = -1f; quadVerts[qIdx++] = -1f;
            quadVerts[qIdx++] = x1; quadVerts[qIdx++] = y0; quadVerts[qIdx++] =  1f; quadVerts[qIdx++] = -1f;
            quadVerts[qIdx++] = x1; quadVerts[qIdx++] = y1; quadVerts[qIdx++] =  1f; quadVerts[qIdx++] =  1f;
            quadVerts[qIdx++] = x0; quadVerts[qIdx++] = y0; quadVerts[qIdx++] = -1f; quadVerts[qIdx++] = -1f;
            quadVerts[qIdx++] = x1; quadVerts[qIdx++] = y1; quadVerts[qIdx++] =  1f; quadVerts[qIdx++] =  1f;
            quadVerts[qIdx++] = x0; quadVerts[qIdx++] = y1; quadVerts[qIdx++] = -1f; quadVerts[qIdx++] =  1f;
        }

        GL.BindBuffer(BufferTarget.ArrayBuffer, _dotVBO);
        GL.BufferSubData(BufferTarget.ArrayBuffer, IntPtr.Zero, qIdx * sizeof(float), quadVerts);
        GL.BindVertexArray(_dotVAO);

        // Draw one quad per wave (each needs its own dotColor uniform so we call draw per wave)
        for (int ki = 0; ki < kCount; ki++)
        {
            float wy = gpuData[ki * _numPoints + (_numPoints - 1)];
            if (!float.IsFinite(wy)) wy = 0;
            Vector2 center = anim.ToNDC(anim.CursorX, wy);
            float dotAspect = (float)_viewH / _viewW;

            _dotShader.Set("dotColor",   WaveColors[ki % WaveColors.Length]);
            _dotShader.Set("center",     center);
            _dotShader.Set("radius",     dotR);
            _dotShader.Set("aspect",     dotAspect);
            GL.DrawArrays(PrimitiveType.Triangles, ki * 6, 6);
        }

        GL.BindVertexArray(0);
    }

    void DrawAxes(double xMin, double xMax, double yMin = -0.5, double yMax = 3.0)
    {
        // Compute NDC for y=0 line and for each integer x tick
        _axisShader.Use();
        _axisShader.Set("color", new Vector3(0.25f, 0.25f, 0.35f));
        GL.LineWidth(1.0f);

        // Horizontal axis at y=0
        float yAxis = (float)((-yMin) / (yMax - yMin) * 2.0 - 1.0);
        float[] axisVerts = [ -1f, yAxis, 1f, yAxis ];
        GL.BindBuffer(BufferTarget.ArrayBuffer, _lineVBO);
        GL.BufferData(BufferTarget.ArrayBuffer, axisVerts.Length * sizeof(float), axisVerts, BufferUsageHint.StreamDraw);
        GL.BindVertexArray(_lineVAO);
        GL.DrawArrays(PrimitiveType.Lines, 0, 2);
        GL.BindVertexArray(0);

        // Vertical ticks at each visible integer x
        _axisShader.Set("color", new Vector3(0.18f, 0.18f, 0.28f));
        for (int ix = (int)Math.Ceiling(xMin); ix <= (int)Math.Floor(xMax); ix++)
        {
            float xNDC = (float)((ix - xMin) / (xMax - xMin) * 2.0 - 1.0);
            float[] tick = [ xNDC, -1f, xNDC, 1f ];
            GL.BindBuffer(BufferTarget.ArrayBuffer, _lineVBO);
            GL.BufferData(BufferTarget.ArrayBuffer, tick.Length * sizeof(float), tick, BufferUsageHint.StreamDraw);
            GL.BindVertexArray(_lineVAO);
            GL.DrawArrays(PrimitiveType.Lines, 0, 2);
            GL.BindVertexArray(0);
        }
    }

    void ComputeAndUploadRealFunction()
    {
        // CPU evaluation for static real plot (GPU path via compute_real.glsl coming soon)
        float[] verts = new float[_numPoints * 2];
        float yMin = float.MaxValue, yMax = float.MinValue;

        for (int i = 0; i < _numPoints; i++)
        {
            double x = _xMin + (_xMax - _xMin) * i / (_numPoints - 1);
            double y = MathFunctions.Evaluate(_funcId, x, _alpha, _beta, _m);
            if (double.IsFinite(y)) { yMin = Math.Min(yMin, (float)y); yMax = Math.Max(yMax, (float)y); }
        }
        float yRange = yMax - yMin;
        if (yRange < 1e-9f) yRange = 1f;
        float yPad = yRange * 0.1f;

        for (int i = 0; i < _numPoints; i++)
        {
            double x = _xMin + (_xMax - _xMin) * i / (_numPoints - 1);
            double y = MathFunctions.Evaluate(_funcId, x, _alpha, _beta, _m);
            if (!double.IsFinite(y)) y = yMin;
            float nx = -1f + 2f * i / (_numPoints - 1);
            float ny = -1f + 2f * (float)((y - yMin + yPad) / (yRange + 2 * yPad));
            verts[i * 2]     = nx;
            verts[i * 2 + 1] = ny;
        }

        GL.BindBuffer(BufferTarget.ArrayBuffer, _lineVBO);
        GL.BufferData(BufferTarget.ArrayBuffer, verts.Length * sizeof(float), verts, BufferUsageHint.DynamicDraw);
    }

    public void Resize(int w, int h) { _viewW = w; _viewH = h; }

    public void Dispose()
    {
        _computeWaves.Dispose(); _computeReal.Dispose();
        _lineShader.Dispose(); _dotShader.Dispose(); _axisShader.Dispose();
        GL.DeleteBuffer(_waveSSBO);
        GL.DeleteVertexArray(_lineVAO); GL.DeleteBuffer(_lineVBO);
        GL.DeleteVertexArray(_dotVAO);  GL.DeleteBuffer(_dotVBO);
    }

    // ── Color palette ──────────────────────────────────────────────────────────
    static Vector3[] GenerateColors(int n)
    {
        var cols = new Vector3[n];
        for (int i = 0; i < n; i++)
        {
            float h = i / (float)n;          // evenly spaced hue
            HsvToRgb(h, 0.85f, 0.95f, out float r, out float g, out float b);
            cols[i] = new Vector3(r, g, b);
        }
        return cols;
    }

    static void HsvToRgb(float h, float s, float v, out float r, out float g, out float b)
    {
        int   i = (int)(h * 6);
        float f = h * 6 - i;
        float p = v * (1 - s), q = v * (1 - f * s), t = v * (1 - (1 - f) * s);
        (r, g, b) = (i % 6) switch
        {
            0 => (v, t, p), 1 => (q, v, p), 2 => (p, v, t),
            3 => (p, q, v), 4 => (t, p, v), _ => (v, p, q),
        };
    }
}
