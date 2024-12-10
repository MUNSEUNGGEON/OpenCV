import sys
import os
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 애플리케이션 스타일 설정
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    return app.exec_()

if __name__ == '__main__':
    main() 