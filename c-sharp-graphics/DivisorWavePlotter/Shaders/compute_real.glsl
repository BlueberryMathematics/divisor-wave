#version 430 core
// Single real-valued function compute shader.
// Evaluates f(x) for funcId across a 1D x-grid in parallel.

layout(local_size_x = 256) in;

layout(std430, binding = 0) buffer RealData {
    float values[];
};

uniform int   funcId;
uniform float xMin, xMax;
uniform int   numPoints;
uniform float alpha, beta, mCoeff;

const float PI = 3.14159265358979;

// ── Helpers ──────────────────────────────────────────────────────────────────

// Non-recursive Lanczos gamma: computes Gamma(z+1) for z >= -0.5
float lanczos_core(float z)
{
    float g[9] = float[](
        0.99999999999980993, 676.5203681218851, -1259.1392167224028,
        771.32342877765313, -176.61502916214059, 12.507343278686905,
        -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7);
    float t = z + 7.5;
    float a = g[0];
    for (int i = 1; i < 9; i++) a += g[i] / (z + float(i));
    return sqrt(2.0*PI) * pow(t, z + 0.5) * exp(-t) * a;
}

float gammaReal(float x)
{
    // Reflection formula for x < 0.5 — no recursion needed:
    // Gamma(x) = pi / (sin(pi*x) * Gamma(1-x)), and Gamma(1-x) = lanczos_core(-(x))
    if (x < 0.5) return PI / (sin(PI * x) * lanczos_core(-x));
    return lanczos_core(x - 1.0);
}

float normVal(float v, float m)
{
    if (v <= 0.0) return 0.0;
    float r = pow(v, -m);
    return r / max(gammaReal(r + 1.0), 1e-30);
}

// ── Functions ────────────────────────────────────────────────────────────────

float fn1(float x)   // a(x) product of sin
{
    int K = max(2, int(x));
    K = min(K, 60);
    float r = 1.0;
    for (int k = 2; k <= K; k++)
        r *= abs(alpha * (x / float(k)) * sin(PI * x / float(k)));
    return abs(r);
}

float fn2(float x)   // b(x) Weierstrass product
{
    int K = max(2, int(x));
    K = min(K, 30);
    float result = 1.0;
    for (int k = 2; k <= K; k++) {
        float inner = PI * x;
        for (int n = 2; n <= K; n++)
            inner *= (1.0 - x*x / (float(n*n) * float(k*k)));
        result *= abs(beta * x / float(k) * inner);
    }
    return result;
}

float fn3(float x) { float a = fn1(x); return normVal(a, mCoeff); }  // A(x)
float fn4(float x) { float b = fn2(x); return normVal(b, mCoeff); }  // B(x)

float fn5(float x)  // Riesz cos
{
    int K = max(2, int(x)); K = min(K, 40);
    float r = 1.0;
    for (int n = 2; n <= K; n++) r *= (1.0 + abs(cos(PI * x * float(n))));
    return normVal(r, mCoeff);
}

float fn6(float x)  // Riesz sin
{
    int K = max(2, int(x)); K = min(K, 40);
    float r = 1.0;
    for (int n = 2; n <= K; n++) r *= (1.0 + abs(sin(PI * x * float(n))));
    return normVal(r, mCoeff);
}

float fn7(float x)  // Riesz tan
{
    int K = max(2, int(x)); K = min(K, 40);
    float r = 1.0;
    for (int n = 2; n <= K; n++) {
        float t = tan(PI * x * float(n));
        if (!isnan(t) && !isinf(t)) r *= (1.0 + abs(t));
    }
    return normVal(r, mCoeff);
}

float fn8(float x)  // Viète cos (constant, ignores x)
{
    float r = 1.0;
    for (int n = 1; n <= 50; n++) r *= cos(PI / pow(2.0, float(n+1)));
    return r;
}

float fn19(float x) { return log(abs(gammaReal(x)) + 1e-30); }
float fn20(float x) { return 1.0 / (1.0 + x*x); }
float fn21(float x) { return x > 0.0 ? pow(x, x) : 0.0; }
float fn22(float x) { return abs(gammaReal(x)); }

float fn11(float x) { return abs(cos(fn1(x))); }
float fn12(float x) { return abs(sin(fn1(x))); }
float fn13(float x) { return abs(cos(fn2(x))); }
float fn14(float x) { return abs(sin(fn2(x))); }

float evalFunc(float x)
{
    switch (funcId) {
        case  1: return fn1(x);
        case  2: return fn2(x);
        case  3: return fn3(x);
        case  4: return fn4(x);
        case  5: return fn5(x);
        case  6: return fn6(x);
        case  7: return fn7(x);
        case  8: return fn8(x);
        case 11: return fn11(x);
        case 12: return fn12(x);
        case 13: return fn13(x);
        case 14: return fn14(x);
        case 19: return fn19(x);
        case 20: return fn20(x);
        case 21: return fn21(x);
        case 22: return fn22(x);
        default: return fn1(x);
    }
}

void main()
{
    uint idx = gl_GlobalInvocationID.x;
    if (int(idx) >= numPoints) return;

    float x   = xMin + (xMax - xMin) * float(idx) / float(numPoints - 1);
    float val = evalFunc(x);
    values[idx] = (isnan(val) || isinf(val)) ? 0.0 : val;
}
