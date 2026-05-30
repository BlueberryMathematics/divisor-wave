using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;

namespace DivisorWavePlotter.Rendering;

// GPU-accelerated 3D surface renderer.
// Compute shader produces a height field; the surface shader renders it
// as a lit mesh with the Prism/Jet/Plasma colourmap.
sealed class Renderer3DSurface : IDisposable
{
    ShaderProgram _compute;
    ShaderProgram _surface;

    int _nx = 200, _ny = 120;
    int _heightSSBO;
    int _vao, _ebo;
    int _indexCount;

    int   _funcId    = 1;
    float _alpha     = 1.0f, _beta = 1.0f, _m = 0.0465f;
    float _xMin = 2f, _xMax = 20f, _yMin = -5f, _yMax = 5f;
    float _elev = 30f, _azim = -70f;
    bool  _normalize = false;
    bool  _dirty     = true;

    int   _viewW, _viewH;

    public Renderer3DSurface(int w, int h)
    {
        _viewW = w; _viewH = h;
        _compute = ShaderProgram.ComputeFromFile("compute_complex.glsl");
        _surface = ShaderProgram.FromFiles("surface.vert.glsl", "surface.frag.glsl");
        BuildMesh();
    }

    public void SetFunction(string funcId, Dictionary<string, System.Text.Json.JsonElement>? p)
    {
        _funcId    = int.TryParse(funcId, out int fid) ? fid : 1;
        _alpha     = p != null && p.TryGetValue("alpha",     out var ae)  ? (float)ae.GetDouble()  : 1.0f;
        _beta      = p != null && p.TryGetValue("beta",      out var be)  ? (float)be.GetDouble()  : 1.0f;
        _m         = p != null && p.TryGetValue("m",         out var me)  ? (float)me.GetDouble()  : 0.0465f;
        _xMin      = p != null && p.TryGetValue("xMin",      out var xmn) ? (float)xmn.GetDouble() : 2f;
        _xMax      = p != null && p.TryGetValue("xMax",      out var xmx) ? (float)xmx.GetDouble() : 20f;
        _yMin      = p != null && p.TryGetValue("yMin",      out var ymn) ? (float)ymn.GetDouble() : -5f;
        _yMax      = p != null && p.TryGetValue("yMax",      out var ymx) ? (float)ymx.GetDouble() : 5f;
        _elev      = p != null && p.TryGetValue("elev",      out var elv) ? (float)elv.GetDouble() : 30f;
        _azim      = p != null && p.TryGetValue("azim",      out var azm) ? (float)azm.GetDouble() : -70f;
        _normalize = p != null && p.TryGetValue("normalize", out var nrm) && nrm.GetString() == "Y";
        _dirty = true;
    }

    public void Draw()
    {
        if (_dirty) { ComputeHeights(); _dirty = false; }

        GL.Enable(EnableCap.DepthTest);
        GL.Clear(ClearBufferMask.DepthBufferBit);

        float aspect = (float)_viewW / _viewH;
        var proj = Matrix4.CreatePerspectiveFieldOfView(MathHelper.DegreesToRadians(45f), aspect, 0.1f, 500f);

        // Orbit camera from elevation + azimuth
        float elRad  = MathHelper.DegreesToRadians(_elev);
        float azRad  = MathHelper.DegreesToRadians(_azim);
        float dist   = 18f;
        float cx     = (_xMin + _xMax) * 0.5f;
        var camPos   = new Vector3(
            cx + dist * MathF.Cos(elRad) * MathF.Cos(azRad),
                 dist * MathF.Sin(elRad),
            (_yMin + _yMax) * 0.5f + dist * MathF.Cos(elRad) * MathF.Sin(azRad));
        var camTarget = new Vector3(cx, 0f, (_yMin + _yMax) * 0.5f);
        var view = Matrix4.LookAt(camPos, camTarget, Vector3.UnitY);

        _surface.Use();
        _surface.Set("proj",  proj);
        _surface.Set("view",  view);
        _surface.Set("xMin",  _xMin);
        _surface.Set("xMax",  _xMax);
        _surface.Set("yMin",  _yMin);
        _surface.Set("yMax",  _yMax);
        _surface.Set("nx",    _nx);
        _surface.Set("ny",    _ny);
        _surface.Set("lightDir", Vector3.Normalize(new Vector3(0.5f, 1f, 0.5f)));

        GL.BindBufferBase(BufferRangeTarget.ShaderStorageBuffer, 0, _heightSSBO);
        GL.BindVertexArray(_vao);
        GL.DrawElements(PrimitiveType.Triangles, _indexCount, DrawElementsType.UnsignedInt, 0);
        GL.BindVertexArray(0);
        GL.Disable(EnableCap.DepthTest);
    }

