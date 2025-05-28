from PySide6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget,
                              QStatusBar, QToolBar,  QLabel)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction

from modules.preprocessing import PreprocessingModule
from modules.model_management import ModelManagementModule
from modules.postprocessing import PostprocessingModule
from modules.pipeline import PipelineModule
from modules.inference import InferenceModule

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle("松科变色立木检测系统")
        self.setMinimumSize(1200, 800)
        self.setWindowIcon(QIcon("Qt/resources/icons/logo.png"))
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("系统就绪")
        
        # 创建工具栏
        self.toolbar = QToolBar("主工具栏")
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        
        # 添加工具栏按钮
        self.add_toolbar_actions()
        
        # 创建选项卡窗口
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(True)
        
        # 添加各个模块选项卡
        self.preprocessing_module = PreprocessingModule()
        self.model_management_module = ModelManagementModule()
        self.postprocessing_module = PostprocessingModule()
        self.pipeline_module = PipelineModule()
        self.inference_module = InferenceModule()
        
        self.tab_widget.addTab(self.preprocessing_module, "预处理管理")
        self.tab_widget.addTab(self.model_management_module, "推理模型管理")
        self.tab_widget.addTab(self.postprocessing_module, "后处理管理")
        self.tab_widget.addTab(self.pipeline_module, "Pipeline管理")
        self.tab_widget.addTab(self.inference_module, "推理")
        
        # 设置中央窗口
        self.setCentralWidget(self.tab_widget)
        
    def add_toolbar_actions(self):
        # 添加工具栏按钮
        self.home_action = QAction(QIcon("Qt/resources/icons/home.png"), "主页", self)
        self.home_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        
        self.settings_action = QAction(QIcon("Qt/resources/icons/settings.png"), "设置", self)
        self.settings_action.triggered.connect(self.show_settings)
        
        self.help_action = QAction(QIcon("Qt/resources/icons/help.png"), "帮助", self)
        self.help_action.triggered.connect(self.show_help)
        
        self.toolbar.addAction(self.home_action)
        self.toolbar.addAction(self.settings_action)
        self.toolbar.addAction(self.help_action)
        
    def show_settings(self):
        # 显示设置对话框
        self.statusBar.showMessage("设置功能尚未实现")
        
    def show_help(self):
        # 显示帮助对话框
        self.statusBar.showMessage("帮助功能尚未实现")