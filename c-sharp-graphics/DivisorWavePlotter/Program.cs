using OpenTK.Mathematics;
using OpenTK.Windowing.Common;
using OpenTK.Windowing.Desktop;

namespace DivisorWavePlotter;

static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        var opts = ParseArgs(args);

        var nws = new NativeWindowSettings
        {
            ClientSize      = new Vector2i(opts.Width, opts.Height),
            Title           = "Divisor Wave GPU Plotter",
            WindowBorder    = WindowBorder.Hidden,
            WindowState     = WindowState.Normal,
            NumberOfSamples = 4,
            APIVersion      = new Version(4, 3),  // require OpenGL 4.3 for compute shaders
            Flags           = ContextFlags.ForwardCompatible,
            // Start hidden when embedding so the window doesn't flash as a top-level window
            // before SetParent re-parents it into the Electron window.
            StartVisible    = opts.ParentHwnd == 0,
        };

        var gws = new GameWindowSettings
        {
            UpdateFrequency = 60,
        };

        using var win = new MainWindow(gws, nws, opts);
        win.Run();
    }

    static LaunchOptions ParseArgs(string[] args)
    {
        var o = new LaunchOptions();
        for (int i = 0; i < args.Length - 1; i++)
        {
            string val = args[i + 1];
            switch (args[i])
            {
                case "--parent-hwnd": if (long.TryParse(val, out var hw)) o.ParentHwnd = hw; i++; break;
                case "--embed-x":     if (int.TryParse(val,  out var ex)) o.EmbedX     = ex; i++; break;
                case "--embed-y":     if (int.TryParse(val,  out var ey)) o.EmbedY     = ey; i++; break;
                case "--width":       if (int.TryParse(val,  out var ew)) o.Width      = ew; i++; break;
                case "--height":      if (int.TryParse(val,  out var eh)) o.Height     = eh; i++; break;
            }
        }
        return o;
    }
}
