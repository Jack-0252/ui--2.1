import argparse
import os
from utils.txt_to_shp import batch_process

def main():
    parser = argparse.ArgumentParser(description='将YOLO格式标签转换为Shapefile')
    parser.add_argument('--tif-folder', '-tf', required=True, help='TIF图像文件夹路径')
    parser.add_argument('--tfw-folder', '-tw', required=True, help='TFW文件夹路径')
    parser.add_argument('--txt-folder', '-tx', required=True, help='YOLO标签文件夹路径')
    parser.add_argument('--output', '-o', required=True, help='输出Shapefile文件夹路径')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    # 执行转换
    batch_process(args.tif_folder, args.tfw_folder, args.txt_folder, args.output)
    
    print(f"转换完成。Shapefile保存在: {args.output}")

if __name__ == "__main__":
    main()