from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QListWidget, QListWidgetItem, QTextEdit, 
                              QPushButton, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

class ModelManagementModule(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 主布局
        main_layout = QHBoxLayout()
        
        # 左侧列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        list_label = QLabel("推理模型工具列表")
        list_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.tool_list = QListWidget()
        self.tool_list.currentItemChanged.connect(self.show_tool_details)
        
        # 添加推理模型工具
        tools = [
            {"name": "HSV颜色检测 (hsv_batch_cli)", "icon": "hsv.png", "desc": "基于HSV颜色检测生成YOLO格式标签"},
            {"name": "VIT推理 (vit_predict_cli)", "icon": "vit.png", "desc": "使用VIT模型进行图像分类推理"},
            {"name": "YOLO推理 (yolo_predict_cli)", "icon": "yolo.png", "desc": "使用YOLO模型进行目标检测"}
        ]
        
        for tool in tools:
            item = QListWidgetItem(tool["name"])
            item.setData(Qt.UserRole, tool)
            self.tool_list.addItem(item)
        
        left_layout.addWidget(list_label)
        left_layout.addWidget(self.tool_list)
        
        # 右侧详情
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        
        self.tool_title = QLabel("选择一个工具查看详情")
        self.tool_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.tool_title.setAlignment(Qt.AlignCenter)
        
        self.tool_description = QTextEdit()
        self.tool_description.setReadOnly(True)
        self.tool_description.setMinimumHeight(100)
        
        # 参数说明区域
        self.params_group = QGroupBox("参数说明")
        self.params_layout = QGridLayout()
        self.params_group.setLayout(self.params_layout)
        
        # 使用示例区域
        self.example_group = QGroupBox("使用示例")
        self.example_layout = QVBoxLayout()
        self.example_text = QTextEdit()
        self.example_text.setReadOnly(True)
        self.example_layout.addWidget(self.example_text)
        self.example_group.setLayout(self.example_layout)
        
        self.right_layout.addWidget(self.tool_title)
        self.right_layout.addWidget(self.tool_description)
        self.right_layout.addWidget(self.params_group)
        self.right_layout.addWidget(self.example_group)
        
        # 设置左右布局比例
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 3)
        
        self.setLayout(main_layout)
        
    def show_tool_details(self, current, previous):
        if current is None:
            return
            
        tool_data = current.data(Qt.UserRole)
        self.tool_title.setText(tool_data["name"])
        self.tool_description.setText(tool_data["desc"])
        
        # 清除旧的参数说明
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # 根据不同工具显示不同参数
        if "hsv_batch_cli" in tool_data["name"]:
            params = [
                ("--input, -i", "输入图像文件夹路径", "必需"),
                ("--output, -o", "输出YOLO标签文件夹路径", "必需")
            ]
            example = "python cli/hsv_batch_cli.py --input data/images --output data/labels"
            
        elif "vit_predict_cli" in tool_data["name"]:
            params = [
                ("--img-dir, -i", "输入图像文件夹路径", "必需"),
                ("--txt-dir, -t", "输入TXT文件夹路径", "必需"),
                ("--output, -o", "输出标签文件夹路径", "必需"),
                ("--json-path, -j", "类别索引JSON文件路径", "必需"),
                ("--model-path, -m", "模型权重文件路径", "必需"),
                ("--use-cuda, -c", "是否使用CUDA", "可选，默认不使用")
            ]
            example = "python cli/vit_predict_cli.py --img-dir data/images --txt-dir data/labels --output data/results --json-path config/classes.json --model-path models/vit_model.pth --use-cuda"
            
        elif "yolo_predict_cli" in tool_data["name"]:
            params = [
                ("--input, -i", "输入图像文件夹路径", "必需"),
                ("--model, -m", "YOLO模型路径", "必需"),
                ("--output, -o", "输出标签文件夹路径", "必需"),
                ("--conf, -c", "置信度阈值", "可选，默认0.3"),
                ("--iou", "IOU阈值", "可选，默认0.01"),
                ("--img-size, -s", "图像大小", "可选，默认640")
            ]
            example = "python cli/yolo_predict_cli.py --input data/images --model models/yolo_model.pt --output data/results --conf 0.4 --img-size 640"
        
        # 添加参数说明
        for row, (param, desc, required) in enumerate(params):
            self.params_layout.addWidget(QLabel(param), row, 0)
            self.params_layout.addWidget(QLabel(desc), row, 1)
            req_label = QLabel(required)
            if "必需" in required:
                req_label.setStyleSheet("color: red;")
            self.params_layout.addWidget(req_label, row, 2)
        
        # 设置示例
        self.example_text.setText(example)