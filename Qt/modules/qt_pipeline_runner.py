from PySide6.QtCore import QThread, Signal
import subprocess
import sys
import os
import json
import importlib
import inspect

class QtPipelineRunnerThread(QThread):
    """支持进度条的流程运行线程"""
    step_started = Signal(int, str)  # 步骤开始信号
    step_completed = Signal(int)     # 步骤完成信号
    step_failed = Signal(int, str)   # 步骤失败信号
    log_message = Signal(str)        # 日志消息信号
    progress_updated = Signal(int, int)  # 进度更新信号（当前进度，总进度）
    pipeline_completed = Signal(bool)  # 流程完成信号，参数表示是否成功
    
    def __init__(self, config_path, start_from=0, progress_bar=None):
        super().__init__()
        self.config_path = config_path
        self.start_from = start_from
        self.is_running = True
        self.progress_bar = progress_bar
        
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
                
                # 检查是否是支持进度条的步骤
                script_path = step.get("script", "")
                if self._is_progress_supported_step(script_path):
                    # 使用Python模块方式直接调用，传递进度条参数
                    success = self._run_step_with_progress(step, i)
                    if not success:
                        break
                else:
                    # 使用命令行方式调用
                    success = self._run_step_with_subprocess(step, i)
                    if not success:
                        break
                
                self.step_completed.emit(i)
            
            self.pipeline_completed.emit(success)
            
        except Exception as e:
            self.log_message.emit(f"流程运行异常: {str(e)}")
            self.pipeline_completed.emit(False)
    
    def _is_progress_supported_step(self, script_path):
        """检查步骤是否支持进度条"""
        # 检查是否是HSV_Batch2txt.py或shp_kuang_cut.py相关的CLI脚本
        return "hsv_batch_cli.py" in script_path or "shp_kuang_cut_cli.py" in script_path
    
    def _run_step_with_progress(self, step, step_index):
        """使用进度条运行步骤"""
        try:
            script_path = step.get("script", "")
            params = step.get("params", {})
            
            # 根据脚本路径确定要调用的函数
            if "hsv_batch_cli.py" in script_path:
                from utils.HSV_Batch2txt import process_images_to_yolo_format
                
                input_folder = params.get("input", "")
                output_folder = params.get("output", "")
                
                self.log_message.emit(f"使用进度条执行HSV颜色检测: {input_folder} -> {output_folder}")
                
                # 调用函数，传递进度条参数
                process_images_to_yolo_format(
                    input_folder, 
                    output_folder,
                    progress_bar=self.progress_bar,
                    progress_signal=self.progress_updated,
                    log_signal=self.log_message
                )
                
                return True
                
            elif "shp_kuang_cut_cli.py" in script_path:
                from utils.shp_kuang_cut import crop_and_save_raster
                
                input_tif = params.get("input", "")
                shapefile = params.get("shapefile", "")
                output_dir = params.get("output", "")
                scale = params.get("scale", 1.0)
                
                self.log_message.emit(f"使用进度条执行图像裁剪: {input_tif} -> {output_dir}")
                
                # 调用函数，传递进度条参数
                crop_and_save_raster(
                    input_tif,
                    shapefile,
                    output_dir,
                    scale,
                    progress_bar=self.progress_bar,
                    progress_signal=self.progress_updated,
                    log_signal=self.log_message
                )
                
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"步骤执行异常: {str(e)}"
            self.log_message.emit(error_msg)
            self.step_failed.emit(step_index, error_msg)
            return False
    
    def _run_step_with_subprocess(self, step, step_index):
        """使用子进程运行步骤"""
        try:
            # 准备命令
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(self.config_path))), step["script"])
            if not os.path.exists(script_path):
                error_msg = f"脚本文件不存在: {script_path}"
                self.log_message.emit(error_msg)
                self.step_failed.emit(step_index, error_msg)
                return False
            
            # 添加项目根目录到PYTHONPATH
            env = os.environ.copy()
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(self.config_path)))
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = project_root
            
            # 处理参数中的路径，确保data目录在项目根目录下
            params = step["params"].copy()
            for k, v in params.items():
                if isinstance(v, str) and v.startswith("data/"):
                    # 确保data目录存在
                    data_dir = os.path.join(project_root, "data")
                    os.makedirs(data_dir, exist_ok=True)
                    # 确保子目录存在
                    sub_dir = os.path.join(project_root, v)
                    os.makedirs(os.path.dirname(sub_dir), exist_ok=True)
            
            command = [sys.executable, script_path]
            for k, v in params.items():
                command.extend([f"--{k}", str(v)])
            
            self.log_message.emit(f"执行命令: {' '.join(command)}")
            
            # 获取总步骤数，用于恢复进度条范围
            total_steps_in_pipeline = 0
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f_config:
                    pipeline_config = json.load(f_config)
                    total_steps_in_pipeline = len(pipeline_config.get("pipeline_steps", []))
            except Exception:
                # 如果无法获取总步骤数，默认使用100，或之前设置的范围
                pass

            original_progress_bar_range = None
            if self.progress_bar is not None:
                original_progress_bar_range = (self.progress_bar.minimum(), self.progress_bar.maximum())
                self.progress_bar.setRange(0, 0)  # 不确定状态
            
            result = subprocess.run(
                command,
                check=True,
                text=True,
                capture_output=True,
                env=env
            )
            
            # 恢复进度条状态
            if self.progress_bar is not None and original_progress_bar_range is not None:
                if total_steps_in_pipeline > 0:
                    self.progress_bar.setRange(0, total_steps_in_pipeline)
                else:
                    self.progress_bar.setRange(original_progress_bar_range[0], original_progress_bar_range[1])
                # 具体的值由 on_step_completed 设置，这里不需要 setValue
            
            self.log_message.emit(result.stdout)
            if result.stderr:
                self.log_message.emit(f"警告信息: {result.stderr}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"步骤执行失败: {e.stderr}"
            self.log_message.emit(error_msg)
            self.step_failed.emit(step_index, error_msg)
            return False
        except Exception as e:
            error_msg = f"步骤执行异常: {str(e)}"
            self.log_message.emit(error_msg)
            self.step_failed.emit(step_index, error_msg)
            return False
    
    def stop(self):
        """停止流程"""
        self.is_running = False