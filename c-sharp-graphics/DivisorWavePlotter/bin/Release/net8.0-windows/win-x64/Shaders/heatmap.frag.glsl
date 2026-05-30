#version 430 core
in  vec2 vUV;
out vec4 fragColor;
uniform sampler2D heatmap;
void main() { fragColor = texture(heatmap, vUV); }
