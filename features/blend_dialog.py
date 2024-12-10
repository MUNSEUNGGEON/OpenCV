import cv2
import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QSlider, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

class BlendDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image1 = None
        self.image2 = None
        self.result_image = None
        self.alpha = 0.5
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("이미지 블렌딩")
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
        
        # 이미지 표시 영역들
        image_layout = QHBoxLayout()
        self.image_label1 = QLabel("이미지 1")
        self.image_label2 = QLabel("이미지 2")
        self.result_label = QLabel("결과")
        for label in [self.image_label1, self.image_label2, self.result_label]:
            label.setMinimumSize(300, 200)
            label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_label1)
        image_layout.addWidget(self.image_label2)
        image_layout.addWidget(self.result_label)
        layout.addLayout(image_layout)
        
        # 슬라이더
        slider_layout = QHBoxLayout()
        slider_label = QLabel("블렌딩 비율:")
        self.value_label = QLabel("50%")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)
        self.slider.valueChanged.connect(self.update_alpha)
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.value_label)
        layout.addLayout(slider_layout)
        
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
                    self.display_image(self.image_label1, image)
                else:
                    self.image2 = image
                    self.display_image(self.image_label2, image)
                
                if self.image1 is not None and self.image2 is not None:
                    # 두 이미지의 크기를 맞춤
                    h1, w1 = self.image1.shape[:2]
                    h2, w2 = self.image2.shape[:2]
                    target_size = (max(w1, w2), max(h1, h2))
                    self.image1 = cv2.resize(self.image1, target_size)
                    self.image2 = cv2.resize(self.image2, target_size)
                    self.update_blend()
    
    def update_alpha(self, value):
        self.alpha = value / 100
        self.value_label.setText(f"{value}%")
        self.update_blend()
    
    def update_blend(self):
        if self.image1 is not None and self.image2 is not None:
            self.result_image = cv2.addWeighted(
                self.image1, 1-self.alpha,
                self.image2, self.alpha, 0)
            self.display_image(self.result_label, self.result_image)
    
    def display_image(self, label, image):
        height, width = image.shape[:2]
        bytes_per_line = 3 * width
        
        q_img = QImage(
            image.data,
            width, height,
            bytes_per_line,
            QImage.Format_RGB888
        )
        
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap) 