import argparse
import os

def create_txt_for_files(input_folder, output_folder):
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    for file in os.listdir(input_folder):
        if os.path.isfile(os.path.join(input_folder, file)):
            name, ext = os.path.splitext(file)
            if ext:  # 确保文件有扩展名
                txt_file_path = os.path.join(output_folder, name + '.txt')
                with open(txt_file_path, 'w') as f:
                    f.write("0 0.5 0.5 1.0 1.0\n")

def main():
    parser = argparse.ArgumentParser(description='为文件夹中的每个文件创建对应的TXT文件')
    parser.add_argument('--input', '-i', required=True, help='输入文件夹路径')
    parser.add_argument('--output', '-o', required=True, help='输出TXT文件夹路径')
    
    args = parser.parse_args()
    
    # 执行创建
    create_txt_for_files(args.input, args.output)
    
    print(f"TXT文件创建完成。保存在: {args.output}")

if __name__ == "__main__":
    main()