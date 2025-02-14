# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GPMGridRasterReaderDialog
                                 A QGIS plugin
 Read gridded data of GPM (L3 reguarly gridded)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-12-14
        git sha              : $Format:%H$
        copyright            : (C) 2023 by GES DISC & George Mason University
        email                : gyu@gmu.edu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import math
import json
import xml.etree.ElementTree as ET
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from osgeo import gdal

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gpm_grid_data_reader_dialog_add_layer.ui'))


class GPMGridRasterReaderDialogAddLayer(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None,
                 table_content:list[tuple]=None, table_header:list=None):
        """Constructor."""
        super(GPMGridRasterReaderDialogAddLayer, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface=iface
        self.setupUi(self)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Add Layers")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(
            self._handle_add_layers)
        self.lineEdit.textChanged.connect(self._table_filter)
        self.toolButton.clicked.connect(self._table_select_all)
        self.toolButton_2.clicked.connect(self._table_deselect_all)
        self.tableWidget.itemSelectionChanged.connect(self._handle_table_select_change)
        self._load_table(table_content=table_content, table_header=table_header)

    def _handle_table_select_change(self):
        the_list = self.tableWidget.selectedItems()
        if len(the_list) > 0:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def _load_table(self, table_content:list[tuple], table_header:list):
        if table_header is None:
            return
        _n_cols = len(table_header)
        self.tableWidget.setColumnCount(_n_cols)
        self.tableWidget.setHorizontalHeaderLabels(table_header)

        if table_content is None:
            return
        _n_rows = len(table_content)
        self.tableWidget.setRowCount(_n_rows)
        for row in range(_n_rows):
            for col in range(_n_cols):
                item = QtWidgets.QTableWidgetItem(table_content[row][col])
                item.setToolTip(str(table_content[row][col]))
                self.tableWidget.setItem(row,col,item)

        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch)
        
    def _table_filter(self, filter_text:str):
        for i in range(self.tableWidget.rowCount()):
            for j in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(i, j)
                match = filter_text.lower() not in item.text().lower()
                self.tableWidget.setRowHidden(i, match)
                if not match:
                    break
    
    def _table_select_all(self):
        self.tableWidget.selectAll()

    def _table_deselect_all(self):
        self.tableWidget.clearSelection()

    def _handle_add_layers(self):
        the_items = self.tableWidget.selectedItems()
        # Get dataset name
        _the_selected_datasets=[]
        for item in the_items:            
            if item.column() == 0:
                _the_selected_datasets.append(item.text())
        the_str = ",".join(_the_selected_datasets)
        #msgbox = QtWidgets.QMessageBox.information(self, "Infomration",
        #                                           the_str)
        # Create layers
        for the_ds in _the_selected_datasets:
            self._add_dataset_as_layer_to_qgis(the_ds)
    
    def _add_dataset_as_layer_to_qgis(self,dataset_name:str):
        gdal.DontUseExceptions()
        _the_ds = gdal.Open(dataset_name,gdal.GA_ReadOnly)
        _the_info = gdal.Info(_the_ds, format="json",
                                deserialize=True, computeMinMax=True,
                                reportHistograms=False, reportProj4=True,
                                stats=False, approxStats=False,
                                computeChecksum=False, showGCPs=True,
                                showMetadata=True, showRAT=False,
                                showColorTable=False, listMDD=False,
                                showFileList=True)
        # msgbox = QtWidgets.QMessageBox.information(self,"Information", json.dumps(_the_info))
        _the_file = _the_info["files"][0]
        _the_filename = os.path.basename(_the_file)
        _the_dataset_name = dataset_name.replace(_the_file,"")
        _the_dataset_names = _the_dataset_name.split(':')
        if len(_the_dataset_names) == 3:
            _the_ds_name = _the_dataset_names[-1]
            _the_layer_name = f"{_the_filename}.{_the_ds_name}"
        else:
            _the_layer_name = _the_filename
        the_version = gdal.VersionInfo()
        # IGNORE_XY_AXIS_NAME_CHECKS=[YES/NOA]: (GDAL >= 3.4.0) 
        if (not (int(the_version) < int('3040000')) and
            _the_ds.GetGeoTransform() != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0)):
            rlayer = self.iface.addRasterLayer(dataset_name,_the_layer_name, "gdal")
            if rlayer.isValid():
                msgbox = QtWidgets.QMessageBox.information(
                    self,"information",
                    "Layer added using regular Raster reader with parsed GeoTransform info. "
                    "If incorrect, projection may have to be re-assigned with correct one in WKT.")
            else:
                msgbox = QtWidgets.QmessageBox.warnning(self,"warning", "Falied to add the layer.")
        else:
            the_vrt_dataset = self._create_dataset_vrt_geotransform(
                dataset_name, _the_file,_the_ds,_the_info)
            if the_vrt_dataset:
                rlayer = self.iface.addRasterLayer(the_vrt_dataset,_the_layer_name, "gdal")
            else:
                rlayer = self.iface.addRasterLayer(dataset_name,_the_layer_name, "gdal")
    
    def _create_dataset_vrt_geotransform(self,
                                         dataset_name,
                                         filename,
                                         dataset, dataset_info)->str:
        if 'GEOLOCATION' in dataset_info['metadata']:
            return self._create_dataset_vrt_geotransform_with_geolocation(
                dataset_name=dataset_name,
                filename=filename,dataset=dataset,
                dataset_info=dataset_info)
        # try form the vrt from bounding info
        the_ret = self._create_dataset_vrt_geotransform_with_boundings(
                dataset_name=dataset_name,
                filename=filename,dataset=dataset,
                dataset_info=dataset_info)
        if the_ret:
            return the_ret
        msgbox = QtWidgets.QMessageBox.warning(
            self,"Warning",
            "Unable to calculate GeoTransform from data: <br/>"
            "Failed after trying the following -<br/>"
            "<ol><li> 'GEOLOCATION' recognized by gdal</li>"
            "<li> Looking for the following example tags -"
            "<ul><li>Registration=CENTER</li><li>LatitudeResolution=0.25</li>"
            "<li>LongitudeResolution=0.25;</li><li>NorthBoundingCoordinate=90;</li>"
            "<li>SouthBoundingCoordinate=-90;</li><li>EastBoundingCoordinate=180;</li>"
            "<li>WestBoundingCoordinate=-180;</li><li>Origin=SOUTHWEST;</li></ul>"
            "</li>"
            "</ol")
        return None

    def _create_dataset_vrt_geotransform_with_boundings(
            self,
            dataset_name,
            filename,
            dataset, dataset_info)->str:
        """
            Try to get GeoTransform from the following tags:
            FROM: gdalinfo - ['metadata']['']['Grid_GridHeader']
            EXPECT: 
                'BinMethod=ARITHMETIC_MEAN;\nRegistration=CENTER;\nLatitudeResolution=0.25;\nLongitudeResolution=0.25;\nNorthBoundingCoordinate=90;\nSouthBoundingCoordinate=-90;\nEastBoundingCoordinate=180;\nWestBoundingCoordinate=-180;\nOrigin=SOUTHWEST;\n'
        """
        if 'Grid_GridHeader' not in dataset_info['metadata']['']:
            return None
        
        _the_grid_header = dataset_info['metadata']['']['Grid_GridHeader']
        _the_headers = _the_grid_header.split(";\n")
        _the_header_dict = self._convert_properties_to_dict(_the_headers)
        if "latituderesolution" not in _the_header_dict:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"warning", "LatitudeResolution: Not found.")
            return None
        _the_lat_res = float(_the_header_dict["latituderesolution"])
        if "longituderesolution" not in _the_header_dict:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"warning", "LongitudeResolution: Not found.")
            return None
        _the_lon_res = float(_the_header_dict["longituderesolution"])
        if "southboundingcoordinate" not in _the_header_dict:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"warning", "SouthBoundingCoordinate: Not found.")
            return None
        _the_lat_0 = float(_the_header_dict["southboundingcoordinate"])
        if "northboundingcoordinate" not in _the_header_dict:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"warning", "NorthBoundingCoordinate: Not found.")
            return None
        _the_lat_1 = float(_the_header_dict["northboundingcoordinate"])
        if "eastboundingcoordinate" not in _the_header_dict:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"warning", "EastBoundingCoordinate: Not found.")
            return None
        _the_lon_1 = float(_the_header_dict["eastboundingcoordinate"])
        if "westboundingcoordinate" not in _the_header_dict:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"warning", "WestBoundingCoordinate: Not found.")
            return None
        _the_lon_0 = float(_the_header_dict["westboundingcoordinate"])
        if "origin" not in _the_header_dict:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"warning", "Origin: Not found.")
            return None
        _the_origin = _the_header_dict["origin"].upper()
        if "registration" in _the_header_dict:
            _the_registration = _the_header_dict["registration"]
        else:
            _the_registration = "CENTER"

        if "SOUTH" in _the_origin:
            _the_y_0 = _the_lat_0
            _the_y_n = _the_lat_1
        else:
            _the_y_0 = _the_lat_1
            _the_y_n = _the_lat_0

        if "WEST" in _the_origin:
            _the_x_0 = _the_lon_0
            _the_x_n = _the_lon_1
        else:
            _the_x_0 = _the_lon_1
            _the_x_n = _the_lon_0


        # assuming lat/lon for now - will implement the testing
        _the_coord_order_reverse = True # mapping (2,1)

        _the_x_resolution = _the_lon_res
        _the_y_resolution = _the_lat_res

        if _the_coord_order_reverse:
            _the_geotransform_array= [
            _the_x_0,0.0, _the_x_resolution,
            _the_y_0,_the_y_resolution,0.0]
        else:
            _the_geotransform_array = [
                _the_x_0,_the_x_resolution,0.0,
                _the_y_n,0.0,-_the_y_resolution]
        
        _the_raster_x_size = dataset.RasterXSize
        _the_raster_y_size = dataset.RasterYSize

        if _the_coord_order_reverse:
            _axis_map_data_to_srs = "2,1"
        else:
            _axis_map_data_to_srs = "1,2"
        # assuming EPSG:4326
        _srs_projection = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST],AUTHORITY["EPSG","4326"]]'

        #Create the vrt
        _the_doc = ET.Element("VRTDataset")
        _the_doc.set("rasterXSize",str(_the_raster_x_size))
        _the_doc.set("rasterYSize",str(_the_raster_y_size))
        _the_child = ET.SubElement(_the_doc,"GeoTransform")
        _the_child.text = ','.join(map(str,_the_geotransform_array))
        _the_child = ET.SubElement(_the_doc,"SRS")
        _the_child.set("dataAxisToSRSAxisMapping", _axis_map_data_to_srs)
        _the_child.text = _srs_projection
        _the_meta = ET.SubElement(_the_doc,"Metadata")
        _the_info_meta = dataset_info['metadata']['']
        for k in _the_info_meta:
            _the_child = ET.SubElement(_the_meta, "MDI")
            _the_child.set("key", k)
            _the_child.text = _the_info_meta[k]
        # GEOLOCATION section needs to be created
        _the_meta = ET.SubElement(_the_doc,"Metadata")
        _the_meta.set("domain", "GEOLOCATION")
        # registration
        _the_child = ET.SubElement(_the_meta, "MDI")
        _the_child.set("key", "Registration")
        _the_child.text = _the_registration
        # LatitudeResolution
        _the_child = ET.SubElement(_the_meta, "MDI")
        _the_child.set("key", "LatitudeResolution")
        _the_child.text = str(_the_lat_res)
        # LongitudeResolution
        _the_child = ET.SubElement(_the_meta, "MDI")
        _the_child.set("key", "LongitudeResolution")
        _the_child.text = str(_the_lon_res)
        # NorthBoundingCoordinate
        _the_child = ET.SubElement(_the_meta, "MDI")
        _the_child.set("key", "NorthBoundingCoordinate")
        _the_child.text = str(_the_lat_1)
        # SouthBoundingCoordinate
        _the_child = ET.SubElement(_the_meta, "MDI")
        _the_child.set("key", "SouthBoundingCoordinate")
        _the_child.text = str(_the_lat_0)
        # EastBoundingCoordinate
        _the_child = ET.SubElement(_the_meta, "MDI")
        _the_child.set("key", "EastBoundingCoordinate")
        _the_child.text = str(_the_lon_1)
        # WestBoundingCoordinate
        _the_child = ET.SubElement(_the_meta, "MDI")
        _the_child.set("key", "WestBoundingCoordinate")
        _the_child.text = str(_the_lon_0)
        # Origin
        _the_child = ET.SubElement(_the_meta, "MDI")
        _the_child.set("key", "Origin")
        _the_child.text = _the_origin
        # SRS
        _the_child = ET.SubElement(_the_meta, "MDI")
        _the_child.set("key", "SRS")
        _the_child.text = _srs_projection
        
        for b in dataset_info['bands']:
            _the_band = ET.SubElement(_the_doc,"VRTRasterBand")
            _the_band.set("dataType",b['type'])
            _the_band.set("band",str(b['band']))
            _the_band.set("blockXSize",str(b["block"][0]))
            _the_band.set("blockYSize",str(b["block"][1]))
            _the_meta = ET.SubElement(_the_band,"Metadata")
            _the_info_meta = b['metadata']['']
            for k in _the_info_meta:
                _the_child = ET.SubElement(_the_meta, "MDI")
                _the_child.set("key", k)
                _the_child.text = _the_info_meta[k]
            if 'noDataValue' in b:
                _the_child = ET.SubElement(_the_band,"NoDataValue")
                _the_child.text = str(b['noDataValue'])
            if 'unit' in b:
                _the_child = ET.SubElement(_the_band,"UnitType")
                _the_child.text = b['unit']
            _the_source =  ET.SubElement(_the_band,"SimpleSource")
            _the_child = ET.SubElement(_the_source,"SourceFilename")
            _the_child.set("relativeToVRT", str(b['band']))
            _the_child.text = dataset_name
            _the_child = ET.SubElement(_the_source,"SourceBand")
            _the_child.text = str(b['band'])
            _the_child = ET.SubElement(_the_source,"SourceProperties")
            _the_child.set("RasterXSize", str(_the_raster_x_size))
            _the_child.set("RasterYSize", str(_the_raster_y_size))
            _the_child.set("DataType",b['type'])
            _the_child.set("blockXSize",str(b["block"][0]))
            _the_child.set("blockYSize",str(b["block"][1]))
            _the_child = ET.SubElement(_the_source,"SrcRect")
            _the_child.set("xOff", str(0))
            _the_child.set("yOff", str(0))
            _the_child.set("xSize", str(_the_raster_x_size))
            _the_child.set("ySize", str(_the_raster_y_size))
            _the_child = ET.SubElement(_the_source,"DstRect")
            _the_child.set("xOff", str(0))
            _the_child.set("yOff", str(0))
            _the_child.set("xSize", str(_the_raster_x_size))
            _the_child.set("ySize", str(_the_raster_y_size))
        _the_tree = ET.ElementTree(_the_doc)
        _the_out_vrt_filename = self._form_variable_vrt_name(
            filename, dataset_name)
        #msgbox = QtWidgets.QMessageBox.information(
        #    self,"Information", _the_out_vrt_filename)
        _the_tree.write(_the_out_vrt_filename)

        return _the_out_vrt_filename


    def _convert_properties_to_dict(self,property_array:list[str])->dict:
        the_ret = dict()
        for the_prop in property_array:
            if '=' in the_prop:
                the_pair = the_prop.split('=',1)
                the_ret[the_pair[0].lower()]=the_pair[1]
        return the_ret
  
    def _create_dataset_vrt_geotransform_with_geolocation(self,
                                         dataset_name,
                                         filename,
                                         dataset, dataset_info)->str:
        _the_raster_x_size = dataset.RasterXSize
        _the_raster_y_size = dataset.RasterYSize
        if 'X_DATASET' not in dataset_info['metadata']['GEOLOCATION']:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"Warning",
                "Unable to process data: No X_DATASET in 'GEOLOCATION'"
                " identified.")
            return None
        _the_x_dataset_name = dataset_info['metadata']['GEOLOCATION']['X_DATASET']
        _the_x_varname = self._get_variable_name(
            filename,_the_x_dataset_name)
        if 'X_BAND' not in dataset_info['metadata']['GEOLOCATION']:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"Warning",
                "Unable to calculate GeoTransform from data: "
                "No X_BAND in 'GEOLOCATION' identified.")
            return None
        _the_x_band = dataset_info['metadata']['GEOLOCATION']['X_BAND']
        _the_x_size, _the_x_0, _the_x_n, _the_x_resolution = self._gdal_calc_transform(
            _the_x_dataset_name)
        if 'Y_DATASET' not in dataset_info['metadata']['GEOLOCATION']:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"Warning",
                "Unable to calculate GeoTransform from data: "
                " No Y_DATASET in 'GEOLOCATION' identified.")
            return None
        _the_y_dataset_name = dataset_info['metadata']['GEOLOCATION']['Y_DATASET']
        _the_y_varname = self._get_variable_name(
            filename,_the_y_dataset_name)
        if 'Y_BAND' not in dataset_info['metadata']['GEOLOCATION']:
            msgbox = QtWidgets.QMessageBox.warning(
                self,"Warning",
                "Unable to calculate GeoTransform from data: "
                "No Y_BAND in 'GEOLOCATION' identified.")
            return None
        _the_y_band = dataset_info['metadata']['GEOLOCATION']['Y_BAND']
        _the_y_size, _the_y_0, _the_y_n, _the_y_resolution = self._gdal_calc_transform(
            _the_y_dataset_name)

        # assuming lat/lon for now - will implement the testing
        _the_coord_order_reverse = True # mapping (2,1)

        if _the_coord_order_reverse:
            _the_geotransform_array= [
            _the_x_n,0.0, -_the_x_resolution,
            _the_y_0,_the_y_resolution,0.0]
        else:
            _the_geotransform_array = [
                _the_x_0,_the_x_resolution,0.0,
                _the_y_n,0.0,-_the_y_resolution]
        
        if _the_coord_order_reverse:
            _axis_map_data_to_srs = "2,1"
        else:
            _axis_map_data_to_srs = "1,2"
        # assuming EPSG:4326
        _srs_projection = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST],AUTHORITY["EPSG","4326"]]'


        #Create the vrt
        _the_doc = ET.Element("VRTDataset")
        _the_doc.set("rasterXSize",str(_the_raster_x_size))
        _the_doc.set("rasterYSize",str(_the_raster_y_size))
        _the_child = ET.SubElement(_the_doc,"GeoTransform")
        _the_child.text = ','.join(map(str,_the_geotransform_array))
        _the_child = ET.SubElement(_the_doc,"SRS")
        _the_child.set("dataAxisToSRSAxisMapping", _axis_map_data_to_srs)
        _the_child.text = _srs_projection
        _the_meta = ET.SubElement(_the_doc,"Metadata")
        _the_info_meta = dataset_info['metadata']['']
        for k in _the_info_meta:
            _the_child = ET.SubElement(_the_meta, "MDI")
            _the_child.set("key", k)
            _the_child.text = _the_info_meta[k]
        _the_meta = ET.SubElement(_the_doc,"Metadata")
        _the_meta.set("domain", "GEOLOCATION")
        _the_info_meta = dataset_info['metadata']['GEOLOCATION']
        for k in _the_info_meta:
            _the_child = ET.SubElement(_the_meta, "MDI")
            _the_child.set("key", k)
            _the_child.text = _the_info_meta[k]
        
        for b in dataset_info['bands']:
            _the_band = ET.SubElement(_the_doc,"VRTRasterBand")
            _the_band.set("dataType",b['type'])
            _the_band.set("band",str(b['band']))
            _the_band.set("blockXSize",str(b["block"][0]))
            _the_band.set("blockYSize",str(b["block"][1]))
            _the_meta = ET.SubElement(_the_band,"Metadata")
            _the_info_meta = b['metadata']['']
            for k in _the_info_meta:
                _the_child = ET.SubElement(_the_meta, "MDI")
                _the_child.set("key", k)
                _the_child.text = _the_info_meta[k]
            if 'noDataValue' in b:
                _the_child = ET.SubElement(_the_band,"NoDataValue")
                _the_child.text = str(b['noDataValue'])
            if 'unit' in b:
                _the_child = ET.SubElement(_the_band,"UnitType")
                _the_child.text = b['unit']
            _the_source =  ET.SubElement(_the_band,"SimpleSource")
            _the_child = ET.SubElement(_the_source,"SourceFilename")
            _the_child.set("relativeToVRT", str(b['band']))
            _the_child.text = dataset_name
            _the_child = ET.SubElement(_the_source,"SourceBand")
            _the_child.text = str(b['band'])
            _the_child = ET.SubElement(_the_source,"SourceProperties")
            _the_child.set("RasterXSize", str(_the_raster_x_size))
            _the_child.set("RasterYSize", str(_the_raster_y_size))
            _the_child.set("DataType",b['type'])
            _the_child.set("blockXSize",str(b["block"][0]))
            _the_child.set("blockYSize",str(b["block"][1]))
            _the_child = ET.SubElement(_the_source,"SrcRect")
            _the_child.set("xOff", str(0))
            _the_child.set("yOff", str(0))
            _the_child.set("xSize", str(_the_raster_x_size))
            _the_child.set("ySize", str(_the_raster_y_size))
            _the_child = ET.SubElement(_the_source,"DstRect")
            _the_child.set("xOff", str(0))
            _the_child.set("yOff", str(0))
            _the_child.set("xSize", str(_the_raster_x_size))
            _the_child.set("ySize", str(_the_raster_y_size))
        _the_tree = ET.ElementTree(_the_doc)
        _the_out_vrt_filename = self._form_variable_vrt_name(
            filename, dataset_name)
        #msgbox = QtWidgets.QMessageBox.information(
        #    self,"Information", _the_out_vrt_filename)
        _the_tree.write(_the_out_vrt_filename)
        return _the_out_vrt_filename


    def _get_variable_name(self, filename, dataset_name)->str:
        _the_dataset_name = dataset_name.replace(filename,"")
        _the_dataset_names = _the_dataset_name.split(':')
        if len(_the_dataset_names) == 3:
            _the_var_name = _the_dataset_names[-1]
            _the_vars = _the_var_name.split("/")
            _the_ret = _the_vars[-1]
            return _the_ret
        return None

    def _form_variable_vrt_name(self, filename, dataset_name)->str:
        _the_dataset_name = dataset_name.replace(filename,"")
        _the_dataset_names = _the_dataset_name.split(':')
        if len(_the_dataset_names) == 3:
            _the_var_name = _the_dataset_names[-1]
            _the_var_name = _the_var_name.replace("/",".")
            the_ret_filename = f"{filename}.{_the_var_name}.vrt"
        else:
            the_ret_filename = f"{filename}.vrt"
        return the_ret_filename

    def _gdal_calc_transform(self, axis_datasetname, pixel_is_area=False):
        _the_ds = gdal.Open(axis_datasetname,gdal.GA_ReadOnly)
        _axis_size = _the_ds.RasterXSize
        _the_array = _the_ds.GetRasterBand(1).ReadAsArray()
        _the_axis_array = _the_array[0]
        _axis_resolution = self.calc_mean_step_size(_the_axis_array)
        # assuming pixel-as-point
        if not pixel_is_area:
            _axis_0 = _the_axis_array[0] - _axis_resolution/2
            _axis_n = _the_axis_array[-1] + _axis_resolution/2
        else:
            _axis_0 = _the_axis_array[0]
            _axis_n = _the_axis_array[-1]
        #verify the step-size
        #if self.verify_equal_intervals(_the_axis_array):
        return _axis_size, _axis_0, _axis_n, _axis_resolution
    

    def _gdal_get_band_dim(self,dataset_info)->str:
        the_coord_key = [k for k in dataset_info['metadata'][''] if k.endswith('coordinates')]
        the_coord_dim = dataset_info['metadata'][''][the_coord_key[0]]

    def calc_mean_step_size(self, arr:list):
        step_sizes = [arr[i+1] - arr[i] for i in range(len(arr)-1)]
        mean_step_size = sum(step_sizes)/len(step_sizes)
        return mean_step_size

    def verify_equal_intervals(self, arr, tolerance=1e-9):
        step_sizes = [arr[i+1] - arr[i] for i in range(len(arr)-1)]
        mean_step_size = sum(step_sizes)/len(step_sizes)
        return all(math.isclose(step_sizes[i], mean_step_size,
                            rel_tol=tolerance, abs_tol=tolerance) for i in range(
                                len(step_sizes)))

