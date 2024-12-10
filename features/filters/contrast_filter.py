import cv2
import numpy as np
from .filter import Filter

class ContrastFilter(Filter):
    def apply(self, image):
        # 대비 증가 (alpha는 대비 강도)
        alpha = 1.5
        return cv2.convertScaleAbs(image, alpha=alpha, beta=0) 