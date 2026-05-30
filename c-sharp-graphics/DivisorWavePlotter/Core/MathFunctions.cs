namespace DivisorWavePlotter.Core;

// CPU implementations of all divisor-wave special functions.
// These are used for CPU fallback and for computing dot positions during animation.
// GPU equivalents live in the GLSL compute shaders.
static class MathFunctions
{
    const double PI = Math.PI;

    // ── Divisor wave primitives ────────────────────────────────────────────────

    // a_k(x) = |α * x/k * sin(π*x/k)|
    public static double Ak(double x, int k, double alpha = 1.0)
        => Math.Abs(alpha * (x / k) * Math.Sin(PI * x / k));

    // a(x) = ∏_{k=2}^{floor(x)} a_k(x)
    public static double AProduct(double x, double alpha = 1.0, int kMax = -1)
    {
        int km = kMax > 0 ? kMax : Math.Max(2, (int)Math.Abs(x));
        double r = 1.0;
        for (int k = 2; k <= km; k++) r *= Ak(x, k, alpha);
        return Math.Abs(r);
    }

    // A(x) = a(x)^{-m} / Γ(a(x)^{-m})  normalized product-of-sin
    public static double ANormalized(double x, double alpha = 1.0, double m = 0.0465)
    {
        double a = AProduct(x, alpha);
        if (a <= 0) return 0;
        double v = Math.Pow(a, -m);
        return v / GammaFunc(v + 1.0);
    }

    // b(x) — Weierstrass product representation:
    // ∏_{k=2}^{x} |β*x/k * π*x * ∏_{n=2}^{x}(1 − x²/(n²k²))|
    public static double BProduct(double x, double beta = 1.0)
    {
        int km = Math.Max(2, (int)Math.Abs(x));
        double result = 1.0;
        for (int k = 2; k <= km; k++)
        {
            double inner = PI * x;
            for (int n = 2; n <= km; n++)
                inner *= (1.0 - x * x / ((double)n * n * k * k));
            result *= Math.Abs(beta * x / k * inner);
        }
        return result;
    }

    // B(x) normalized Weierstrass
    public static double BNormalized(double x, double beta = 1.0, double m = 0.0125)
    {
        double b = BProduct(x, beta);
        if (b <= 0) return 0;
        double v = Math.Pow(b, -m);
        return v / GammaFunc(v + 1.0);
    }

    // ── Riesz products ─────────────────────────────────────────────────────────

    public static double RieszCos(double x, double m = 0.0125)
    {
        int km = Math.Max(2, (int)Math.Abs(x));
        double r = 1.0;
        for (int n = 2; n <= km; n++) r *= (1.0 + Math.Abs(Math.Cos(PI * x * n)));
        return Normalize(r, m);
    }

    public static double RieszSin(double x, double m = 0.0125)
    {
        int km = Math.Max(2, (int)Math.Abs(x));
        double r = 1.0;
        for (int n = 2; n <= km; n++) r *= (1.0 + Math.Abs(Math.Sin(PI * x * n)));
        return Normalize(r, m);
    }

    public static double RieszTan(double x, double m = 0.0125)
    {
        int km = Math.Max(2, (int)Math.Abs(x));
        double r = 1.0;
        for (int n = 2; n <= km; n++)
        {
            double t = Math.Tan(PI * x * n);
            if (double.IsFinite(t)) r *= (1.0 + Math.Abs(t));
        }
        return Normalize(r, m);
    }

    // ── Viète products ─────────────────────────────────────────────────────────

    public static double VieteCos(int terms = 50)
    {
        double r = 1.0;
        for (int n = 1; n <= terms; n++)
            r *= Math.Cos(PI / Math.Pow(2, n + 1));
        return r;
    }

    public static double VieteSin(double x, int terms = 50)
    {
        double r = 1.0;
        for (int n = 1; n <= terms; n++)
            r *= Math.Sin(PI * x / Math.Pow(2, n));
        return r;
    }

    // ── Nested roots ───────────────────────────────────────────────────────────

    public static double NestedRootsSum(double x, int terms = 40)
    {
        if (x <= 0) return 0;
        double r = 0;
        for (int n = 1; n <= terms; n++)
            r += Math.Log(Math.Pow(x, Math.Pow(2, -n)));
        return r;
    }

