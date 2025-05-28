from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QProgressBar, QTextEdit, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal
import subprocess
import sys
import os
import json
from .qt_pipeline_runner import QtPipelineRunnerThread

class PipelineRunnerThread(QThread):
    """运行流程的线程"""
    step_started = Signal(int, str)  # 步骤开始信号
    step_completed = Signal(int)     # 步骤完成信号
    step_failed = Signal(int, str)   # 步骤失败信号
    log_message = Signal(str)        # 日志消息信号
    pipeline_completed = Signal(bool)  # 流程完成信号，参数表示是否成功
    
    def __init__(self, config_path, start_from=0):
        super().__init__()
        self.config_path = config_path
        self.start_from = start_from
        self.is_running = True
        
    def run(self):
        """运行流程"""
        try:
            # 加载配置
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            steps = config.get("pipeline_steps", [])
            if not steps:
                self.log_message.emit("错误: 流程为空")
                self.pipeline_completed.emit(False)
                return
                
            total_steps = len(steps)
            success = True
            
            for i, step in enumerate(steps[self.start_from:], start=self.start_from):
                if not self.is_running:
                    self.log_message.emit("流程被用户中止")
                    self.pipeline_completed.emit(False)
                    return
                    
                step_name = step.get("name", f"步骤{i+1}")
                self.step_started.emit(i, step_name)
                
                # 准备命令
                script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(self.config_path))), step["script"])
                if not os.path.exists(script_path):
                    error_msg = f"脚本文件不存在: {script_path}"
                    self.log_message.emit(error_msg)
                    self.step_failed.emit(i, error_msg)
                    success = False
                    break
                
                # 添加项目根目录到PYTHONPATH
                env = os.environ.copy()
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(self.config_path)))
                if 'PYTHONPATH' in env:
                    env['PYTHONPATH'] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
                else:
                    env['PYTHONPATH'] = project_root
                
                command = [sys.executable, script_path]
                for k, v in step["params"].items():
                    command.extend([f"--{k}", str(v)])
                
                self.log_message.emit(f"执行命令: {' '.join(command)}")
                
                try:
                    result = subprocess.run(
                        command,
                        check=True,
                        text=True,
                        capture_output=True,
                        env=env
                    )
                    
                    self.log_message.emit(result.stdout)
                    if result.stderr:
                        self.log_message.emit(f"警告信息: {result.stderr}")
                    
                    self.step_completed.emit(i)
                    
                except subprocess.CalledProcessError as e:
                    error_msg = f"步骤执行失败: {e.stderr}"
                    self.log_message.emit(error_msg)
                    self.step_failed.emit(i, error_msg)
                    success = False
                    break
                except Exception as e:
                    error_msg = f"步骤执行异常: {str(e)}"
                    self.log_message.emit(error_msg)
                    self.step_failed.emit(i, error_msg)
                    success = False
                    break
            
            self.pipeline_completed.emit(success)
            
        except Exception as e:
            self.log_message.emit(f"流程运行异常: {str(e)}")
            self.pipeline_completed.emit(False)
    
    def stop(self):
        """停止流程"""
        self.is_running = False


