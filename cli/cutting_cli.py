import argparse
import os
from utils.cutting import cutting

def main():
    parser = argparse.ArgumentParser(description='裁剪大图为小图并生成TFW文件')
    parser.add_argument('--input', '-i', required=True, help='输入栅格图像路径')
    parser.add_argument('--output-image', '-oi', required=True, help='输出小图文件夹路径')
    parser.add_argument('--output-tfw', '-ot', required=True, help='输出TFW文件夹路径')
    parser.add_argument('--crop-size-x', '-cx', type=int, default=640, help='裁剪宽度(像素)')
    parser.add_argument('--crop-size-y', '-cy', type=int, default=640, help='裁剪高度(像素)')
    parser.add_argument('--step-size-x', '-sx', type=int, default=640, help='X方向步长(像素)')
    parser.add_argument('--step-size-y', '-sy', type=int, default=640, help='Y方向步长(像素)')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output_image, exist_ok=True)
    os.makedirs(args.output_tfw, exist_ok=True)
    
    # 执行裁剪
    cutting(args.input, args.output_image, args.output_tfw, 
            args.crop_size_x, args.crop_size_y, 
            args.step_size_x, args.step_size_y)
    
    print(f"裁剪完成。输出图像保存在: {args.output_image}")
    print(f"TFW文件保存在: {args.output_tfw}")

if __name__ == "__main__":
    main()