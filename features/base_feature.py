from abc import ABC, abstractmethod
import cv2
import numpy as np

class ImageFeature(ABC):
    @abstractmethod
    def process(self, image: np.ndarray) -> np.ndarray:
        """
        이미지를 처리하는 추상 메서드
        :param image: 처리할 이미지
        :return: 처리된 이미지
        """
        pass 