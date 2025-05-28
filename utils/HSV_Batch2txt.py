import cv2
import numpy as np
import os
from tqdm import tqdm

def process_images_to_yolo_format(input_folder, yolo_output_folder, lower_bound=None, upper_bound=None,
                                  min_area_ratio=0.005, progress_bar=None, progress_signal=None, log_signal=None):
    """
    处理图像，筛选出符合条件的目标并生成YOLO格式的标签文件。

    参数：
    input_folder (str): 输入图像文件夹路径
    yolo_output_folder (str): YOLO标签文件保存路径
    lower_bound (array): HSV颜色空间下界，默认为None
    upper_bound (array): HSV颜色空间上界，默认为None
    min_area_ratio (float): 最小目标面积占图像面积的比例，默认为0.01（即1%）
    """

    # 设置默认的HSV颜色区间（如果未传入）
    if lower_bound is None:
        lower_bound = np.array([35, 30, 30])  # H通道下界
    if upper_bound is None:
        upper_bound = np.array([90, 255, 255])  # H通道上界

    # 类别ID（假设只有一个类别）
    class_id = 0

    # 创建YOLO标签输出文件夹（如果不存在）
    os.makedirs(yolo_output_folder, exist_ok=True)

    # 获取所有图像文件列表
    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
    
    # 使用tqdm创建进度条，如果提供了Qt进度条参数，则使用QtTqdm
    if progress_bar is not None or progress_signal is not None:
        from utils.qt_tqdm import QtTqdm
        progress_iterator = QtTqdm(
            image_files, 
            desc="处理图像", 
            unit="张",
            progress_bar=progress_bar,
            progress_signal=progress_signal,
            log_signal=log_signal,
            step_name="HSV颜色检测"
        )
    else:
        progress_iterator = tqdm(image_files, desc="处理图像", unit="张")
    
    for file_name in progress_iterator:
        file_path = os.path.join(input_folder, file_name)

        # 检查文件是否为图像
        if not (file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))):
            continue  # 跳过非图像文件

        # 读取图像
        image_bgr = cv2.imread(file_path)
        if image_bgr is None:
            print(f"无法加载图像：{file_name}")
            continue

        # 转换到HSV色彩空间
        image_hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

        # 创建掩膜（H通道在指定范围内）
        mask = cv2.inRange(image_hsv, lower_bound, upper_bound)

        # 进行形态学闭运算
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 8))
        closed_mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 取黑色部分（掩膜的反转部分）
        inverted_mask = cv2.bitwise_not(closed_mask)

        # 找到轮廓并计算面积
        contours, _ = cv2.findContours(inverted_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = min_area_ratio * image_bgr.shape[0] * image_bgr.shape[1]  # 面积阈值

        # 如果找到的轮廓符合条件，就生成YOLO格式的txt文件
        if contours:
            yolo_txt_path = os.path.join(yolo_output_folder, file_name.split('.')[0] + '.txt')

            with open(yolo_txt_path, 'w') as f:
                # 遍历每个轮廓，计算并保存YOLO格式标签
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area >= min_area:
                        x, y, w, h = cv2.boundingRect(contour)

                        # 计算矩形框的中心、宽度和高度的归一化值
                        x_center = (x + w / 2) / image_bgr.shape[1]
                        y_center = (y + h / 2) / image_bgr.shape[0]
                        width = w / image_bgr.shape[1]
                        height = h / image_bgr.shape[0]

                        # 写入YOLO格式标签
                        f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")

    print(f"批量处理完成，YOLO标签已保存到：{yolo_output_folder}")


# 示例用法
# input_folder = r"D:\Color_test\TiffShow\test"  # 替换为您的输入文件夹路径
# yolo_output_folder = r"D:\Color_test\TiffShow\yolo_labels"  # YOLO标签输出文件夹路径
#
# # 调用函数进行处理
# process_images_to_yolo_format(input_folder, yolo_output_folder)
