import sys
import math
import time
import os
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap, qRgb
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PIL import Image

os.environ['QT_QPA_PLATFORM'] = 'xcb'

class LoadScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Darkmoon Engine Loading')
        self.setGeometry(100, 100, 1280, 720)
        layout = QVBoxLayout()
        self.label = QLabel('Loading Scene, please wait...', self)
        layout.addWidget(self.label)
        self.setLayout(layout)

class RayTracingWorker(QThread):
    update_signal = pyqtSignal()

    def run(self):
        # Simulate a long-running process
        time.sleep(2)  # Replace this with actual initialization
        self.update_signal.emit()

class RayTracingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Darkmoon Engine')
        self.width, self.height = 1600, 900
        self.setGeometry(100, 100, self.width, self.height)

        # Initialize the screen and load worker
        self.load_screen = LoadScreen()
        self.load_screen.show()

        self.worker = RayTracingWorker()
        self.worker.update_signal.connect(self.on_loading_complete)
        self.worker.start()

    def on_loading_complete(self):
        self.load_screen.close()
        self.setupMainUI()
        self.show()

    def setupMainUI(self):
        self.camera_position = (0, 3, 7)
        self.sphere_center = (0, 1, 0)
        self.sphere_radius = 1
        self.light_position = (-3, 5, 9)
        self.light_intensity = 1.0
        self.plane_y = 0
        self.hdri_image = self.load_hdri_image("meadow_2.jpg")
        self.ray_count = 0
        self.last_time = time.time()

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.width, self.height)

        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("color: white; font-size: 16px; background-color: rgba(0, 0, 0, 100%);")
        self.info_label.setGeometry(10, 10, 300, 30)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(0)

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

        self.label.setPixmap(QPixmap.fromImage(image))

    def compute_shadow(self, hit_point):
        shadow_ray_direction = subtract(self.light_position, hit_point)
        shadow_ray_direction = normalize(shadow_ray_direction)
        
        oc = subtract(hit_point, self.sphere_center)
        a = dot(shadow_ray_direction, shadow_ray_direction)
        b = 2.0 * dot(oc, shadow_ray_direction)
        c = dot(oc, oc) - self.sphere_radius * self.sphere_radius
        discriminant = b * b - 4 * a * c

        shadow_intensity = 1.0  # Inicialmente no hay sombra

        if discriminant >= 0:
            t_sphere = (-b - math.sqrt(discriminant)) / (2.0 * a)
            if t_sphere > 0:
                shadow_intensity = 0.3  # Ajusta la intensidad de la sombra según la distancia

        indirect_light = 0.2  # Ajusta según sea necesario
        shadow_intensity = shadow_intensity * (1 - indirect_light)
        
        return (shadow_intensity, shadow_intensity, shadow_intensity)

    def compute_lighting(self, hit_point, normal):
        light_direction = normalize(subtract(self.light_position, hit_point))
        ambient_intensity = 0.1
        diffuse_intensity = max(dot(normal, light_direction), 0.0)
        reflection_direction = subtract(light_direction, multiply(normal, 2 * dot(light_direction, normal)))
        specular_intensity = max(dot(reflection_direction, normalize(subtract(self.camera_position, hit_point))), 0.0)
        specular_intensity = specular_intensity ** 16
        
        shadow_intensity = self.compute_shadow(hit_point)[0]

        color = multiply((ambient_intensity + shadow_intensity * diffuse_intensity + specular_intensity), (1.0, 1.0, 1.0))
        return color

# Helper functions
def subtract(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def multiply(a, b):
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return (a[0] * b[0], a[1] * b[1], a[2] * b[2])
    elif isinstance(a, (tuple, list)) and isinstance(b, (int, float)):
        return (a[0] * b, a[1] * b, a[2] * b)
    elif isinstance(a, (int, float)) and isinstance(b, (tuple, list)):
        return (a * b[0], a * b[1], a * b[2])
    else:
        raise ValueError("Arguments must be either both tuples/lists or one tuple/list and one number")


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def normalize(v):
    length = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / length, v[1] / length, v[2] / length)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RayTracingWindow()
    sys.exit(app.exec_())
