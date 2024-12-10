import cv2
import numpy as np
from .filter import Filter

"""스케치 필터"""
class SketchFilter(Filter):
    def apply(self, image):
        # 스케치 효과
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        inv_gray = 255 - gray
        blur = cv2.GaussianBlur(inv_gray, (21, 21), 0)
        return cv2.divide(gray, 255 - blur, scale=256.0) 