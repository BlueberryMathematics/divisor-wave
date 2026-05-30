#version 430 core
// 3D surface vertex shader.
// Grid (xi, yi) indices arrive as vertex attributes; height is fetched from the SSBO.

layout(location = 0) in ivec2 aGrid;  // (xi, yi)

layout(std430, binding = 0) readonly buffer HeightData {
    float heights[];
};

uniform mat4  proj, view;
uniform float xMin, xMax, yMin, yMax;
uniform int   nx, ny;

out float vHeight;
out vec3  vNormal;

void main()
{
    int xi = aGrid.x, yi = aGrid.y;
    float h = heights[yi * nx + xi];

    float x = xMin + (xMax - xMin) * float(xi) / float(nx - 1);
    float z = yMin + (yMax - yMin) * float(yi) / float(ny - 1);

    // Approximate normal via finite differences
    float hr = (xi < nx-1) ? heights[yi*nx + xi+1] : h;
    float hl = (xi > 0)    ? heights[yi*nx + xi-1] : h;
    float hu = (yi < ny-1) ? heights[(yi+1)*nx + xi] : h;
    float hd = (yi > 0)    ? heights[(yi-1)*nx + xi] : h;
    float dx = (xMax - xMin) / float(nx - 1);
    float dz = (yMax - yMin) / float(ny - 1);
    vNormal   = normalize(vec3(-(hr - hl) / (2.0*dx), 2.0, -(hu - hd) / (2.0*dz)));

    vHeight = h;
    gl_Position = proj * view * vec4(x, h * 0.18, z, 1.0);
}
