import time
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QPixmap
import sys

class LoadScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Darkmoon Engine Loading')
        
        # Establecer un tamaño más pequeño para el splash screen
        self.setFixedSize(800, 400)
        
        # Eliminar los bordes y la barra de título
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Establecer color de fondo
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150); border: 2px solid white;")
        
        layout = QVBoxLayout()
        
        # Añadir texto
        self.label = QLabel('Loading Scene, please wait...', self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 18px;")
        layout.addWidget(self.label)

        self.setLayout(layout)
        
        # Centrar la ventana en la pantalla
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        QTimer.singleShot(0, self.main_window.setupMainUI)

    def loading(self):
        self.show()
        self.main_window.hide()
        fps = self.main_window.get_fps()
        if isinstance(fps, (int, float)) and fps > 0:
            self.hide()
            self.main_window.show()
        else:
            QTimer.singleShot(1, self.loading)
        
