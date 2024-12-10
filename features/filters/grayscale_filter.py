import cv2
import numpy as np
from .filter import Filter

"""흑백 필터"""
class GrayscaleFilter(Filter):
    def apply(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR) 