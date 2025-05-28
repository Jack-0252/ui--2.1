import argparse
import os
from utils.shp_kuang_cut import crop_and_save_raster

def main():
    parser = argparse.ArgumentParser(description='根据Shapefile裁剪栅格图像')
    parser.add_argument('--input', '-i', required=True, help='输入栅格图像路径')
    parser.add_argument('--shapefile', '-s', required=True, help='用于裁剪的Shapefile路径')
    parser.add_argument('--output', '-o', required=True, help='输出裁剪后图像的文件夹路径')
    parser.add_argument('--scale', '-sc', type=float, default=1.0, help='缩放因子')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    # 执行裁剪
    crop_and_save_raster(args.input, args.shapefile, args.output, args.scale, progress_bar=None, progress_signal=None, log_signal=None)
    
    print(f"裁剪完成。裁剪后的图像保存在: {args.output}")

if __name__ == "__main__":
    main()