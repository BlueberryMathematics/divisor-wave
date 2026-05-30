#version 430 core
// Renders a smooth anti-aliased filled circle dot.
// The quad UV coords run (-1,-1) to (1,1); we discard outside the unit circle.

in  vec2 vUV;
out vec4 fragColor;

uniform vec3  dotColor;
uniform vec2  center;    // NDC centre (not used in fragment — UV is relative)
uniform float radius;    // NDC radius (for aspect correction hint)
uniform float aspect;    // width / height (unused here, corrected in vertex)

void main()
{
    float dist = length(vUV);
    if (dist > 1.0) discard;

    // Smooth border
    float alpha = 1.0 - smoothstep(0.75, 1.0, dist);

    // Inner highlight
    float highlight = smoothstep(0.5, 0.0, dist) * 0.35;

    vec3 col = dotColor + highlight;
    fragColor = vec4(col, alpha);
}
