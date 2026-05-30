#version 430 core
// Complex-plane function compute shader.
// Writes |f(x+iy)| to an image2D (2D heatmap) OR to an SSBO (3D surface heights).
// outputMode == 0 → image2D,  outputMode == 1 → SSBO

layout(local_size_x = 16, local_size_y = 16) in;

layout(rgba32f, binding = 0) writeonly uniform image2D outImage;

layout(std430, binding = 1) buffer HeightData {
    float heights[];
};

uniform int   funcId;
uniform float xMin, xMax, yMin, yMax;
uniform int   nx, ny;
uniform float alpha, beta, mCoeff;
uniform bool  normalize;
uniform int   outputMode;   // 0 = image, 1 = SSBO

const float PI = 3.14159265358979;

// ── Complex arithmetic ──────────────────────────────────────────────────────

vec2 cmul(vec2 a, vec2 b) { return vec2(a.x*b.x - a.y*b.y, a.x*b.y + a.y*b.x); }
vec2 cdiv(vec2 a, vec2 b) {
    float d = dot(b, b) + 1e-30;
    return vec2(dot(a, b), a.y*b.x - a.x*b.y) / d;
}
vec2 cexp(vec2 z) { return exp(z.x) * vec2(cos(z.y), sin(z.y)); }
vec2 clog(vec2 z) { return vec2(log(length(z) + 1e-30), atan(z.y, z.x)); }
vec2 csin(vec2 z) { return vec2(sin(z.x)*cosh(z.y), cos(z.x)*sinh(z.y)); }
vec2 ccos(vec2 z) { return vec2(cos(z.x)*cosh(z.y), -sin(z.x)*sinh(z.y)); }
vec2 ctan(vec2 z) { return cdiv(csin(z), ccos(z)); }
float cabs(vec2 z) { return length(z); }

// Non-recursive Lanczos gamma (GLSL forbids recursion).
// lanczos_core(z): computes Gamma(z+1) for z >= -0.5
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
    // Reflection formula for x < 0.5 (avoids recursion):
    // Gamma(x) = pi / (sin(pi*x) * Gamma(1-x))
    // Gamma(1-x) = lanczos_core(-x)  since (1-x) - 1 = -x
    if (x < 0.5) return PI / (sin(PI * x) * lanczos_core(-x));
    return lanczos_core(x - 1.0);
}

float normVal(float v, float m)
{
    if (v <= 0.0) return 0.0;
    float raised = pow(v, -m);
    float g = gammaReal(raised + 1.0);
    return raised / max(g, 1e-30);
}

// ── Function implementations ─────────────────────────────────────────────────

// fn1 – Product of Sin:  ∏_{k=2}^{floor(x)} |α·(x/k)·sin(π·z/k)|
float fn1(vec2 z)
{
    int K = max(2, int(z.x));
    K = min(K, 50);
    vec2 result = vec2(1.0, 0.0);
    for (int k = 2; k <= K; k++) {
        float kf = float(k);
        vec2 sv = csin(PI * z / kf);
        vec2 coeff = vec2(alpha * z.x / kf, 0.0);
        result = cmul(result, cmul(coeff, sv));
    }
    float mag = cabs(result);
    return normalize ? normVal(mag, mCoeff) : pow(max(mag, 1e-30), -mCoeff);
}

// fn2 – Weierstrass product:  ∏_{k=2}^x |β·x/k · πz · ∏_{n=2}^x(1 − z²/(n²k²))|
float fn2(vec2 z)
{
    int K = max(2, int(z.x));
    K = min(K, 30);
    vec2 result = vec2(1.0, 0.0);
    for (int k = 2; k <= K; k++) {
        float kf = float(k);
        vec2 inner = PI * z;
        for (int n = 2; n <= K; n++) {
            float nf = float(n);
            float denom = nf*nf * kf*kf;
            vec2 factor = vec2(1.0, 0.0) - cmul(z, z) / denom;
            inner = cmul(inner, factor);
        }
        float coeff = beta * z.x / kf;
        result = cmul(result, vec2(abs(coeff) * cabs(inner), 0.0));
    }
    float mag = cabs(result);
    return normalize ? normVal(mag, mCoeff) : pow(max(mag, 1e-30), -mCoeff);
}

