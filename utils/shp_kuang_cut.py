import os
import fiona
import rasterio
from rasterio.mask import mask
from shapely.geometry import shape, mapping, Polygon
from shapely.affinity import rotate, scale
import numpy as np
from tqdm import tqdm


def get_minimum_rotated_rectangle(geom, scale_factor=1.0):
    """获取最小外接矩形并旋转至水平，允许调整矩形大小倍数"""
    min_rect = geom.minimum_rotated_rectangle
    coords = list(min_rect.exterior.coords)
    edge1 = np.array(coords[1]) - np.array(coords[0])
    edge2 = np.array(coords[2]) - np.array(coords[1])
    edge = edge1 if np.linalg.norm(edge1) > np.linalg.norm(edge2) else edge2
    angle = np.degrees(np.arctan2(edge[1], edge[0]))
    rotated_rect = rotate(min_rect, -angle, origin='center')

    # 根据给定的比例缩放最小外接矩形
    if scale_factor != 1.0:
        rotated_rect = scale(rotated_rect, xfact=scale_factor, yfact=scale_factor, origin='center')

    return rotated_rect


def write_tfw(transform, output_tfw):
    """生成tfw文件"""
    with open(output_tfw, 'w') as tfw:
        tfw.write(f'{transform.a:.10f}\n')
        tfw.write(f'{transform.b:.10f}\n')
        tfw.write(f'{transform.d:.10f}\n')
        tfw.write(f'{transform.e:.10f}\n')
        tfw.write(f'{transform.xoff:.10f}\n')
        tfw.write(f'{transform.yoff:.10f}\n')


def crop_and_save_raster(input_tif, input_shp, output_dir, scale_factor=1.0, progress_bar=None, progress_signal=None, log_signal=None):
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 读取shp文件
    with fiona.open(input_shp, 'r') as shp:
        features = [feature for feature in shp]
        schema = shp.schema
        crs = shp.crs

    # 读取大tif图像
    with rasterio.open(input_tif) as src:
        # 使用tqdm创建进度条，如果提供了Qt进度条参数，则使用QtTqdm
        if progress_bar is not None or progress_signal is not None:
            from utils.qt_tqdm import QtTqdm
            progress_iterator = QtTqdm(
                features, 
                desc="裁剪图像", 
                unit="块",
                progress_bar=progress_bar,
                progress_signal=progress_signal,
                log_signal=log_signal,
                step_name="裁剪图像"
            )
        else:
            progress_iterator = tqdm(features, desc="裁剪图像", unit="块")
            
        for i, feature in enumerate(progress_iterator):
            try:
                # 获取标注框的几何形状
                geom = shape(feature['geometry'])

                # 如果几何对象为空，则跳过
                if geom.is_empty:
                    continue

                # 计算最小外接矩形并旋转至水平，同时调整矩形大小
                rotated_rect = get_minimum_rotated_rectangle(geom, scale_factor=scale_factor)

                # 裁剪tif图像
                out_image, out_transform = mask(src, [mapping(rotated_rect)], crop=True)

                # 创建子文件夹
                subfolder = os.path.join(output_dir, f'crop_y{i}')
                if not os.path.exists(subfolder):
                    os.makedirs(subfolder)

                # 输出文件路径
                output_tif = os.path.join(subfolder, f'crop_y{i}.tif')
                output_shp = os.path.join(subfolder, f'crop_y{i}.shp')
                output_tfw = os.path.join(subfolder, f'crop_y{i}.tfw')

                # 保存裁剪后的tif图像
                out_meta = src.meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })

                with rasterio.open(output_tif, 'w', **out_meta) as dest:
                    dest.write(out_image)

                # 生成并保存tfw文件
                write_tfw(out_transform, output_tfw)

                # 创建新的shp文件
                with fiona.open(output_shp, 'w', driver='ESRI Shapefile', crs=crs, schema=schema) as dest_shp:
                    new_feature = {
                        'geometry': mapping(rotated_rect),
                        'properties': feature['properties']
                    }
                    dest_shp.write(new_feature)

            except Exception as e:
                print(f"Error processing feature {i}: {e}")

# # 输入文件路径
# input_tif = 'D:\\病树检测\\code_merge\\sicktree_merge_code\\data\\10\\2.tif'
# input_shp = 'D:\\病树检测\\code_merge\\sicktree_merge_code\\data\\merge_shp\\merged_shapefile.shp'
# output_dir = 'D:\\病树检测\\code_merge\\sicktree_merge_code\\data\\ceshi\\10\\diecai'
# scale_factor = 1.5  # 例如放大1.5倍
#
# # 执行裁剪并保存
# crop_and_save_raster(input_tif, input_shp, output_dir, scale_factor)
