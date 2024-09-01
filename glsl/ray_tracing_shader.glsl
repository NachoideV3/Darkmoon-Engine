#version 330 core

in vec2 fragCoord;
out vec4 FragColor;

uniform vec3 camera_position;
uniform vec3 sphere_center;
uniform float sphere_radius;
uniform vec3 light_position;
uniform float light_intensity;
uniform vec3 plane_normal;
uniform float plane_d;
uniform sampler2D hdri_image;

vec3 normalize(vec3 v) {
    return v / length(v);
}

float dot(vec3 v1, vec3 v2) {
    return v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
}

vec3 sample_hdri(vec3 direction) {
    float theta = acos(direction.y);
    float phi = atan(direction.z, direction.x);
    float u = phi / (2.0 * 3.14159265);
    float v = theta / 3.14159265;
    return texture(hdri_image, vec2(u, v)).rgb;
}

void main() {
    vec3 ray_direction = normalize(vec3(fragCoord.xy, -1.0));
    vec3 oc = camera_position - sphere_center;
    float a = dot(ray_direction, ray_direction);
    float b = 2.0 * dot(oc, ray_direction);
    float c = dot(oc, oc) - sphere_radius * sphere_radius;
    float discriminant = b * b - 4.0 * a * c;

    if (discriminant >= 0.0) {
        // Hit sphere
        FragColor = vec4(1.0, 0.0, 0.0, 1.0); // Red
    } else {
        // Miss
        FragColor = sample_hdri(ray_direction);
    }
}
