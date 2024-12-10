from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QSlider, QFileDialog, QColorDialog, QFrame, QScrollArea, QComboBox, QMenu, QAction, QInputDialog, QDialog, QTabWidget, QToolBox, QDockWidget, QMessageBox, QShortcut)
from PyQt5.QtCore import Qt, QPoint, QSize, QTimer
from PyQt5.QtGui import QFont, QKeySequence
import cv2
import numpy as np
from features.tools import PenTool, EraserTool, RectangleTool, CircleTool, TextTool, SelectTool, PolygonTool
from features.history_manager import HistoryManager
from features.filters import (
    GrayscaleFilter, BlurFilter, MosaicFilter, SharpenFilter, EdgeFilter, BrightnessFilter, ContrastFilter, SepiaFilter, CartoonFilter, SketchFilter, MorphologyFilter
)
from features.camera import CameraDialog  # 상단에 import 추가
from features.selection_tools import SelectionTool
from features.blend_tools import BlendTool, ImageSelectDialog
from features.mosaic_tool import MosaicTool  # 상단에 import 추가
from features.scan_tool import ScanTool  # 상단에 import 추가
from features.blend_dialog import BlendDialog
from features.chromakey_tool import ChromakeyDialog, ChromakeyTool
from features.seamless_clone_tool import SeamlessCloneDialog, SeamlessCloneTool
from features.background_removal_tool import BackgroundRemovalTool
from features.video.video_processor import VideoProcessor  # 수정된 import 경로
from features.panorama_tool import PanoramaTool
from features.panorama_dialog import PanoramaDialog
from gui.preview_menu import PreviewMenu  # 추가된 import 문
from features.screen_recorder import ScreenRecorder
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("이미 편집기")
        self.setGeometry(100, 100, 1200, 800)
        
        # 다 테마 스타일 설정
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)
        
        # 버튼 스타일을 다크 테마로 수정
        self.button_style = """
            QPushButton {
                font-family: 'Segoe UI Emoji', 'Apple Color Emoji';
                font-size: 14px;
                min-width: 150px;
                min-height: 30px;
                padding: 3px;
                border: 1px solid #333333;
                border-radius: 3px;
                background-color: #2d2d2d;
                color: #ffffff;
                text-align: left;
                padding-left: 8px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
            QPushButton:checked {
                background-color: #0d47a1;
                border-color: #1976d2;
            }
            QLabel {
                padding: 5px;
                color: #ffffff;
            }
            QSlider {
                margin: 8px;
            }
            QSlider::groove:horizontal {
                background: #4d4d4d;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #1976d2;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """
        
        # 초기값 설정
        self.canvas_size = (800, 600)
        self.zoom_level = 1.0
        
        # 도구 및 필터 초기화
        self.history_manager = HistoryManager()
        self.tools = {
            'pen': PenTool(),
            'eraser': EraserTool(),
            'polygon': PolygonTool(),
            'circle': CircleTool(),
            'text': TextTool(),
            'select': SelectionTool(parent=self),
            'blend': BlendTool(),
            'mosaic': MosaicTool(),
            'scan': ScanTool(),
            'chromakey': ChromakeyTool(),
            'seamless': SeamlessCloneTool(),
            'bg_removal': BackgroundRemovalTool()
        }
        
        # 파노라마 도구 초기화
        self.panorama_tool = PanoramaTool()
        
        # 필터 초기화 가
        self.filters = {
            '흑백': GrayscaleFilter(),
            '블러': BlurFilter(),
            '선명하게': SharpenFilter(),
            '엣지 (Canny)': EdgeFilter(),
            '밝기 증가': BrightnessFilter(),
            '대비 증가': ContrastFilter(),
            '세피아': SepiaFilter(),
            '카툰': CartoonFilter(),
            '스케치': SketchFilter(),
            '모자이크': MosaicFilter(),
            '모폴로지-팽창': MorphologyFilter('dilate'),
            '모폴로지-침식': MorphologyFilter('erode'),
            '모폴로지-열기': MorphologyFilter('opening'),
            '모폴로지-닫기': MorphologyFilter('closing')
        }
        
        self.current_tool = self.tools['pen']
        
        # 레이어 
        self.layers = []  # 레이어 리스트
        self.current_layer = 0  # 재 활성화된 레이어
        
        # 비디오 처리 관련 속성은 유
        self.video_processor = VideoProcessor()
        self.current_frame_idx = 0
        
        # GUI 설정
        self.setup_gui()
        
        # GUI 설정 후  이어 생성
        self.add_new_layer()
        
        # 단축키 설정
        self.setup_shortcuts()
        
        self.screen_recorder = ScreenRecorder(self)

    def setup_shortcuts(self):
        """키보드 단축키 설정"""
        # Ctrl + Z: 실행 취소
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.undo)
        
        # Ctrl + Y: 다시 실행 (또는 Ctrl + Shift + Z)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_shortcut.activated.connect(self.redo)
        redo_shortcut2 = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        redo_shortcut2.activated.connect(self.redo)

    def setup_gui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 전체 레이아웃
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 상단 툴바 영역
        top_toolbar = QHBoxLayout()
        self.setup_top_toolbar(top_toolbar)
        
        # 메인 영역 (왼쪽 도구 패널 + 이미지 영역)
        content_layout = QHBoxLayout()
        
        # 왼쪽 도구 패널
        self.tool_layout = QVBoxLayout()
        self.setup_tool_panel(self.tool_layout)
        
        # 도구 패널 위젯 생성 및 설정
        tool_widget = QWidget()
        tool_widget.setLayout(self.tool_layout)
        tool_widget.setFixedWidth(170)
        
        # 이미지 표시 영역
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border: 1px solid #333333;
            }
        """)
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.mouse_press
        self.image_label.mouseReleaseEvent = self.mouse_release
        self.image_label.mouseMoveEvent = self.mouse_move
        
        # 스크롤 영역 추가
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        
        # 레에 위젯 가
        content_layout.addWidget(tool_widget)
        content_layout.addWidget(scroll_area)
        
        # 메인 레이아웃에 추
        main_layout.addLayout(top_toolbar)
        main_layout.addLayout(content_layout)
        
        #  
        self.current_image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        self.update_image_display()

    def setup_top_toolbar(self, layout):
        """상단 툴바 설정"""
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-bottom: 1px solid #333333;
            }
            QPushButton {
                min-width: 80px;
                min-height: 30px;
                padding: 5px 15px;
                border: none;
                background-color: transparent;
                color: #ffffff;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QMenu {
                background-color: #383838;
                border: 1px solid #555555;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #0d47a1;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 5px 0px;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setSpacing(0)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)

        # 파일 메뉴
        file_button = QPushButton(" 파일")
        file_menu = QMenu(self)
        file_menu.addAction("📂 열기", lambda: self.handle_file_menu("열기"))
        file_menu.addAction("💾 저장", lambda: self.handle_file_menu("저장"))
        file_button.clicked.connect(lambda: file_menu.exec_(file_button.mapToGlobal(file_button.rect().bottomLeft())))

        # 편집 메뉴
        edit_button = QPushButton("✏️ 편집")
        edit_menu = QMenu(self)
        edit_menu.addAction("↩️ 실행 취소", lambda: self.handle_edit_menu("실행 취소"))
        edit_menu.addAction("↪️ 다시 실행", lambda: self.handle_edit_menu("다시 실행"))
        edit_button.clicked.connect(lambda: edit_menu.exec_(edit_button.mapToGlobal(edit_button.rect().bottomLeft())))

        # 카메라 버튼 추가
        camera_button = QPushButton("📹 카메라")
        camera_button.clicked.connect(self.open_camera)

        # 카메 녹화 버튼 추가
        camera_record_button = QPushButton("📹 카메라 녹화")
        camera_record_button.setCheckable(True)
        camera_record_button.clicked.connect(self.toggle_camera_recording)
        
        # 필터 메뉴
        filter_button = QPushButton("🎨 필터")
        filter_menu = QMenu(self)
        filter_items = {
            '흑백': '⚫',
            '블러': '🌫️',
            '선명하게': '✨',
            '밝기 증가': '☀️',
            '대비 증가': '🌗',
            '모자이크': '🔲',
            '세피아': '📜',
            '카툰': '🎨',
            '스케치': '✏️'
        }
        
        for name, icon in filter_items.items():
            filter_menu.addAction(f"{icon} {name}", lambda n=name: self.apply_filter_from_menu(n))
        filter_button.clicked.connect(lambda: filter_menu.exec_(filter_button.mapToGlobal(filter_button.rect().bottomLeft())))

        # 엣지 검출 버튼 추가
        edge_button = QPushButton("📐 엣지")
        edge_menu = QMenu(self)
        edge_items = {
            '엣지-캐니': EdgeFilter('canny'),
            '엣지-소벨': EdgeFilter('sobel'),
            '엣지-라플라시안': EdgeFilter('laplacian'),
            '엣지-프리윗': EdgeFilter('prewitt')
        }
        
        for name, filter_obj in edge_items.items():
            action = edge_menu.addAction(name)
            action.triggered.connect(lambda checked, name=name: self.apply_filter_from_menu(name))
            self.filters[name] = filter_obj
        
        edge_button.clicked.connect(lambda: edge_menu.exec_(edge_button.mapToGlobal(edge_button.rect().bottomLeft())))

        # 모폴로지 메뉴
        morph_button = QPushButton("🔄 모폴로지")
        morph_menu = QMenu(self)
        morph_items = {
            '모폴로지-팽창': '➡️',
            '모폴로지-침식': '⬅️',
            '모폴로지-열기': '⬆️',
            '모폴로지-닫기': '⬇️'
        }
        for name, icon in morph_items.items():
            morph_menu.addAction(f"{icon} {name}", lambda n=name: self.apply_filter_from_menu(n))
        morph_button.clicked.connect(lambda: morph_menu.exec_(morph_button.mapToGlobal(morph_button.rect().bottomLeft())))

        # 레이아웃에 추가
        toolbar_layout.addWidget(file_button)
        toolbar_layout.addWidget(edit_button)
        toolbar_layout.addWidget(camera_button)
        toolbar_layout.addWidget(camera_record_button)  # 카메라 녹화 버튼만 남김
        toolbar_layout.addWidget(filter_button)
        toolbar_layout.addWidget(edge_button)
        toolbar_layout.addWidget(morph_button)
        toolbar_layout.addStretch()

        layout.addWidget(toolbar_widget)

    def handle_file_menu(self, action):
        """파일 메뉴 처리"""
        if action == "열기":
            self.open_image()
        elif action == "저장":
            self.save_image()

    def handle_edit_menu(self, action):
        """편집 메뉴 처리"""
        if action == "실행 취소":
            self.undo()
        elif action == "다시 실행":
            self.redo()

    def handle_tools_menu(self, action):
        """도구 메뉴 처리"""
        if action == "카메라":
            self.open_camera()
        elif action == "파노라마":
            dialog = PanoramaDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                if dialog.image1 is not None and dialog.image2 is not None:
                    panorama = self.panorama_tool.create_panorama(dialog.image1, dialog.image2)
                    if panorama is not None:
                        self.current_image = panorama
                        self.update_image_display()
                        self.history_manager.add(self.current_image.copy())
                        self.statusBar().showMessage("파노라마 생성되었습니다.")
                    else:
                        QMessageBox.warning(self, "오류", "파노라마 생성에 실패했습다.")

    def apply_filter_from_menu(self, filter_name):
        """메뉴에서 필터 적용"""
        if filter_name in self.filters:
            # 필터가 처음 적용되는 경우
            if not hasattr(self.filters[filter_name], 'is_applied'):
                self.filters[filter_name].is_applied = False
            
            if not self.filters[filter_name].is_applied:
                # 필터 적용
                if not hasattr(self, 'original_image') or self.original_image is None:
                    self.original_image = self.current_image.copy()
                
                self.current_image = self.filters[filter_name].apply(self.current_image.copy())
                self.filters[filter_name].is_applied = True
            else:
                # 필터 해제
                if hasattr(self, 'original_image') and self.original_image is not None:
                    self.current_image = self.original_image.copy()
                self.filters[filter_name].is_applied = False
            
            self.update_image_display()
            self.history_manager.add(self.current_image.copy())

    def create_toolbar_button(self, icon_text, tooltip):
        button = QPushButton(icon_text)
        button.setToolTip(tooltip)
        return button

    def setup_tool_panel(self, layout):
        """왼쪽 도구 패널 설정"""
        # QToolBox 생성
        tool_box = QToolBox()
        tool_box.setStyleSheet("""
            QToolBox::tab {
                background: #2d2d2d;
                border: 1px solid #333333;
                border-radius: 3px;
                color: white;
                padding: 5px;
            }
            QToolBox::tab:selected {
                background: #0d47a1;
                font-weight: bold;
            }
            QToolBox::tab:hover {
                background: #3d3d3d;
            }
            QWidget {
                background: #1e1e1e;
            }
        """)
        
        # 그리기 도구 페이지
        drawing_page = QWidget()
        drawing_layout = QVBoxLayout(drawing_page)
        drawing_tools = [
            ("✏️ 펜", "펜 도구", 'pen'),
            ("🧽 지우개", "지우개", 'eraser'),
            ("🔷 다각형", "다각형", 'polygon'),
            ("⭕ 원", "원", 'circle'),
            ("📝 텍스트", "텍스트", 'text')
        ]
        for text, tooltip, tool_name in drawing_tools:
            button = self.create_tool_button(text, tooltip, tool_name)
            drawing_layout.addWidget(button)
        drawing_layout.addStretch()
        
        # 편집 도구 페이지
        edit_page = QWidget()
        edit_layout = QVBoxLayout(edit_page)
        edit_tools = [
            ("🎯 선택", "선택", 'select'),
            ("🔲 모자이크", "모자이크", 'mosaic'),
            ("📄 문서 스캔", "문서 스캔", 'scan'),
            ("️🖼️ 배경 제거", "배경 제거", 'bg_removal'),
            ("🌅 파노라마", "파노라마 생성", 'panorama')
        ]
        for text, tooltip, tool_name in edit_tools:
            button = self.create_tool_button(text, tooltip, tool_name)
            edit_layout.addWidget(button)
        edit_layout.addStretch()
        
        # 색상 및 선 굵기 페이지
        style_page = QWidget()
        style_layout = QVBoxLayout(style_page)
        
        color_button = self.create_tool_button("🎨 색상 선택", "색상 선택")
        color_button.clicked.connect(self.select_color)
        style_layout.addWidget(color_button)
        
        thickness_label = QLabel("선 굵기")
        style_layout.addWidget(thickness_label)
        
        thickness_slider = QSlider(Qt.Horizontal)
        thickness_slider.setMinimum(1)
        thickness_slider.setMaximum(20)
        thickness_slider.setValue(2)
        thickness_slider.valueChanged.connect(self.set_thickness)
        style_layout.addWidget(thickness_slider)
        style_layout.addStretch()
        
        # 합성 도구 페이지
        blend_page = QWidget()
        blend_layout = QVBoxLayout(blend_page)
        
        blend_button = self.create_tool_button("🔀 알파 블렌딩", "이미지 합성", 'blend')
        blend_layout.addWidget(blend_button)
        
        self.blend_slider = QSlider(Qt.Horizontal)
        self.blend_slider.setMinimum(0)
        self.blend_slider.setMaximum(100)
        self.blend_slider.setValue(50)
        self.blend_slider.setEnabled(False)
        self.blend_slider.valueChanged.connect(self.update_blend_alpha)
        blend_layout.addWidget(self.blend_slider)
        
        self.blend_value_label = QLabel("50%")
        self.blend_value_label.setAlignment(Qt.AlignCenter)
        blend_layout.addWidget(self.blend_value_label)
        
        chromakey_button = self.create_tool_button("🎬 크로마키", "크로마키 합성", 'chromakey')
        blend_layout.addWidget(chromakey_button)
        
        seamless_button = self.create_tool_button(" 자연스러운 합성", "자연스러운 합성", 'seamless')
        blend_layout.addWidget(seamless_button)
        
        blend_layout.addStretch()
        
        # 레디오 도구 페이지 수정
        video_page = QWidget()
        video_layout = QVBoxLayout(video_page)
        
        # 비디오 관련 버튼들
        video_tools = [
            ("📹 비디오 열기", "비디오 파일 열기", self.load_video),
            ("⏯️ 재생/일시정지", "비디오 재생 또는 일시정지", self.toggle_play),
            ("👁️ 물체 추적", "물체 추적 켜기/끄기", self.toggle_tracking),
            ("🎯 물체 감지", "물체 감지 켜기/끄기", self.toggle_detection),  # 추가
        ]
        
        for text, tooltip, callback in video_tools:
            button = QPushButton(text)
            button.setStyleSheet(self.button_style)
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            video_layout.addWidget(button)
        
        # 프레임 이동 슬라이더
        frame_label = QLabel("프레임 이동")
        video_layout.addWidget(frame_label)
        
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setEnabled(False)
        self.frame_slider.valueChanged.connect(self.frame_changed)
        video_layout.addWidget(self.frame_slider)
        
        video_layout.addStretch()
        
        # 툴박스에 페이지들 추가
        tool_box.addItem(drawing_page, "🎨 그림 도구")
        tool_box.addItem(edit_page, "✂️ 편집 도구")
        tool_box.addItem(style_page, "🖌️ 스타일")
        tool_box.addItem(blend_page, "🔀 합성")
        tool_box.addItem(video_page, "📹 비디오")  # 비디오 페이지 추가
        
        layout.addWidget(tool_box)

    def create_tool_button(self, text, tooltip, tool_name=None):
        button = QPushButton(text)
        button.setStyleSheet(self.button_style)
        button.setToolTip(tooltip)
        if tool_name:
            button.setCheckable(True)
            button.clicked.connect(lambda: self.set_current_tool(tool_name))
        return button

    def set_current_tool(self, tool_name):
        if tool_name == 'panorama':
            dialog = PanoramaDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                if dialog.image1 is not None and dialog.image2 is not None:
                    panorama = self.panorama_tool.create_panorama(dialog.image1, dialog.image2)
                    if panorama is not None:
                        self.current_image = panorama
                        self.update_image_display()
                        self.history_manager.add(self.current_image.copy())
                        self.statusBar().showMessage("파노라마가 생성되었습니다.")
                    else:
                        QMessageBox.warning(self, "오류", "파노라마 생성에 실패했습니다.")
            # 버튼 선택 태 해
            for child in self.findChildren(QPushButton):
                if child.isChecked():
                    child.setChecked(False)
            return  # 파노라마 도구는 여기서 처리 종료

        # 다른 도구들 처리
        self.current_tool = self.tools[tool_name]
        
        if tool_name == 'chromakey':
            dialog = ChromakeyDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                result = self.current_tool.apply_chromakey(dialog)
                if result is not None:
                    self.current_image = result
                    self.update_image_display()
                    self.history_manager.add(self.current_image.copy())
        elif tool_name == 'seamless':
            dialog = SeamlessCloneDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                result = self.current_tool.apply_seamless_clone(dialog)
                if result is not None:
                    self.current_image = result
                    self.update_image_display()
                    self.history_manager.add(self.current_image.copy())
        elif tool_name == 'bg_removal':
            result = self.current_tool.remove_background(self.current_image.copy())
            if result is not None:
                self.current_image = result
                self.update_image_display()
                self.history_manager.add(self.current_image.copy())
        else:
            # 합 도구가 선택된 경우
            if tool_name == 'blend':
                dialog = ImageSelectDialog(self)
                if dialog.exec_() == QDialog.Accepted:
                    if dialog.image1 is not None and dialog.image2 is not None:
                        self.current_tool.set_images(dialog.image1, dialog.image2)
                        self.current_tool.set_parent(self)
                        
                        # 슬라이더 활성화
                        self.blend_slider.setEnabled(True)
                        
                        # 초기 블딩 적용
                        self.current_image = self.current_tool.blend_images(self.current_image)
                        self.update_image_display()
            else:
                # 다른 도구 택시 슬라더 비활성화
                if hasattr(self, 'blend_slider'):
                    self.blend_slider.setEnabled(False)
        
        # 형 가 선면 각 수 설정
        if tool_name == 'polygon':
            if not self.current_tool.set_sides():
                # 취소하면 이전 도로 돌감
                for child in self.findChildren(QPushButton):
                    if child.isChecked():
                        child.setChecked(False)

    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_tool.set_color((color.red(), color.green(), color.blue()))
            
    def set_thickness(self, value):
        self.current_tool.set_thickness(value)

    def mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.get_image_position(event.pos())
            if pos:
                self.is_drawing = True
                self.current_image = self.current_tool.on_press(self.current_image.copy(), pos)
                self.update_image_display()
        elif event.button() == Qt.RightButton and isinstance(self.current_tool, SelectionTool):
            # 택 도구에 대한 컨텍스트 메
            menu = QMenu(self)
            
            copy_action = QAction("복사", self)
            copy_action.triggered.connect(lambda: self.copy_selection())
            
            paste_action = QAction("붙여넣기", self)
            paste_action.triggered.connect(lambda: self.paste_selection(event.pos()))
            
            delete_action = QAction("삭제", self)
            delete_action.triggered.connect(lambda: self.delete_selection())
            
            menu.addAction(copy_action)
            menu.addAction(paste_action)
            menu.addAction(delete_action)
            
            menu.exec_(event.globalPos())

    def copy_selection(self):
        if isinstance(self.current_tool, SelectionTool):
            self.clipboard_content = self.current_tool.copy_selection(self.current_image)
            if self.clipboard_content is not None:
                self.history_manager.add(self.current_image.copy())

    def paste_selection(self, pos):
        if isinstance(self.current_tool, SelectionTool) and hasattr(self, 'clipboard_content'):
            pos = self.get_image_position(pos)
            if pos:
                self.current_image = self.current_tool.paste_selection(
                    self.current_image.copy(), pos)
                self.update_image_display()
                self.history_manager.add(self.current_image.copy())

    def delete_selection(self):
        if isinstance(self.current_tool, SelectionTool):
            self.current_image = self.current_tool.delete_selection(self.current_image.copy())
            self.update_image_display()
            self.history_manager.add(self.current_image.copy())

    def mouse_move(self, event):
        pos = self.get_image_position(event.pos())
        if pos and hasattr(self, 'is_drawing') and self.is_drawing:
            self.current_image = self.current_tool.on_move(self.current_image.copy(), pos)
            self.update_image_display()

    def mouse_release(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, 'is_drawing'):
            self.is_drawing = False
            pos = self.get_image_position(event.pos())
            if pos:
                self.current_image = self.current_tool.on_release(self.current_image.copy(), pos)
                self.history_manager.add(self.current_image.copy())
                self.update_image_display()

    def get_image_position(self, pos):
        """위젯 좌표를 미지 좌표로 변환"""
        if self.image_label.pixmap():
            rect = self.image_label.geometry()
            scaled_rect = self.image_label.pixmap().rect()
            
            x_offset = (rect.width() - scaled_rect.width()) // 2
            y_offset = (rect.height() - scaled_rect.height()) // 2
            
            x = pos.x() - x_offset
            y = pos.y() - y_offset
            
            if (0 <= x < scaled_rect.width() and 
                0 <= y < scaled_rect.height()):
                return QPoint(x, y)
        return None

    def update_image_display(self):
        """이미지 업데이트"""
        height, width = self.current_image.shape[:2]
        new_width = int(width * self.zoom_level)
        new_height = int(height * self.zoom_level)
        
        resized = cv2.resize(self.current_image, (new_width, new_height))
        
        # 카메라 녹화 중일 때만 REC 표시
        if hasattr(self, 'screen_recorder') and self.screen_recorder.recording:
            # 녹화 표시 추가
            preview_frame = resized.copy()
            cv2.circle(preview_frame, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(preview_frame, "REC", (45, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            resized = preview_frame
        
        bytes_per_line = 3 * new_width
        from PyQt5.QtGui import QImage, QPixmap
        
        q_img = QImage(
            resized.data,
            new_width,
            new_height,
            bytes_per_line,
            QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap)

    def toggle_filter(self, filter_obj, action):
        """필터 토글"""
        self.current_image = filter_obj.toggle(self.current_image.copy())
        self.update_image_display()
        self.history_manager.add(self.current_image.copy())
        
        # 다른 필터들 체크 상태 해제
        menu = action.parent()
        if isinstance(menu, QMenu):
            for other_action in menu.actions():
                if other_action != action and other_action.isChecked():
                    other_action.setChecked(False)
                    if hasattr(self.filters[other_action.text()], 'is_applied'):
                        self.filters[other_action.text()].is_applied = False

    def undo(self):
        """행 취소"""
        self.current_image = self.history_manager.undo(self.current_image)
        self.update_image_display()

    def redo(self):
        """시 실행"""
        self.current_image = self.history_manager.redo(self.current_image)
        self.update_image_display()

    def save_image(self):
        """이미지 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "이미지 저장", "", 
            "Images (*.png *.jpg);;All Files (*.*)")
        if file_path:
            cv2.imwrite(file_path, cv2.cvtColor(self.current_image, cv2.COLOR_RGB2BGR))

    def open_image(self):
        """이미지 열기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "이미지 열기", "", 
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)")
        if file_path:
            image = cv2.imread(file_path)
            if image is not None:
                self.current_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.update_image_display()
                self.history_manager.add(self.current_image.copy())
        
    def zoom_in(self):
        self.zoom_level *= 1.2
        self.update_image_display()
    
    def zoom_out(self):
        self.zoom_level /= 1.2
        self.update_image_display()
        
    def open_camera(self):
        """카메라 다이얼로그 열기"""
        dialog = CameraDialog(self)
        dialog.exec_()
    
    def set_current_image(self, image):
        """카메라로 찍은 이미지 설정"""
        self.current_image = image
        self.update_image_display()
        self.history_manager.add(self.current_image.copy())
        
    def create_separator(self):
        """구분선 생성"""
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator

    def setup_filter_menu(self, menu, filter_names):
        """필터 메뉴 설정"""
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                padding: 5px;
                color: #ffffff;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #0d47a1;
            }
        """)
        
        for filter_name in filter_names:
            action = menu.addAction(filter_name)
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked, f=self.filters[filter_name], a=action: 
                self.toggle_filter(f, a)
            )
    
    def add_new_layer(self):
        """새 레이블 추가"""
        new_layer = np.ones((600, 800, 3), dtype=np.uint8) * 255  # 흰색 배경
        self.layers.append(new_layer)
        self.current_layer = len(self.layers) - 1
        self.update_layer_display()
    
    def highlight_selected_layer(self, layer_index):
        """선택된 레이어 강조 표시"""
        self.current_layer = layer_index
        self.update_layer_display()
    
    def update_layer_display(self):
        """모든 레이어를 합성하여 표시"""
        if not self.layers:
            return
            
        # 레이어 합성
        result = self.layers[0].copy()
        for layer in self.layers[1:]:
            # 알파 블렌딩으로 레이어 합성
            mask = (layer < 255).any(axis=2)
            result[mask] = layer[mask]
        
        self.current_image = result
        self.update_image_display()
    
    def update_blend_alpha(self, value):
        if isinstance(self.current_tool, BlendTool):
            self.blend_value_label.setText(f"{value}%")
            self.current_tool.alpha = value / 100
            self.current_image = self.current_tool.blend_images(self.current_image)
            self.update_image_display()
    

    # 비디오 관 다른 메서들은 유지
    def load_video(self):
        """비디오 ���일을 로드합니다."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "비디오 파일 선택",
            "",
            "Video Files (*.mp4 *.avi *.mov *.wmv)"
        )
        
        if file_path:
            if self.video_processor.load_video(file_path):
                # 비디오가 로드되면 슬라이더 설정
                self.frame_slider.setEnabled(True)
                self.frame_slider.setMinimum(0)
                self.frame_slider.setMaximum(self.video_processor.get_frame_count() - 1)
                self.show_frame(0)
    
    def show_frame(self, frame_idx):
        """표시된 프레임을 화면에 표시합니다."""
        frame = self.video_processor.get_frame(frame_idx)
        if frame is not None:
            self.current_image = frame
            self.update_image_display()
    
    def toggle_play(self):
        """비디오 재생/일시정지 합니다."""
        if not hasattr(self, 'play_timer'):
            self.play_timer = QTimer()
            self.play_timer.timeout.connect(self.play_next_frame)
            self.is_playing = False
        
        if self.is_playing:
            self.play_timer.stop()
            self.is_playing = False
        else:
            if self.video_processor.is_loaded():
                self.play_timer.start(1000 // 30)  # 30 FPS
                self.is_playing = True
    
    def play_next_frame(self):
        """다 프레임을 재생합니다."""
        if self.video_processor.is_loaded():
            self.current_frame_idx += 1
            if self.current_frame_idx >= self.video_processor.get_frame_count():
                self.current_frame_idx = 0
            
            # 프레임 가져오기
            frame = self.video_processor.get_frame(self.current_frame_idx)
            if frame is not None:
                # 현재 적용된 필터들을 프레임에 적용
                for filter_name, filter_obj in self.filters.items():
                    if hasattr(filter_obj, 'is_applied') and filter_obj.is_applied:
                        frame = filter_obj.apply(frame)
                
                self.current_image = frame
                self.update_image_display()
            
            if hasattr(self, 'frame_slider'):
                self.frame_slider.setValue(self.current_frame_idx)
    
    def frame_changed(self, value):
        """프레임 슬레이더 값이 변경 되었을 때 호출됩니."""
        if self.video_processor.is_loaded():
            self.current_frame_idx = value
            self.show_frame(value)
    
    def toggle_tracking(self):
        """물체 추적 기능을 켭니다."""
        if self.video_processor.is_loaded():
            is_tracking = self.video_processor.toggle_tracking()
            # 현 프레임을 다시 표시하여 변경사항 반영
            self.show_frame(self.current_frame_idx)
            
            # 버튼 상태 업데이트 (선택사)
            sender = self.sender()
            if sender:
                sender.setChecked(is_tracking)
    
    def restore_original_image(self):
        """필터 메뉴가 닫힐 때 원본 이미지 복ㄴ원"""
        if hasattr(self, 'original_image') and self.original_image is not None:
            self.current_image = self.original_image.copy()
            self.update_image_display()
            self.original_image = None
    
    def toggle_recording(self):
        sender = self.sender()
        if sender.isChecked():
            # 녹화 시작
            height, width = self.current_image.shape[:2]
            self.screen_recorder.start_recording((width, height))
            sender.setText("⏹️ 녹화 중지")
            self.statusBar().showMessage("녹화를 시작했습니다.")
        else:
            # 녹화 중지
            self.screen_recorder.stop_recording()
            sender.setText("🔴 녹화")
            self.statusBar().showMessage("녹��가 저장되었습니다.")

    def toggle_camera_recording(self):
        """카메라 녹화 글"""
        sender = self.sender()
        if sender.isChecked():
            # 카메라 녹화 시작
            if self.screen_recorder.start_camera_recording():
                sender.setText("⏹️ 카메라 녹화 중지")
                self.statusBar().showMessage("카메라 녹화를 시작했습니다.")
                
                # 카메라 프레임 업데이트 타이머 시작
                self.camera_timer = QTimer()
                self.camera_timer.timeout.connect(self.update_camera_frame)
                self.camera_timer.start(33)  # 약 30fps
            else:
                sender.setChecked(False)
                QMessageBox.warning(self, "오류", "카메라를 시작할 수 없습니다.")
        else:
            # 카메라 녹화 중지
            self.screen_recorder.stop_camera_recording()
            sender.setText("📹 카메라 녹화")
            self.statusBar().showMessage("카메라 녹화가 저장되었습니다.")
            if hasattr(self, 'camera_timer'):
                self.camera_timer.stop()

    def update_camera_frame(self):
        """메라 프레임 업데이트"""
        frame = self.screen_recorder.capture_camera_frame()
        if frame is not None:
            self.current_image = frame
            self.update_image_display()

    def capture_frame(self):
        """현재 프레임을 이미지로 저장"""
        if self.video_processor.is_loaded():
            frame = self.video_processor.get_frame(self.current_frame_idx)
            if frame is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"frame_capture_{timestamp}.jpg"
                cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                self.statusBar().showMessage(f"프레임이 {filename}으로 저장되었습니다.")

    def prev_frame(self):
        """이전 프레임으로 이동"""
        if self.video_processor.is_loaded():
            self.current_frame_idx = max(0, self.current_frame_idx - 1)
            self.show_frame(self.current_frame_idx)
            self.frame_slider.setValue(self.current_frame_idx)

    def next_frame(self):
        """다음 프레임으로 이동"""
        if self.video_processor.is_loaded():
            max_frames = self.video_processor.get_frame_count() - 1
            self.current_frame_idx = min(max_frames, self.current_frame_idx + 1)
            self.show_frame(self.current_frame_idx)
            self.frame_slider.setValue(self.current_frame_idx)

    def toggle_loop(self):
        """반복 재생 설정"""
        if not hasattr(self, 'loop_enabled'):
            self.loop_enabled = False
        self.loop_enabled = not self.loop_enabled
        sender = self.sender()
        if sender:
            sender.setChecked(self.loop_enabled)
        status = "켜짐" if self.loop_enabled else "꺼짐"
        self.statusBar().showMessage(f"반복 재생: {status}")

    def setup_video_controls(self):
        # 재생 속도 조절 슬라이더 추가
        speed_layout = QHBoxLayout()
        speed_label = QLabel("재생 속도:")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(25)  # 0.25x
        self.speed_slider.setMaximum(400)  # 4x
        self.speed_slider.setValue(100)    # 1x (기본값)
        self.speed_slider.valueChanged.connect(self.update_playback_speed)
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        
    def update_playback_speed(self, value):
        """재생 속도 업데이트"""
        if hasattr(self, 'play_timer'):
            speed = value / 100.0  # 1.0이 정상 속도
            interval = int(1000 / (30 * speed))  # 30 FPS 기준
            if self.is_playing:
                self.play_timer.setInterval(interval)
            self.statusBar().showMessage(f"재생 속도: {speed:.2f}x")

    def setup_video_tools(self):
        # 비디오 관련 버튼들
        video_tools = [
            ("📹 비디오 열기", "비디오 파일 열기", self.load_video),
            ("⏯️ 재생/일시정지", "비디오 재생 또는 일시정지", self.toggle_play),
            ("👁️ 물체 추적", "물체 추적 켜기/끄기", self.toggle_tracking),
            ("🎯 물체 감지", "물체 감지 켜기/끄기", self.toggle_detection),  # 추가
        ]
        
        for text, tooltip, callback in video_tools:
            button = QPushButton(text)
            button.setStyleSheet(self.button_style)
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            self.tool_layout.addWidget(button)
        
        # 구간 반복 버튼 추가
        repeat_layout = QHBoxLayout()
        set_start_btn = QPushButton("구간 시작 설정")
        set_end_btn = QPushButton("구간 끝 설정")
        clear_repeat_btn = QPushButton("구간 초기화")
        
        set_start_btn.clicked.connect(self.set_repeat_start)
        set_end_btn.clicked.connect(self.set_repeat_end)
        clear_repeat_btn.clicked.connect(self.clear_repeat_points)
        
        repeat_layout.addWidget(set_start_btn)
        repeat_layout.addWidget(set_end_btn)
        repeat_layout.addWidget(clear_repeat_btn)
        
        self.tool_layout.addLayout(repeat_layout)

    def set_repeat_start(self):
        """구간 반복 시작점 설정"""
        self.start_point = self.current_frame_idx
        self.statusBar().showMessage(f"구간 시작: {self.start_point} 프레임")

    def set_repeat_end(self):
        """구간 반복 끝점 설정"""
        self.end_point = self.current_frame_idx
        self.statusBar().showMessage(f"구간 끝: {self.end_point} 프레임")

    def clear_repeat_points(self):
        """구간 반복 설정 초기화"""
        self.start_point = None
        self.end_point = None
        self.statusBar().showMessage("구간 반복 설정이 초기화되었습니다.")

    def toggle_detection(self):
        """물체 감지 기능을 켭니다."""
        if self.video_processor.is_loaded():
            is_detecting = self.video_processor.toggle_detection()
            # 현재 프레임을 다시 표시하여 변경사항 반영
            self.show_frame(self.current_frame_idx)
            
            # 버튼 상태 업데이트
            sender = self.sender()
            if sender:
                sender.setChecked(is_detecting)