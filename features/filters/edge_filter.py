import cv2
import numpy as np
from .filter import Filter

class EdgeFilter(Filter):
    """
    이미지의 경계선을 검출하는 필터 클래스
    다양한 엣지 검출 알고리즘(Canny, Sobel, Laplacian, Prewitt)을 지원합니다.
    """
    def __init__(self, method='canny'):
        """
        EdgeFilter 클래스 생성자
        
        Args:
            method (str): 사용할 엣지 검출 알고리즘
                - 'canny': Canny 엣지 검출
                - 'sobel': Sobel 엣지 검출
                - 'laplacian': Laplacian 엣지 검출
                - 'prewitt': Prewitt 엣지 검출
        """
        super().__init__()
        self.method = method
        
    def apply(self, image):
        """
        이미지에 엣지 검출을 적용합니다.
        
        Args:
            image (np.ndarray): 입력 이미지
            
        Returns:
            np.ndarray: 엣지가 검출된 이미지
        """
        # 그레이스케일 변환 (엣지 검출은 흑백 이미지에서 수행)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        if self.method == 'canny':
            # Canny 엣지 검출: 노이즈에 강하고 정확한 엣지 검출이 가능
            edges = cv2.Canny(gray, 100, 200)
        elif self.method == 'sobel':
            # Sobel 엣지 검출: x, y 방향의 기울기를 계산하여 엣지 검출
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)  # x방향 미분
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)  # y방향 미분
            # 두 방향의 기울기를 결합하여 엣지 강도 계산
            edges = cv2.magnitude(sobelx, sobely)
            # 값 범위를 0-255로 정규화
            edges = cv2.normalize(edges, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        elif self.method == 'laplacian':
            # Laplacian 엣지 검출: 2차 미분을 이용한 엣지 검출
            edges = cv2.Laplacian(gray, cv2.CV_64F)
            edges = np.uint8(np.absolute(edges))
        elif self.method == 'prewitt':
            # Prewitt 엣지 검출: Sobel과 유사하나 더 단순한 커널 사용
            kernelx = np.array([[1,1,1],[0,0,0],[-1,-1,-1]])  # x방향 커널
            kernely = np.array([[-1,0,1],[-1,0,1],[-1,0,1]])  # y방향 커널
            img_prewittx = cv2.filter2D(gray, -1, kernelx)
            img_prewitty = cv2.filter2D(gray, -1, kernely)
            # x, y 방향 엣지를 가중 평균하여 결합
            edges = cv2.addWeighted(img_prewittx, 0.5, img_prewitty, 0.5, 0)
        else:
            # 잘못된 method가 지정된 경우 기본값으로 Canny 사용
            edges = cv2.Canny(gray, 100, 200)
            
        # 그레이스케일 결과를 BGR 형식으로 변환하여 반환
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR) 