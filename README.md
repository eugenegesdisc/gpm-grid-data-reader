# gpm-grid-data-reader
A QGIS plugin to assist in load GPM gridded data (L3) as a raster layer.

## Install (Windows)

1. clone the repository to your local machine.
2. Copy the directory "gpm-grid-data-reader" to your profile's qgis plugins directory. Normally, the plugin directory is in the following pattern.

C:\Users\username\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins

"username" should be your user profile name.

3. Start or re-start QGIS
4. Enable the plugin by checking the installed "GPM Grid Data Reader".
[Plugins] -> [Manage and Install Plugins...] -> [Installed] -> [GPM Grid Data Reader]

## Use the plugin

The following steps started the reader:

[Plugins] -> [GPM Grid Data Reader] -> [GPM Grid Reader]

Click the button "..." to browse and select a file.

Click "Add" button to open the file.

All variable (raster) will be listed. Select one or more. Then, click "Add Layers" to load the data into QGIS.

## Limitations

This plugin has been gone through very limited test. It is intended to be used for reading GPM Level 3 gridded data where the gdal driver does not retrieve the GeoTransform information properly. Older version of gdal drivers may parse those.

Currently supported:

- Add geotransform model with partially parsed by gdal.
- Add geotransform model from tags (i.e. NorthBoundingCoordinate, LongitudeResolution, etc.) in GRID header of HDF5
