from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np

class ImageViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 이미지를 표시할 QLabel
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border: 1px solid #333333;
            }
        """)
        
        # 스크롤 영역 설정
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        
        self.layout.addWidget(self.scroll_area)
        
        # 초기 이미지 생성
        self.current_image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        self.zoom_level = 1.0
        self.update_display()
        
    def update_display(self, image=None):
        """이미지 디스플레이 업데이트"""
        if image is not None:
            self.current_image = image
            
        height, width = self.current_image.shape[:2]
        new_width = int(width * self.zoom_level)
        new_height = int(height * self.zoom_level)
        
        resized = cv2.resize(self.current_image, (new_width, new_height))
        bytes_per_line = 3 * new_width
        
        q_img = QImage(
            resized.data,
            new_width,
            new_height,
            bytes_per_line,
            QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap)
        
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
                return QPoint(x, y)
        return None 