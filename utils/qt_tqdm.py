import time
from tqdm import tqdm

class QtTqdm(tqdm):
    """
    自定义的tqdm类，可以将进度信息传递给Qt界面
    """
    def __init__(self, *args, **kwargs):
        # 从kwargs中提取Qt进度条和信号
        self.progress_bar = kwargs.pop('progress_bar', None)
        self.progress_signal = kwargs.pop('progress_signal', None)
        self.log_signal = kwargs.pop('log_signal', None)
        self.step_name = kwargs.pop('step_name', '当前步骤')
        
        # 初始化父类
        super().__init__(*args, **kwargs)
        
        # 记录上次更新时间，避免过于频繁的更新UI
        self.last_update_time = time.time()
        self.update_interval = 0.1  # 更新间隔，秒
    
    def update(self, n=1):
        # 调用父类的update方法
        super().update(n)
        
        # 检查是否需要更新UI
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            
            # 如果提供了进度条，更新进度条
            if self.progress_bar is not None:
                # 计算百分比
                percentage = int(self.n / self.total * 100) if self.total else 0
                # 设置进度条范围和值
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(percentage)
            
            # 如果提供了信号，发送进度信息
            if self.progress_signal is not None:
                # 发送当前进度和总进度
                self.progress_signal.emit(self.n, self.total)
            
            # 如果提供了日志信号，发送进度信息
            # 在开始、结束和每10%的进度点发送日志
            log_points = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            current_percentage = int(self.n / self.total * 100) if self.total else 0
            prev_percentage = int((self.n - n) / self.total * 100) if self.total else 0
            
            # 检查是否跨越了任何日志点
            if self.log_signal is not None:
                for point in log_points:
                    if prev_percentage < point and current_percentage >= point:
                        self.log_signal.emit(f"{self.step_name}: {point}% ({self.n}/{self.total})")
                        break
                
                # 确保在完成时发送最终日志
                if self.n == self.total:
                    self.log_signal.emit(f"{self.step_name}: 100% ({self.total}/{self.total})")
                    
    def close(self):
        # 确保在关闭时更新进度条到100%
        if self.progress_bar is not None:
            self.progress_bar.setValue(100)
        
        if self.progress_signal is not None:
            self.progress_signal.emit(self.total, self.total)
            
        if self.log_signal is not None:
            self.log_signal.emit(f"{self.step_name}: 完成 (100%)")
            
        super().close()