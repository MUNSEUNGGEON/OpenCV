import cv2
import numpy as np
from .filter import Filter

"""블러 필터"""
class BlurFilter(Filter):
    def apply(self, image):
        return cv2.GaussianBlur(image, (5, 5), 0) 