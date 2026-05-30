using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;

namespace DivisorWavePlotter.Rendering;

// GPU-accelerated 2D complex-plane heatmap (equivalent to Python's 2D mode).
// A compute shader evaluates |f(x+iy)| on the full grid, writes to a texture,
// and a full-screen quad colours each pixel by magnitude.
sealed class Renderer2DComplex : IDisposable
{
    ShaderProgram _compute;
    ShaderProgram _quad;

    int _texWidth, _texHeight;
    int _outTex;             // RGBA32F texture written by compute shader
    int _vao;                // full-screen quad

    int  _funcId   = 1;
    float _alpha   = 1.0f, _beta = 1.0f, _m = 0.0465f;
    float _xMin    = 2f, _xMax = 20f, _yMin = -5f, _yMax = 5f;
    bool  _normalize = false;
    bool  _dirty     = true;

    static readonly float[] QuadVerts =
    [ -1f,-1f, 0f,0f,  1f,-1f, 1f,0f,  1f,1f, 1f,1f,
      -1f,-1f, 0f,0f,  1f,1f, 1f,1f, -1f,1f, 0f,1f ];

    public Renderer2DComplex(int w, int h)
    {
        _texWidth = w; _texHeight = h;

        _compute = ShaderProgram.ComputeFromFile("compute_complex.glsl");
        _quad    = ShaderProgram.FromFiles("heatmap.vert.glsl", "heatmap.frag.glsl");

        BuildTexture();
        BuildQuadVAO();
    }

    public void SetFunction(string funcId, Dictionary<string, System.Text.Json.JsonElement>? p)
    {
        _funcId    = int.TryParse(funcId, out int fid) ? fid : 1;
        _alpha     = p != null && p.TryGetValue("alpha",     out var ae) ? (float)ae.GetDouble() : 1.0f;
        _beta      = p != null && p.TryGetValue("beta",      out var be) ? (float)be.GetDouble() : 1.0f;
        _m         = p != null && p.TryGetValue("m",         out var me) ? (float)me.GetDouble() : 0.0465f;
        _xMin      = p != null && p.TryGetValue("xMin",      out var xmn) ? (float)xmn.GetDouble() : 2f;
        _xMax      = p != null && p.TryGetValue("xMax",      out var xmx) ? (float)xmx.GetDouble() : 20f;
        _yMin      = p != null && p.TryGetValue("yMin",      out var ymn) ? (float)ymn.GetDouble() : -5f;
        _yMax      = p != null && p.TryGetValue("yMax",      out var ymx) ? (float)ymx.GetDouble() : 5f;
        _normalize = p != null && p.TryGetValue("normalize", out var nrm) && nrm.GetString() == "Y";
        _dirty = true;
    }

    public void Draw()
    {
        if (_dirty) { ComputeGrid(); _dirty = false; }

        GL.ActiveTexture(TextureUnit.Texture0);
        GL.BindTexture(TextureTarget.Texture2D, _outTex);

        _quad.Use();
        _quad.Set("heatmap", 0);

        GL.BindVertexArray(_vao);
        GL.DrawArrays(PrimitiveType.Triangles, 0, 6);
        GL.BindVertexArray(0);
    }

    void ComputeGrid()
    {
        _compute.Use();
        _compute.Set("funcId",    _funcId);
        _compute.Set("xMin",      _xMin);
        _compute.Set("xMax",      _xMax);
        _compute.Set("yMin",      _yMin);
        _compute.Set("yMax",      _yMax);
        _compute.Set("nx",        _texWidth);
        _compute.Set("ny",        _texHeight);
        _compute.Set("alpha",     _alpha);
        _compute.Set("beta",      _beta);
        _compute.Set("mCoeff",    _m);
        _compute.Set("normalize", _normalize);

        // bind output image
        GL.BindImageTexture(0, _outTex, 0, false, 0, TextureAccess.WriteOnly, SizedInternalFormat.Rgba32f);

        int gx = (_texWidth  + 15) / 16;
        int gy = (_texHeight + 15) / 16;
        GL.DispatchCompute(gx, gy, 1);
        GL.MemoryBarrier(MemoryBarrierFlags.ShaderImageAccessBarrierBit | MemoryBarrierFlags.TextureFetchBarrierBit);
    }

    void BuildTexture()
    {
        _outTex = GL.GenTexture();
        GL.BindTexture(TextureTarget.Texture2D, _outTex);
        GL.TexImage2D(TextureTarget.Texture2D, 0, PixelInternalFormat.Rgba32f,
            _texWidth, _texHeight, 0, PixelFormat.Rgba, PixelType.Float, IntPtr.Zero);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMinFilter, (int)TextureMinFilter.Linear);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMagFilter, (int)TextureMagFilter.Linear);
    }

    void BuildQuadVAO()
    {
        _vao = GL.GenVertexArray();
        int vbo = GL.GenBuffer();
        GL.BindVertexArray(_vao);
        GL.BindBuffer(BufferTarget.ArrayBuffer, vbo);
        GL.BufferData(BufferTarget.ArrayBuffer, QuadVerts.Length * sizeof(float), QuadVerts, BufferUsageHint.StaticDraw);
        GL.VertexAttribPointer(0, 2, VertexAttribPointerType.Float, false, 4 * sizeof(float), 0);
        GL.EnableVertexAttribArray(0);
        GL.VertexAttribPointer(1, 2, VertexAttribPointerType.Float, false, 4 * sizeof(float), 2 * sizeof(float));
        GL.EnableVertexAttribArray(1);
        GL.BindVertexArray(0);
    }

    public void Resize(int w, int h)
    {
        _texWidth = w; _texHeight = h;
        GL.DeleteTexture(_outTex);
        BuildTexture();
        _dirty = true;
    }

    public void Dispose()
    {
        _compute.Dispose(); _quad.Dispose();
        GL.DeleteTexture(_outTex); GL.DeleteVertexArray(_vao);
    }
}
