import cv2
import numpy as np
from PyQt5.QtCore import QPoint
from .tools import DrawingTool

class ScanTool(DrawingTool):
    def __init__(self):
        super().__init__()
        self.temp_image = None
        
    def on_press(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        """마우스 클릭 시 자동으로 문서 검출 및 스캔"""
        self.temp_image = image.copy()
        return self.scan_document(image)
    
    def on_move(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image
    
    def on_release(self, image: np.ndarray, pos: QPoint) -> np.ndarray:
        return image
    
    def scan_document(self, image: np.ndarray) -> np.ndarray:
        """문서 스캔 처리"""
        # 문서 코너 검출
        corners = self.detect_document(image)
        if corners is None:
            return image
            
        # 원근 변환 적용
        result = self.apply_perspective_transform(image, corners)
        
        # 이미지 개선
        result = self.enhance_scanned_image(result)
        
        return result
    
    def detect_document(self, image: np.ndarray) -> np.ndarray:
        """문서 영역 자동 검출"""
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # 가우시안 블러로 노이즈 제거
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 캐니 엣지 검출
        edges = cv2.Canny(blurred, 75, 200)
        
        # 컨투어 찾기
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # 가장 큰 컨투어 찾기
        max_contour = max(contours, key=cv2.contourArea)
        
        # 컨투어 근사화
        epsilon = 0.02 * cv2.arcLength(max_contour, True)
        approx = cv2.approxPolyDP(max_contour, epsilon, True)
        
        # 4개의 꼭짓점이 검출되지 않은 경우
        if len(approx) != 4:
            return None
            
        # 꼭짓점 좌표를 리스트로 변환
        corners = np.float32([point[0] for point in approx])
        
        return corners
    
    def apply_perspective_transform(self, image: np.ndarray, corners: np.ndarray) -> np.ndarray:
        """원근 변환 적용"""
        # 코너 포인트 정렬
        rect = self.order_points(corners)
        (tl, tr, br, bl) = rect
        
        # 변환될 이미지의 크기 계산
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # 출력 포인트 설정
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")
        
        # 변환 행렬 계산
        M = cv2.getPerspectiveTransform(rect, dst)
        
        # 원근 변환 적용
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped
    
    def order_points(self, pts: np.ndarray) -> np.ndarray:
        """코너 포인트 순서 정렬 (좌상단, 우상단, 우하단, 좌하단)"""
        rect = np.zeros((4, 2), dtype="float32")
        
        # 좌표 합과 차이 계산
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # 좌상단
        rect[2] = pts[np.argmax(s)]  # 우하단
        
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  # 우상단
        rect[3] = pts[np.argmax(diff)]  # 좌하단
        
        return rect
    
    def enhance_scanned_image(self, image: np.ndarray) -> np.ndarray:
        """스캔된 이미지 개선"""
        # 이미지 크기 조정
        height, width = image.shape[:2]
        
        # A4 용지 비율(1:1.414)을 유지하면서 너비를 800픽셀로 조정
        new_width = 800
        new_height = int(new_width * 1.414)  # A4 비율 유지
        
        # 원본 이미지 비율이 A4보다 더 길쭉한 경우
        if height/width > 1.414:
            new_height = int(height * (new_width / width))
        
        image = cv2.resize(image, (new_width, new_height))
        
        # 컬러 이미지 개선
        # 밝기와 대비 향상
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # L 채널에 대해서만 CLAHE 적용
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced_l = clahe.apply(l)
        
        # 채널 합치기
        enhanced_lab = cv2.merge([enhanced_l, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
        
        # 선명도 향상
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoisingColored(sharpened)
        
        return denoised 