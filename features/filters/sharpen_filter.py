import cv2
import numpy as np
from .filter import Filter

"""샤프닝필터"""
class SharpenFilter(Filter):
    def apply(self, image):
        # 샤프닝 커널
        kernel = np.array([[-1,-1,-1],
                         [-1, 9,-1],
                         [-1,-1,-1]])
        return cv2.filter2D(image, -1, kernel) 
    
