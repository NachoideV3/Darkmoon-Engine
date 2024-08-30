import sys
import math
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
from PIL import Image  # Asegúrate de tener Pillow instalado

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
    return (v[0] / length, v[1] / length, v[2] / length)

class RayTracingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Darkmoon Engine')
        self.width, self.height = 1280, 720
        self.setGeometry(100, 100, self.width, self.height)

        # Configuraciones de la escena
        self.camera_position = (0, 0, -1)
        self.sphere_center = (0, 0, 3)
        self.sphere_radius = 1
        self.light_position = (5, 5, -10)
        self.light_intensity = 1.0
        self.sphere_position = (5, 5, -10)
        self.plane_y = 2  # Altura del plano (piso)

        # Cargar la imagen JPG
        self.hdri_image = self.load_hdri_image("symmetrical_garden_02.jpg")

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
            # Cargar la imagen JPG usando PIL
            with Image.open(file_path) as img:
                img = img.convert('RGB')  # Asegúrate de que la imagen esté en formato RGB
                hdri_image = np.array(img, dtype=np.float32) / 255.0  # Normalizar a [0, 1]
            return hdri_image
        except Exception as e:
            print(f"Error loading image: {e}")
            # Si no se puede cargar la imagen, volver al gradiente simple
            hdri_width, hdri_height = 512, 256
            hdri_image = np.zeros((hdri_height, hdri_width, 3), dtype=np.float32)
            for y in range(hdri_height):
                for x in range(hdri_width):
                    hdri_image[y, x] = (x / hdri_width, y / hdri_height, 0.5)  # Gradiente simple
            return hdri_image

    def sample_hdri(self, direction):
        # Convertir la dirección en coordenadas esféricas
        theta = math.acos(direction[1])  # Ángulo polar
        phi = math.atan2(direction[2], direction[0])  # Ángulo azimutal
        phi = phi if phi >= 0 else (2 * math.pi + phi)  # Ajustar a rango [0, 2*pi]

        # Mapear a coordenadas de la imagen
        u = phi / (2 * math.pi)
        v = theta / math.pi

        v = 1 - v

        # Convertir a coordenadas de pixel
        x = int(u * self.hdri_image.shape[1])
        y = int(v * self.hdri_image.shape[0])

        # Obtener el color del JPG
        color = self.hdri_image[y % self.hdri_image.shape[0], x % self.hdri_image.shape[1]]
        return (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))

    def update_scene(self):
        self.render_scene()

        # Calcular FPS
        current_time = time.time()
        elapsed_time = current_time - self.last_time
        self.last_time = current_time
        fps = 1.0 / elapsed_time if elapsed_time > 0 else 0

        # Actualizar QLabel con FPS y cantidad de rayos
        self.info_label.setText(f"FPS: {fps:.2f} | Rays: {self.ray_count}")
    def render_scene(self):
        # Crear una imagen en blanco
        image = QImage(self.width, self.height, QImage.Format_RGB32)
        self.ray_count = 0  # Reiniciar contador de rayos para cada cuadro

        # Ray tracing simple
        for y in range(self.height):
            for x in range(self.width):
                # Calcular el rayo de visión
                px = (x / self.width) * 2 - 1
                py = (y / self.height) * 2 - 1
                ray_direction = normalize((px, py, 1))

                # Calcular la intersección con la esfera
                oc = subtract(self.camera_position, self.sphere_center)
                a = dot(ray_direction, ray_direction)
                b = 2.0 * dot(oc, ray_direction)
                c = dot(oc, oc) - self.sphere_radius * self.sphere_radius
                discriminant = b * b - 4 * a * c

                # Calcular la intersección con el plano
                plane_normal = (0, 1, 0)  # Normal del plano (piso)
                plane_d = -self.plane_y  # Distancia del plano al origen
                denom = dot(ray_direction, plane_normal)

                self.ray_count += 1  # Incrementar contador de rayos

                # Inicializar valores para comparación
                t_sphere = float('inf')
                t_plane = float('inf')

                # Calcular intersección con la esfera
                if discriminant >= 0:
                    t_sphere = (-b - math.sqrt(discriminant)) / (2.0 * a)

                # Calcular intersección con el plano
                if abs(denom) > 1e-6:  # Evitar divisiones por cero
                    t_plane = -(dot(self.camera_position, plane_normal) + plane_d) / denom

                if t_plane > 0 and (t_plane < t_sphere or t_sphere == float('inf')):
                    # Renderizar plano
                    plane_hit_point = add(self.camera_position, multiply(ray_direction, t_plane))
                    color = (0.5, 0.5, 0.5)  # Color del piso
                    color = tuple(int(c * 255) for c in color)
                    image.setPixel(x, y, qRgb(*color))
                elif t_sphere < float('inf'):
                    # Renderizar esfera
                    hit_point = add(self.camera_position, multiply(ray_direction, t_sphere))
                    normal = normalize(subtract(hit_point, self.sphere_center))
                    light_dir = normalize(subtract(self.light_position, hit_point))

                    # Calcular iluminación difusa
                    diff = max(dot(normal, light_dir), 0) * self.light_intensity

                    # Calcular reflexión de la imagen de fondo
                    reflection_dir = subtract(ray_direction, multiply(normal, 2 * dot(ray_direction, normal)))
                    reflection_color = self.sample_hdri(reflection_dir)

                    # Combinar iluminación difusa y reflexión
                    color = multiply(add(reflection_color, (diff, diff, diff)), 0.5)
                    color = tuple(int(c * 255) for c in color)
                    image.setPixel(x, y, qRgb(*color))
                else:
                    # Usar el JPG como fondo
                    bg_color = self.sample_hdri(ray_direction)
                    image.setPixel(x, y, qRgb(*bg_color))

        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)
    

def qRgb(r, g, b):
    """ Helper function to convert RGB values to the integer representation """
    return (r << 16) + (g << 8) + b

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RayTracingWindow()
    window.show()
    sys.exit(app.exec_())
