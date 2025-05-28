import os
import numpy as np
from osgeo import gdal, ogr, osr
from shapely.geometry import Polygon
from tqdm import tqdm

def read_tfw(tfw_path):
    with open(tfw_path, 'r') as f:
        lines = f.readlines()
        x_pixel_size = float(lines[0])
        rotation_1 = float(lines[1])
        rotation_2 = float(lines[2])
        y_pixel_size = float(lines[3])
        top_left_x = float(lines[4])
        top_left_y = float(lines[5])
    return top_left_x, top_left_y, x_pixel_size, y_pixel_size

def read_image_size(tif_path):
    dataset = gdal.Open(tif_path)
    width = dataset.RasterXSize
    height = dataset.RasterYSize
    return width, height

def read_yolo_labels(label_path):
    labels = []
    with open(label_path, 'r') as f:
        for line in f.readlines():
            parts = line.strip().split()
            cls = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])
            #if float(parts[5]) > 0.8:
            labels.append((cls, x_center, y_center, width, height))
    return labels

def pixel_to_geo(x_pix, y_pix, top_left_x, top_left_y, x_pixel_size, y_pixel_size):
    x_geo = top_left_x + x_pix * x_pixel_size
    y_geo = top_left_y + y_pix * y_pixel_size
    return x_geo, y_geo

def create_shapefile(output_path, labels, top_left_x, top_left_y, x_pixel_size, y_pixel_size, img_width, img_height):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(output_path)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # 根据你的坐标系修改
    layer = data_source.CreateLayer("labels", srs, ogr.wkbPolygon)

    field_class = ogr.FieldDefn("Class", ogr.OFTInteger)
    layer.CreateField(field_class)

    for label in labels:
        cls, x_center, y_center, width, height = label
        x_pix_center = x_center * img_width
        y_pix_center = y_center * img_height
        box_width = width * img_width
        box_height = height * img_height
        x_pix_min = x_pix_center - box_width / 2
        y_pix_min = y_pix_center - box_height / 2
        x_pix_max = x_pix_center + box_width / 2
        y_pix_max = y_pix_center + box_height / 2

        geo_coords = [
            pixel_to_geo(x_pix_min, y_pix_min, top_left_x, top_left_y, x_pixel_size, y_pixel_size),
            pixel_to_geo(x_pix_max, y_pix_min, top_left_x, top_left_y, x_pixel_size, y_pixel_size),
            pixel_to_geo(x_pix_max, y_pix_max, top_left_x, top_left_y, x_pixel_size, y_pixel_size),
            pixel_to_geo(x_pix_min, y_pix_max, top_left_x, top_left_y, x_pixel_size, y_pixel_size),
            pixel_to_geo(x_pix_min, y_pix_min, top_left_x, top_left_y, x_pixel_size, y_pixel_size)
        ]

        poly = Polygon(geo_coords)
        wkt = poly.wkt
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField("Class", cls)
        geom = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(geom)
        layer.CreateFeature(feature)
        feature = None

    data_source = None

def batch_process(tif_folder, tfw_folder, txt_folder, output_folder):
    tif_files = [f for f in os.listdir(tif_folder) if f.endswith('.tif')]
    for tif_file in tqdm(tif_files, desc='txt_to_shp'):
        base_name = os.path.splitext(tif_file)[0]
        tif_path = os.path.join(tif_folder, tif_file)
        tfw_path = os.path.join(tfw_folder, base_name + '.tfw')
        txt_path = os.path.join(txt_folder, base_name + '.txt')
        output_subfolder = os.path.join(output_folder, base_name)
        os.makedirs(output_subfolder, exist_ok=True)
        output_shp_path = os.path.join(output_subfolder, base_name + '.shp')

        if os.path.exists(tfw_path) and os.path.exists(txt_path):
            top_left_x, top_left_y, x_pixel_size, y_pixel_size = read_tfw(tfw_path)
            img_width, img_height = read_image_size(tif_path)
            labels = read_yolo_labels(txt_path)
            create_shapefile(output_shp_path, labels, top_left_x, top_left_y, x_pixel_size, y_pixel_size, img_width, img_height)
            print(f"Shapefile created for {tif_file}")
        else:
            print(f"Missing TFW or TXT file for {tif_file}")
