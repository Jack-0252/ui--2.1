import argparse
import os
import torch
from utils.predect import predict_and_move

def main():
    parser = argparse.ArgumentParser(description='使用VIT模型进行推理')
    parser.add_argument('--tif-dir', '-i', required=True, help='输入图像文件夹路径')
    parser.add_argument('--txt-dir', '-t', required=True, help='输入TXT文件夹路径')
    parser.add_argument('--output', '-o', required=True, help='输出标签文件夹路径')

    parser.add_argument('--json-path', '-j', default="config/class_indices.json", help='类别索引JSON文件路径(默认: class_indices.json)')
    parser.add_argument('--model-path', '-m', default="config/vit_gq.pth", help='模型权重文件路径(默认: vit_gq.pth)')

    parser.add_argument('--use-cuda', '-c', action='store_true', help='是否使用CUDA')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    # 设置设备
    device = torch.device("cuda:0" if args.use_cuda and torch.cuda.is_available() else "cpu")
    
    # 执行推理
    predict_and_move(args.tif_dir, args.txt_dir, args.output, args.json_path, args.model_path, device)
    
    print(f"VIT推理完成。结果保存在: {args.output}")

if __name__ == "__main__":
    main()