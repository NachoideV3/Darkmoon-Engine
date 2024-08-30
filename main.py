import sys
import math
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QImage, QPixmap, qRgb
from PyQt5.QtCore import Qt, QTimer
from PIL import Image

def dot(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

def subtract(v1, v2):
    return (v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2])

def add(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2])

def multiply(v, scalar):
    return (v[0] * scalar, v[1] * scalar, v[2] * scalar)

def normalize(v):
    length = math.sqrt(dot(v, v))
    if length == 0:
        return (0, 0, 0)
    return (v[0] / length, v[1] / length, v[2] / length)

class RayTracingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Darkmoon Engine')
        self.width, self.height = 1600, 900
        self.setGeometry(100, 100, self.width, self.height)

        # Configuraciones de la escena
        self.camera_position = (0, 3, 7)
        self.sphere_center = (0, 1, 0)
        self.sphere_radius = 1

        # Posicionar la luz detrás de la cámara y un poco hacia un lado
        self.light_position = (-3, 5, 9)  # Invertido respecto a la cámara
        self.light_intensity = 1.0
        self.plane_y = 0

        # Cargar la imagen HDRI
        self.hdri_image = self.load_hdri_image("meadow_2.jpg")

        # Contadores para rayos y tiempo
        self.ray_count = 0
        self.last_time = time.time()

        # QLabel para mostrar la imagen renderizada
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.width, self.height)

        # QLabel para mostrar los FPS y la cantidad de rayos
        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("color: white; font-size: 16px; background-color: rgba(0, 0, 0, 100%);")
        self.info_label.setGeometry(10, 10, 300, 30)

        # Temporizador para actualizar la escena
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(0)  # Actualiza tan rápido como sea posible

    def load_hdri_image(self, file_path):
        try:
            with Image.open(file_path) as img:
                img = img.convert('RGB')
                hdri_image = np.array(img, dtype=np.float32) / 255.0
            return hdri_image
        except Exception as e:
            print(f"Error loading image: {e}")
            hdri_width, hdri_height = 512, 256
            hdri_image = np.zeros((hdri_height, hdri_width, 3), dtype=np.float32)
            for y in range(hdri_height):
                for x in range(hdri_width):
                    hdri_image[y, x] = (x / hdri_width, y / hdri_height, 0.5)
            return hdri_image

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

    def update_scene(self):
        self.render_scene()
        current_time = time.time()
        elapsed_time = current_time - self.last_time
        self.last_time = current_time
        fps = 1.0 / elapsed_time if elapsed_time > 0 else 0
        self.info_label.setText(f"FPS: {fps:.2f} | Rays: {self.ray_count}")

    def render_scene(self):
        image = QImage(self.width, self.height, QImage.Format_RGB32)
        self.ray_count = 0

        for y in range(self.height):
            for x in range(self.width):
                px = (x / self.width) * 2 - 1
                py = 1 - (y / self.height) * 2
                ray_direction = normalize((px, py, -1))

                oc = subtract(self.camera_position, self.sphere_center)
                a = dot(ray_direction, ray_direction)
                b = 2.0 * dot(oc, ray_direction)
                c = dot(oc, oc) - self.sphere_radius * self.sphere_radius
                discriminant = b * b - 4 * a * c

                plane_normal = (0, 1, 0)
                plane_d = -self.plane_y
                denom = dot(ray_direction, plane_normal)

                self.ray_count += 1

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
                    color = tuple(int(min(max(c * 255, 0), 255)) for c in shadow_color)
                    image.setPixel(x, y, qRgb(*color))
                elif t_sphere < float('inf'):
                    hit_point = add(self.camera_position, multiply(ray_direction, t_sphere))
                    normal = normalize(subtract(hit_point, self.sphere_center))
                    reflection_direction = subtract(ray_direction, multiply(normal, 2 * dot(ray_direction, normal)))
                    reflection_color = self.sample_hdri(reflection_direction)
                    color = self.compute_lighting(hit_point, normal)
                    # Aplicar color metálico (rojo) con reflexión
                    metallic_color = (1.0, 0.0, 0.0)  # Rojo metálico
                    reflection_intensity = 0.5  # Ajustar la intensidad de la reflexión
                    color = add(multiply(metallic_color, 1 - reflection_intensity), multiply(reflection_color, reflection_intensity))
                    # Incrementar el brillo de la reflexión
                    color = multiply(color, 1.2)
                    color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                    image.setPixel(x, y, qRgb(*color))
                else:
                    color = self.sample_hdri(ray_direction)
                    # Incrementar el brillo de fondo para que contraste más
                    color = multiply(color, 1.2)
                    color = tuple(int(min(max(c * 255, 0), 255)) for c in color)
                    image.setPixel(x, y, qRgb(*color))

        self.label.setPixmap(QPixmap.fromImage(image))

    def compute_shadow(self, hit_point):
        shadow_ray_direction = subtract(self.light_position, hit_point)
        shadow_ray_direction = normalize(shadow_ray_direction)
        oc = subtract(hit_point, self.sphere_center)
        a = dot(shadow_ray_direction, shadow_ray_direction)
        b = 2.0 * dot(oc, shadow_ray_direction)
        c = dot(oc, oc) - self.sphere_radius * self.sphere_radius
        discriminant = b * b - 4 * a * c

        if discriminant >= 0:
            t = (-b - math.sqrt(discriminant)) / (2.0 * a)
            if 0 < t < 1:
                return (0.2, 0.2, 0.2)  # Sombra
        return (1.0, 1.0, 1.0)  # Luz completa

    def compute_lighting(self, hit_point, normal):
        light_direction = subtract(self.light_position, hit_point)
        light_direction = normalize(light_direction)
        ambient = 0.1
        diffuse = max(dot(normal, light_direction), 0)
        color = add(multiply((1.0, 1.0, 1.0), ambient + diffuse), (0.2, 0.2, 0.2))
        return color

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RayTracingWindow()
    window.show()
    sys.exit(app.exec_())