class PipelineRunDialog(QDialog):
    """流程运行对话框"""
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.runner_thread = None
        self.init_ui()
        self.load_steps()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("流程运行")
        self.resize(800, 600)
        
        main_layout = QVBoxLayout()
        
        # 顶部信息
        info_layout = QHBoxLayout()
        self.config_label = QLabel("配置文件:")
        info_layout.addWidget(self.config_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout)
        
        # 步骤列表
        self.steps_layout = QVBoxLayout()
        self.step_widgets = []
        main_layout.addLayout(self.steps_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("总进度:"))
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_layout)
        
        # 日志区域
        main_layout.addWidget(QLabel("运行日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        self.start_from_checkbox = QCheckBox("从选中步骤开始")
        button_layout.addWidget(self.start_from_checkbox)
        button_layout.addStretch()
        
        self.run_button = QPushButton("运行")
        self.run_button.clicked.connect(self.run_pipeline)
        button_layout.addWidget(self.run_button)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_pipeline)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def load_steps(self):
        """加载流程步骤"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            steps = config.get("pipeline_steps", [])
            if not steps:
                self.log_message("错误: 流程为空")
                return
                
            self.config_label.setText(f"配置文件: {os.path.basename(self.config_path)}")
            
            # 清除旧步骤
            for widget in self.step_widgets:
                widget.setParent(None)
            self.step_widgets.clear()
            
            # 添加新步骤
            for i, step in enumerate(steps):
                step_name = step.get("name", f"步骤{i+1}")
                step_widget = QWidget()
                step_layout = QHBoxLayout(step_widget)
                
                # 步骤选择复选框
                checkbox = QCheckBox()
                checkbox.setChecked(i == 0)  # 默认选中第一个步骤
                step_layout.addWidget(checkbox)
                
                # 步骤序号和名称
                step_label = QLabel(f"{i+1}. {step_name}")
                step_layout.addWidget(step_label)
                
                # 状态标签
                status_label = QLabel("等待中")
                step_layout.addWidget(status_label)
                
                step_layout.addStretch()
                
                self.steps_layout.addWidget(step_widget)
                self.step_widgets.append({
                    "widget": step_widget,
                    "checkbox": checkbox,
                    "label": step_label,
                    "status": status_label
                })
            
            # 设置进度条
            self.progress_bar.setRange(0, len(steps))
            self.progress_bar.setValue(0)
            
        except Exception as e:
            self.log_message(f"加载流程步骤失败: {str(e)}")
    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def run_pipeline(self):
        """运行流程"""
        # 确定起始步骤
        start_from = 0
        if self.start_from_checkbox.isChecked():
            for i, step_widget in enumerate(self.step_widgets):
                if step_widget["checkbox"].isChecked():
                    start_from = i
                    break
        
        # 重置状态
        for i, step_widget in enumerate(self.step_widgets):
            if i < start_from:
                step_widget["status"].setText("已跳过")
                step_widget["status"].setStyleSheet("color: gray;")
            else:
                step_widget["status"].setText("等待中")
                step_widget["status"].setStyleSheet("")
        
        self.progress_bar.setValue(start_from)
        self.log_text.clear()
        self.log_message(f"开始运行流程，从步骤 {start_from+1} 开始")
        
        # 禁用运行按钮，启用停止按钮
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 创建并启动线程
        # 使用支持进度条的QtPipelineRunnerThread
        self.runner_thread = QtPipelineRunnerThread(self.config_path, start_from, self.progress_bar)
        self.runner_thread.step_started.connect(self.on_step_started)
        self.runner_thread.step_completed.connect(self.on_step_completed)
        self.runner_thread.step_failed.connect(self.on_step_failed)
        self.runner_thread.log_message.connect(self.log_message)
        self.runner_thread.progress_updated.connect(self.on_progress_updated)
        self.runner_thread.pipeline_completed.connect(self.on_pipeline_completed)
        self.runner_thread.start()
    
    def stop_pipeline(self):
        """停止流程"""
        if self.runner_thread and self.runner_thread.isRunning():
            self.log_message("正在停止流程...")
            self.runner_thread.stop()
            self.stop_button.setEnabled(False)
    
    def on_step_started(self, step_index, step_name):
        """步骤开始回调"""
        if step_index < len(self.step_widgets):
            self.step_widgets[step_index]["status"].setText("运行中...")
            self.step_widgets[step_index]["status"].setStyleSheet("color: blue;")
            self.log_message(f"开始执行步骤 {step_index+1}: {step_name}")
    
    def on_step_completed(self, step_index):
        """步骤完成回调"""
        if step_index < len(self.step_widgets):
            self.step_widgets[step_index]["status"].setText("已完成")
            self.step_widgets[step_index]["status"].setStyleSheet("color: green;")
            self.progress_bar.setValue(step_index + 1)
            self.log_message(f"步骤 {step_index+1} 执行完成")
    
    def on_step_failed(self, step_index, error_msg):
        """步骤失败回调"""
        if step_index < len(self.step_widgets):
            self.step_widgets[step_index]["status"].setText("失败")
            self.step_widgets[step_index]["status"].setStyleSheet("color: red;")
            self.log_message(f"步骤 {step_index+1} 执行失败: {error_msg}")
    
    def on_progress_updated(self, current, total):
        """进度更新回调"""
        # 计算当前步骤内的进度百分比
        if total > 0:
            percentage = int(current / total * 100)
            # 只记录日志，不再修改总进度条的 range 和 value
            # 总进度条由 on_step_completed 更新
            # self.progress_bar.setRange(0, 100) # 不要修改总进度条的范围
            # self.progress_bar.setValue(percentage) # 不要修改总进度条的值
            
            # 每10%记录一次日志，避免日志过多
            # 注意：这里的current和total是针对当前支持进度的步骤内部的
            log_interval = max(int(total / 10), 1)
            if current == 0 or current == total or current % log_interval == 0:
                self.log_message(f"当前活动步骤内部进度: {percentage}% ({current}/{total})")
    
    def on_pipeline_completed(self, success):
        """流程完成回调"""
        # 启用运行按钮，禁用停止按钮
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if success:
            self.log_message("流程执行成功完成！")
        else:
            self.log_message("流程执行失败！")