// fn5 – Riesz cos:  ∏_{n=2}^x (1 + |cos(πzn)|)  normalized
float fn5(vec2 z)
{
    int K = max(2, int(z.x));
    K = min(K, 40);
    float r = 1.0;
    for (int n = 2; n <= K; n++)
        r *= (1.0 + cabs(ccos(PI * z * float(n))));
    return normVal(r, mCoeff);
}

// fn6 – Riesz sin
float fn6(vec2 z)
{
    int K = max(2, int(z.x));
    K = min(K, 40);
    float r = 1.0;
    for (int n = 2; n <= K; n++)
        r *= (1.0 + cabs(csin(PI * z * float(n))));
    return normVal(r, mCoeff);
}

// fn7 – Riesz tan
float fn7(vec2 z)
{
    int K = max(2, int(z.x));
    K = min(K, 40);
    float r = 1.0;
    for (int n = 2; n <= K; n++) {
        vec2 t = ctan(PI * z * float(n));
        float tl = cabs(t);
        if (!isnan(tl) && !isinf(tl)) r *= (1.0 + tl);
    }
    return normVal(r, mCoeff);
}

// fn8 – Viète cos
float fn8(vec2 z)
{
    float r = 1.0;
    for (int n = 1; n <= 50; n++)
        r *= cos(PI / pow(2.0, float(n+1)));
    return r;
}

// fn19 – |log Γ(z)|
float fn19(vec2 z)
{
    return log(abs(gammaReal(z.x)) + 1e-30);
}

// fn20 – 1/|1+z²|
float fn20(vec2 z)
{
    vec2 z2   = cmul(z, z);
    vec2 denom = vec2(1.0 + z2.x, z2.y);
    return 1.0 / max(cabs(denom), 1e-10);
}

// fn21 – |z^z| = |exp(z·log(z))|
float fn21(vec2 z)
{
    if (cabs(z) < 1e-6) return 0.0;
    return cabs(cexp(cmul(z, clog(z))));
}

// fn22 – |Γ(z)|
float fn22(vec2 z)
{
    return abs(gammaReal(z.x));
}

// fn11 – cos of product of sin
float fn11(vec2 z) { return abs(cos(fn1(z))); }

// fn12 – sin of product of sin
float fn12(vec2 z) { return abs(sin(fn1(z))); }

float evalFunc(vec2 z)
{
    switch (funcId) {
        case  1: return fn1(z);
        case  2: return fn2(z);
        case  5: return fn5(z);
        case  6: return fn6(z);
        case  7: return fn7(z);
        case  8: return fn8(z);
        case 11: return fn11(z);
        case 12: return fn12(z);
        case 19: return fn19(z);
        case 20: return fn20(z);
        case 21: return fn21(z);
        case 22: return fn22(z);
        default: return fn1(z);
    }
}

// ── Colormap (Viridis) ────────────────────────────────────────────────────────
vec3 viridis(float t)
{
    t = clamp(t, 0.0, 1.0);
    vec3 c0 = vec3(0.2777, 0.0050, 0.3342);
    vec3 c1 = vec3(0.1050, 0.5302, 0.5010);
    vec3 c2 = vec3(0.9300, 0.8790, 0.1500);
    if (t < 0.5) return mix(c0, c1, t*2.0);
    return mix(c1, c2, (t-0.5)*2.0);
}

void main()
{
    uvec2 gid = gl_GlobalInvocationID.xy;
    if (int(gid.x) >= nx || int(gid.y) >= ny) return;

    float x = xMin + (xMax - xMin) * float(gid.x) / float(nx - 1);
    float y = yMin + (yMax - yMin) * float(gid.y) / float(ny - 1);

    float val = evalFunc(vec2(x, y));
    if (isnan(val) || isinf(val)) val = 0.0;

    int flatIdx = int(gid.y) * nx + int(gid.x);

    if (outputMode == 1) {
        // SSBO for 3D surface
        heights[flatIdx] = val;
    } else {
        // Image for 2D heatmap — tone-map through viridis
        float normed = val / (val + 1.0);  // soft clamp
        vec3 color = viridis(normed);
        imageStore(outImage, ivec2(gid), vec4(color, 1.0));
    }
}
