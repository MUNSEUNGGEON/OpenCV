from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import QTimer

class PreviewMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.apply_preview)
        self.current_action = None
        self.original_image = None
        
        # 메뉴 항목에 마우스가 올라갈 때의 이벤트 연결
        self.hovered.connect(self.on_action_hovered)
        
    def on_action_hovered(self, action):
        self.current_action = action
        # 원본 이미지 저장
        if self.original_image is None:
            self.original_image = self.main_window.current_image.copy()
        # 미리보기 타이머 재시작
        self.preview_timer.start(100)  # 100ms 후에 미리보기 적용
    
    def apply_preview(self):
        if self.current_action and hasattr(self.current_action, 'filter_name'):
            filter_name = self.current_action.filter_name
            if filter_name in self.main_window.filters:
                # ���리보기 적용
                preview_image = self.main_window.filters[filter_name].toggle(self.original_image.copy())
                self.main_window.current_image = preview_image
                self.main_window.update_image_display()
    
    def mouseReleaseEvent(self, event):
        # 메뉴 항목 선택 시
        action = self.activeAction()
        if action and hasattr(action, 'filter_name'):
            filter_name = action.filter_name
            if filter_name in self.main_window.filters:
                # 필터 적용 및 히스토리에 추가
                self.main_window.current_image = self.main_window.filters[filter_name].toggle(self.original_image.copy())
                self.main_window.update_image_display()
                self.main_window.history_manager.add(self.main_window.current_image.copy())
        self.original_image = None  # 원본 이미지 참조 제거
        super().mouseReleaseEvent(event)

    def hideEvent(self, event):
        # 메뉴가 닫힐 때 원본 이미지 복원
        if self.original_image is not None and not self.activeAction():
            self.main_window.current_image = self.original_image
            self.main_window.update_image_display()
        self.original_image = None
        super().hideEvent(event) 