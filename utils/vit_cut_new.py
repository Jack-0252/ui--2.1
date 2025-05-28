import os
from PIL import Image
import rasterio
from rasterio.windows import Window

def generate_tfw_from_geotiff(tif_path, output_path, window=None):
    """
    生成对应裁剪区域的 .tfw 文件，使用 rasterio 获取地理信息
    """
    with rasterio.open(tif_path) as src:
        # 获取地理变换信息
        transform = src.transform

        if window is not None:
            # 计算裁剪区域的左上角坐标 (地理坐标)
            top_left_x, top_left_y = transform * (window.col_off, window.row_off)
            # 获取像素的分辨率
            pixel_size_x = transform[0]  # X方向的像素大小
            pixel_size_y = transform[4]  # Y方向的像素大小 (通常是负值)

            # 构建 .tfw 文件内容
            tfw_content = f"""\
{pixel_size_x}
0.0
0.0
{pixel_size_y}
{top_left_x}
{top_left_y}
"""
        else:
            # 如果没有传入 window, 使用原图的地理变换信息
            tfw_content = f"""\
{transform[0]}
0.0
0.0
{transform[4]}
{transform[2]}
{transform[5]}
"""

        # 保存 .tfw 文件
        with open(output_path, 'w') as f:
            f.write(tfw_content)

def crop_tif_images(input_folder, output_image_folder, output_tfw_folder, x=400, min_size=50):
    """
    输入图像文件夹，输出裁剪后的图像和对应的tfw文件
    """
    if not os.path.exists(output_image_folder):
        os.makedirs(output_image_folder)
    if not os.path.exists(output_tfw_folder):
        os.makedirs(output_tfw_folder)

    # 遍历输入文件夹中的所有TIF文件
    for tif_file in os.listdir(input_folder):
        if tif_file.lower().endswith('.tif'):
            tif_path = os.path.join(input_folder, tif_file)
            image = Image.open(tif_path)
            width, height = image.size

            # 获取地理变换信息 (使用 rasterio 提取)
            with rasterio.open(tif_path) as src:
                geo_transform = src.transform

            # 判断图像大小
            if width >= min_size and height >= min_size and width <= x and height <= x:
                # 如果图像尺寸在 [50, 400] 范围内，则直接保存原图
                cropped_image_file = os.path.join(output_image_folder, tif_file)
                image.save(cropped_image_file)

                # 生成对应的 tfw 文件
                generate_tfw_from_geotiff(tif_path, os.path.join(output_tfw_folder, tif_file.replace('.tif', '.tfw')))
                print(f"保留原图: {cropped_image_file} 和 TFW 文件已生成")
            elif width > x or height > x:
                # 如果图像尺寸大于 400，则进行裁剪
                x_blocks = (width + x - 1) // x
                y_blocks = (height + x - 1) // x

                for i in range(x_blocks):
                    for j in range(y_blocks):
                        # 计算裁剪区域
                        left = i * x
                        upper = j * x
                        right = min(left + x, width)
                        lower = min(upper + x, height)

                        # 裁剪图像
                        cropped_image = image.crop((left, upper, right, lower))

                        # 只有裁剪后的图像尺寸大于min_size才保存
                        if cropped_image.width >= min_size and cropped_image.height >= min_size:
                            # 保存裁剪后的图像
                            cropped_image_file = os.path.join(output_image_folder, f"{os.path.splitext(tif_file)[0]}_{i}_{j}.tif")
                            cropped_image.save(cropped_image_file)

                            # 使用 rasterio 获取裁剪区域的地理信息 (window 坐标)
                            with rasterio.open(tif_path) as src:
                                window = Window(left, upper, right - left, lower - upper)
                                # 生成对应的 tfw 文件
                                generate_tfw_from_geotiff(tif_path, os.path.join(output_tfw_folder, f"{os.path.splitext(tif_file)[0]}_{i}_{j}.tfw"), window)
                                print(f"裁剪图像: {cropped_image_file} 和 TFW 文件已生成")
                        else:
                            print(f"裁剪图像: {cropped_image_file} 太小，已跳过")
            else:
                # 如果图像尺寸小于50，则不保存
                print(f"图像: {tif_file} 太小，已跳过")

# if __name__ == "__main__":
#     input_folder = r"C:\Users\jack\Desktop\pic"  # 输入图像文件夹
#     output_image_folder = r"C:\Users\jack\Desktop\b"  # 输出裁剪后的图像文件夹
#     output_tfw_folder = r"C:\Users\jack\Desktop\c"  # 输出TFW文件夹
#     crop_tif_images(input_folder, output_image_folder, output_tfw_folder)
