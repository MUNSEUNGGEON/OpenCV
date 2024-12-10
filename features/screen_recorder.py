import cv2
import numpy as np
from datetime import datetime

class ScreenRecorder:
    def __init__(self, parent=None):
        self.recording = False
        self.writer = None
        self.parent = parent
        self.cap = None
        
    def start_camera_recording(self):
        """웹캠 녹화 시작"""
        if not self.recording:
            self.cap = cv2.VideoCapture(0)  # 기본 웹캠
            if not self.cap.isOpened():
                return False
                
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"camera_recording_{timestamp}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
            self.recording = True
            return True
            
    def stop_camera_recording(self):
        """웹캠 녹화 중지"""
        if self.recording:
            self.recording = False
            if self.writer:
                self.writer.release()
                self.writer = None
            if self.cap:
                self.cap.release()
                self.cap = None
                
    def capture_camera_frame(self):
        """웹캠 프레임 캡처 및 녹화"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # BGR을 RGB로 변환하여 화면에 표시
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 녹화 중이면 프레임 저장
                if self.recording and self.writer:
                    self.writer.write(frame)  # BGR 형식으로 저장
                    
                return frame_rgb
        return None
            