import cv2
import numpy as np

class PanoramaTool:
    def __init__(self):
        # SIFT 특징점 검출기 생성
        self.descriptor = cv2.SIFT_create()
        # BF 매칭기 생성
        self.matcher = cv2.DescriptorMatcher_create("BruteForce")
    
    def create_panorama(self, img_left, img_right):
        """두 이미지를 받아서 파노라마 이미지를 생성합니다."""
        try:
            # 이미지 크기 가져오기
            hl, wl = img_left.shape[:2]
            hr, wr = img_right.shape[:2]
            
            # RGB to BGR 변환 (OpenCV는 BGR 사용)
            img_left_bgr = cv2.cvtColor(img_left, cv2.COLOR_RGB2BGR)
            img_right_bgr = cv2.cvtColor(img_right, cv2.COLOR_RGB2BGR)
            
            # 그레이스케일 변환
            gray_left = cv2.cvtColor(img_left_bgr, cv2.COLOR_BGR2GRAY)
            gray_right = cv2.cvtColor(img_right_bgr, cv2.COLOR_BGR2GRAY)
            
            # SIFT 특징점 검출
            kps_left, features_left = self.descriptor.detectAndCompute(gray_left, None)
            kps_right, features_right = self.descriptor.detectAndCompute(gray_right, None)
            
            # KNN 매칭 수행
            matches = self.matcher.knnMatch(features_right, features_left, 2)
            
            # 좋은 매칭점 선별
            good_matches = []
            for m in matches:
                if len(m) == 2 and m[0].distance < m[1].distance * 0.75:
                    good_matches.append((m[0].trainIdx, m[0].queryIdx))
            
            # 좋은 매칭점이 4개 이상이면 파노라마 생성
            if len(good_matches) > 4:
                pts_left = np.float32([kps_left[i].pt for (i, _) in good_matches])
                pts_right = np.float32([kps_right[i].pt for (_, i) in good_matches])
                
                # 호모그래피 행렬 계산
                matrix, status = cv2.findHomography(pts_right, pts_left, cv2.RANSAC, 4.0)
                
                # 오른쪽 이미지를 변환하여 파노라마 생성
                panorama = cv2.warpPerspective(img_right_bgr, matrix, (wr + wl, hr))
                panorama[0:hl, 0:wl] = img_left_bgr
                
                # BGR to RGB 변환하여 반환
                return cv2.cvtColor(panorama, cv2.COLOR_BGR2RGB)
            
            return img_left_bgr
            
        except Exception as e:
            print(f"파노라마 생성 중 오류 발생: {str(e)}")
            return None