import cv2
import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from features.tools import DrawingTool

class SelectionTool(DrawingTool):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.start_pos = None
        self.temp_image = None
        self.selected_area = None
        self.selected_content = None
        self.is_moving = False
        self.drag_start = None
        self.current_tool = 'rectangle'
        
        if self.parent:
            self.setup_shortcuts()
    
    def setup_shortcuts(self):
        # 사각형 선택 도구 단축키 (R)
        self.rect_shortcut = QShortcut(QKeySequence('R'), self.parent)
        self.rect_shortcut.activated.connect(self.activate_rectangle_tool)
        
        # 자유 선택 도구 단축키 (F)
        self.free_shortcut = QShortcut(QKeySequence('F'), self.parent)
        self.free_shortcut.activated.connect(self.activate_free_selection)
        
        # 지우개 도구 단축키 (E)
        self.eraser_shortcut = QShortcut(QKeySequence('E'), self.parent)
        self.eraser_shortcut.activated.connect(self.activate_eraser)
    
    def activate_rectangle_tool(self):
        # 사각형 선택 도구 활성화
        self.current_tool = 'rectangle'
        print("사각형 선택 도구 활성화")  # 디버깅용
        
    def activate_free_selection(self):
        # 자유 선택 도구 활성화
        self.current_tool = 'free'
        print("자유 선택 도구 활성화")  # 디버깅용
        
    def activate_eraser(self):
        # 지우개 도구 활성화
        self.current_tool = 'eraser'
        print("지우개 도구 활성화")  # 디버깅용
    
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        # 이미 선택된 영역이 있고, 그 안을 클릭했다면 이동 모드
        if self.selected_area:
            x, y, w, h = self.selected_area
            if (x <= pos.x() <= x + w and y <= pos.y() <= y + h):
                self.is_moving = True
                self.drag_start = pos
                self.temp_image = image.copy()
                return self.draw_selection_border(image)
        
        # 새로운 선택 시작
        self.start_pos = pos
        self.temp_image = image.copy()
        self.selected_area = None
        self.selected_content = None
        self.is_moving = False
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.is_moving and self.selected_content is not None:
            # 선택 영역 이동
            image = self.temp_image.copy()
            dx = pos.x() - self.drag_start.x()
            dy = pos.y() - self.drag_start.y()
            
            x, y, w, h = self.selected_area
            new_x = max(0, min(x + dx, image.shape[1] - w))
            new_y = max(0, min(y + dy, image.shape[0] - h))
            
            # 이전 위치를 흰색으로 채우기
            image[y:y+h, x:x+w] = 255
            
            # 새 위치에 선택된 내용 표시
            image[new_y:new_y+h, new_x:new_x+w] = self.selected_content
            
            # 선택 영역 업데이트
            self.selected_area = (new_x, new_y, w, h)
            self.drag_start = pos
            
            return self.draw_selection_border(image)
            
        elif self.start_pos:
            # 새로운 선택 영역 표시
            image = self.temp_image.copy()
            x1, y1 = self.start_pos.x(), self.start_pos.y()
            x2, y2 = pos.x(), pos.y()
            
            # 점선 테두리로 선택 영역 표시
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            
            # 점선 테두리 그리기
            for i in range(0, w, 4):
                cv2.line(image, (x+i, y), (min(x+i+2, x+w), y), (0,0,0), 1)
                cv2.line(image, (x+i, y+h), (min(x+i+2, x+w), y+h), (0,0,0), 1)
            for i in range(0, h, 4):
                cv2.line(image, (x, y+i), (x, min(y+i+2, y+h)), (0,0,0), 1)
                cv2.line(image, (x+w, y+i), (x+w, min(y+i+2, y+h)), (0,0,0), 1)
            
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.is_moving:
            # 이동 완료
            x, y, w, h = self.selected_area
            # 원래 위치는 이미 흰색으로 채워져 있음
            image[y:y+h, x:x+w] = self.selected_content
            self.is_moving = False
            return self.draw_selection_border(image)
            
        elif self.start_pos:
            # 새로운 선택 영역 설정
            x1, y1 = self.start_pos.x(), self.start_pos.y()
            x2, y2 = pos.x(), pos.y()
            
            self.selected_area = (
                min(x1, x2),
                min(y1, y2),
                abs(x2 - x1),
                abs(y2 - y1)
            )
            
            # 선택된 영역의 내용 저장
            x, y, w, h = self.selected_area
            self.selected_content = image[y:y+h, x:x+w].copy()
            
            return self.draw_selection_border(image)
            
        return image

    def draw_selection_border(self, image: np.ndarray) -> np.ndarray:
        """선택 영역 테두리 그리기"""
        if self.selected_area:
            x, y, w, h = self.selected_area
            # 점선 테두리 그리기
            for i in range(0, w, 4):
                cv2.line(image, (x+i, y), (min(x+i+2, x+w), y), (0,0,0), 1)
                cv2.line(image, (x+i, y+h), (min(x+i+2, x+w), y+h), (0,0,0), 1)
            for i in range(0, h, 4):
                cv2.line(image, (x, y+i), (x, min(y+i+2, y+h)), (0,0,0), 1)
                cv2.line(image, (x+w, y+i), (x+w, min(y+i+2, y+h)), (0,0,0), 1)
        return image

    def copy_selection(self, image: np.ndarray) -> np.ndarray:
        """선택 영역 복사"""
        if self.selected_area and self.selected_content is not None:
            return self.selected_content.copy()
        return None

    def paste_selection(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        """복사된 내용 붙여넣기"""
        if self.selected_content is not None:
            h, w = self.selected_content.shape[:2]
            x = max(0, min(pos.x(), image.shape[1] - w))
            y = max(0, min(pos.y(), image.shape[0] - h))
            
            # 새로운 위치에 붙여넣기
            image[y:y+h, x:x+w] = self.selected_content.copy()
            
            # 붙여넣은 영역을 새로운 선택 영역으로 설정
            self.selected_area = (x, y, w, h)
            return self.draw_selection_border(image)
        return image

    def delete_selection(self, image: np.ndarray) -> np.ndarray:
        """선택 영역 삭제"""
        if self.selected_area:
            x, y, w, h = self.selected_area
            image[y:y+h, x:x+w] = 255  # 흰색으로 채우기
            self.selected_area = None
            self.selected_content = None
        return image