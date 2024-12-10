from abc import ABC, abstractmethod
import cv2
import numpy as np

class ImageFilter(ABC):
    def __init__(self):
        self.is_applied = False  # 필터 적용 상태
        self.original_image = None  # 원본 이미지 저장
        
    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        pass
    
    def toggle(self, image: np.ndarray) -> np.ndarray:
        """필터 켜고 끄기"""
        if not self.is_applied:
            self.original_image = image.copy()
            result = self.apply(image)
            self.is_applied = True
        else:
            result = self.original_image.copy()
            self.is_applied = False
            self.original_image = None
        return result

class GrayscaleFilter(ImageFilter):
    def __init__(self):
        super().__init__()
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)

class BlurFilter(ImageFilter):
    def __init__(self, kernel_size=(5,5)):
        super().__init__()
        self.kernel_size = kernel_size
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        return cv2.GaussianBlur(image, self.kernel_size, 0)

class SharpenFilter(ImageFilter):
    def __init__(self):
        super().__init__()
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        return cv2.filter2D(image, -1, kernel)

class EdgeFilter(ImageFilter):
    def __init__(self):
        super().__init__()
        self.threshold1 = 100  # 최소 임계값
        self.threshold2 = 200  # 최대 임계값
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        # 그레이스케일로 변환
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # 노이즈 제거를 위한 가우시안 블러
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Canny 엣지 검출
        edges = cv2.Canny(blurred, 
                         self.threshold1, 
                         self.threshold2)
        
        # 3채널로 변환 (메인 이미지와 호환되도록)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

class BrightnessFilter(ImageFilter):
    def __init__(self, beta=30):
        super().__init__()
        self.beta = beta
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        return cv2.convertScaleAbs(image, alpha=1.0, beta=self.beta)

class ContrastFilter(ImageFilter):
    def __init__(self, alpha=1.5):
        super().__init__()
        self.alpha = alpha
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        return cv2.convertScaleAbs(image, alpha=self.alpha, beta=0)

class SepiaFilter(ImageFilter):
    def __init__(self):
        super().__init__()
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        kernel = np.array([[0.272, 0.534, 0.131],
                          [0.349, 0.686, 0.168],
                          [0.393, 0.769, 0.189]])
        return cv2.transform(image, kernel)

class CartoonFilter(ImageFilter):
    def __init__(self):
        super().__init__()
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                    cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(image, 9, 300, 300)
        return cv2.bitwise_and(color, color, mask=edges)

class EmbossFilter(ImageFilter):
    def __init__(self):
        super().__init__()
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        kernel = np.array([[-2,-1,0], [-1,1,1], [0,1,2]])
        return cv2.filter2D(image, -1, kernel) + 128

class WaterColorFilter(ImageFilter):
    def __init__(self):
        super().__init__()
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        temp = cv2.bilateralFilter(image, 9, 75, 75)
        temp = cv2.bilateralFilter(temp, 9, 75, 75)
        return cv2.bilateralFilter(temp, 9, 75, 75)

class SketchFilter(ImageFilter):
    def __init__(self):
        super().__init__()
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        inv_gray = 255 - gray
        blur = cv2.GaussianBlur(inv_gray, (21, 21), 0)
        return cv2.divide(gray, 255 - blur, scale=256.0)

class SobelEdgeFilter(ImageFilter):
    def __init__(self):
        super().__init__()
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Sobel 엣지 검출 (X방향과 Y방향)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # 절대값 변환
        abs_sobelx = np.absolute(sobelx)
        abs_sobely = np.absolute(sobely)
        
        # X와 Y방향 엣지 합치기
        edges = np.uint8(np.sqrt(sobelx**2 + sobely**2))
        
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

class LaplacianEdgeFilter(ImageFilter):
    def __init__(self):
        super().__init__()
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Laplacian 엣지 검출
        laplacian = cv2.Laplacian(blurred, cv2.CV_64F)
        
        # 절대값 변환 및 스케일링
        edges = np.uint8(np.absolute(laplacian))
        
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB) 

class ColorQuantizationFilter(ImageFilter):
    def __init__(self, k=8):
        super().__init__()
        self.k = k
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        # K-means 색상 양자화
        data = image.reshape((-1, 3))
        data = np.float32(data)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(data, self.k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        centers = np.uint8(centers)
        res = centers[labels.flatten()]
        return res.reshape(image.shape)

class InpaintingFilter(ImageFilter):
    def __init__(self):
        super().__init__()
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        # 마스크 생성 (예: 흰색 픽셀을 복원 대상으로)
        mask = cv2.inRange(image, (250, 250, 250), (255, 255, 255))
        return cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)

class StyleTransferFilter(ImageFilter):
    def __init__(self):
        super().__init__()
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        # 스타일 전송 효과
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        color = cv2.stylization(image, sigma_s=60, sigma_r=0.6)
        return cv2.bitwise_and(color, color, mask=edges)

class HDRFilter(ImageFilter):
    def __init__(self):
        super().__init__()
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        # HDR 효과
        hdr = cv2.detailEnhance(image, sigma_s=12, sigma_r=0.15)
        return cv2.convertScaleAbs(hdr, alpha=1.3, beta=30)

class DenoisingFilter(ImageFilter):
    def __init__(self):
        super().__init__()
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        # 노이즈 제거
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

class MorphologyFilter(ImageFilter):
    def __init__(self, operation='dilate'):
        super().__init__()
        self.operation = operation
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        kernel = np.ones((5,5), np.uint8)
        if self.operation == 'dilate':
            return cv2.dilate(image, kernel, iterations=1)
        elif self.operation == 'erode':
            return cv2.erode(image, kernel, iterations=1)
        elif self.operation == 'opening':
            return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        elif self.operation == 'closing':
            return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        return image

class PencilSketchFilter(ImageFilter):
    def __init__(self):
        super().__init__()
        
    def apply(self, image: np.ndarray) -> np.ndarray:
        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blur_image = cv2.GaussianBlur(gray_image, (21, 21), 0, 0)
        sketch_image = cv2.divide(gray_image, blur_image, scale=256.0)
        return cv2.cvtColor(sketch_image, cv2.COLOR_GRAY2RGB) 