using System.Text.Json;
using System.Text.Json.Serialization;

namespace DivisorWavePlotter.Interop;

// JSON shape arriving from Electron over stdin
sealed class PlotCommand
{
    [JsonPropertyName("cmd")]     public string? Cmd    { get; set; }
    [JsonPropertyName("mode")]    public string? Mode   { get; set; }
    [JsonPropertyName("funcId")]  public string? FuncId { get; set; }
    // Free-form parameter bag: kMax, alpha, beta, m, speed, dotRadius,
    // xMin, xMax, yMin, yMax, nx, ny, elev, azim, x, y, w, h ...
    [JsonPropertyName("params")]  public Dictionary<string, JsonElement>? Params { get; set; }

    // Convenience helpers
    public int    GetInt   (string k, int    def = 0)   => Params != null && Params.TryGetValue(k, out var e) ? e.GetInt32()  : def;
    public double GetDouble(string k, double def = 0.0) => Params != null && Params.TryGetValue(k, out var e) ? e.GetDouble() : def;
    public bool   GetBool  (string k, bool   def = false) => Params != null && Params.TryGetValue(k, out var e) ? e.GetBoolean() : def;
    public string GetStr   (string k, string def = "")  => Params != null && Params.TryGetValue(k, out var e) ? e.GetString() ?? def : def;
}
