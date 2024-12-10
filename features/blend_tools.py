import cv2
import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QSlider, QVBoxLayout, QLabel, QWidget, QDialog, QPushButton, QFileDialog, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from .tools import DrawingTool

class ImageSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image1 = None
        self.image2 = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("이미지 선택")
        layout = QVBoxLayout()
        
        # 이미지 선택 버튼들
        btn_layout = QHBoxLayout()
        self.select_btn1 = QPushButton("첫 번째 이미지 선택")
        self.select_btn2 = QPushButton("두 번째 이미지 선택")
        self.select_btn1.clicked.connect(lambda: self.select_image(1))
        self.select_btn2.clicked.connect(lambda: self.select_image(2))
        btn_layout.addWidget(self.select_btn1)
        btn_layout.addWidget(self.select_btn2)
        layout.addLayout(btn_layout)
        
        # 확인/취소 버튼
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("확인")
        self.cancel_btn = QPushButton("취소")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def select_image(self, image_num):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"이미지 {image_num} 선택", "", 
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)")
        if file_path:
            image = cv2.imread(file_path)
            if image is not None:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                if image_num == 1:
                    self.image1 = image
                    self.select_btn1.setText("✓ 첫 번째 이미지")
                else:
                    self.image2 = image
                    self.select_btn2.setText("✓ 두 번째 이미지")
                
                if self.image1 is not None and self.image2 is not None:
                    self.ok_btn.setEnabled(True)

class BlendTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.image1 = None
        self.image2 = None
        self.alpha = 0.5
        self.slider_widget = None
        
    def setup_slider(self, parent):
        """알파값 조절을 위한 슬라이더 위젯 설정"""
        self.slider_widget = QWidget(parent)
        layout = QVBoxLayout()
        
        # 라벨 추가
        label = QLabel("블렌딩 비율")
        label.setStyleSheet("font-weight: bold; border-bottom: 1px solid #ddd;")
        layout.addWidget(label)
        
        # 슬라이더
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(int(self.alpha * 100))
        self.slider.valueChanged.connect(self.update_alpha)
        layout.addWidget(self.slider)
        
        # 값 표시 라벨
        self.value_label = QLabel(f"{int(self.alpha * 100)}%")
        layout.addWidget(self.value_label)
        
        self.slider_widget.setLayout(layout)
        return self.slider_widget
    
    def update_alpha(self, value):
        """슬라이더 값이 변경될 때 호출"""
        self.alpha = value / 100
        self.value_label.setText(f"{value}%")
        if hasattr(self, 'parent') and self.parent:
            self.parent.current_image = self.blend_images(
                self.parent.current_image.copy())
            self.parent.update_image_display()
    
    def set_images(self, image1, image2):
        """합성할 이미지들 설정"""
        if image1 is not None and image2 is not None:
            h1, w1 = image1.shape[:2]
            h2, w2 = image2.shape[:2]
            target_size = (max(w1, w2), max(h1, h2))
            self.image1 = cv2.resize(image1, target_size)
            self.image2 = cv2.resize(image2, target_size)
    
    def set_parent(self, parent):
        """부모 윈도우 설정"""
        self.parent = parent
    
    def blend_images(self, image):
        """이미지 합성"""
        if self.image1 is not None and self.image2 is not None:
            return cv2.addWeighted(self.image1, 1-self.alpha, self.image2, self.alpha, 0)
        return image
    
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return self.blend_images(image)
    
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image
    
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image