#version 430 core
in  float vHeight;
in  vec3  vNormal;
out vec4  fragColor;

uniform vec3 lightDir;

// Viridis colormap
vec3 viridis(float t)
{
    t = clamp(t, 0.0, 1.0);
    vec3 c0 = vec3(0.277, 0.005, 0.334);
    vec3 c1 = vec3(0.105, 0.530, 0.501);
    vec3 c2 = vec3(0.930, 0.879, 0.150);
    if (t < 0.5) return mix(c0, c1, t * 2.0);
    return mix(c1, c2, (t - 0.5) * 2.0);
}

void main()
{
    float normed  = vHeight / (vHeight + 1.0);
    vec3  base    = viridis(normed);
    float diffuse = max(dot(normalize(vNormal), normalize(lightDir)), 0.0);
    vec3  lit     = base * (0.35 + 0.65 * diffuse);
    fragColor = vec4(lit, 1.0);
}
