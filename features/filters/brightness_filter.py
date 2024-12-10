import cv2
import numpy as np
from .filter import Filter

class BrightnessFilter(Filter):
    def apply(self, image):
        # 밝기 증가 (50은 조절 가능한 값)
        brightness = 50
        return cv2.add(image, np.ones(image.shape, dtype='uint8') * brightness) 