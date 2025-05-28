from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFileDialog, QProgressBar, 
                              QTextEdit, QGroupBox, QFormLayout, QLineEdit,
                              QMessageBox, QSplitter)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage
import os
import json
import subprocess
import sys
import shutil
import time
import cv2
import numpy as np
from pathlib import Path

class InferenceThread(QThread):
    """推理线程"""
    progress_update = Signal(int, int)  # 当前进度，总进度
    log_message = Signal(str)  # 日志消息
    inference_completed = Signal(bool, str)  # 是否成功，输出路径
    yolo_step_started = Signal(str, str)  # YOLO步骤开始信号，参数：tif文件夹路径，标签文件夹路径
    
    def __init__(self, input_image, config_path, output_dir):
        super().__init__()
        self.input_image = input_image
        self.config_path = config_path
        self.output_dir = output_dir
        self.is_running = True
        
    def run(self):
        """运行推理"""
        try:
            # 添加项目根目录到Python路径
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if project_root not in sys.path:
                sys.path.append(project_root)
                
            # 使用pipeline_runner来执行流程
            from pipeline_runner import PipelineRunner
            
            # 创建临时配置文件
            temp_config_path = os.path.join(self.output_dir, "temp_config.json")
            with open(self.config_path, 'r', encoding='utf-8') as f_in:
                config = json.load(f_in)
                
                # 修改配置中的输入图像路径
                for step in config.get('pipeline_steps', []):
                    params = step.get('params', {})
                    if 'input' in params and params['input'].endswith('.tif'):
                        params['input'] = self.input_image
                
                # 不再修改输出路径，保持data目录在代码目录下
                # 只需确保输入图像路径正确即可
            
            # 保存修改后的配置
            with open(temp_config_path, 'w', encoding='utf-8') as f_out:
                json.dump(config, f_out, indent=4, ensure_ascii=False)
            
            # 创建pipeline runner
            runner = PipelineRunner(temp_config_path, self.input_image)
            
            # 获取总步骤数
            total_steps = len(config.get('pipeline_steps', []))
            self.log_message.emit(f"总共 {total_steps} 个步骤需要执行")
            
            # 设置进度条初始状态
            self.progress_update.emit(0, total_steps)
            
            # 执行pipeline，并在每个步骤完成后更新进度
            success = runner.run(callback=self.step_callback)
            
            # 查找最终的merge_shp文件夹
            final_merge_shp_dir = ""
            steps = config.get('pipeline_steps', [])
            for step in reversed(steps):
                if "merge_shp_cli.py" in step.get("script", ""):
                    output_param = step.get("params", {}).get("output", "")
                    if output_param and "merge_shp" in output_param:
                        # 获取相对于项目根目录的路径
                        if not os.path.isabs(output_param):
                            final_merge_shp_dir = os.path.join(project_root, output_param)
                        else:
                            final_merge_shp_dir = output_param
                        break
            
            # 复制merge_shp文件夹到用户指定的输出目录
            final_output_dir = ""
            if final_merge_shp_dir and os.path.exists(final_merge_shp_dir):
                # 提取文件夹名称
                merge_shp_folder_name = os.path.basename(final_merge_shp_dir)
                # 目标文件夹完整路径
                target_merge_shp_dir = os.path.join(self.output_dir, merge_shp_folder_name)
                
                # 如果目标文件夹已存在，先删除
                if os.path.exists(target_merge_shp_dir):
                    shutil.rmtree(target_merge_shp_dir)
                
                # 复制文件夹
                self.log_message.emit(f"正在复制结果文件夹到: {target_merge_shp_dir}")
                shutil.copytree(final_merge_shp_dir, target_merge_shp_dir)
                final_output_dir = target_merge_shp_dir
                self.log_message.emit(f"文件夹复制完成: {target_merge_shp_dir}")
            
            # 确保最终进度为100%
            self.progress_update.emit(total_steps, total_steps)
            self.log_message.emit("推理完成！")
            self.inference_completed.emit(True, final_output_dir)
            
        except Exception as e:
            self.log_message.emit(f"推理过程异常: {str(e)}")
            self.inference_completed.emit(False, "")
    
    def step_callback(self, step_index, step_name, status):
        """步骤执行回调函数"""
        if status == "started":
            self.log_message.emit(f"开始执行步骤 {step_index+1}: {step_name}")
            
            # 检测是否是YOLO推理步骤
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    steps = config.get('pipeline_steps', [])
                    current_step = steps[step_index]
                    
                    # 如果是YOLO推理步骤，发出信号
                    if "yolo_predict_cli.py" in current_step.get("script", ""):
                        self.log_message.emit("检测到YOLO推理步骤，准备监控检测结果")
                        
                        # 获取TIF文件夹路径
                        tif_folder = current_step.get("params", {}).get("input", "")
                        # 获取项目根目录
                        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        
                        # 确保TIF文件夹路径是绝对路径
                        if not os.path.isabs(tif_folder):
                            tif_folder = os.path.join(project_root, tif_folder)
                        
                        # 标签文件夹是固定的runs/detect/predict/labels
                        labels_folder = os.path.join(project_root, "runs", "detect", "predict", "labels")
                        
                        # 发出YOLO步骤开始信号
                        self.log_message.emit(f"开始监控YOLO检测结果: {labels_folder}")
                        self.yolo_step_started.emit(tif_folder, labels_folder)
            except Exception as e:
                self.log_message.emit(f"检测YOLO步骤时出错: {str(e)}")
                import traceback
                self.log_message.emit(traceback.format_exc())
                
        elif status == "completed":
            # 获取总步骤数（从配置文件中）
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    total_steps = len(config.get('pipeline_steps', []))
                    # 更新进度条，当前完成的步骤数为 step_index+1
                    self.progress_update.emit(step_index+1, total_steps)
                    self.log_message.emit(f"步骤 {step_index+1}/{total_steps} 执行完成: {step_name}")
            except Exception as e:
                self.log_message.emit(f"更新进度时出错: {str(e)}")
        elif status == "failed":
            self.log_message.emit(f"步骤 {step_index+1} 执行失败: {step_name}")
    
    def stop(self):
        """停止推理"""
        self.is_running = False


