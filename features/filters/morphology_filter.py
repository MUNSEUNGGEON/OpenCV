import cv2
import numpy as np
from .filter import Filter

class MorphologyFilter(Filter):
    def __init__(self, operation='dilate'):
        """MorphologyFilter 클래스 생성자 """
        super().__init__()
        self.operation = operation
        # 5x5 크기의 정방형 커널 생성
        self.kernel = np.ones((5,5), np.uint8)
        
    def apply(self, image):
        if self.operation == 'dilate':
            # 팽창 연산: 객체의 크기를 확장하며, 작은 구멍을 메우는 효과
            return cv2.dilate(image, self.kernel, iterations=1)
        elif self.operation == 'erode':
            # 침식 연산: 객체의 크기를 축소하며, 작은 돌기를 제거하는 효과
            return cv2.erode(image, self.kernel, iterations=1)
        elif self.operation == 'opening':
            # 열림 연산: 침식 후 팽창을 수행하여 작은 노이즈를 제거하면서 객체의 크기는 보존
            return cv2.morphologyEx(image, cv2.MORPH_OPEN, self.kernel)
        elif self.operation == 'closing':
            # 닫힘 연산: 팽창 후 침식을 수행하여 작은 구멍을 메우면서 객체의 크기는 보존
            return cv2.morphologyEx(image, cv2.MORPH_CLOSE, self.kernel)
        else:
            # 잘못된 연산이 지정된 경우 기본적으로 팽창 연산 수행
            return cv2.dilate(image, self.kernel, iterations=1) 