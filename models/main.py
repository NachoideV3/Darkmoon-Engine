import sys
import time
import os
os.environ['QT_QPA_PLATFORM'] = 'xcb'
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from loading import LoadScreen
from render_engine import Renderer  # Importar Renderer
from ImageLoader import ImageLoader

class RayTracingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Darkmoon Engine')
        self.width, self.height = 1600, 900
        self.setGeometry(100, 100, self.width, self.height)

        self.load_screen = LoadScreen(self)
        self.load_screen.loading()

    def setupMainUI(self):
        self.camera_position = (0, 3, 7)
        self.sphere_center = (0, 2, 0)
        self.sphere_radius = 2
        self.light_position = (-3, 5, 9)
        self.light_intensity = 1.0
        self.plane_y = 0
        self.hdri_image = ImageLoader.load_image("hdri/meadow_2.jpg")

        self.renderer = Renderer(
            self.camera_position,
            self.sphere_center,
            self.sphere_radius,
            self.light_position,
            self.light_intensity,
            self.plane_y,
            self.hdri_image,
            use_ray_tracing=False
        )
        self.ray_count = 0
        self.last_time = time.time()

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.width, self.height)

        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("color: white; font-size: 16px; background-color: rgba(0, 0, 0, 100%);")
        self.info_label.setGeometry(10, 10, 300, 30)

        self.toggle_ray_tracing_button = QPushButton('Toggle RT', self)
        self.toggle_ray_tracing_button.setGeometry(self.width - 200, 10, 190, 30)
        self.toggle_ray_tracing_button.clicked.connect(self.toggle_ray_tracing)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(0)

    def toggle_ray_tracing(self):
        # Alterna entre ray tracing y renderizado simple
        #self.load_screen.show()
        self.renderer.use_ray_tracing = not self.renderer.use_ray_tracing
        state = "ON" if self.renderer.use_ray_tracing else "OFF"
        self.info_label.setText(f"RT {state} | FPS: {self.info_label.text().split('|')[1]}")

    def update_scene(self):
        image, self.ray_count = self.renderer.render_scene(self.width, self.height)
        self.label.setPixmap(QPixmap.fromImage(image))
        
        current_time = time.time()
        elapsed_time = current_time - self.last_time
        self.last_time = current_time
        fps = 1.0 / elapsed_time if elapsed_time > 0 else 0
        self.info_label.setText(f"FPS: {fps:.2f} | Rays: {self.ray_count} | RT {'ON' if self.renderer.use_ray_tracing else 'OFF'}")
        self.current_fps = fps

    def get_fps(self):
        return getattr(self, 'current_fps', 0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RayTracingWindow()
    sys.exit(app.exec_())
