import math
import glm
import numpy as np
from PyQt5.QtGui import QImage, qRgb

class Renderer:
    def __init__(self, camera_position, sphere_center, sphere_radius, light_position, light_intensity, plane_y, hdri_image, use_ray_tracing=True):
        self.camera_position = glm.vec3(*camera_position)
        self.sphere_center = glm.vec3(*sphere_center)
        self.sphere_radius = sphere_radius
        self.light_position = glm.vec3(*light_position)
        self.light_intensity = light_intensity
        self.plane_y = plane_y
        self.hdri_image = hdri_image
        self.use_ray_tracing = use_ray_tracing

        # Pre-calculate plane normal and plane distance
        self.plane_normal = glm.vec3(0, 1, 0)
        self.plane_d = -self.plane_y

    def sample_hdri(self, direction):
        direction = glm.normalize(direction)
        theta = math.acos(direction.y)
        phi = math.atan2(direction.z, direction.x)
        phi = phi if phi >= 0 else (2 * math.pi + phi)
        u = phi / (2 * math.pi)
        v = theta / math.pi
        x = int(u * self.hdri_image.shape[1])
        y = int(v * self.hdri_image.shape[0])
        color = self.hdri_image[y % self.hdri_image.shape[0], x % self.hdri_image.shape[1]]
        return tuple(color)

    def compute_shadow(self, hit_point):
        shadow_ray_direction = glm.normalize(self.light_position - hit_point)
        
        oc = hit_point - self.sphere_center
        a = glm.dot(shadow_ray_direction, shadow_ray_direction)
        b = 2.0 * glm.dot(oc, shadow_ray_direction)
        c = glm.dot(oc, oc) - self.sphere_radius * self.sphere_radius
        discriminant = b * b - 4 * a * c

        shadow_intensity = 1.0  # Light with no shadow
        if discriminant >= 0:
            shadow_intensity = 0.3  # Adjust shadow intensity if an intersection is detected

        return (shadow_intensity, shadow_intensity, shadow_intensity)

    def compute_lighting(self, hit_point, normal):
        light_direction = glm.normalize(self.light_position - hit_point)
        diff = max(glm.dot(normal, light_direction), 0)
        color = (diff * self.light_intensity, diff * self.light_intensity, diff * self.light_intensity)
        return color

    def render_scene(self, width, height):
        image = QImage(width, height, QImage.Format_RGB32)
        ray_count = 0

        for y in range(height):
            for x in range(width):
                px = (x / width) * 2 - 1
                py = 1 - (y / height) * 2
                ray_direction = glm.normalize(glm.vec3(px, py, -1))

                if not self.use_ray_tracing:
                    oc = self.camera_position - self.sphere_center
                    a = glm.dot(ray_direction, ray_direction)
                    b = 2.0 * glm.dot(oc, ray_direction)
                    c = glm.dot(oc, oc) - self.sphere_radius * self.sphere_radius
                    discriminant = b * b - 4 * a * c

                    denom = glm.dot(ray_direction, self.plane_normal)

                    if discriminant >= 0:
                        t_sphere = (-b - math.sqrt(discriminant)) / (2.0 * a)
                        if t_sphere > 0:
                            color = glm.vec3(1.0, 0.0, 0.0)  # Solid red for the sphere
                            color = glm.clamp(color, 0.0, 1.0)
                            color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                            image.setPixel(x, y, qRgb(*color))
                            continue

                    if abs(denom) > 1e-6:
                        t_plane = -(glm.dot(self.camera_position, self.plane_normal) + self.plane_d) / denom
                        if t_plane > 0:
                            color = glm.vec3(0.5, 0.5, 0.5)  # Solid gray for the plane
                            color = glm.clamp(color, 0.0, 1.0)
                            color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                            image.setPixel(x, y, qRgb(*color))
                            continue

                    color = self.sample_hdri(ray_direction)
                    color = glm.vec3(*color)
                    color = glm.clamp(color, 0.0, 1.0)
                    color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                    image.setPixel(x, y, qRgb(*color))

                else:
                    oc = self.camera_position - self.sphere_center
                    a = glm.dot(ray_direction, ray_direction)
                    b = 2.0 * glm.dot(oc, ray_direction)
                    c = glm.dot(oc, oc) - self.sphere_radius * self.sphere_radius
                    discriminant = b * b - 4 * a * c

                    denom = glm.dot(ray_direction, self.plane_normal)

                    ray_count += 1

                    t_sphere = float('inf')
                    t_plane = float('inf')

                    if discriminant >= 0:
                        t_sphere = (-b - math.sqrt(discriminant)) / (2.0 * a)

                    if abs(denom) > 1e-6:
                        t_plane = -(glm.dot(self.camera_position, self.plane_normal) + self.plane_d) / denom

                    if t_plane > 0 and (t_plane < t_sphere or t_sphere == float('inf')):
                        plane_hit_point = self.camera_position + ray_direction * t_plane
                        shadow_color = self.compute_shadow(plane_hit_point)
                        color = glm.vec3(0.5, 0.5, 0.5)  # Plane color
                        shadow_color = glm.vec3(*shadow_color)
                        color = glm.clamp(color + shadow_color, 0.0, 1.0)
                        color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                        image.setPixel(x, y, qRgb(*color))
                    elif t_sphere < float('inf'):
                        hit_point = self.camera_position + ray_direction * t_sphere
                        normal = glm.normalize(hit_point - self.sphere_center)
                        reflection_direction = glm.normalize(ray_direction - normal * 2 * glm.dot(ray_direction, normal))
                        reflection_color = self.sample_hdri(reflection_direction)
                        color = self.compute_lighting(hit_point, normal)
                        metallic_color = glm.vec3(1.0, 0.0, 0.0)  # Metallic red
                        reflection_intensity = 0.5  # Adjust reflection intensity
                        color = (1 - reflection_intensity) * metallic_color + reflection_intensity * glm.vec3(*reflection_color)
                        color *= 1.2
                        color = glm.clamp(color, 0.0, 1.0)
                        color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                        image.setPixel(x, y, qRgb(*color))
                    else:
                        color = self.sample_hdri(ray_direction)
                        color = glm.vec3(*color)
                        color *= 1.2
                        color = glm.clamp(color, 0.0, 1.0)
                        color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                        image.setPixel(x, y, qRgb(*color))

        return image, ray_count
