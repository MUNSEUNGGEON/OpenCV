import cv2
import numpy as np
from .tools import DrawingTool
from PyQt5.QtCore import QPoint

class MosaicTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.temp_image = None
        self.block_size = 15
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        self.start_pos = pos
        self.temp_image = image.copy()
        return image
        
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.start_pos:
            image = self.temp_image.copy()
            x1, y1 = self.start_pos.x(), self.start_pos.y()
            x2, y2 = pos.x(), pos.y()
            
            # 선택 영역의 좌표 계산
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            
            # 점선 테두리 그리기
            dash_length = 5
            for i in range(0, w, dash_length*2):
                # 상단 가로선
                cv2.line(image, (x+i, y), (x+min(i+dash_length, w), y), (0,0,0), 1)
                # 하단 가로선
                cv2.line(image, (x+i, y+h), (x+min(i+dash_length, w), y+h), (0,0,0), 1)
            
            for i in range(0, h, dash_length*2):
                # 좌측 세로선
                cv2.line(image, (x, y+i), (x, y+min(i+dash_length, h)), (0,0,0), 1)
                # 우측 세로선
                cv2.line(image, (x+w, y+i), (x+w, y+min(i+dash_length, h)), (0,0,0), 1)
            
            # 크기 조절을 위한 작은 사각형 표시
            square_size = 4
            # 모서리에 작은 사각형 그리기
            cv2.rectangle(image, (x-square_size, y-square_size), (x+square_size, y+square_size), (0,0,0), 1)
            cv2.rectangle(image, (x+w-square_size, y-square_size), (x+w+square_size, y+square_size), (0,0,0), 1)
            cv2.rectangle(image, (x-square_size, y+h-square_size), (x+square_size, y+h+square_size), (0,0,0), 1)
            cv2.rectangle(image, (x+w-square_size, y+h-square_size), (x+w+square_size, y+h+square_size), (0,0,0), 1)
            # 중간 점에 작은 사각형 그리기
            cv2.rectangle(image, (x+w//2-square_size, y-square_size), (x+w//2+square_size, y+square_size), (0,0,0), 1)
            cv2.rectangle(image, (x+w//2-square_size, y+h-square_size), (x+w//2+square_size, y+h+square_size), (0,0,0), 1)
            cv2.rectangle(image, (x-square_size, y+h//2-square_size), (x+square_size, y+h//2+square_size), (0,0,0), 1)
            cv2.rectangle(image, (x+w-square_size, y+h//2-square_size), (x+w+square_size, y+h//2+square_size), (0,0,0), 1)
            
            return image
        return image
        
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        if self.start_pos:
            x1, y1 = self.start_pos.x(), self.start_pos.y()
            x2, y2 = pos.x(), pos.y()
            
            # 선택 영역 좌표 계산
            x = min(x1, x2)
            y = min(y1, y2)
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            
            # 원본 이미지를 사용하여 모자이크 처리
            image = self.temp_image.copy()  # 선이 그려지지 않은 원본 이미지 사용
            
            # 선택 영역만 모자이크 처리
            roi = image[y:y+h, x:x+w]
            if roi.size > 0:  # 영역이 유효한 경우
                small = cv2.resize(roi, (w//self.block_size, h//self.block_size),
                                 interpolation=cv2.INTER_LINEAR)
                mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
                image[y:y+h, x:x+w] = mosaic
            
            self.start_pos = None
            
        return image