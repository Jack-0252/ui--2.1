import os
import shutil
from tqdm import tqdm


def tiqu(input_folder, output_folder, extension):
    """
    从输入文件夹及其所有子文件夹中提取指定扩展名的图像并复制到输出文件夹。

    参数:
    input_folder (str): 输入文件夹路径
    output_folder (str): 输出文件夹路径
    extension (str): 要提取的文件的扩展名（例如 '.tif'）
    """
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 统计所有匹配的文件数量
    file_list = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith(extension):
                file_list.append(os.path.join(root, file))

    # 使用tqdm显示进度条
    for source_file in tqdm(file_list, desc="tiqu_tif&tfw"):
        # 构建目标文件路径
        target_file = os.path.join(output_folder, os.path.basename(source_file))
        # 将文件复制到输出文件夹
        shutil.copy2(source_file, target_file)

    print(f"所有 {extension} 图像已提取到文件夹 {output_folder} 中。")


# # 示例用法
# tiqu('/path/to/input/folder', '/path/to/output/folder', '.tif')

# # 示例调用
# input_folder = 'D:\\病树检测\\code_merge\\sicktree_merge_code\\data\\ceshi\\10\\diecai'
# output_folder = 'D:\\病树检测\\code_merge\\sicktree_merge_code\\data\\ceshi\\10\\image_folder'
# file_extension = '.tif'
# tiqu(input_folder, output_folder, file_extension)
