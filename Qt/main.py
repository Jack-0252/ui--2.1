import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from login import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    # 加载样式表
    # with open("Qt/resources/styles/style.qss", "r", encoding="utf-8") as f:
    #     app.setStyleSheet(f.read())
    
    # 显示登录窗口
    login_window = LoginWindow()
    login_window.show()
    
    sys.exit(app.exec())