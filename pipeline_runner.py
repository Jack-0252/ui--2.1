import subprocess
import json
import os
import sys
from typing import List, Dict, Any

class PipelineRunner:
    def __init__(self, config_path: str, input_image: str = None):
        """初始化pipeline运行器
        
        Args:
            config_path: pipeline配置文件的路径
            input_image: 输入图像路径(可选)
        """
        self.config_path = config_path
        self.input_image = input_image
        self.steps = self._load_config()
        
    def _load_config(self) -> List[Dict[str, Any]]:
        """加载pipeline配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 如果提供了输入图像，则更新配置中的输入图像路径
            if self.input_image and os.path.exists(self.input_image):
                steps = config.get('pipeline_steps', [])
                for step in steps:
                    params = step.get('params', {})
                    # 更新输入图像路径（通常是第一个步骤或特定步骤）
                    if 'input' in params and params['input'].endswith('.tif'):
                        params['input'] = self.input_image
            
            return config['pipeline_steps']
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            sys.exit(1)
            
    def _validate_step(self, step: Dict[str, Any]) -> bool:
        """验证步骤配置的有效性"""
        required_fields = ['name', 'script', 'params']
        return all(field in step for field in required_fields)
    
    def _prepare_command(self, step: Dict[str, Any]) -> List[str]:
        """准备命令行参数"""
        script_path = os.path.join(os.path.dirname(__file__), step['script'])
        
        # 检查是否为打包后的环境
        if getattr(sys, 'frozen', False):
            # 打包后的环境，直接导入并执行模块
            return self._execute_module_directly(step)
        else:
            # 开发环境，使用subprocess
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"脚本文件不存在: {script_path}")
                
            # 添加项目根目录到PYTHONPATH
            env = os.environ.copy()
            project_root = os.path.dirname(__file__)
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = project_root
                
            command = [sys.executable, script_path]
            for k, v in step['params'].items():
                command.extend([f"--{k}", str(v)])
            return command, env
    
    def _execute_module_directly(self, step: Dict[str, Any]):
        """在打包环境中直接执行模块"""
        import importlib.util
        import sys
        
        # 获取脚本路径
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        
        script_path = os.path.join(base_path, step['script'])
        
        # 动态导入模块
        spec = importlib.util.spec_from_file_location("temp_module", script_path)
        module = importlib.util.module_from_spec(spec)
        
        # 设置命令行参数
        old_argv = sys.argv
        sys.argv = ['script']
        for k, v in step['params'].items():
            sys.argv.extend([f"--{k}", str(v)])
        
        try:
            # 执行模块
            spec.loader.exec_module(module)
            if hasattr(module, 'main'):
                module.main()
        finally:
            # 恢复原始argv
            sys.argv = old_argv
    
    def run(self, start_from: int = 0, callback=None) -> bool:
        """运行pipeline
        
        Args:
            start_from: 从第几步开始运行（0-based）
            callback: 回调函数，用于通知步骤执行状态
                      callback(step_index, step_name, status)
                      status可以是 "started", "completed", "failed"
            
        Returns:
            bool: 是否成功完成所有步骤
        """
        total_steps = len(self.steps)
        
        for i, step in enumerate(self.steps[start_from:], start=start_from):
            if not self._validate_step(step):
                print(f"步骤 {step.get('name', f'步骤{i}')} 配置无效")
                if callback:
                    callback(i, step.get('name', f'步骤{i}'), "failed")
                return False
                
            print(f"\n[{i+1}/{total_steps}] 正在执行: {step['name']}")
            # 通知步骤开始执行
            if callback:
                callback(i, step['name'], "started")
                
            try:
                command, env = self._prepare_command(step)
                print(f"执行命令: {' '.join(command)}")
                
                result = subprocess.run(
                    command,
                    check=True,
                    text=True,
                    capture_output=True,
                    env=env  # 使用修改后的环境变量
                )
                
                print(result.stdout)
                if result.stderr:
                    print("警告信息:", result.stderr, file=sys.stderr)
                    
                # 通知步骤完成
                if callback:
                    callback(i, step['name'], "completed")
                    
            except subprocess.CalledProcessError as e:
                print(f"步骤 {step['name']} 执行失败:")
                print(f"错误码: {e.returncode}")
                print(f"错误信息: {e.stderr}")
                # 通知步骤失败
                if callback:
                    callback(i, step['name'], "failed")
                return False
            except Exception as e:
                print(f"步骤 {step['name']} 发生异常: {e}")
                # 通知步骤失败
                if callback:
                    callback(i, step['name'], "failed")
                return False
                
            print(f"步骤 {step['name']} 完成")
            
        print("\n所有步骤执行完成!")
        return True

def main():
    """主函数"""
    # 支持从命令行传入配置文件路径和输入图像路径
    import argparse
    parser = argparse.ArgumentParser(description='运行处理流程')
    parser.add_argument('--config', '-c', default='cvy_pipeline_config.json', 
                        help='配置文件路径')
    parser.add_argument('--input', '-i', help='输入图像路径')
    args = parser.parse_args()
    
    config_path = os.path.join(os.path.dirname(__file__), args.config)
    runner = PipelineRunner(config_path, args.input)
    success = runner.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()