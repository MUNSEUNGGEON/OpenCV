import cv2
import numpy as np
from .filter import Filter

class MosaicFilter(Filter):
    def apply(self, image):
        height, width = image.shape[:2]
        rate = 30
        small = cv2.resize(image, (width//rate, height//rate))
        return cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)
        # 이미지를 축소했다가 확대하여 모자이크 효과 생성