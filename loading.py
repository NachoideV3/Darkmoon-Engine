# loading.py

import time
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from PIL import Image

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

    def __init__(self):
        super().__init__()
        self.hdri_image = None

    def run(self):
        # Aquí carga la escena de manera real
        self.hdri_image = self.load_hdri_image("meadow_2.jpg")
        # Simula un trabajo real de carga
        time.sleep(2)  # Aquí deberías reemplazarlo con el proceso real de carga
        self.update_signal.emit()

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
