from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QListWidget, QListWidgetItem, 
                              QComboBox, QFileDialog, QInputDialog, QMessageBox,
                              QGroupBox, QScrollArea, QFrame, QSplitter, QMenu)
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDrag, QIcon, QPixmap
import json
import os
import shutil
from .pipeline_run_dialog import PipelineRunDialog
from .pipeline_step_config import StepConfigDialog

class DraggableListWidget(QListWidget):
    """可拖拽的列表控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setSelectionMode(QListWidget.SingleSelection)
        
    def startDrag(self, supportedActions):
        """开始拖拽"""
        item = self.currentItem()
        if not item:
            return
            
        mime_data = QMimeData()
        mime_data.setText(item.text())
        mime_data.setData("application/x-item-data", str(item.data(Qt.UserRole)).encode())
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # 设置拖拽时的图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        drag.setPixmap(pixmap)
        
        if drag.exec_(supportedActions) == Qt.MoveAction:
            # 如果是从工具列表拖到流程列表，不删除原始项
            if self.objectName() != "pipeline_list":
                pass
            else:
                self.takeItem(self.row(item))


class PipelineModule(QWidget):
    """Pipeline管理模块"""
    def __init__(self):
        super().__init__()
        self.current_config_path = None
        self.pipeline_steps = []
        self.init_ui()
        self.load_tools()
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QHBoxLayout()
        
        # 左侧工具列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 工具类别选择
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("工具类别:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["全部工具", "预处理工具", "推理模型", "后处理工具"])
        self.category_combo.currentIndexChanged.connect(self.filter_tools)
        category_layout.addWidget(self.category_combo)
        left_layout.addLayout(category_layout)
        
        # 工具列表
        tools_group = QGroupBox("可用工具")
        tools_layout = QVBoxLayout()
        self.tools_list = DraggableListWidget()
        self.tools_list.setObjectName("tools_list")
        tools_layout.addWidget(self.tools_list)
        tools_group.setLayout(tools_layout)
        left_layout.addWidget(tools_group)
        
        # 右侧流程设计
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 流程操作按钮
        pipeline_buttons = QHBoxLayout()
        self.new_button = QPushButton("新建流程")
        self.new_button.clicked.connect(self.new_pipeline)
        pipeline_buttons.addWidget(self.new_button)
        
        self.open_button = QPushButton("打开流程")
        self.open_button.clicked.connect(self.open_pipeline)
        pipeline_buttons.addWidget(self.open_button)
        
        self.save_button = QPushButton("保存流程")
        self.save_button.clicked.connect(self.save_pipeline)
        pipeline_buttons.addWidget(self.save_button)
        
        self.save_as_button = QPushButton("另存为")
        self.save_as_button.clicked.connect(self.save_pipeline_as)
        pipeline_buttons.addWidget(self.save_as_button)
        
        right_layout.addLayout(pipeline_buttons)
        
        # 流程名称
        pipeline_name_layout = QHBoxLayout()
        pipeline_name_layout.addWidget(QLabel("流程名称:"))
        self.pipeline_name_label = QLabel("未命名流程")
        pipeline_name_layout.addWidget(self.pipeline_name_label)
        pipeline_name_layout.addStretch()
        right_layout.addLayout(pipeline_name_layout)
        
        # 流程步骤列表
        pipeline_group = QGroupBox("流程步骤")
        pipeline_layout = QVBoxLayout()
        
        self.pipeline_list = DraggableListWidget()
        self.pipeline_list.setObjectName("pipeline_list")
        self.pipeline_list.setMinimumHeight(300)
        self.pipeline_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pipeline_list.customContextMenuRequested.connect(self.show_pipeline_context_menu)
        
        pipeline_layout.addWidget(self.pipeline_list)
        
        # 步骤操作按钮
        step_buttons = QHBoxLayout()
        self.edit_step_button = QPushButton("编辑步骤")
        self.edit_step_button.clicked.connect(self.edit_step)
        step_buttons.addWidget(self.edit_step_button)
        
        self.remove_step_button = QPushButton("删除步骤")
        self.remove_step_button.clicked.connect(self.remove_step)
        step_buttons.addWidget(self.remove_step_button)
        
        self.move_up_button = QPushButton("上移")
        self.move_up_button.clicked.connect(self.move_step_up)
        step_buttons.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("下移")
        self.move_down_button.clicked.connect(self.move_step_down)
        step_buttons.addWidget(self.move_down_button)
        
        pipeline_layout.addLayout(step_buttons)
        pipeline_group.setLayout(pipeline_layout)
        right_layout.addWidget(pipeline_group)
        
        # 运行按钮
        run_layout = QHBoxLayout()
        run_layout.addStretch()
        self.run_button = QPushButton("运行流程")
        self.run_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;")
        self.run_button.clicked.connect(self.run_pipeline)
        run_layout.addWidget(self.run_button)
        right_layout.addLayout(run_layout)
        
        # 设置左右布局比例
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def load_tools(self):
        """加载可用工具"""
        tools = [
            # 预处理工具
            {"name": "图像裁剪", "script": "cli/cutting_cli.py", "category": "预处理工具", "icon": "cut.png"},
            {"name": "SHP框裁剪", "script": "cli/shp_kuang_cut_cli.py", "category": "预处理工具", "icon": "crop.png"},
            {"name": "文件提取", "script": "cli/tiqu_cli.py", "category": "预处理工具", "icon": "extract.png"},
            {"name": "创建TXT文件", "script": "cli/create_txt_cli.py", "category": "预处理工具", "icon": "create.png"},
            
            # 推理模型
            {"name": "HSV颜色检测", "script": "cli/hsv_batch_cli.py", "category": "推理模型", "icon": "hsv.png"},
            {"name": "VIT推理", "script": "cli/vit_predict_cli.py", "category": "推理模型", "icon": "vit.png"},
            {"name": "YOLO推理", "script": "cli/yolo_predict_cli.py", "category": "推理模型", "icon": "yolo.png"},
            
            # 后处理工具
            {"name": "TXT转SHP", "script": "cli/txt_to_shp_cli.py", "category": "后处理工具", "icon": "convert.png"},
            {"name": "合并SHP", "script": "cli/merge_shp_cli.py", "category": "后处理工具", "icon": "merge.png"}
        ]
        
        self.all_tools = tools
        self.update_tools_list(tools)
    
    def update_tools_list(self, tools):
        """更新工具列表"""
        self.tools_list.clear()
        for tool in tools:
            item = QListWidgetItem(tool["name"])
            item.setData(Qt.UserRole, tool)
            self.tools_list.addItem(item)
    
    def filter_tools(self):
        """根据类别筛选工具"""
        category = self.category_combo.currentText()
        if category == "全部工具":
            self.update_tools_list(self.all_tools)
        else:
            filtered_tools = [tool for tool in self.all_tools if tool["category"] == category]
            self.update_tools_list(filtered_tools)
    
    def new_pipeline(self):
        """新建流程"""
        if self.pipeline_steps and self.confirm_discard_changes():
            return
            
        name, ok = QInputDialog.getText(self, "新建流程", "请输入流程名称:")
        if ok and name:
            self.pipeline_name_label.setText(name)
            self.pipeline_steps = []
            self.pipeline_list.clear()
            self.current_pipeline_path = None
    
    def open_pipeline(self):
        """打开流程"""
        if self.pipeline_steps and self.confirm_discard_changes():
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开流程配置", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                steps = config.get("pipeline_steps", [])
                if not steps:
                    QMessageBox.warning(self, "警告", "流程为空或格式不正确")
                    return
                    
                self.pipeline_steps = steps
                self.current_pipeline_path = file_path
                self.pipeline_name_label.setText(os.path.basename(file_path).replace(".json", ""))
                
                # 更新列表
                self.pipeline_list.clear()
                for step in steps:
                    item = QListWidgetItem(step.get("name", "未命名步骤"))
                    item.setData(Qt.UserRole, step)
                    self.pipeline_list.addItem(item)
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开流程失败: {str(e)}")
    
    def save_pipeline(self):
        """保存流程"""
        if not self.pipeline_steps:
            QMessageBox.warning(self, "警告", "流程为空，无法保存")
            return
            
        if not self.current_pipeline_path:
            self.save_pipeline_as()
        else:
            self._save_to_file(self.current_pipeline_path)
    
    def save_pipeline_as(self):
        """另存为流程"""
        if not self.pipeline_steps:
            QMessageBox.warning(self, "警告", "流程为空，无法保存")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存流程配置", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            if not file_path.endswith(".json"):
                file_path += ".json"
                
            self._save_to_file(file_path)
            self.current_pipeline_path = file_path
            self.pipeline_name_label.setText(os.path.basename(file_path).replace(".json", ""))
    
    def _save_to_file(self, file_path):
        """保存到文件"""
        try:
            config = {
                "pipeline_steps": self.pipeline_steps
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            QMessageBox.information(self, "成功", "流程保存成功")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存流程失败: {str(e)}")
    
    def edit_step(self):
        """编辑步骤"""
        current_item = self.pipeline_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择一个步骤")
            return
            
        current_row = self.pipeline_list.currentRow()
        step_data = current_item.data(Qt.UserRole)
        
        dialog = StepConfigDialog(step_data, self)
        if dialog.exec_():
            updated_step = dialog.get_step_data()
            self.pipeline_steps[current_row] = updated_step
            current_item.setText(updated_step.get("name", "未命名步骤"))
            current_item.setData(Qt.UserRole, updated_step)
    
    def remove_step(self):
        """删除步骤"""
        current_row = self.pipeline_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择一个步骤")
            return
            
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这个步骤吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.pipeline_list.takeItem(current_row)
            self.pipeline_steps.pop(current_row)
    
    def move_step_up(self):
        """上移步骤"""
        current_row = self.pipeline_list.currentRow()
        if current_row <= 0:
            return
            
        # 交换列表项
        item = self.pipeline_list.takeItem(current_row)
        self.pipeline_list.insertItem(current_row - 1, item)
        self.pipeline_list.setCurrentRow(current_row - 1)
        
        # 交换步骤数据
        self.pipeline_steps[current_row], self.pipeline_steps[current_row - 1] = \
            self.pipeline_steps[current_row - 1], self.pipeline_steps[current_row]
    
    def move_step_down(self):
        """下移步骤"""
        current_row = self.pipeline_list.currentRow()
        if current_row < 0 or current_row >= self.pipeline_list.count() - 1:
            return
            
        # 交换列表项
        item = self.pipeline_list.takeItem(current_row)
        self.pipeline_list.insertItem(current_row + 1, item)
        self.pipeline_list.setCurrentRow(current_row + 1)
        
        # 交换步骤数据
        self.pipeline_steps[current_row], self.pipeline_steps[current_row + 1] = \
            self.pipeline_steps[current_row + 1], self.pipeline_steps[current_row]
    
    def run_pipeline(self):
        """运行流程"""
        if not self.pipeline_steps:
            QMessageBox.warning(self, "警告", "流程为空，无法运行")
            return
            
        # 如果未保存，先保存
        if not self.current_pipeline_path:
            reply = QMessageBox.question(
                self, "保存流程", "流程未保存，是否先保存再运行？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self.save_pipeline_as()
                if not self.current_pipeline_path:  # 用户取消了保存
                    return
        
        # 打开运行对话框
        dialog = PipelineRunDialog(self.current_pipeline_path, self)
        dialog.exec_()
    
    def show_pipeline_context_menu(self, position):
        """显示流程步骤的右键菜单"""
        menu = QMenu()
        edit_action = menu.addAction("编辑步骤")
        remove_action = menu.addAction("删除步骤")
        menu.addSeparator()
        move_up_action = menu.addAction("上移")
        move_down_action = menu.addAction("下移")
        
        # 获取当前选中的项
        current_item = self.pipeline_list.itemAt(position)
        if not current_item:
            return
            
        action = menu.exec_(self.pipeline_list.mapToGlobal(position))
        
        if action == edit_action:
            self.edit_step()
        elif action == remove_action:
            self.remove_step()
        elif action == move_up_action:
            self.move_step_up()
        elif action == move_down_action:
            self.move_step_down()
    
    def confirm_discard_changes(self):
        """确认是否放弃更改"""
        reply = QMessageBox.question(
            self, "确认", "当前流程未保存，是否放弃更改？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        return reply == QMessageBox.No