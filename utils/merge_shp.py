import os
import geopandas as gpd
import pandas as pd
from tqdm import tqdm

def merge_shp(input_folder, output_file, target_crs='EPSG:4326'):
    # 创建输出文件夹
    output_folder = os.path.dirname(output_file)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    gdfs = []
    sub_folders = [os.path.join(input_folder, sub_folder) for sub_folder in os.listdir(input_folder) if
                   os.path.isdir(os.path.join(input_folder, sub_folder))]

    for sub_folder_path in tqdm(sub_folders, desc='merge_shp'):
        for file in os.listdir(sub_folder_path):
            if file.endswith('.shp'):
                file_path = os.path.join(sub_folder_path, file)
                gdf = gpd.read_file(file_path)
                gdf = gdf.to_crs(target_crs)
                gdfs.append(gdf)

    if not gdfs:
        print("No shapefiles found in the specified input folder.")
        return

    merged_gdf = pd.concat(gdfs, ignore_index=True)
    merged_gdf.to_file(output_file)
    print(f"Merged shapefile saved to {output_file}")
