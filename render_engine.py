import math
import numpy as np
from PyQt5.QtGui import QImage, qRgb

def normalize(v):
    norm = math.sqrt(sum(i ** 2 for i in v))
    return tuple(i / norm for i in v)

def subtract(v1, v2):
    return tuple(v1[i] - v2[i] for i in range(3))

def add(v1, v2):
    return tuple(v1[i] + v2[i] for i in range(3))

def multiply(v, scalar):
    return tuple(i * scalar for i in v)

def dot(v1, v2):
    return sum(v1[i] * v2[i] for i in range(3))

class Renderer:
    def __init__(self, camera_position, sphere_center, sphere_radius, light_position, light_intensity, plane_y, hdri_image):
        self.camera_position = camera_position
        self.sphere_center = sphere_center
        self.sphere_radius = sphere_radius
        self.light_position = light_position
        self.light_intensity = light_intensity
        self.plane_y = plane_y
        self.hdri_image = hdri_image

    def sample_hdri(self, direction):
        theta = math.acos(direction[1])
        phi = math.atan2(direction[2], direction[0])
        phi = phi if phi >= 0 else (2 * math.pi + phi)
        u = phi / (2 * math.pi)
        v = theta / math.pi
        x = int(u * self.hdri_image.shape[1])
        y = int(v * self.hdri_image.shape[0])
        color = self.hdri_image[y % self.hdri_image.shape[0], x % self.hdri_image.shape[1]]
        return (color[0], color[1], color[2])

    def compute_shadow(self, hit_point):
        shadow_ray_direction = subtract(self.light_position, hit_point)
        shadow_ray_direction = normalize(shadow_ray_direction)
        
        oc = subtract(hit_point, self.sphere_center)
        a = dot(shadow_ray_direction, shadow_ray_direction)
        b = 2.0 * dot(oc, shadow_ray_direction)
        c = dot(oc, oc) - self.sphere_radius * self.sphere_radius
        discriminant = b * b - 4 * a * c

        shadow_intensity = 1.0  # Luz sin sombra
        if discriminant >= 0:
            shadow_intensity = 0.3  # Ajusta la intensidad de la sombra si se detecta una intersección

        return (shadow_intensity, shadow_intensity, shadow_intensity)

    def compute_lighting(self, hit_point, normal):
        light_direction = subtract(self.light_position, hit_point)
        light_direction = normalize(light_direction)
        diff = max(dot(normal, light_direction), 0)
        color = (diff * self.light_intensity, diff * self.light_intensity, diff * self.light_intensity)
        return color

    def render_scene(self, width, height):
        image = QImage(width, height, QImage.Format_RGB32)
        ray_count = 0

        for y in range(height):
            for x in range(width):
                px = (x / width) * 2 - 1
                py = 1 - (y / height) * 2
                ray_direction = normalize((px, py, -1))

                oc = subtract(self.camera_position, self.sphere_center)
                a = dot(ray_direction, ray_direction)
                b = 2.0 * dot(oc, ray_direction)
                c = dot(oc, oc) - self.sphere_radius * self.sphere_radius
                discriminant = b * b - 4 * a * c

                plane_normal = (0, 1, 0)
                plane_d = -self.plane_y
                denom = dot(ray_direction, plane_normal)

                ray_count += 1

                t_sphere = float('inf')
                t_plane = float('inf')

                if discriminant >= 0:
                    t_sphere = (-b - math.sqrt(discriminant)) / (2.0 * a)

                if abs(denom) > 1e-6:
                    t_plane = -(dot(self.camera_position, plane_normal) + plane_d) / denom

                if t_plane > 0 and (t_plane < t_sphere or t_sphere == float('inf')):
                    plane_hit_point = add(self.camera_position, multiply(ray_direction, t_plane))
                    shadow_color = self.compute_shadow(plane_hit_point)
                    color = (0.5, 0.5, 0.5)  # Color del piso
                    color = tuple(int(min(max(c * 255, 0), 255)) for c in add(shadow_color, color))
                    image.setPixel(x, y, qRgb(*color))
                elif t_sphere < float('inf'):
                    hit_point = add(self.camera_position, multiply(ray_direction, t_sphere))
                    normal = normalize(subtract(hit_point, self.sphere_center))
                    reflection_direction = subtract(ray_direction, multiply(normal, 2 * dot(ray_direction, normal)))
                    reflection_color = self.sample_hdri(reflection_direction)
                    color = self.compute_lighting(hit_point, normal)
                    metallic_color = (1.0, 0.0, 0.0)  # Rojo metálico
                    reflection_intensity = 0.5  # Ajustar la intensidad de la reflexión
                    color = add(multiply(metallic_color, 1 - reflection_intensity), multiply(reflection_color, reflection_intensity))
                    color = multiply(color, 1.2)
                    color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                    image.setPixel(x, y, qRgb(*color))
                else:
                    color = self.sample_hdri(ray_direction)
                    color = multiply(color, 1.2)
                    color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                    image.setPixel(x, y, qRgb(*color))

        return image, ray_count
