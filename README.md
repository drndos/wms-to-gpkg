# wms-to-gpkg
Scrapes the data from WMS service for given square and saves it as GeoPackage vector / shape with information. "So it is basically doing the WMS to WFS conversion in a sense." The result can be viewed, filtered, styled in QGIS.

Notes:
- It works best when it is square
- if you increase the size of the boundaries, it is advised to also increase the size of svg
- Sometimes the big size SVG didn't work, sometimes the smaller svg was not enough and didn't work, always check the resulting svg file whether it is OK for your needs
- Requires the WMS service to support SVG output format and GeoJSON GetFeatureInfo output format but can be adapted to any other output formats.
- Handling of polygons might be a little bit too naive with removing the "Z" directive
- BEWARE it is taking only first path from the "g", because the service I was using had unnecessary duplicates
- Always tune this script to your needs

TODO: 
- Determine the scale factor from svg itself (you can check the structure of the SVG file when it is downloaded and tune the script based on that for now)
- Tiling for bigger boundaries


