import cv2
import numpy as np
from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

class CameraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.setup_camera()
        
    def setup_ui(self):
        self.setWindowTitle("카메라")
        self.setFixedSize(800, 600)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        
        # 카메라 미리보기
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_label)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        self.capture_button = QPushButton(" 촬영")
        self.capture_button.clicked.connect(self.capture_image)
        
        self.close_button = QPushButton("닫기")
        self.close_button.clicked.connect(self.close_camera)
        
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def setup_camera(self):
        self.camera = cv2.VideoCapture(0)  # 기본 카메라 사용
        if not self.camera.isOpened():
            print("카메라를 열 수 없습니다.")
            self.close()
            return
            
        # 타이머 설정 (30fps)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)
        
    def update_frame(self):
        ret, frame = self.camera.read()
        if ret:
            # OpenCV BGR -> RGB 변환
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 미리보기 크기에 맞게 조정
            height, width = frame.shape[:2]
            preview_size = self.preview_label.size()
            
            # 비율 유지하면서 크기 조정
            scale = min(preview_size.width() / width, preview_size.height() / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            frame = cv2.resize(frame, (new_width, new_height))
            
            # QImage로 변환
            image = QImage(frame.data, new_width, new_height, 
                         new_width * 3, QImage.Format_RGB888)
            
            self.preview_label.setPixmap(QPixmap.fromImage(image))
            
    def capture_image(self):
        ret, frame = self.camera.read()
        if ret:
            # BGR -> RGB 변환
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 메인 윈도우에 이미지 전달
            if self.parent:
                self.parent.set_current_image(frame)
            
            # 촬영 후 카메라 창 닫기
            self.close_camera()
            
    def close_camera(self):
        self.timer.stop()
        self.camera.release()
        self.close() 