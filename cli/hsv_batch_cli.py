import argparse
import os
from utils.HSV_Batch2txt import process_images_to_yolo_format

def main():
    parser = argparse.ArgumentParser(description='基于HSV颜色检测生成YOLO格式标签')
    parser.add_argument('--input', '-i', required=True, help='输入图像文件夹路径')
    parser.add_argument('--output', '-o', required=True, help='输出YOLO标签文件夹路径')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    # 执行颜色检测
    process_images_to_yolo_format(args.input, args.output, progress_bar=None, progress_signal=None, log_signal=None)
    
    print(f"颜色检测完成。YOLO标签保存在: {args.output}")

if __name__ == "__main__":
    main()