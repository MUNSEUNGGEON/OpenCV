from .base_feature import ImageFeature
import cv2
import numpy as np
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QColorDialog, QFileDialog, QInputDialog
from enum import Enum

class DrawingMode(Enum):
    PEN = 1
    ERASER = 2
    RECTANGLE = 3
    CIRCLE = 4
    TEXT = 5
    SELECT = 6

class FilterMode(Enum):
    GRAYSCALE = 1
    BLUR = 2
    SHARPEN = 3
    EDGE = 4

class DrawingTool(ImageFeature):
    def __init__(self):
        self.drawing = False
        self.last_point = None
        self.color = (0, 0, 0)  # 기본 검정색
        self.thickness = 2
        self.mode = DrawingMode.PEN
        self.start_pos = None
        self.history = []
        self.redo_stack = []
        self.text = ""
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 1
        self.selected_area = None
        
    def process(self, image: np.ndarray, event, pos) -> np.ndarray:
        if self.mode == DrawingMode.TEXT and event == "press":
            text, ok = QInputDialog.getText(None, '텍스트 입력', '텍스트:')
            if ok and text:
                self.text = text
                cv2.putText(image, text, 
                           (pos.x(), pos.y()), 
                           self.font, self.font_scale, 
                           self.color[::-1], self.thickness)
                self.add_to_history(image.copy())
            return image
            
        elif self.mode == DrawingMode.SELECT:
            if event == "press":
                self.drawing = True
                self.start_pos = pos
                self.temp_image = image.copy()
            elif event == "move" and self.drawing:
                image = self.temp_image.copy()
                cv2.rectangle(image,
                            (self.start_pos.x(), self.start_pos.y()),
                            (pos.x(), pos.y()),
                            (0, 0, 255),
                            2)
            elif event == "release":
                self.drawing = False
                self.selected_area = (
                    min(self.start_pos.x(), pos.x()),
                    min(self.start_pos.y(), pos.y()),
                    abs(pos.x() - self.start_pos.x()),
                    abs(pos.y() - self.start_pos.y())
                )
            return image
            
        elif event == "press":
            self.drawing = True
            self.last_point = pos
            self.start_pos = pos
            if self.mode in [DrawingMode.RECTANGLE, DrawingMode.CIRCLE]:
                self.temp_image = image.copy()
            
        elif event == "move" and self.drawing:
            if self.mode == DrawingMode.PEN:
                if self.last_point:
                    cv2.line(image, 
                            (self.last_point.x(), self.last_point.y()),
                            (pos.x(), pos.y()),
                            self.color[::-1],
                            self.thickness)
                self.last_point = pos
            
            elif self.mode == DrawingMode.ERASER:
                if self.last_point:
                    cv2.line(image,
                            (self.last_point.x(), self.last_point.y()),
                            (pos.x(), pos.y()),
                            (255, 255, 255),
                            self.thickness * 2)
                self.last_point = pos
            
            elif self.mode == DrawingMode.RECTANGLE:
                image = self.temp_image.copy()
                cv2.rectangle(image,
                            (self.start_pos.x(), self.start_pos.y()),
                            (pos.x(), pos.y()),
                            self.color[::-1],
                            self.thickness)
            
            elif self.mode == DrawingMode.CIRCLE:
                image = self.temp_image.copy()
                radius = int(((pos.x() - self.start_pos.x())**2 + 
                            (pos.y() - self.start_pos.y())**2)**0.5)
                cv2.circle(image,
                          (self.start_pos.x(), self.start_pos.y()),
                          radius,
                          self.color[::-1],
                          self.thickness)
                
        elif event == "release":
            self.drawing = False
            self.last_point = None
            self.add_to_history(image.copy())
            
        return image
    
    def set_mode(self, mode: DrawingMode):
        self.mode = mode
    
    def set_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = (color.red(), color.green(), color.blue())
    
    def set_thickness(self, value):
        self.thickness = value
    
    def add_to_history(self, image):
        self.history.append(image.copy())
        self.redo_stack.clear()
        if len(self.history) > 10:  # 최대 히스토리 개수 제한
            self.history.pop(0)
    
    def undo(self, current_image):
        if len(self.history) > 0:
            self.redo_stack.append(current_image.copy())
            return self.history.pop()
        return current_image
    
    def redo(self, current_image):
        if len(self.redo_stack) > 0:
            self.history.append(current_image.copy())
            return self.redo_stack.pop()
        return current_image
    
    def apply_filter(self, image: np.ndarray, filter_mode: FilterMode) -> np.ndarray:
        if filter_mode == FilterMode.GRAYSCALE:
            return cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        elif filter_mode == FilterMode.BLUR:
            return cv2.GaussianBlur(image, (5, 5), 0)
        elif filter_mode == FilterMode.SHARPEN:
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            return cv2.filter2D(image, -1, kernel)
        elif filter_mode == FilterMode.EDGE:
            return cv2.Canny(image, 100, 200)
        return image