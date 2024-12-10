import cv2
import numpy as np
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFileDialog, QSlider)
from PyQt5.QtGui import QImage, QPixmap
from .tools import DrawingTool

class BackgroundRemovalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.mask = None
        self.rect = None
        self.drawing = False
        self.result_image = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("배경 제거")
        layout = QVBoxLayout()
        
        # 안내 메시지
        self.info_label = QLabel("마우스로 전경 영역을 드래그하여 선택하세요")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # 이미지 표시 영역
        self.image_label = QLabel()
        self.image_label.setMinimumSize(600, 400)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.mousePressEvent = self.on_mouse_press
        self.image_label.mouseMoveEvent = self.on_mouse_move
        self.image_label.mouseReleaseEvent = self.on_mouse_release
        layout.addWidget(self.image_label)
        
        # 반복 횟수 조절 슬라이더
        slider_layout = QHBoxLayout()
        slider_label = QLabel("반복 횟수:")
        self.iter_slider = QSlider(Qt.Horizontal)
        self.iter_slider.setMinimum(1)
        self.iter_slider.setMaximum(10)
        self.iter_slider.setValue(5)
        self.iter_value = QLabel("5")
        self.iter_slider.valueChanged.connect(
            lambda v: self.iter_value.setText(str(v)))
        
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.iter_slider)
        slider_layout.addWidget(self.iter_value)
        layout.addLayout(slider_layout)
        
        # 버튼들
        btn_layout = QHBoxLayout()
        
        self.remove_btn = QPushButton("배경 제거")
        self.remove_btn.clicked.connect(self.remove_background)
        self.remove_btn.setEnabled(False)
        
        self.reset_btn = QPushButton("초기화")
        self.reset_btn.clicked.connect(self.reset)
        
        self.ok_btn = QPushButton("확인")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def set_image(self, image):
        self.image = image.copy()
        self.display_image(self.image)
        self.mask = np.zeros(self.image.shape[:2], np.uint8)
    
    def display_image(self, image):
        if image is not None:
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
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
    
    def get_image_position(self, pos):
        if self.image_label.pixmap():
            rect = self.image_label.geometry()
            scaled_rect = self.image_label.pixmap().rect()
            
            x_offset = (rect.width() - scaled_rect.width()) // 2
            y_offset = (rect.height() - scaled_rect.height()) // 2
            
            x = pos.x() - x_offset
            y = pos.y() - y_offset
            
            if (0 <= x < scaled_rect.width() and 
                0 <= y < scaled_rect.height()):
                scale_x = self.image.shape[1] / scaled_rect.width()
                scale_y = self.image.shape[0] / scaled_rect.height()
                
                real_x = int(x * scale_x)
                real_y = int(y * scale_y)
                
                return (real_x, real_y)
        return None
    
    def on_mouse_press(self, event):
        pos = self.get_image_position(event.pos())
        if pos:
            self.drawing = True
            self.rect = [pos[0], pos[1], 0, 0]
            self.display_with_rect()
    
    def on_mouse_move(self, event):
        if self.drawing:
            pos = self.get_image_position(event.pos())
            if pos:
                self.rect[2] = pos[0] - self.rect[0]
                self.rect[3] = pos[1] - self.rect[1]
                self.display_with_rect()
    
    def on_mouse_release(self, event):
        if self.drawing:
            self.drawing = False
            self.remove_btn.setEnabled(True)
    
    def display_with_rect(self):
        if self.rect is not None:
            display = self.image.copy()
            x, y, w, h = self.rect
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
            self.display_image(display)
    
    def remove_background(self):
        if self.rect is not None:
            x, y, w, h = self.rect
            if w < 0:
                x, w = x + w, -w
            if h < 0:
                y, h = y + h, -h
                
            # GrabCut 초기화
            self.mask = np.zeros(self.image.shape[:2], np.uint8)
            rect = (x, y, w, h)
            bgd_model = np.zeros((1,65), np.float64)
            fgd_model = np.zeros((1,65), np.float64)
            
            # GrabCut 실행
            cv2.grabCut(self.image, self.mask, rect, 
                       bgd_model, fgd_model, 
                       self.iter_slider.value(), 
                       cv2.GC_INIT_WITH_RECT)
            
            # 마스크 생성
            mask2 = np.where((self.mask==2)|(self.mask==0), 0, 1).astype('uint8')
            
            # 배경을 흰색으로
            self.result_image = self.image.copy()
            self.result_image[mask2 == 0] = [255, 255, 255]
            
            self.display_image(self.result_image)
            self.ok_btn.setEnabled(True)
    
    def reset(self):
        if self.image is not None:
            self.rect = None
            self.mask = np.zeros(self.image.shape[:2], np.uint8)
            self.result_image = None
            self.display_image(self.image)
            self.remove_btn.setEnabled(False)
            self.ok_btn.setEnabled(False)

class BackgroundRemovalTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.result_image = None
        
    def remove_background(self, image):
        dialog = BackgroundRemovalDialog()
        dialog.set_image(image)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.result_image
        return None
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image 