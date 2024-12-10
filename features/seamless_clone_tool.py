import cv2
import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFileDialog, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from .tools import DrawingTool

class SeamlessCloneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_image = None
        self.target_image = None
        self.clone_mode = cv2.NORMAL_CLONE
        self.center_pos = None  # 합성 위치 저장
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("자연스러운 합성")
        layout = QVBoxLayout()
        
        # 이미지 선택 버튼들
        btn_layout = QHBoxLayout()
        self.source_btn = QPushButton("합성할 이미지 선택")
        self.target_btn = QPushButton("배경 이미지 선택")
        self.source_btn.clicked.connect(lambda: self.select_image('source'))
        self.target_btn.clicked.connect(lambda: self.select_image('target'))
        btn_layout.addWidget(self.source_btn)
        btn_layout.addWidget(self.target_btn)
        layout.addLayout(btn_layout)
        
        # 이미지 표시 영역
        self.image_label = QLabel()
        self.image_label.setMinimumSize(600, 400)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.mousePressEvent = self.on_image_click
        layout.addWidget(self.image_label)
        
        # 안내 메지
        self.info_label = QLabel("배경 이미지에서 합성할 위치를 클릭하세요")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # 합성 모드 선택
        mode_layout = QHBoxLayout()
        mode_label = QLabel("합성 모드:")
        self.normal_mode = QRadioButton("Normal")
        self.mixed_mode = QRadioButton("Mixed")
        self.normal_mode.setChecked(True)
        
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.normal_mode)
        mode_group.addButton(self.mixed_mode)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.normal_mode)
        mode_layout.addWidget(self.mixed_mode)
        layout.addLayout(mode_layout)
        
        # 확인/취소 버튼
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("확인")
        self.cancel_btn = QPushButton("취소")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn.setEnabled(False)  # 초기에는 비활성화
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def select_image(self, img_type):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"이미지 선택", "", 
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)")
        if file_path:
            image = cv2.imread(file_path)
            if image is not None:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                if img_type == 'source':
                    self.source_image = image
                    self.source_btn.setText("✓ 합성할 이미지")
                else:
                    self.target_image = image
                    self.target_btn.setText("✓ 배경 이미지")
                    self.display_target_image()  # 배경 이미지 표시
                
                # 위치 선택 전까지는 확인 버튼 비활성화
                self.ok_btn.setEnabled(False)
    
    def display_target_image(self):
        if self.target_image is not None:
            height, width = self.target_image.shape[:2]
            bytes_per_line = 3 * width
            
            q_img = QImage(
                self.target_image.data,
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
        """위젯 좌표를 이미지 좌표로 변환"""
        if self.image_label.pixmap():
            rect = self.image_label.geometry()
            scaled_rect = self.image_label.pixmap().rect()
            
            x_offset = (rect.width() - scaled_rect.width()) // 2
            y_offset = (rect.height() - scaled_rect.height()) // 2
            
            x = pos.x() - x_offset
            y = pos.y() - y_offset
            
            if (0 <= x < scaled_rect.width() and 
                0 <= y < scaled_rect.height()):
                # 스케일 비율 계산
                scale_x = self.target_image.shape[1] / scaled_rect.width()
                scale_y = self.target_image.shape[0] / scaled_rect.height()
                
                # 실제 이미지 좌표로 변환
                real_x = int(x * scale_x)
                real_y = int(y * scale_y)
                
                return (real_x, real_y)
        return None
    
    def on_image_click(self, event):
        if self.source_image is not None and self.target_image is not None:
            pos = self.get_image_position(event.pos())
            if pos:
                self.center_pos = pos
                self.ok_btn.setEnabled(True)
                # 미리보기 표시
                self.show_preview()
    
    def show_preview(self):
        """합성 미리보기 표시"""
        if (self.source_image is not None and 
            self.target_image is not None and 
            self.center_pos is not None):
            result = self.apply_seamless_clone()
            if result is not None:
                height, width = result.shape[:2]
                bytes_per_line = 3 * width
                
                q_img = QImage(
                    result.data,
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
    
    def apply_seamless_clone(self):
        if (self.source_image is not None and 
            self.target_image is not None and 
            self.center_pos is not None):
            # 마스크 생성
            mask = np.full_like(self.source_image, 255)
            
            # 소스 이미지 크기 조정
            source_height, source_width = self.source_image.shape[:2]
            target_height, target_width = self.target_image.shape[:2]
            scale = min(0.3 * target_width/source_width, 0.3 * target_height/source_height)
            new_width = int(source_width * scale)
            new_height = int(source_height * scale)
            self.source_image = cv2.resize(self.source_image, (new_width, new_height))
            mask = cv2.resize(mask, (new_width, new_height))
            
            # 합성 모드 설정
            mode = cv2.MIXED_CLONE if self.mixed_mode.isChecked() else cv2.NORMAL_CLONE
            
            try:
                result = cv2.seamlessClone(
                    self.source_image, 
                    self.target_image, 
                    mask, 
                    self.center_pos, 
                    mode
                )
                return result
            except cv2.error:
                return None

class SeamlessCloneTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.result_image = None
        
    def apply_seamless_clone(self, dialog):
        self.result_image = dialog.apply_seamless_clone()
        return self.result_image
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image 