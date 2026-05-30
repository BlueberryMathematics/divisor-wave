using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;

namespace DivisorWavePlotter.Rendering;

sealed class ShaderProgram : IDisposable
{
    public readonly int Handle;

    public ShaderProgram(string vertSrc, string fragSrc)
    {
        int vert = Compile(ShaderType.VertexShader,   vertSrc);
        int frag = Compile(ShaderType.FragmentShader, fragSrc);
        Handle   = GL.CreateProgram();
        GL.AttachShader(Handle, vert);
        GL.AttachShader(Handle, frag);
        GL.LinkProgram(Handle);
        GL.GetProgram(Handle, GetProgramParameterName.LinkStatus, out int ok);
        if (ok == 0) throw new Exception("Shader link error:\n" + GL.GetProgramInfoLog(Handle));
        GL.DeleteShader(vert);
        GL.DeleteShader(frag);
    }

    // For compute shaders (single stage)
    public ShaderProgram(string compSrc)
    {
        int comp = Compile(ShaderType.ComputeShader, compSrc);
        Handle   = GL.CreateProgram();
        GL.AttachShader(Handle, comp);
        GL.LinkProgram(Handle);
        GL.GetProgram(Handle, GetProgramParameterName.LinkStatus, out int ok);
        if (ok == 0) throw new Exception("Compute shader link error:\n" + GL.GetProgramInfoLog(Handle));
        GL.DeleteShader(comp);
    }

    static int Compile(ShaderType type, string src)
    {
        int id = GL.CreateShader(type);
        GL.ShaderSource(id, src);
        GL.CompileShader(id);
        GL.GetShader(id, ShaderParameter.CompileStatus, out int ok);
        if (ok == 0) throw new Exception($"Shader compile error ({type}):\n" + GL.GetShaderInfoLog(id));
        return id;
    }

    public void Use() => GL.UseProgram(Handle);

    public int Loc(string name) => GL.GetUniformLocation(Handle, name);

    public void Set(string name, int    v) => GL.Uniform1(Loc(name), v);
    public void Set(string name, float  v) => GL.Uniform1(Loc(name), v);
    public void Set(string name, bool   v) => GL.Uniform1(Loc(name), v ? 1 : 0);
    public void Set(string name, Vector2 v) => GL.Uniform2(Loc(name), v);
    public void Set(string name, Vector3 v) => GL.Uniform3(Loc(name), v);
    public void Set(string name, Vector4 v) => GL.Uniform4(Loc(name), v);
    public void Set(string name, Matrix4 m) => GL.UniformMatrix4(Loc(name), false, ref m);

    public void Dispose() => GL.DeleteProgram(Handle);

    // ── Shader source loaders ─────────────────────────────────────────────────

    static string ShaderDir =>
        Path.Combine(AppContext.BaseDirectory, "Shaders");

    public static ShaderProgram FromFiles(string vertFile, string fragFile) =>
        new(File.ReadAllText(Path.Combine(ShaderDir, vertFile)),
            File.ReadAllText(Path.Combine(ShaderDir, fragFile)));

    public static ShaderProgram ComputeFromFile(string compFile) =>
        new(File.ReadAllText(Path.Combine(ShaderDir, compFile)));
}
