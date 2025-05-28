import os
import json
import torch
from PIL import Image
from torchvision import transforms
from torch.utils.data import DataLoader, Dataset
from utils.vit_model import vit_base_patch16_224_in21k as create_model
from tqdm import tqdm
import shutil
"""
该VIT用来将图像文件夹中预测非病树图像的同名ｔｘｔ文件从ｔｘｔ文件夹转移到另一个文件夹中
img_path：存放ｔｉｆ图文件夹
source_txt_dir：存放ｔｉｆ图对应的同名ＹＯＬＯ格式的ｔｘｔ文件夹
target_txt_dir：存放经VIT判断后非病树图像对应的txt文件夹。
"""

class CustomDataset(Dataset):
    def __init__(self, img_paths, transform=None):
        self.img_paths = img_paths
        self.transform = transform

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img_path = self.img_paths[idx]
        img = Image.open(img_path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, img_path


def move_yolo_txt(img_path, source_txt_dir, target_txt_dir):
    """Move YOLO format annotation txt files to the target directory."""
    # Get the base name of the image (without extension)
    img_name = os.path.basename(img_path)
    txt_name = os.path.splitext(img_name)[0] + ".txt"

    source_txt_path = os.path.join(source_txt_dir, txt_name)
    target_txt_path = os.path.join(target_txt_dir, txt_name)

    # If the txt file exists, move it to the new directory
    if os.path.exists(source_txt_path):
        shutil.move(source_txt_path, target_txt_path)
        print(f"Moved: {txt_name}")
    else:
        print(f"Warning: No corresponding txt file for {img_name}.")


def predict_and_move(img_dir, yolo_txt_dir, target_txt_dir, json_path, model_weight_path, device, batch_size=64):
    data_transform = transforms.Compose(
        [transforms.Resize(256),
         transforms.CenterCrop(224),
         transforms.ToTensor(),
         transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])])

    # Load images from directory
    assert os.path.exists(img_dir), f"directory: '{img_dir}' does not exist."
    img_paths = [os.path.join(img_dir, img_name) for img_name in os.listdir(img_dir) if img_name.endswith('.tif')]

    # Create the target directory for non-diseased tree txt files
    os.makedirs(target_txt_dir, exist_ok=True)

    # Read class_indict
    assert os.path.exists(json_path), f"file: '{json_path}' does not exist."
    with open(json_path, "r") as f:
        class_indict = json.load(f)

    # Create model
    model = create_model(num_classes=2, has_logits=False).to(device)
    # Load model weights
    model.load_state_dict(torch.load(model_weight_path, map_location=device))
    model.eval()

    # Create a DataLoader
    dataset = CustomDataset(img_paths, transform=data_transform)
    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    for imgs, img_paths in tqdm(data_loader, desc="Predicting"):
        imgs = imgs.to(device)
        with torch.no_grad():
            outputs = model(imgs)
            predicts = torch.softmax(outputs, dim=1)
            predict_clas = torch.argmax(predicts, dim=1)

        for i in range(len(img_paths)):
            img_path = img_paths[i]
            predict_cla = predict_clas[i].item()
            prob = predicts[i][predict_cla].item()

            # 根据预测类别打印结果
            print_res = f"Image: {img_path} - class: {class_indict[str(predict_cla)]}   prob: {prob:.3f}"
            print(print_res)

            # 如果是健康树（即类别为 1），则移动相应的 YOLO txt 文件
            if predict_cla == 1:  # 预测为健康树
                move_yolo_txt(img_path, yolo_txt_dir, target_txt_dir)

# Usage example:

# img_dir = "path/to/tif_images"
# yolo_txt_dir = "path/to/yolo_txts"
# target_txt_dir = "path/to/save/target_txts"
# json_path = "path/to/class_indices.json"
# model_weight_path = "path/to/vit_model_weights.pth"
# device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# predict_and_move(img_dir, yolo_txt_dir, target_txt_dir, json_path, model_weight_path, device)
