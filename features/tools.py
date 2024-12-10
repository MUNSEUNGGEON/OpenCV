from abc import ABC, abstractmethod
import cv2
import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QInputDialog, QFontDialog, QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel, QSpinBox
from PIL import Image, ImageDraw, ImageFont

class DrawingTool(ABC):
    """그리기 도구의 추상 기본 클래스"""
    def __init__(self):
        """초기화 메서드"""
        self.color = (0, 0, 0)
        self.thickness = 2
        
    @abstractmethod
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        """마우스 버튼을 눌렀을 때 호출되는 추상 메서드 """
        pass
        
    @abstractmethod
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        """마우스를 움직일 때 호출되는 추상 메서드"""
        pass
        
    @abstractmethod
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        """마우스 버튼을 놓았을 때 호출되는 추상 메서드 """
        pass

    def set_color(self, color):
        """그리기 색상 설정 메서드 """
        self.color = color

    def set_thickness(self, thickness):
        """선 두께 설정 메서드"""
        self.thickness = thickness

class PenTool(DrawingTool):
    """펜 도구 클래스"""
    def __init__(self):
        super().__init__()
        self.last_point = None  # 마지막 점의 위치를 저장하는 변수
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        """마우스 버튼을 눌렀을 때 호출되는 메서드"""
        self.last_point = pos
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        """마우스를 움직일 때 호출되는 메서드"""
        if self.last_point:
            cv2.line(image, 
                    (self.last_point.x(), self.last_point.y()),
                    (pos.x(), pos.y()),
                    self.color[::-1],  # BGR -> RGB 색상 변환
                    self.thickness)
        self.last_point = pos
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        """마우스 버튼을 놓았을 때 호출되는 메서드"""
        self.last_point = None
        return image
class EraserTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.last_point = None
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        self.last_point = pos
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.last_point:
            cv2.line(image,
                    (self.last_point.x(), self.last_point.y()),
                    (pos.x(), pos.y()),
                    (255, 255, 255),
                    self.thickness * 2)
        self.last_point = pos
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        self.last_point = None
        return image

class RectangleTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.temp_image = None
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        self.start_pos = pos
        self.temp_image = image.copy()
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.start_pos:
            image = self.temp_image.copy()
            cv2.rectangle(image,
                        (self.start_pos.x(), self.start_pos.y()),
                        (pos.x(), pos.y()),
                        self.color[::-1],
                        self.thickness)
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        self.start_pos = None
        self.temp_image = None
        return image

class CircleTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.temp_image = None
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        self.start_pos = pos
        self.temp_image = image.copy()
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.start_pos:
            image = self.temp_image.copy()
            radius = int(((pos.x() - self.start_pos.x())**2 + 
                         (pos.y() - self.start_pos.y())**2)**0.5)
            cv2.circle(image,
                      (self.start_pos.x(), self.start_pos.y()),
                      radius,
                      self.color[::-1],
                      self.thickness)
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        self.start_pos = None
        self.temp_image = None
        return image

class FontDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("글꼴 설정")
        layout = QVBoxLayout()
        
        # 글꼴 선택 콤보박스
        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "맑은 고딕",
            "굴림",
            "궁서",
            "바탕",
            "한컴돋움"
        ])
        layout.addWidget(QLabel("글꼴:"))
        layout.addWidget(self.font_combo)
        
        # 글꼴 크기 선택
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(32)
        layout.addWidget(QLabel("크기:"))
        layout.addWidget(self.size_spin)
        
        # 확인/취소 버튼
        buttons = QVBoxLayout()
        ok_button = QPushButton("확인")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        
        self.setLayout(layout)

class TextTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.text = ""
        self.color = (0, 0, 0)  # RGB 형식
        self.font_size = 32
        self.font_name = "맑은 고딕"
        self.position = None
        
        # 글꼴 경로 매핑
        self.font_paths = {
            "맑은 고딕": "C:/Windows/Fonts/malgun.ttf",
            "굴림": "C:/Windows/Fonts/gulim.ttc",
            "궁서": "C:/Windows/Fonts/batang.ttc",
            "바탕": "C:/Windows/Fonts/HANBatang.ttf",
            "한컴돋움": "C:/Windows/Fonts/HANDotum.TTF"
        }
        
    def on_press(self, image, pos):
        # 텍스트 입력 받기
        text, ok = QInputDialog.getText(None, "텍스트 입력", "텍스트:")
        if not ok or not text:
            return image
            
        # 글꼴 설정 대화상자
        font_dialog = FontDialog()
        if font_dialog.exec_() == QDialog.Accepted:
            self.font_name = font_dialog.font_combo.currentText()
            self.font_size = font_dialog.size_spin.value()
        else:
            return image
            
        self.text = text
        self.position = pos
        
        try:
            # 선택된 글꼴로 텍스트 그리기
            font_path = self.font_paths.get(self.font_name)
            print(f"Loading font from: {font_path}")  # 디버깅용
            font = ImageFont.truetype(font_path, self.font_size)
            
            # OpenCV BGR을 RGB로 변환
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # PIL Image로 변환
            pil_image = Image.fromarray(rgb_image)
            draw = ImageDraw.Draw(pil_image)
            
            # RGB 색상 형식으로 변환
            rgb_color = self.color[::-1]  # BGR에서 RGB로 변환
            
            # 텍스트 그리기
            draw.text((pos.x(), pos.y()), self.text, 
                     font=font, fill=rgb_color)
            
            # RGB를 BGR로 다시 변환
            result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return result
            
        except Exception as e:
            print(f"폰트 로드 실패: {e}")
            print(f"시도한 폰트: {self.font_name}")
            print(f"시도한 경로: {font_path}")
            # 폰트 로드 실패시 기본 OpenCV 텍스트 사용
            return cv2.putText(image, self.text, 
                             (pos.x(), pos.y()), 
                             cv2.FONT_HERSHEY_SIMPLEX, 
                             1, self.color[::-1], 2)

    def on_move(self, image, pos):
        return image
        
    def on_release(self, image, pos):
        return image
        
    def set_color(self, color):
        self.color = color
        
    def set_thickness(self, thickness):
        self.font_size = thickness / 2  # 두께를 폰트 크기로 변환

class SelectTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.temp_image = None
        self.selected_area = None
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        self.start_pos = pos
        self.temp_image = image.copy()
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.start_pos:
            image = self.temp_image.copy()
            cv2.rectangle(image,
                        (self.start_pos.x(), self.start_pos.y()),
                        (pos.x(), pos.y()),
                        (0, 0, 255),
                        2)
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.start_pos:
            self.selected_area = (
                min(self.start_pos.x(), pos.x()),
                min(self.start_pos.y(), pos.y()),
                abs(pos.x() - self.start_pos.x()),
                abs(pos.y() - self.start_pos.y())
            )
        self.start_pos = None
        self.temp_image = None
        return image

class PolygonTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.temp_image = None
        self.sides = 4  # 기본값은 사각형
        
    def set_sides(self):
        """다각형 각의 수 설정"""
        sides, ok = QInputDialog.getInt(None, "다각형 설정", 
                                      "각의 수를 입력하세요 (3-12):",
                                      value=self.sides, min=3, max=12)
        if ok:
            self.sides = sides
        return ok
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        self.start_pos = pos
        self.temp_image = image.copy()
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.start_pos:
            image = self.temp_image.copy()
            
            # 중심점과 반지름 계산
            center_x = self.start_pos.x()
            center_y = self.start_pos.y()
            radius = int(np.sqrt((pos.x() - center_x)**2 + 
                               (pos.y() - center_y)**2))
            
            # 다각형 꼭지점 계산
            points = []
            for i in range(self.sides):
                angle = 2 * np.pi * i / self.sides - np.pi / 2
                x = center_x + int(radius * np.cos(angle))
                y = center_y + int(radius * np.sin(angle))
                points.append([x, y])
            
            # 다형 그리기
            points = np.array(points, np.int32)
            points = points.reshape((-1, 1, 2))
            cv2.polylines(image, [points], True, self.color[::-1], self.thickness)
            
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.start_pos:
            image = self.on_move(image, pos)
            self.start_pos = None
            self.temp_image = None
        return image