import argparse
import os
from utils.merge_shp import merge_shp

def main():
    parser = argparse.ArgumentParser(description='合并多个Shapefile文件')
    parser.add_argument('--input', '-i', required=True, help='包含Shapefile的文件夹路径')
    parser.add_argument('--output', '-o', required=True, help='输出合并后的Shapefile路径')
    parser.add_argument('--crs', default='EPSG:4326', help='目标坐标参考系统')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    output_dir = os.path.dirname(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    # 执行合并
    merge_shp(args.input, args.output, args.crs)
    
    print(f"合并完成。合并后的Shapefile保存在: {args.output}")

if __name__ == "__main__":
    main()