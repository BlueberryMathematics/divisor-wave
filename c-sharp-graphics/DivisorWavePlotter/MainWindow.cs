using OpenTK.Graphics.OpenGL4;
using OpenTK.Mathematics;
using OpenTK.Windowing.Common;
using OpenTK.Windowing.Desktop;
using OpenTK.Windowing.GraphicsLibraryFramework;
using System.Runtime.InteropServices;
using DivisorWavePlotter.Interop;
using DivisorWavePlotter.Rendering;

namespace DivisorWavePlotter;

sealed class MainWindow : GameWindow
{
    readonly LaunchOptions _opts;
    readonly ElectronBridge _bridge;

    Renderer2DReal?    _r2d;
    Renderer2DComplex? _r2dCx;
    Renderer3DSurface? _r3d;
    AnimationState     _anim = new();

    PlotCommand? _pending;
    readonly object _lock = new();

    public MainWindow(GameWindowSettings gws, NativeWindowSettings nws, LaunchOptions opts)
        : base(gws, nws)
    {
        _opts   = opts;
        _bridge = new ElectronBridge(cmd => { lock (_lock) _pending = cmd; });
    }

    // ── Lifecycle ──────────────────────────────────────────────────────────────

    protected override void OnLoad()
    {
        base.OnLoad();

        GL.ClearColor(0.024f, 0.024f, 0.055f, 1f);
        GL.Enable(EnableCap.Blend);
        GL.BlendFunc(BlendingFactor.SrcAlpha, BlendingFactor.OneMinusSrcAlpha);
        GL.Enable(EnableCap.LineSmooth);
        GL.Hint(HintTarget.LineSmoothHint, HintMode.Nicest);

        _r2d   = new Renderer2DReal   (Size.X, Size.Y);
        _r2dCx = new Renderer2DComplex(Size.X, Size.Y);
        _r3d   = new Renderer3DSurface (Size.X, Size.Y);

        if (_opts.ParentHwnd != 0)
        {
            try { EmbedInParent(); }
            catch (Exception ex) { Console.Error.WriteLine($"[embed] {ex.Message}"); }
        }

        _bridge.Start();
        _bridge.Send(new
        {
            type = "ready",
            gpu  = GL.GetString(StringName.Renderer),
            glsl = GL.GetString(StringName.ShadingLanguageVersion),
        });
    }

    protected override void OnUpdateFrame(FrameEventArgs args)
    {
        base.OnUpdateFrame(args);

        PlotCommand? cmd;
        lock (_lock) { cmd = _pending; _pending = null; }
        if (cmd != null) Apply(cmd);

        _anim.Advance((float)args.Time);

        if (KeyboardState.IsKeyPressed(Keys.Escape) && _opts.ParentHwnd == 0)
            Close();
    }

    protected override void OnRenderFrame(FrameEventArgs args)
    {
        base.OnRenderFrame(args);
        GL.Viewport(0, 0, Size.X, Size.Y);
        GL.Clear(ClearBufferMask.ColorBufferBit | ClearBufferMask.DepthBufferBit);

        switch (_anim.Mode)
        {
            case PlotMode.DivisorWaveAnim: _r2d?.DrawAnimation(_anim); break;
            case PlotMode.Real2D:          _r2d?.Draw();               break;
            case PlotMode.Complex2D:       _r2dCx?.Draw();             break;
            case PlotMode.Complex3D:       _r3d?.Draw();               break;
        }

        SwapBuffers();

        // Report cursor position back to Electron at ~5 fps
        if (_anim.Mode == PlotMode.DivisorWaveAnim && _anim.Playing
            && (int)(args.Time * 5) % 1 == 0)
        {
            _bridge.Send(new { type = "cursorX", x = Math.Round(_anim.CursorX, 3) });
        }
    }

    protected override void OnResize(ResizeEventArgs e)
    {
        base.OnResize(e);
        _r2d?.Resize(e.Width, e.Height);
        _r2dCx?.Resize(e.Width, e.Height);
        _r3d?.Resize(e.Width, e.Height);
    }