class YoloMonitorThread(QThread):
    """YOLO检测结果监控线程"""
    new_detection = Signal(str, str)  # 新检测结果信号，参数：tif文件路径，txt文件路径
    monitoring_stopped = Signal()  # 监控停止信号
    
    def __init__(self, tif_folder, labels_folder):
        super().__init__()
        self.tif_folder = tif_folder
        self.labels_folder = labels_folder
        self.is_running = True
        self.processed_files = set()  # 已处理的文件集合
        
    def run(self):
        """运行监控线程"""
        # 监控循环
        while self.is_running:
            try:
                # 检查标签文件夹中的txt文件
                if os.path.exists(self.labels_folder):
                    txt_files = [f for f in os.listdir(self.labels_folder) if f.endswith('.txt')]
                    
                    for txt_file in txt_files:
                        # 如果是新文件（未处理过）
                        if txt_file not in self.processed_files:
                            # 获取对应的tif文件路径
                            tif_file = txt_file.replace('.txt', '.tif')
                            tif_path = os.path.join(self.tif_folder, tif_file)
                            
                            # 如果tif文件存在
                            if os.path.exists(tif_path):
                                txt_path = os.path.join(self.labels_folder, txt_file)
                                # 发出新检测结果信号
                                self.new_detection.emit(tif_path, txt_path)
                                # 添加到已处理集合
                                self.processed_files.add(txt_file)
            except Exception as e:
                print(f"监控YOLO检测结果时出错: {str(e)}")
                
            # 短暂休眠，避免CPU占用过高
            time.sleep(0.5)
            
        # 发出监控停止信号
        self.monitoring_stopped.emit()
        
    def stop(self):
        """停止监控"""
        self.is_running = False


