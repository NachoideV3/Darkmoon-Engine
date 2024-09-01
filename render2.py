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

        self.plane_normal = glm.vec3(0, 1, 0)
        self.plane_d = -self.plane_y

        self.last_camera_position = None
        self.last_sphere_center = None
        self.last_sphere_radius = None
        self.last_light_position = None
        self.last_light_intensity = None
        self.last_plane_y = None
        self.last_hdri_image = None
        self.last_use_ray_tracing = None

    def scene_has_changed(self):
        return (self.camera_position != self.last_camera_position or
                self.sphere_center != self.last_sphere_center or
                self.sphere_radius != self.last_sphere_radius or
                self.light_position != self.last_light_position or
                self.light_intensity != self.last_light_intensity or
                self.plane_y != self.last_plane_y or
                self.hdri_image is not self.last_hdri_image or
                self.use_ray_tracing != self.last_use_ray_tracing)

    def update_last_parameters(self):
        self.last_camera_position = self.camera_position
        self.last_sphere_center = self.sphere_center
        self.last_sphere_radius = self.sphere_radius
        self.last_light_position = self.light_position
        self.last_light_intensity = self.light_intensity
        self.last_plane_y = self.plane_y
        self.last_hdri_image = self.hdri_image
        self.last_use_ray_tracing = self.use_ray_tracing

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

        shadow_intensity = 1.0
        if discriminant >= 0:
            t_sphere = (-b - math.sqrt(discriminant)) / (2.0 * a)
            if t_sphere > 0:
                shadow_intensity = 0.3
        return (shadow_intensity, shadow_intensity, shadow_intensity)

    def compute_lighting(self, hit_point, normal):
        light_direction = glm.normalize(self.light_position - hit_point)
        diffuse = max(glm.dot(normal, light_direction), 0)
        
        view_direction = glm.normalize(self.camera_position - hit_point)
        reflection_direction = glm.reflect(-light_direction, normal)
        specular = pow(max(glm.dot(view_direction, reflection_direction), 0), 32) # Phong specular exponent

        ambient_intensity = 0.1
        diffuse_intensity = self.light_intensity * diffuse
        specular_intensity = self.light_intensity * specular
        
        ambient_color = glm.vec3(0.1, 0.1, 0.1)
        diffuse_color = glm.vec3(1.0, 1.0, 1.0)
        specular_color = glm.vec3(1.0, 1.0, 1.0)

        color = ambient_intensity * ambient_color + diffuse_intensity * diffuse_color + specular_intensity * specular_color
        return glm.clamp(color, 0.0, 1.0)

    def compute_reflection_refraction(self, ray_direction, hit_point, normal):
        ior_air = 1.0  # Índice de refracción del aire
        ior_sphere = 1.5  # Índice de refracción de la esfera

        # Calcular el vector de vista
        view_direction = glm.normalize(self.camera_position - hit_point)

        # Calcular el vector de reflexión
        reflection_direction = glm.reflect(ray_direction, normal)

        # Calcular el vector de refracción
        eta = ior_air / ior_sphere
        cos_theta = max(0.0, -glm.dot(normal, ray_direction))
        sin_theta_squared = eta * eta * (1.0 - cos_theta * cos_theta)

        if sin_theta_squared > 1.0:  # Reflexión total interna
            refraction_direction = glm.vec3(0.0)
        else:
            refraction_direction = eta * ray_direction + (eta * cos_theta - math.sqrt(1.0 - sin_theta_squared)) * normal

        # Calcular la reflectancia de Fresnel
        r0 = ((ior_air - ior_sphere) / (ior_air + ior_sphere)) ** 2
        fresnel = r0 + (1.0 - r0) * pow(1.0 - max(0.0, -glm.dot(view_direction, normal)), 5.0)

        return reflection_direction, refraction_direction, fresnel


    def render_scene(self, width, height):
        aspect_ratio = width / height
        if not self.scene_has_changed():
            return self.last_image, self.ray_count

        image = QImage(width, height, QImage.Format_RGB32)
        ray_count = 0

        for y in range(height):
            for x in range(width):
                px = (x / width) * 2 - 1
                py = 1 - (y / height) * 2
                ray_direction = glm.normalize(glm.vec3(px * aspect_ratio, py, -1))

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
                            color = glm.vec3(1.0, 0.0, 0.0)
                            color = glm.clamp(color, 0.0, 1.0)
                            color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                            image.setPixel(x, y, qRgb(*color))
                            continue

                    if abs(denom) > 1e-6:
                        t_plane = -(glm.dot(self.camera_position, self.plane_normal) + self.plane_d) / denom
                        if t_plane > 0:
                            color = glm.vec3(0.5, 0.5, 0.5)
                            color = glm.clamp(color, 0.0, 1.0)
                            color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                            image.setPixel(x, y, qRgb(*color))
                            continue

                    # Render HDRI as black in simple mode
                    color = glm.vec3(0.0, 0.0, 0.0)
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
                        color = glm.vec3(0.5, 0.5, 0.5)
                        shadow_color = glm.vec3(*shadow_color)
                        color = glm.clamp(color + shadow_color, 0.0, 1.0)
                        color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                        image.setPixel(x, y, qRgb(*color))
                    elif t_sphere < float('inf'):
                        hit_point = self.camera_position + ray_direction * t_sphere
                        normal = glm.normalize(hit_point - self.sphere_center)
                        reflection_direction, refraction_direction, fresnel = self.compute_reflection_refraction(ray_direction, hit_point, normal)
                        # Calcular el color final
                        reflection_color = self.sample_hdri(reflection_direction)
                        refraction_color = (8.0, 0.1, 0.1)  
                        color = 0.1 * glm.vec3(*refraction_color) + 0.9 * glm.vec3(*reflection_color)
                        color = self.compute_lighting(hit_point, normal) * color
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

        self.last_image = image
        self.ray_count = ray_count
        self.update_last_parameters()
        return image, ray_count