    public static double NestedRootsProd(double x, int terms = 40)
    {
        if (x <= 0) return 0;
        double exp = 0;
        for (int n = 1; n <= terms; n++) exp += Math.Pow(2, -n);
        return Math.Pow(x, exp);
    }

    // ── Prime indicators (real-axis approximations) ───────────────────────────

    public static double PrimeIndicatorH(double x)
    {
        double b = BProduct(x);
        return Math.Abs(b) < 1e-10 ? 1.0 : 0.0;
    }

    public static double PrimeIndicatorJ(double x)
        => x * (1.0 - PrimeIndicatorH(x));

    // ── Standard analytic functions ────────────────────────────────────────────

    public static double LogGamma(double x)
    {
        if (x <= 0) return 0;
        try { return Math.Log(Math.Abs(GammaFunc(x))); } catch { return 0; }
    }

    public static double ZPowZ(double x)
        => x > 0 ? Math.Pow(x, x) : 0;

    public static double InvOnePlusX2(double x)
        => 1.0 / (1.0 + x * x);

    // ── Compositions ──────────────────────────────────────────────────────────

    public static double CosOfAProduct(double x, double alpha = 1.0)
        => Math.Abs(Math.Cos(AProduct(x, alpha)));

    public static double SinOfAProduct(double x, double alpha = 1.0)
        => Math.Abs(Math.Sin(AProduct(x, alpha)));

    public static double CosOfBProduct(double x, double beta = 1.0)
        => Math.Abs(Math.Cos(BProduct(x, beta)));

    public static double SinOfBProduct(double x, double beta = 1.0)
        => Math.Abs(Math.Sin(BProduct(x, beta)));

    // ── Generic dispatch by function ID string ────────────────────────────────

    public static double Evaluate(string funcId, double x,
        double alpha = 1.0, double beta = 1.0, double m = 0.0465, int kMax = -1)
    {
        try
        {
            return funcId switch
            {
                "1"  or "ak_product"    => AProduct(x, alpha, kMax),
                "2"  or "bk_product"    => BProduct(x, beta),
                "3"  or "ak_norm"       => ANormalized(x, alpha, m),
                "4"  or "bk_norm"       => BNormalized(x, beta, m),
                "5"  or "riesz_cos"     => RieszCos(x, m),
                "6"  or "riesz_sin"     => RieszSin(x, m),
                "7"  or "riesz_tan"     => RieszTan(x, m),
                "8"  or "viete_cos"     => VieteCos(),
                "9"  or "viete_sin"     => VieteSin(x),
                "11" or "cos_a"         => CosOfAProduct(x, alpha),
                "12" or "sin_a"         => SinOfAProduct(x, alpha),
                "13" or "cos_b"         => CosOfBProduct(x, beta),
                "14" or "sin_b"         => SinOfBProduct(x, beta),
                "15" or "prime_h"       => PrimeIndicatorH(x),
                "16" or "prime_j"       => PrimeIndicatorJ(x),
                "19" or "loggamma"      => LogGamma(x),
                "20" or "inv1px2"       => InvOnePlusX2(x),
                "21" or "zpowz"         => ZPowZ(x),
                "22" or "gamma"         => Math.Abs(GammaFunc(x)),
                "31" or "nested_sum"    => NestedRootsSum(x),
                "nested_prod"           => NestedRootsProd(x),
                _                       => AProduct(x, alpha),
            };
        }
        catch { return 0; }
    }

    // ── Helpers ────────────────────────────────────────────────────────────────

    static double Normalize(double val, double m)
    {
        if (val <= 0) return 0;
        double v = Math.Pow(val, -m);
        return v / GammaFunc(v + 1.0);
    }

    // Lanczos approximation (g=7)
    public static double GammaFunc(double x)
    {
        if (x < 0.5)
            return PI / (Math.Sin(PI * x) * GammaFunc(1 - x));

        x -= 1;
        double[] g = {
            0.99999999999980993, 676.5203681218851, -1259.1392167224028,
            771.32342877765313, -176.61502916214059, 12.507343278686905,
            -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
        };
        double t = x + 7.5;
        double a = g[0];
        for (int i = 1; i < 9; i++) a += g[i] / (x + i);
        return Math.Sqrt(2 * PI) * Math.Pow(t, x + 0.5) * Math.Exp(-t) * a;
    }
}
