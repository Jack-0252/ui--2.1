import os
import numpy as np
from tqdm import tqdm
from osgeo import gdal  # 添加了这行导入


def generate_tfw(geo_transform, x_offset, y_offset, output_path):
    """
    根据裁剪区域的地理变换信息生成 TFW 文件
    """
    pixel_size_x = geo_transform[1]
    pixel_size_y = geo_transform[5]
    upper_left_x = geo_transform[0] + x_offset * pixel_size_x
    upper_left_y = geo_transform[3] + y_offset * pixel_size_y

    tfw_content = f"""\
{pixel_size_x}
0.0
0.0
{pixel_size_y}
{upper_left_x}
{upper_left_y}
"""

    with open(output_path, 'w') as f:
        f.write(tfw_content)


def find_valid_area(raster_band):
    """
    查找影像中有效区域（非空白区域）的边界
    """
    data = raster_band.ReadAsArray()
    valid_mask = data != 0  # 假设空白区域像素值为 0

    rows = np.any(valid_mask, axis=1)
    cols = np.any(valid_mask, axis=0)

    min_row, max_row = np.where(rows)[0][[0, -1]]
    min_col, max_col = np.where(cols)[0][[0, -1]]

    return min_row, max_row, min_col, max_col


def cutting(input_raster, output_image_folder, output_tfw_folder, crop_size_x, crop_size_y, step_size_x, step_size_y):
    """
    裁剪大图的有效区域并生成小图及其 TFW 文件，分别存储在不同文件夹中
    """
    ds = gdal.Open(input_raster)
    geo_transform = ds.GetGeoTransform()
    raster_band = ds.GetRasterBand(1)

    # 找到有效区域
    min_row, max_row, min_col, max_col = find_valid_area(raster_band)

    os.makedirs(output_image_folder, exist_ok=True)
    os.makedirs(output_tfw_folder, exist_ok=True)

    count = 0
    total_steps = ((max_col - min_col - crop_size_x) // step_size_x + 1) * ((max_row - min_row - crop_size_y) // step_size_y + 1)

    with tqdm(total=total_steps, desc="Cutting") as pbar:
        for x_offset in range(min_col, max_col - crop_size_x + 1, step_size_x):
            for y_offset in range(min_row, max_row - crop_size_y + 1, step_size_y):
                # 确保裁剪窗口在有效区域内
                width = min(crop_size_x, max_col - x_offset)
                height = min(crop_size_y, max_row - y_offset)

                output_raster = os.path.join(output_image_folder, f"crop_{count}.tif")
                output_tfw = os.path.join(output_tfw_folder, f"crop_{count}.tfw")

                # 读取裁剪区域数据，检查是否为空
                sub_data = raster_band.ReadAsArray(x_offset, y_offset, width, height)
                if np.all(sub_data == 0):
                    pbar.update(1)
                    continue

                # 裁剪并生成 TFW 文件
                gdal.Translate(output_raster, ds, srcWin=[x_offset, y_offset, width, height])
                generate_tfw(geo_transform, x_offset, y_offset, output_tfw)

                count += 1
                pbar.update(1)

    ds = None


# # 示例用法
# input_raster = "path_to_your_large_image.tif"
# output_image_folder = "path_to_output_images"
# output_tfw_folder = "path_to_output_tfws"
# crop_size_x = 512
# crop_size_y = 512
# step_size_x = 256  # 步长，可以调整以获得不同的重叠程度
# step_size_y = 256  # 步长，可以调整以获得不同的重叠程度
#
# cutting(input_raster, output_image_folder, output_tfw_folder, crop_size_x, crop_size_y, step_size_x, step_size_y)
