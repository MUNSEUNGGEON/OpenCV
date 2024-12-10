from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import cv2
import numpy as np

class PanoramaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("파노라마 생성")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # 이미지 저장 변수
        self.image1 = None
        self.image2 = None
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 이미지 선택 영역
        image_layout = QHBoxLayout()
        
        # 첫 번째 이미지
        img1_layout = QVBoxLayout()
        self.img1_label = QLabel("이미지 1")
        self.img1_label.setAlignment(Qt.AlignCenter)
        self.img1_label.setMinimumSize(150, 150)
        self.img1_label.setStyleSheet("border: 1px solid #333333;")
        img1_button = QPushButton("이미지 1 선택")
        img1_button.clicked.connect(lambda: self.select_image(1))
        img1_layout.addWidget(self.img1_label)
        img1_layout.addWidget(img1_button)
        
        # 두 번째 이미지
        img2_layout = QVBoxLayout()
        self.img2_label = QLabel("이미지 2")
        self.img2_label.setAlignment(Qt.AlignCenter)
        self.img2_label.setMinimumSize(150, 150)
        self.img2_label.setStyleSheet("border: 1px solid #333333;")
        img2_button = QPushButton("이미지 2 선택")
        img2_button.clicked.connect(lambda: self.select_image(2))
        img2_layout.addWidget(self.img2_label)
        img2_layout.addWidget(img2_button)
        
        image_layout.addLayout(img1_layout)
        image_layout.addLayout(img2_layout)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        create_button = QPushButton("파노라마 생성")
        create_button.clicked.connect(self.accept)
        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(create_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(image_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def select_image(self, img_num):
        file_name, _ = QFileDialog.getOpenFileName(
            self, f"이미지 {img_num} 선택", "", 
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_name:
            image = cv2.imread(file_name)
            if image is not None:
                # BGR to RGB 변환
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # 이미지 저장
                if img_num == 1:
                    self.image1 = image
                else:
                    self.image2 = image
                
                # 미리보기 표시
                h, w = image.shape[:2]
                aspect = w / h
                preview_h = 150
                preview_w = int(preview_h * aspect)
                
                preview = cv2.resize(image, (preview_w, preview_h))
                h, w = preview.shape[:2]
                
                q_img = QImage(preview.data, w, h, 3 * w, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)
                
                if img_num == 1:
                    self.img1_label.setPixmap(pixmap)
                else:
                    self.img2_label.setPixmap(pixmap)
            else:
                QMessageBox.warning(self, "오류", "이미지를 불러오는데 실패했습니다.")