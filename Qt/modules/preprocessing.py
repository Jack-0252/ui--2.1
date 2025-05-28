from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QListWidget, QListWidgetItem, QTextEdit, 
                              QPushButton, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

class PreprocessingModule(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 主布局
        main_layout = QHBoxLayout()
        
        # 左侧列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        list_label = QLabel("预处理工具列表")
        list_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.tool_list = QListWidget()
        self.tool_list.currentItemChanged.connect(self.show_tool_details)
        
        # 添加预处理工具
        tools = [
            {"name": "图像裁剪 (cutting)", "icon": "cut.png", "desc": "将大图裁剪为小图并生成TFW文件"},
            {"name": "SHP框裁剪 (shp_kuang_cut)", "icon": "crop.png", "desc": "根据Shapefile裁剪栅格图像"},
            {"name": "文件提取 (tiqu)", "icon": "extract.png", "desc": "从文件夹中提取特定扩展名的文件"},
            {"name": "创建TXT (create_txt)", "icon": "text.png", "desc": "为图像文件创建对应的TXT标签文件"}
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
        if "cutting" in tool_data["name"]:
            params = [
                ("--input, -i", "输入栅格图像路径", "必需"),
                ("--output-image, -oi", "输出小图文件夹路径", "必需"),
                ("--output-tfw, -ot", "输出TFW文件夹路径", "必需"),
                ("--crop-size-x, -cx", "裁剪宽度(像素)", "可选，默认800"),
                ("--crop-size-y, -cy", "裁剪高度(像素)", "可选，默认800"),
                ("--step-size-x, -sx", "X方向步长(像素)", "可选，默认800"),
                ("--step-size-y, -sy", "Y方向步长(像素)", "可选，默认800")
            ]
            example = "python cli/cutting_cli.py --input data/input.tif --output-image data/cut_tif_folder --output-tfw data/cut_tfw_folder --crop-size-x 640 --crop-size-y 640"
            
        elif "shp_kuang_cut" in tool_data["name"]:
            params = [
                ("--input, -i", "输入栅格图像路径", "必需"),
                ("--shapefile, -s", "用于裁剪的Shapefile路径", "必需"),
                ("--output, -o", "输出裁剪后图像的文件夹路径", "必需"),
                ("--scale, -sc", "缩放因子", "可选，默认1.0")
            ]
            example = "python cli/shp_kuang_cut_cli.py --input data/input.tif --shapefile data/areas.shp --output data/cropped_images --scale 1.5"
            
        elif "tiqu" in tool_data["name"]:
            params = [
                ("--input, -i", "输入文件夹路径", "必需"),
                ("--output, -o", "输出文件夹路径", "必需"),
                ("--extension, -e", "要提取的文件扩展名", "必需")
            ]
            example = "python cli/tiqu_cli.py --input data/mixed_files --output data/tif_files --extension .tif"
            
        elif "create_txt" in tool_data["name"]:
            params = [
                ("--input, -i", "输入文件夹路径", "必需"),
                ("--output, -o", "输出TXT文件夹路径", "必需")
            ]
            example = "python cli/create_txt_cli.py --input data/images --output data/labels"
        
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