class InferenceModule(QWidget):
    """推理模块"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.input_image = ""
        self.config_path = ""
        self.output_dir = ""
        self.inference_thread = None
        self.yolo_monitor_thread = None
        self.current_tif_folder = ""
        self.init_ui()
        
        # 创建定时器用于重置预览区域
        self.reset_preview_timer = QTimer()
        self.reset_preview_timer.setSingleShot(True)
        self.reset_preview_timer.timeout.connect(self.reset_preview_area)
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        
        # 顶部标题
        title_label = QLabel("松科变色立木检测系统 - 推理")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 输入配置区域
        input_group = QGroupBox("输入配置")
        input_layout = QFormLayout()
        
        # 输入图像
        image_layout = QHBoxLayout()
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setReadOnly(True)
        image_layout.addWidget(self.image_path_edit)
        
        self.browse_image_button = QPushButton("浏览...")
        self.browse_image_button.clicked.connect(self.browse_input_image)
        image_layout.addWidget(self.browse_image_button)
        
        # 流程配置
        config_layout = QHBoxLayout()
        self.config_path_edit = QLineEdit()
        self.config_path_edit.setReadOnly(True)
        config_layout.addWidget(self.config_path_edit)
        
        self.browse_config_button = QPushButton("浏览...")
        self.browse_config_button.clicked.connect(self.browse_config_file)
        config_layout.addWidget(self.browse_config_button)
        
        # 输出目录
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        output_layout.addWidget(self.output_dir_edit)
        
        self.browse_output_button = QPushButton("浏览...")
        self.browse_output_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.browse_output_button)
        
        # 添加到表单布局
        input_layout.addRow("输入图像:", QWidget(layout=image_layout))
        input_layout.addRow("流程配置:", QWidget(layout=config_layout))
        input_layout.addRow("输出目录:", QWidget(layout=output_layout))
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # 图像预览区域
        preview_group = QGroupBox("图像预览")
        preview_layout = QHBoxLayout()
        
        # 原图预览
        self.original_image_preview = QLabel()
        self.original_image_preview.setAlignment(Qt.AlignCenter)
        self.original_image_preview.setMinimumHeight(300)
        self.original_image_preview.setMinimumWidth(300)
        self.original_image_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        self.original_image_preview.setText("原图")
        
        # 检测结果预览
        self.detection_image_preview = QLabel()
        self.detection_image_preview.setAlignment(Qt.AlignCenter)
        self.detection_image_preview.setMinimumHeight(300)
        self.detection_image_preview.setMinimumWidth(300)
        self.detection_image_preview.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        self.detection_image_preview.setText("检测结果")
        
        # 添加到布局
        preview_layout.addWidget(self.original_image_preview)
        preview_layout.addWidget(self.detection_image_preview)
        
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # 保存对原始图像预览的引用，用于兼容性
        self.image_preview = self.original_image_preview
        
        # 进度和日志区域
        progress_group = QGroupBox("推理进度")
        progress_layout = QVBoxLayout()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        progress_layout.addWidget(self.log_text)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.run_button = QPushButton("开始推理")
        self.run_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;")
        self.run_button.clicked.connect(self.start_inference)
        button_layout.addWidget(self.run_button)
        
        self.clear_workspace_button = QPushButton("清除工作区")
        self.clear_workspace_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px 16px;")
        self.clear_workspace_button.clicked.connect(self.clear_workspace)
        button_layout.addWidget(self.clear_workspace_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def browse_input_image(self):
        """浏览输入图像"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择输入图像", "", "图像文件 (*.tif *.tiff *.jpg *.jpeg *.png)"
        )
        
        if file_path:
            self.input_image = file_path
            self.image_path_edit.setText(file_path)
            self.update_image_preview(file_path)
            
    def browse_config_file(self):
        """浏览配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择流程配置文件", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            self.config_path = file_path
            self.config_path_edit.setText(file_path)
            
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录"
        )
        
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_edit.setText(dir_path)
            
    def update_image_preview(self, image_path):
        """更新原图预览"""
        if not os.path.exists(image_path):
            return
            
        # 加载图像并调整大小以适应预览区域
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                self.original_image_preview.width(), 
                self.original_image_preview.height(),
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.original_image_preview.setPixmap(pixmap)
        else:
            self.original_image_preview.setText("无法加载图像")
            
    def show_detection_result(self, tif_path, txt_path):
        """显示检测结果"""
        try:
            # 读取原始图像
            img = cv2.imread(tif_path)
            if img is None:
                self.log_message(f"无法读取图像: {tif_path}")
                return
                
            # 读取检测结果（YOLO格式的txt文件）
            if os.path.exists(txt_path):
                # 获取图像尺寸
                height, width = img.shape[:2]
                
                # 读取txt文件中的检测框
                with open(txt_path, 'r') as f:
                    lines = f.readlines()
                    
                # 绘制检测框
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 5:  # 类别 + 4个坐标值
                        # YOLO格式：类别 中心x 中心y 宽度 高度（归一化坐标）
                        cls, x_center, y_center, w, h = parts[0], float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                        
                        # 转换为像素坐标
                        x1 = int((x_center - w/2) * width)
                        y1 = int((y_center - h/2) * height)
                        x2 = int((x_center + w/2) * width)
                        y2 = int((y_center + h/2) * height)
                        
                        # 确保坐标在图像范围内
                        x1 = max(0, min(x1, width-1))
                        y1 = max(0, min(y1, height-1))
                        x2 = max(0, min(x2, width-1))
                        y2 = max(0, min(y2, height-1))
                        
                        # 绘制矩形框（红色）
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        
                        # 添加类别标签
                        label = f"Class {cls}"
                        cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # 转换为Qt图像并显示
            height, width, channel = img.shape
            bytes_per_line = 3 * width
            # OpenCV使用BGR格式，需要转换为RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            q_img = QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(q_img)
            pixmap = pixmap.scaled(
                self.detection_image_preview.width(),
                self.detection_image_preview.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.detection_image_preview.setPixmap(pixmap)
            
        except Exception as e:
            self.log_message(f"显示检测结果时出错: {str(e)}")
            self.detection_image_preview.setText("无法显示检测结果")
            
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
    def start_inference(self):
        """开始推理"""
        # 检查输入
        if not self.input_image or not os.path.exists(self.input_image):
            QMessageBox.warning(self, "警告", "请选择有效的输入图像")
            return
            
        if not self.config_path or not os.path.exists(self.config_path):
            QMessageBox.warning(self, "警告", "请选择有效的流程配置文件")
            return
            
        if not self.output_dir or not os.path.exists(self.output_dir):
            QMessageBox.warning(self, "警告", "请选择有效的输出目录")
            return
            
        # 清空日志和重置进度条
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # 重置预览区域
        self.reset_preview_area()
        
        # 禁用运行按钮
        self.run_button.setEnabled(False)
        
        # 创建并启动推理线程
        self.inference_thread = InferenceThread(
            self.input_image, self.config_path, self.output_dir
        )
        self.inference_thread.progress_update.connect(self.update_progress)
        self.inference_thread.log_message.connect(self.log_message)
        self.inference_thread.inference_completed.connect(self.on_inference_completed)
        self.inference_thread.yolo_step_started.connect(self.on_yolo_step_started)
        self.inference_thread.start()
        
    def reset_preview_area(self):
        """重置预览区域"""
        self.original_image_preview.setText("原图")
        self.original_image_preview.setPixmap(QPixmap())
        self.detection_image_preview.setText("检测结果")
        self.detection_image_preview.setPixmap(QPixmap())
        
    def on_yolo_step_started(self, tif_folder, label_folder):
        """YOLO步骤开始时的处理"""
        self.log_message(f"开始监控YOLO检测结果: {label_folder}")
        self.current_tif_folder = tif_folder
        
        # 停止之前的监控线程（如果存在）
        if self.yolo_monitor_thread and self.yolo_monitor_thread.isRunning():
            self.yolo_monitor_thread.stop()
            self.yolo_monitor_thread.wait()
        
        # 创建并启动新的监控线程
        self.yolo_monitor_thread = YoloMonitorThread(tif_folder, label_folder)
        self.yolo_monitor_thread.new_detection.connect(self.on_new_detection)
        self.yolo_monitor_thread.monitoring_stopped.connect(self.on_monitoring_stopped)
        self.yolo_monitor_thread.start()
        
    def on_new_detection(self, tif_path, txt_path):
        """处理新的检测结果"""
        # 更新原图预览
        self.update_image_preview(tif_path)
        # 显示检测结果
        self.show_detection_result(tif_path, txt_path)
        
    def on_monitoring_stopped(self):
        """监控停止时的处理"""
        self.log_message("YOLO检测结果监控已停止")
        # 设置定时器在3秒后重置预览区域
        self.reset_preview_timer.start(3000)
        
    def clear_workspace(self):
        """清除工作区"""
        try:
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 定义要删除的文件夹路径
            runs_folder = os.path.join(project_root, "runs")
            data_folder = os.path.join(project_root, "data")
            
            deleted_folders = []
            
            # 删除runs文件夹
            if os.path.exists(runs_folder):
                shutil.rmtree(runs_folder)
                deleted_folders.append("runs")
                self.log_message("已删除runs文件夹")
            
            # 删除data文件夹
            if os.path.exists(data_folder):
                shutil.rmtree(data_folder)
                deleted_folders.append("data")
                self.log_message("已删除data文件夹")
            
            if deleted_folders:
                self.log_message(f"工作区清除完成，已删除: {', '.join(deleted_folders)}")
                QMessageBox.information(self, "清除完成", f"工作区清除完成！\n已删除: {', '.join(deleted_folders)}")
            else:
                self.log_message("工作区中没有找到runs或data文件夹")
                QMessageBox.information(self, "清除完成", "工作区中没有找到需要清除的文件夹")
                
        except Exception as e:
            error_msg = f"清除工作区时出错: {str(e)}"
            self.log_message(error_msg)
            QMessageBox.warning(self, "清除失败", error_msg)
            
    def update_progress(self, current, total):
        """更新进度条"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        
    def on_inference_completed(self, success, output_path):
        """推理完成回调"""
        # 停止YOLO监控线程
        if self.yolo_monitor_thread and self.yolo_monitor_thread.isRunning():
            self.yolo_monitor_thread.stop()
            self.yolo_monitor_thread.wait()
            self.log_message("YOLO监控已停止")
            
        # 启用运行按钮
        self.run_button.setEnabled(True)
        
        if success:
            self.log_message(f"推理成功完成！")
            
            # 询问是否打开输出文件夹
            if output_path and os.path.exists(output_path):
                self.log_message(f"最终输出路径: {output_path}")
                reply = QMessageBox.question(
                    self, 
                    "推理完成", 
                    "推理已成功完成，是否打开输出文件夹？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 打开输出文件夹
                    try:
                        if os.path.isdir(output_path):
                            os.startfile(output_path)
                        else:
                            os.startfile(os.path.dirname(output_path))
                    except Exception as e:
                        self.log_message(f"打开文件夹失败: {str(e)}")
            else:
                QMessageBox.information(self, "推理完成", "推理已成功完成，但未找到有效的输出路径。")
        else:
            self.log_message("推理失败！")
            QMessageBox.warning(self, "推理失败", "推理过程中发生错误，请检查日志。")
            
        # 重置预览区域
        self.reset_preview_area()