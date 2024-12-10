import cv2
import numpy as np
import os

class ObjectDetector:
    def __init__(self):
        # 현재 디렉토리 기준으로 models 폴더 경로 설정
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        
        try:
            # YOLO Tiny 모델 설정
            weights_path = os.path.join(models_dir, 'yolov3-tiny.weights')
            cfg_path = os.path.join(models_dir, 'yolov3-tiny.cfg')
            names_path = os.path.join(models_dir, 'coco.names')
            
            self.net = cv2.dnn.readNet(weights_path, cfg_path)
            
            # COCO 데이터셋의 클래스 이름 로드
            with open(names_path, "r") as f:
                self.classes = [line.strip() for line in f.readlines()]
                
            self.layer_names = self.net.getLayerNames()
            self.output_layers = [self.layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
            self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))
            
            self.is_detecting = False
            
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            print(f"현재 경로: {os.getcwd()}")
            print(f"모델 경로: {models_dir}")
            self.net = None
            self.is_detecting = False
        
    def detect_objects(self, frame):
        if not self.is_detecting or self.net is None:
            return frame
            
        height, width, _ = frame.shape
        
        # 이미지 전처리
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)
        
        # 감지된 객체 정보
        class_ids = []
        confidences = []
        boxes = []
        
        # 감지된 객체 표시
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > 0.5:  # 신뢰도 임계값
                    # 객체 좌표 계산
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    # 사각형 좌표
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # 노이즈 제거
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        
        # 결과 표시
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = str(self.classes[class_ids[i]])
                confidence = confidences[i]
                color = self.colors[class_ids[i]]
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, f"{label} {confidence:.2f}", 
                          (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                          0.5, color, 2)
        
        return frame
        
    def toggle_detection(self):
        self.is_detecting = not self.is_detecting
        return self.is_detecting 