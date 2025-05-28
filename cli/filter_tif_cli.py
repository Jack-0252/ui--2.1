import argparse
import os
import shutil

def filter_tif_by_txt(tif_folder, txt_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    txt_files = {os.path.splitext(f)[0] for f in os.listdir(txt_folder) if f.endswith('.txt')}
    for tif_file in os.listdir(tif_folder):
        if tif_file.endswith('.tif'):
            tif_name = os.path.splitext(tif_file)[0]  # 获取文件名（去除扩展名）
            if tif_name in txt_files:
                shutil.copy(os.path.join(tif_folder, tif_file), os.path.join(output_folder, tif_file))

def main():
    parser = argparse.ArgumentParser(description='根据TXT文件筛选TIF文件')
    parser.add_argument('--tif-folder', '-t', required=True, help='TIF文件夹路径')
    parser.add_argument('--txt-folder', '-x', required=True, help='TXT文件夹路径')
    parser.add_argument('--output', '-o', required=True, help='输出筛选后的TIF文件夹路径')
    
    args = parser.parse_args()
    
    # 执行筛选
    filter_tif_by_txt(args.tif_folder, args.txt_folder, args.output)
    
    print(f"筛选完成。筛选后的TIF文件保存在: {args.output}")

if __name__ == "__main__":
    main()