    void ComputeHeights()
    {
        _compute.Use();
        _compute.Set("funcId",    _funcId);
        _compute.Set("xMin",      _xMin);
        _compute.Set("xMax",      _xMax);
        _compute.Set("yMin",      _yMin);
        _compute.Set("yMax",      _yMax);
        _compute.Set("nx",        _nx);
        _compute.Set("ny",        _ny);
        _compute.Set("alpha",     _alpha);
        _compute.Set("beta",      _beta);
        _compute.Set("mCoeff",    _m);
        _compute.Set("normalize", _normalize);
        _compute.Set("outputMode", 1); // SSBO mode (not image)

        GL.BindBufferBase(BufferRangeTarget.ShaderStorageBuffer, 1, _heightSSBO);
        GL.DispatchCompute((_nx + 15) / 16, (_ny + 15) / 16, 1);
        GL.MemoryBarrier(MemoryBarrierFlags.ShaderStorageBarrierBit);
    }

    void BuildMesh()
    {
        // Positions are computed in the vertex shader using gl_VertexID + SSBO height,
        // so the VAO only holds (xi, yi) indices as two UShorts.
        int vCount = _nx * _ny;
        int[] verts = new int[vCount * 2];
        for (int yi = 0; yi < _ny; yi++)
        for (int xi = 0; xi < _nx; xi++)
        {
            int idx = (yi * _nx + xi) * 2;
            verts[idx] = xi; verts[idx + 1] = yi;
        }

        _vao = GL.GenVertexArray();
        GL.BindVertexArray(_vao);
        int vbo = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ArrayBuffer, vbo);
        GL.BufferData(BufferTarget.ArrayBuffer, verts.Length * sizeof(int), verts, BufferUsageHint.StaticDraw);
        GL.VertexAttribIPointer(0, 2, VertexAttribIntegerType.Int, 2 * sizeof(int), 0);
        GL.EnableVertexAttribArray(0);

        // Indices for triangle mesh
        var indices = new List<int>((_nx - 1) * (_ny - 1) * 6);
        for (int yi = 0; yi < _ny - 1; yi++)
        for (int xi = 0; xi < _nx - 1; xi++)
        {
            int tl = yi * _nx + xi, tr = tl + 1, bl = tl + _nx, br = bl + 1;
            indices.Add(tl); indices.Add(tr); indices.Add(bl);
            indices.Add(tr); indices.Add(br); indices.Add(bl);
        }
        _indexCount = indices.Count;
        _ebo = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ElementArrayBuffer, _ebo);
        GL.BufferData(BufferTarget.ElementArrayBuffer, _indexCount * sizeof(int),
            indices.ToArray(), BufferUsageHint.StaticDraw);
        GL.BindVertexArray(0);

        _heightSSBO = GL.GenBuffer();
        GL.BindBuffer(BufferTarget.ShaderStorageBuffer, _heightSSBO);
        GL.BufferData(BufferTarget.ShaderStorageBuffer, vCount * sizeof(float), IntPtr.Zero, BufferUsageHint.DynamicDraw);
    }

    public void Resize(int w, int h) { _viewW = w; _viewH = h; }

    public void Dispose()
    {
        _compute.Dispose(); _surface.Dispose();
        GL.DeleteBuffer(_heightSSBO); GL.DeleteVertexArray(_vao); GL.DeleteBuffer(_ebo);
    }
}
