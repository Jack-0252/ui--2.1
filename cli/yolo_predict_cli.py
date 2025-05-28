import argparse
import os
import shutil
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description='使用YOLO模型进行预测')
    parser.add_argument('--input', '-i', required=True, help='输入图像文件夹路径')
    parser.add_argument('--model', '-m', required=True, help='YOLO模型路径')
    parser.add_argument('--output', '-o', required=True, help='输出标签文件夹路径')
    parser.add_argument('--conf', '-c', type=float, default=0.3, help='置信度阈值')
    parser.add_argument('--iou', type=float, default=0.01, help='IOU阈值')
    parser.add_argument('--img-size', '-s', type=int, default=640, help='图像大小')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    # 加载模型
    model = YOLO(args.model)
    
    # 获取图像文件列表
    image_files = [f for f in os.listdir(args.input) if f.endswith(('.jpg', '.png', '.tif', '.jpeg'))]
    
    # 执行预测
    for i, image in enumerate(image_files, start=1):
        image_file_path = os.path.join(args.input, image)
        model.predict(source=image_file_path, save_txt=True, conf=args.conf, iou=args.iou, imgsz=args.img_size)
        print(f"处理进度: {i}/{len(image_files)}")
    
    # 复制标签文件到输出目录
    # 在打包环境中，需要使用绝对路径
    import sys
    if getattr(sys, 'frozen', False):
        # 打包后的环境，使用exe所在目录
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境，使用当前工作目录
        base_dir = os.getcwd()
    
    src_folder = os.path.join(base_dir, 'runs/detect/predict/labels')
    if os.path.exists(src_folder):
        if os.path.exists(args.output):
            shutil.rmtree(args.output)
            print(f"目标文件夹 {args.output} 已删除。")
        shutil.copytree(src_folder, args.output)
        print(f"文件夹 {src_folder} 已成功复制到 {args.output}。")
    else:
        print(f"源文件夹 {src_folder} 不存在。")
        # 尝试查找其他可能的路径
        possible_paths = [
            os.path.join(os.getcwd(), 'runs/detect/predict/labels'),
            os.path.join(os.path.dirname(__file__), '../runs/detect/predict/labels'),
            'runs/detect/predict/labels'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                print(f"找到标签文件夹: {path}")
                if os.path.exists(args.output):
                    shutil.rmtree(args.output)
                    print(f"目标文件夹 {args.output} 已删除。")
                shutil.copytree(path, args.output)
                print(f"文件夹 {path} 已成功复制到 {args.output}。")
                break
        else:
            print("未找到任何标签文件夹。")
    
    print(f"YOLO预测完成。结果保存在: {args.output}")

if __name__ == "__main__":
    main()