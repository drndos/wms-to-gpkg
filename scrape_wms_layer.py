import requests
from lxml import etree
import geopandas as gpd
from shapely.geometry import Polygon
from affine import Affine
import json
from tqdm import tqdm
import time

#
# Mierovo
# x_min = 1933990.0
# y_min = 6116629.0
# x_max = 1936312.0
# y_max = 6118951.0

# Kvetoslavov+Hviezdoslavov
size_map = 6374.0
x_min = 1928111.0
y_min = 6112674.0
x_max = x_min + size_map
y_max = y_min + size_map

size_svg = 2500
width = size_svg
height = size_svg
percent_scale = 75
svg_width = size_svg * (percent_scale / 100.0)
svg_height = size_svg * (percent_scale / 100.0)

wms_url = "https://zoznamstavieb.skgeodesy.sk/stavby/services/WMS/zoznam_stavieb_wms/MapServer/WMSServer"

def call_wms(url, params):
  for attempt in range(5):
    try:
      # full_url = requests.Request('GET', url, params=params).prepare().url
      # print(f"Full URL: {full_url}")
      response = requests.get(url, params=params)

      if response.status_code == 200:
        return response.content
      else:
        print(f"Request failed with status code: {response.status_code}")
        return None
    except Exception as e:
      print("failed to get " + url + " ex:")
      print(e)
      time.sleep(2)
  return None


params = {
  'service': 'WMS',
  'version': '1.3.0',
  'request': 'GetMap',
  'layers': '0',
  'styles': 'default',
  'crs': 'EPSG:3857',
  'bbox': str(x_min) + ',' + str(y_min) + ',' + str(x_max) + ',' + str(y_max),
  'width': str(width),
  'height': str(height),
  'format': 'image/svg+xml',
}

data = call_wms(wms_url, params)

if data is not None:
  with open('output.svg', 'wb') as file:
    file.write(data)
  root = etree.fromstring(data)
  ns = {'svg': 'http://www.w3.org/2000/svg'}
  groups = root.xpath('//svg:g', namespaces=ns)
  geometries = [group.xpath('.//svg:path', namespaces=ns)[0] for group in groups
                if group.xpath('.//svg:path', namespaces=ns)]

  transform = Affine.translation(x_min, y_max) * Affine.scale(
      (x_max - x_min) / width, -(y_max - y_min) / height)

  features = []
  print("number of buildings: " + str(len(geometries)))
  for geometry in tqdm(geometries, desc="Processing geometries"):
    d = geometry.attrib['d'].replace('M', '').replace('L', '').replace(' Z ', ' ').strip().split(" ")
    points = [(float(d[i]), float(d[i + 1])) for i in range(0, len(d), 2)]

    # apply the transformation to the original polygon coordinates
    points_transformed_svg = []
    for point in points:
      new_x = (point[0] + svg_width / 2) / percent_scale * 100
      new_y = (svg_height - (point[1] + svg_height / 2)) / percent_scale * 100
      points_transformed_svg.append((new_x, new_y))
    poly_transformed_svg = Polygon(points_transformed_svg)

    points_transformed = [transform * point for point in points_transformed_svg]
    poly_transformed = Polygon(points_transformed)

    point_on_surface = poly_transformed_svg.point_on_surface()
    params = {
      'service': 'WMS',
      'version': '1.3.0',
      'request': 'GetFeatureInfo',
      'bbox': str(x_min) + ',' + str(y_min) + ',' + str(x_max) + ',' + str(
          y_max),
      'crs': 'EPSG:3857',
      'width': str(width),
      'height': str(height),
      'layers': '0',
      'query_layers': '0',
      'styles': '',
      'format': 'image/svg+xml',
      'info_format': 'application/geojson',
      'i': int(point_on_surface.x),
      'j': int(point_on_surface.y),
    }
    info = call_wms(wms_url, params)

    if info is not None:
      info_json = json.loads(info)
      if 'features' in info_json and len(info_json['features']) > 0:
        info_json['features'][0][
          'geometry'] = poly_transformed.__geo_interface__
        features.append(info_json['features'][0])
      else:
        print("No features for this request:" + geometry.attrib['d'])
    else:
      print("Polygon did not yield any results:" + geometry.attrib['d'])

  feature_collection = {
    'type': 'FeatureCollection',
    'features': features
  }
  gdf = gpd.GeoDataFrame.from_features(feature_collection, crs="EPSG:3857")
  gdf.to_file("output.gpkg", driver="GPKG")
