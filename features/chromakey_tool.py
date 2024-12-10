import cv2
import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QSpinBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from .tools import DrawingTool

class ChromakeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_image = None
        self.foreground_image = None
        self.offset = 20
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("크로마키 합성")
        layout = QVBoxLayout()
        
        # 이미지 선택 버튼들
        btn_layout = QHBoxLayout()
        self.fg_btn = QPushButton("전경 이미지 선택 (크로마키)")
        self.bg_btn = QPushButton("배경 이미지 선택")
        self.fg_btn.clicked.connect(lambda: self.select_image('fg'))
        self.bg_btn.clicked.connect(lambda: self.select_image('bg'))
        btn_layout.addWidget(self.fg_btn)
        btn_layout.addWidget(self.bg_btn)
        layout.addLayout(btn_layout)
        
        # 이미지 미리보기 레이블
        preview_layout = QHBoxLayout()
        self.fg_preview = QLabel("전경 이미지")
        self.bg_preview = QLabel("배경 이미지")
        self.fg_preview.setMinimumSize(200, 150)
        self.bg_preview.setMinimumSize(200, 150)
        self.fg_preview.setAlignment(Qt.AlignCenter)
        self.bg_preview.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.fg_preview)
        preview_layout.addWidget(self.bg_preview)
        layout.addLayout(preview_layout)
        
        # offset 조절
        offset_layout = QHBoxLayout()
        offset_label = QLabel("색상 범위:")
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(1, 50)
        self.offset_spin.setValue(20)
        self.offset_spin.valueChanged.connect(self.update_offset)
        offset_layout.addWidget(offset_label)
        offset_layout.addWidget(self.offset_spin)
        layout.addLayout(offset_layout)
        
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
        
    def select_image(self, img_type):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"이미지 선택", "", 
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)")
        if file_path:
            image = cv2.imread(file_path)
            if image is not None:
                if img_type == 'fg':
                    self.foreground_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    self.fg_btn.setText("✓ 전경 이미지")
                    self.update_preview(self.fg_preview, self.foreground_image)
                else:
                    self.background_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    self.bg_btn.setText("✓ 배경 이미지")
                    self.update_preview(self.bg_preview, self.background_image)
                
                if self.foreground_image is not None and self.background_image is not None:
                    self.ok_btn.setEnabled(True)
    
    def update_preview(self, label, image):
        """이미지 미리보기 업데이트"""
        if image is None:
            return
            
        # 레이블 크기에 맞게 이미지 크기 조정
        h, w = image.shape[:2]
        label_w = label.width()
        label_h = label.height()
        
        # 비율 유지하면서 크기 조정
        scale = min(label_w/w, label_h/h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 이미지 리사이즈
        resized = cv2.resize(image, (new_w, new_h))
        
        # QImage로 변환
        h, w, ch = resized.shape
        bytes_per_line = ch * w
        qt_image = QImage(resized.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # QPixmap으로 변환하여 레이블에 표시
        pixmap = QPixmap.fromImage(qt_image)
        label.setPixmap(pixmap)
    
    def update_offset(self, value):
        self.offset = value
    
    def apply_chromakey(self):
        if self.foreground_image is None or self.background_image is None:
            return None
            
        # 이미지 크기 조정
        fg = self.foreground_image
        bg = self.background_image
        h1, w1 = fg.shape[:2]
        h2, w2 = bg.shape[:2]
        
        # 전경 이미지를 배경 이미지 크기에 맞게 조정
        scale = min(w2/w1, h2/h1)
        new_w = int(w1 * scale)
        new_h = int(h1 * scale)
        fg = cv2.resize(fg, (new_w, new_h))
        
        # 중앙 정렬을 위한 좌표 계산
        x = (w2 - new_w) // 2
        y = (h2 - new_h) // 2
        
        # 크로마키 영역 추출
        chromakey = fg[:10, :10, :]
        
        # HSV 변환
        hsv_chroma = cv2.cvtColor(chromakey, cv2.COLOR_RGB2HSV)
        hsv_fg = cv2.cvtColor(fg, cv2.COLOR_RGB2HSV)
        
        # 크로마키 범위 설정
        chroma_h = hsv_chroma[:,:,0]
        lower = np.array([chroma_h.min()-self.offset, 50, 50])
        upper = np.array([chroma_h.max()+self.offset, 255, 255])
        
        # 마스크 생성
        mask = cv2.inRange(hsv_fg, lower, upper)
        mask_inv = cv2.bitwise_not(mask)
        
        # 합성
        roi = bg[y:y+new_h, x:x+new_w]
        fg_masked = cv2.bitwise_and(fg, fg, mask=mask_inv)
        bg_masked = cv2.bitwise_and(roi, roi, mask=mask)
        combined = cv2.add(fg_masked, bg_masked)
        
        result = bg.copy()
        result[y:y+new_h, x:x+new_w] = combined
        
        return result

class ChromakeyTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.result_image = None
        
    def apply_chromakey(self, dialog):
        self.result_image = dialog.apply_chromakey()
        return self.result_image
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image