    protected override void OnUnload()
    {
        _bridge.Stop();
        _r2d?.Dispose(); _r2dCx?.Dispose(); _r3d?.Dispose();
        base.OnUnload();
    }

    // ── Command dispatch ───────────────────────────────────────────────────────

    void Apply(PlotCommand cmd)
    {
        switch (cmd.Cmd)
        {
            case "plot":
                switch (cmd.Mode)
                {
                    case "real2d":
                        _anim.Mode = PlotMode.Real2D;
                        _r2d!.SetFunction(cmd.FuncId ?? "1", cmd.Params);
                        break;

                    case "complex2d":
                        _anim.Mode = PlotMode.Complex2D;
                        _r2dCx!.SetFunction(cmd.FuncId ?? "1", cmd.Params);
                        break;

                    case "complex3d":
                        _anim.Mode = PlotMode.Complex3D;
                        _r3d!.SetFunction(cmd.FuncId ?? "1", cmd.Params);
                        break;

                    case "divisorwave":
                        _anim.Mode      = PlotMode.DivisorWaveAnim;
                        _anim.KMax      = cmd.GetInt("kMax",      12);
                        _anim.Alpha     = cmd.GetDouble("alpha",  1.0);
                        _anim.Speed     = cmd.GetDouble("speed",  2.0);
                        _anim.DotRadius = cmd.GetDouble("dotRadius", 8.0);
                        _anim.XMin      = cmd.GetDouble("xMin",  -2.0);
                        _anim.Reset();
                        _r2d!.PrepareWaves(_anim);
                        break;
                }
                break;

            case "startAnim":  _anim.Playing = true;  break;
            case "stopAnim":   _anim.Playing = false; break;
            case "resetAnim":  _anim.Reset();         break;

            case "resize":
                int w = cmd.GetInt("w", Size.X);
                int h = cmd.GetInt("h", Size.Y);
                int x = cmd.GetInt("x", _opts.EmbedX);
                int y = cmd.GetInt("y", _opts.EmbedY);
                Size = new Vector2i(w, h);
                if (_opts.ParentHwnd != 0)
                    RepositionInParent(x, y, w, h);
                break;

            case "ping":
                _bridge.Send(new { type = "pong" });
                break;
        }
    }

    // ── Win32 child-window embedding ───────────────────────────────────────────

    [DllImport("user32.dll")] static extern IntPtr SetParent     (IntPtr child,  IntPtr parent);
    [DllImport("user32.dll")] static extern int    SetWindowLong (IntPtr hWnd,   int nIndex, int dwNew);
    [DllImport("user32.dll")] static extern bool   SetWindowPos  (IntPtr hWnd,   IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("user32.dll")] static extern bool   ShowWindow    (IntPtr hWnd,   int cmd);

    const int  GWL_STYLE       = -16;
    const int  WS_CHILD        = 0x40000000;
    const int  WS_VISIBLE      = 0x10000000;
    const int  WS_CLIPSIBLINGS = 0x04000000;
    const uint SWP_SHOWWINDOW  = 0x0040;
    const uint SWP_NOACTIVATE  = 0x0010;
    const uint SWP_NOZORDER    = 0x0004;
    const int  SW_SHOW         = 5;

    unsafe void EmbedInParent()
    {
        var parent = new IntPtr(_opts.ParentHwnd);
        var child  = GLFW.GetWin32Window(WindowPtr);

        // Convert from top-level to child window, then re-parent into Electron window.
        // Must set style before SetParent so the WM sees it as a child from the start.
        SetWindowLong(child, GWL_STYLE, WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS);
        SetParent(child, parent);
        SetWindowPos(child, IntPtr.Zero,
            _opts.EmbedX, _opts.EmbedY, _opts.Width, _opts.Height,
            SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_NOZORDER);
        ShowWindow(child, SW_SHOW);   // make visible now that it's a child
    }

    unsafe void RepositionInParent(int x, int y, int w, int h)
    {
        var child = GLFW.GetWin32Window(WindowPtr);
        SetWindowPos(child, IntPtr.Zero, x, y, w, h,
            SWP_SHOWWINDOW | SWP_NOACTIVATE | SWP_NOZORDER);
    }
}
