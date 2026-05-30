namespace DivisorWavePlotter.Core;

// Mirrors the FUNCTIONS array in Electron's index.js so C# knows about every function.
record FunctionInfo(string Id, string Name, string Group, bool Real = true, bool Complex = true);

static class FunctionRegistry
{
    public static readonly FunctionInfo[] All =
    [
        new("1",  "Product of Sin (a(z))",             "Basic"),
        new("2",  "Product Rep. for Sin (b(z))",        "Basic"),
        new("3",  "Product Rep. for Sin (Complex)",     "Basic"),
        new("4",  "Complex Playground Demo",            "Basic"),
        new("5",  "Riesz — Cos",                       "Riesz"),
        new("6",  "Riesz — Sin",                       "Riesz"),
        new("7",  "Riesz — Tan",                       "Riesz"),
        new("8",  "Viète — Cos",                       "Viète"),
        new("9",  "Viète — Sin",                       "Viète"),
        new("10", "Viète — Tan",                       "Viète"),
        new("11", "Cos of Product of Sin",              "Compositions"),
        new("12", "Sin of Product of Sin",              "Compositions"),
        new("13", "Cos of Product Rep. of Sin",         "Compositions"),
        new("14", "Sin of Product Rep. of Sin",         "Compositions"),
        new("15", "Binary Prime Indicator H",           "Prime"),
        new("16", "Prime Output Indicator J",           "Prime"),
        new("17", "BOPIF Q Alternation Series",         "Prime"),
        new("18", "Dirichlet Eta from BOPIF",           "Prime"),
        new("19", "|loggamma(z)|",                      "Analytic"),
        new("20", "1 / (1 + z²)",                       "Analytic"),
        new("21", "|z^z|",                              "Analytic"),
        new("22", "gamma(z)",                           "Analytic"),
        new("23", "Log of Product Rep. Sin",            "Transforms"),
        new("24", "Gamma of Product Rep. Sin",          "Transforms"),
        new("25", "Gamma Form Product Rep. Sin",        "Transforms"),
        new("26", "Custom Riesz — Tan",                "Custom"),
        new("27", "Custom Viète — Cos",                "Custom"),
        new("28", "Half-Base Viète — Sin",             "Custom"),
        new("29", "Log-Power-Base Viète — Sin",        "Custom"),
        new("30", "Riesz Tan + Prime Indicator",        "Custom"),
        new("31", "Nested Roots Product for 2",         "Experimental"),

        // Real-only divisor wave variants
        new("dw_single",  "a_k(x) — single wave",      "Divisor Waves", Real: true, Complex: false),
        new("dw_product", "a(x) — product of waves",   "Divisor Waves", Real: true, Complex: false),
        new("dw_anim",    "Divisor Wave Animation",     "Divisor Waves", Real: true, Complex: false),
        new("nested_prod","Nested Roots Product",       "Experimental", Real: true, Complex: false),
    ];

    public static FunctionInfo? Get(string id) =>
        All.FirstOrDefault(f => f.Id == id);
}
