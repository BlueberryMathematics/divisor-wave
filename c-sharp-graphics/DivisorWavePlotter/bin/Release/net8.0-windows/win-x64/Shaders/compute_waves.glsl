#version 430 core
// Divisor wave compute shader.
// Evaluates a_k(x) = |alpha * x/k * sin(pi*x/k)| for every (k, x) pair in parallel.
// Output layout: waveValues[kIndex * numPoints + xIndex]

layout(local_size_x = 64, local_size_y = 1) in;

layout(std430, binding = 0) buffer WaveData {
    float waveValues[];
};

uniform float xMin;
uniform float xMax;
uniform int   numPoints;
uniform int   kMin;
uniform int   kMax;
uniform float alpha;

const float PI = 3.14159265358979323846;

void main()
{
    uint xIdx = gl_GlobalInvocationID.x;
    uint kIdx = gl_GlobalInvocationID.y;

    if (int(xIdx) >= numPoints) return;
    int k = int(kIdx) + kMin;
    if (k > kMax) return;

    float x = xMin + (xMax - xMin) * float(xIdx) / float(numPoints - 1);
    float kf = float(k);

    float val = abs(alpha * (x / kf) * sin(PI * x / kf));
    waveValues[kIdx * numPoints + int(xIdx)] = val;
}
