from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QFormLayout, QComboBox,
                              QFileDialog, QMessageBox, QGroupBox, QScrollArea,
                              QWidget, QCheckBox)
from PySide6.QtCore import Qt
import os
import json
import copy

class StepConfigDialog(QDialog):
    """步骤配置对话框"""
    def __init__(self, step_data=None, parent=None):
        super().__init__(parent)
        self.step_data = copy.deepcopy(step_data) if step_data else {}
        self.init_ui()
        self.load_step_data()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("步骤配置")
        self.resize(600, 500)
        
        main_layout = QVBoxLayout()
        
        # 步骤基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        basic_layout.addRow("步骤名称:", self.name_edit)
        
        self.script_combo = QComboBox()
        self.load_available_scripts()
        self.script_combo.currentIndexChanged.connect(self.on_script_changed)
        basic_layout.addRow("脚本:", self.script_combo)
        
        basic_group.setLayout(basic_layout)
        main_layout.addWidget(basic_group)
        
        # 参数配置
        params_group = QGroupBox("参数配置")
        self.params_layout = QFormLayout()
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.params_layout)
        scroll_area.setWidget(scroll_widget)
        
        params_layout = QVBoxLayout()
        params_layout.addWidget(scroll_area)
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def load_available_scripts(self):
        """加载可用脚本"""
        scripts = [
            {"name": "图像裁剪", "script": "cli/cutting_cli.py"},
            {"name": "HSV颜色检测", "script": "cli/hsv_batch_cli.py"},
            {"name": "TXT转SHP", "script": "cli/txt_to_shp_cli.py"},
            {"name": "合并SHP", "script": "cli/merge_shp_cli.py"},
            {"name": "SHP框裁剪", "script": "cli/shp_kuang_cut_cli.py"},
            {"name": "文件提取", "script": "cli/tiqu_cli.py"},
            {"name": "创建TXT文件", "script": "cli/create_txt_cli.py"},
            {"name": "VIT推理", "script": "cli/vit_predict_cli.py"},
            {"name": "YOLO推理", "script": "cli/yolo_predict_cli.py"}
        ]
        
        for script in scripts:
            self.script_combo.addItem(script["name"], script["script"])
    
    def on_script_changed(self):
        """脚本变更时更新参数表单"""
        script = self.script_combo.currentData()
        if not script:
            return
            
        # 清除现有参数表单
        self.clear_params_form()
        
        # 根据脚本类型添加参数表单
        if "cutting_cli.py" in script:
            self.add_cutting_params()
        elif "hsv_batch_cli.py" in script:
            self.add_hsv_params()
        elif "txt_to_shp_cli.py" in script:
            self.add_txt_to_shp_params()
        elif "merge_shp_cli.py" in script:
            self.add_merge_shp_params()
        elif "shp_kuang_cut_cli.py" in script:
            self.add_shp_kuang_cut_params()
        elif "tiqu_cli.py" in script:
            self.add_tiqu_params()
        elif "create_txt_cli.py" in script:
            self.add_create_txt_params()
        elif "vit_predict_cli.py" in script:
            self.add_vit_predict_params()
        elif "yolo_predict_cli.py" in script:
            self.add_yolo_predict_params()
    
    def clear_params_form(self):
        """清除参数表单"""
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)
        
        self.param_widgets = {}
    
    def add_cutting_params(self):
        """添加裁剪参数表单"""
        self.add_param("input", "输入栅格图像路径:", "file", filter="栅格图像 (*.tif *.tiff)")
        self.add_param("output-image", "输出小图文件夹路径:", "folder")
        self.add_param("output-tfw", "输出TFW文件夹路径:", "folder")
        self.add_param("crop-size-x", "裁剪宽度(像素):", "number", default=800)
        self.add_param("crop-size-y", "裁剪高度(像素):", "number", default=800)
        self.add_param("step-size-x", "X方向步长(像素):", "number", default=800)
        self.add_param("step-size-y", "Y方向步长(像素):", "number", default=800)
    
    def add_hsv_params(self):
        """添加HSV颜色检测参数表单"""
        self.add_param("input", "输入图像文件夹路径:", "folder")
        self.add_param("output", "输出YOLO标签文件夹路径:", "folder")
    
    def add_txt_to_shp_params(self):
        """添加TXT转SHP参数表单"""
        self.add_param("tif-folder", "TIF图像文件夹路径:", "folder")
        self.add_param("tfw-folder", "TFW文件夹路径:", "folder")
        self.add_param("txt-folder", "YOLO标签文件夹路径:", "folder")
        self.add_param("output", "输出Shapefile文件夹路径:", "folder")
    
    def add_merge_shp_params(self):
        """添加合并SHP参数表单"""
        self.add_param("input", "包含Shapefile的文件夹路径:", "folder")
        self.add_param("output", "输出合并后的Shapefile路径:", "text")
        self.add_param("crs", "目标坐标参考系统:", "text", default="EPSG:4326")
    
    def add_shp_kuang_cut_params(self):
        """添加SHP框裁剪参数表单"""
        self.add_param("input", "输入栅格图像路径:", "file", filter="栅格图像 (*.tif *.tiff)")
        self.add_param("shapefile", "用于裁剪的Shapefile路径:", "file", filter="Shapefile (*.shp)")
        self.add_param("output", "输出裁剪后图像的文件夹路径:", "folder")
        self.add_param("scale", "缩放因子:", "number", default=1.0)
    
    def add_tiqu_params(self):
        """添加文件提取参数表单"""
        self.add_param("input", "输入文件夹路径:", "folder")
        self.add_param("output", "输出文件夹路径:", "folder")
        self.add_param("extension", "要提取的文件扩展名:", "text", default=".tif")
    
    def add_create_txt_params(self):
        """添加创建TXT文件参数表单"""
        self.add_param("input", "输入文件夹路径:", "folder")
        self.add_param("output", "输出TXT文件夹路径:", "folder")
    
    def add_vit_predict_params(self):
        """添加VIT推理参数表单"""
        self.add_param("img-dir", "输入图像文件夹路径:", "folder")
        self.add_param("txt-dir", "输入TXT文件夹路径:", "folder")
        self.add_param("output", "输出标签文件夹路径:", "folder")
        self.add_param("json-path", "类别索引JSON文件路径:", "file", filter="JSON文件 (*.json)")
        self.add_param("model-path", "模型权重文件路径:", "file", filter="模型文件 (*.pth)")
        self.add_param("use-cuda", "是否使用CUDA:", "checkbox", default=True)
    
    def add_yolo_predict_params(self):
        """添加YOLO推理参数表单"""
        self.add_param("input", "输入图像文件夹路径:", "folder")
        self.add_param("model", "YOLO模型路径:", "file", filter="模型文件 (*.pt)")
        self.add_param("output", "输出标签文件夹路径:", "folder")
        self.add_param("conf", "置信度阈值:", "number", default=0.3)
        self.add_param("iou", "IOU阈值:", "number", default=0.01)
        self.add_param("img-size", "图像大小:", "number", default=640)
    
    def add_param(self, name, label, type, default=None, filter=None):
        """添加参数表单项"""
        if type == "text":
            widget = QLineEdit()
            if default:
                widget.setText(str(default))
        elif type == "number":
            widget = QLineEdit()
            if default is not None:
                widget.setText(str(default))
            widget.setValidator(QDoubleValidator())
        elif type == "file":
            layout = QHBoxLayout()
            widget = QLineEdit()
            if default:
                widget.setText(str(default))
            layout.addWidget(widget)
            
            browse_button = QPushButton("浏览...")
            browse_button.clicked.connect(lambda: self.browse_file(widget, filter))
            layout.addWidget(browse_button)
            
            container = QWidget()
            container.setLayout(layout)
            self.params_layout.addRow(label, container)
            self.param_widgets[name] = widget
            return
        elif type == "folder":
            layout = QHBoxLayout()
            widget = QLineEdit()
            if default:
                widget.setText(str(default))
            layout.addWidget(widget)
            
            browse_button = QPushButton("浏览...")
            browse_button.clicked.connect(lambda: self.browse_folder(widget))
            layout.addWidget(browse_button)
            
            container = QWidget()
            container.setLayout(layout)
            self.params_layout.addRow(label, container)
            self.param_widgets[name] = widget
            return
        elif type == "checkbox":
            widget = QCheckBox()
            if default:
                widget.setChecked(default)
            
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.addWidget(widget)
            layout.addStretch()
            layout.setContentsMargins(0, 0, 0, 0)
            
            self.params_layout.addRow(label, container)
            self.param_widgets[name] = widget
            return
        
        self.params_layout.addRow(label, widget)
        self.param_widgets[name] = widget
    
    def browse_file(self, widget, filter):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", filter)
        if file_path:
            widget.setText(file_path)
    
    def browse_folder(self, widget):
        """浏览文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            widget.setText(folder_path)
    
    def load_step_data(self):
        """加载步骤数据"""
        if not self.step_data:
            return
            
        # 设置基本信息
        self.name_edit.setText(self.step_data.get("name", ""))
        
        script = self.step_data.get("script", "")
        for i in range(self.script_combo.count()):
            if self.script_combo.itemData(i) == script:
                self.script_combo.setCurrentIndex(i)
                break
        
        # 设置参数值
        params = self.step_data.get("params", {})
        for name, value in params.items():
            if name in self.param_widgets:
                widget = self.param_widgets[name]
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
    
    def get_step_data(self):
        """获取步骤数据"""
        step_data = {
            "name": self.name_edit.text(),
            "script": self.script_combo.currentData(),
            "params": {}
        }
        
        for name, widget in self.param_widgets.items():
            if isinstance(widget, QLineEdit):
                value = widget.text()
                # 尝试转换数字
                try:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
                step_data["params"][name] = value
            elif isinstance(widget, QCheckBox):
                step_data["params"][name] = widget.isChecked()
        
        return step_data