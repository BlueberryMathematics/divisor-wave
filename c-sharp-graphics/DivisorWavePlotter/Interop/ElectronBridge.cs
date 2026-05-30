using System.Text.Json;
using System.Text.Json.Serialization;

namespace DivisorWavePlotter.Interop;

// Reads JSON-line commands from stdin (sent by Electron main.js)
// and writes JSON-line responses to stdout.
// All stdin I/O happens on a background thread; the handler callback
// is invoked from that thread and queued by MainWindow into the GL thread.
sealed class ElectronBridge
{
    static readonly JsonSerializerOptions _opts = new()
    {
        PropertyNamingPolicy        = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition      = JsonIgnoreCondition.WhenWritingNull,
    };

    readonly Action<PlotCommand> _handler;
    Thread? _reader;
    volatile bool _running;

    public ElectronBridge(Action<PlotCommand> handler) => _handler = handler;

    public void Start()
    {
        _running = true;
        _reader  = new Thread(ReadLoop) { IsBackground = true, Name = "stdin-reader" };
        _reader.Start();
    }

    public void Stop() => _running = false;

    // Call from the GL update loop to drain any pending work (noop — commands
    // go straight to handler on the reader thread and are locked in MainWindow).
    public void Poll() { }

    public void Send(object payload)
    {
        try
        {
            var line = JsonSerializer.Serialize(payload, _opts);
            Console.WriteLine(line);
        }
        catch { /* ignore write errors — Electron side may have closed */ }
    }

    void ReadLoop()
    {
        while (_running)
        {
            string? line;
            try { line = Console.ReadLine(); }
            catch { break; }

            if (line == null) break;
            line = line.Trim();
            if (line.Length == 0) continue;

            try
            {
                var cmd = JsonSerializer.Deserialize<PlotCommand>(line, _opts);
                if (cmd != null) _handler(cmd);
            }
            catch (Exception ex)
            {
                Send(new { type = "error", message = ex.Message });
            }
        }
    }
}
