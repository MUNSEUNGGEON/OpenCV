import cv2
import numpy as np
from .object_detector import ObjectDetector

class VideoProcessor:
    def __init__(self):
        self.cap = None
        self.frame_count = 0
        self.current_frame = None
        self.tracking_enabled = False
        
        # 물체 추적 관련 변수들
        self.prev_gray = None
        self.prev_points = None
        self.tracking_lines = None
        self.colors = None
        self.term_criteria = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 10, 0.03)

        self.object_detector = ObjectDetector()

    def load_video(self, file_path):
        """비디오 파일을 로드합니다."""
        self.cap = cv2.VideoCapture(file_path)
        if self.cap.isOpened():
            self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            # 추적을 위한 변수 초기화
            self.tracking_lines = None
            self.colors = np.random.randint(0, 255, (200, 3))
            return True
        return False

    def toggle_tracking(self):
        """물체 추적 기능을 켜고 끕니다."""
        self.tracking_enabled = not self.tracking_enabled
        if not self.tracking_enabled:
            # 추적 관련 변수들 초기화
            self.prev_gray = None
            self.prev_points = None
            self.tracking_lines = None
        return self.tracking_enabled

    def get_frame(self, frame_idx):
        """지정된 프레임을 가져오고 물체 추적과 감지를 수행합니다."""
        if not self.is_loaded():
            return None

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        if not ret:
            return None

        if self.tracking_enabled:
            frame = self.track_objects(frame)
        
        # 물체 감지 적용
        frame = self.object_detector.detect_objects(frame)
        
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def track_objects(self, frame):
        """프레임에서 물체를 추적합니다."""
        img_draw = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_gray is None:
            self.prev_gray = gray
            self.prev_points = cv2.goodFeaturesToTrack(self.prev_gray, 200, 0.01, 10)
            self.tracking_lines = np.zeros_like(frame)
        else:
            next_points, status, err = cv2.calcOpticalFlowPyrLK(
                self.prev_gray, gray, self.prev_points, None, 
                criteria=self.term_criteria
            )

            if next_points is not None:
                prev_move = self.prev_points[status == 1]
                next_move = next_points[status == 1]

                for i, (p, n) in enumerate(zip(prev_move, next_move)):
                    px, py = p.ravel().astype(np.int32)
                    nx, ny = n.ravel().astype(np.int32)
                    cv2.line(self.tracking_lines, (px, py), (nx, ny), 
                            self.colors[i].tolist(), 2)
                    cv2.circle(self.tracking_lines, (nx, ny), 5, 
                             self.colors[i].tolist(), -1)

                img_draw = cv2.add(frame, self.tracking_lines)
                self.prev_gray = gray
                self.prev_points = next_move.reshape(-1, 1, 2)

        return img_draw

    def is_loaded(self):
        """비디오가 로드되었는지 확인합니다."""
        return self.cap is not None and self.cap.isOpened()

    def get_frame_count(self):
        """총 프레임 수를 반환합니다."""
        return self.frame_count

    def __del__(self):
        """소멸자: 비디오 캡처 객체를 해제합니다."""
        if self.cap is not None:
            self.cap.release()
        
    def apply_filter(self, filter_func):
        """현재 프레임에 필터를 적용합니다."""
        if self.current_frame is not None:
            return filter_func(self.current_frame)
        return None
        
    def release(self):
        """비디오 캡처 객체 해제합니다."""
        if self.cap is not None:
            self.cap.release()

    def toggle_detection(self):
        """물체 감지 켜기/끄기"""
        return self.object_detector.toggle_detection()