import argparse
import os
from utils.tiqu import tiqu

def main():
    parser = argparse.ArgumentParser(description='从文件夹中提取特定扩展名的文件')
    parser.add_argument('--input', '-i', required=True, help='输入文件夹路径')
    parser.add_argument('--output', '-o', required=True, help='输出文件夹路径')
    parser.add_argument('--extension', '-e', required=True, help='要提取的文件扩展名(如.tif)')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    # 执行提取
    tiqu(args.input, args.output, args.extension)
    
    print(f"提取完成。提取的文件保存在: {args.output}")

if __name__ == "__main__":
    main()