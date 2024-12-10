import numpy as np

class Filter:
    def __init__(self):
        self.is_applied = False
    
    def apply(self, image):
        # 기본 필터 클래스의 추상 메서드
        raise NotImplementedError("필터의 apply 메서드를 구현해야 합니다")
        
    def toggle(self, image):
        """필터 적용/해제를 토글합니다."""
        if not self.is_applied:
            result = self.apply(image)
            self.is_applied = True
            return result
        else:
            self.is_applied = False
            return image