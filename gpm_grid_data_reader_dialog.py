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

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from .gpm_grid_data_reader_dialog_add_layer import GPMGridRasterReaderDialogAddLayer

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gpm_grid_data_reader_dialog_base.ui'))


class GPMGridRasterReaderDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None):
        """Constructor."""
        super(GPMGridRasterReaderDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface=iface
        self.setupUi(self)
        self.toolButton.clicked.connect(self.select_file)
        #self.button_box.apply.connect(self.apply)
        #self.button_box.accepted.connect(self.apply)
        self.button_box.clicked.connect(self.handle_button_click)
        self.button_box.button(QtWidgets.QDialogButtonBox.Apply).setText("Add")
        self.lineEdit.textChanged.connect(self.handle_input_changed)
        self._gdal_set_netcdf_options()
        self.display_options_off()
    
    def select_file(self):
        qfd = QtWidgets.QFileDialog()
        # file_type = self.plugin.tr("Data file")
        file_type = self.tr("Data file(*)")
        file_title = self.tr("Select an input file")
        file_start_dir = "."
        f, _ = QtWidgets.QFileDialog.getOpenFileName(qfd, file_title, file_start_dir, file_type)
        self.lineEdit.setText(f)
        # msgbox = QtWidgets.QMessageBox.warning(self, "Warning0", "Please add a report !")

    def handle_input_changed(self):
        the_text = self.lineEdit.text()
        self.display_options(the_text)
    
    def display_options(self, filename:str):
        self.display_options_off()
        if not filename:
            return
        if filename.lower().startswith("netcdf:"):
            self.display_options_netcdf()
    
    def display_options_netcdf(self):
        self.groupBox.show()

    def display_options_off(self):
        self.groupBox.hide()

    def handle_button_click(self, button):
        role = self.button_box.buttonRole(button)
        if role == QtWidgets.QDialogButtonBox.ApplyRole:
            self.handle_apply_role()

        #print("role=", role)
        #msgbox = QtWidgets.QMessageBox.warning(self, "Warning2", "Please add a report !"+str(role))
    
    def handle_apply_role(self):
        the_file = self.lineEdit.text()
        if the_file:
            the_variables = self._gdal_get_variables(the_file)
            the_header = ["Item", "Description"]
            self.dlg2 = GPMGridRasterReaderDialogAddLayer(
                self,iface=self.iface,table_content=the_variables, 
                table_header=the_header)
            #ph = self.dlg.parent().geometry().height()
            #px = self.dlg.parent().geometry().x()
            #py = self.dlg.parent().geometry().y()
            ph = self.geometry().height()
            pw = self.geometry().width()
            px = self.geometry().x()
            py = self.geometry().y()
            dw = self.dlg2.width()
            dh = self.dlg2.height()   
            #msgbox = QtWidgets.QMessageBox.information(self, "Infomration",
            #                                           f"ph={ph}, px={px},py={py},dw={dw},dh={dh}")
            self.dlg2.setGeometry( int(px+pw/2), int(py+ph/2), dw, dh )
            self.dlg2.show()
        #else:
        #    the_msg = self.tr("Input file is required.")
        #    the_title = self.tr("Error")
        #    msgbox = QtWidgets.QMessageBox.critical(self, the_title, the_msg)


    def _gdal_get_variables(self, dataset_name:str,options:list[str]=None)->list[tuple]:
        if options is not None and len(options) > 0:
            _the_ds = gdal.Open(dataset_name, gdal.GA_ReadOnly,open_options=options)
        else:
            _the_ds = gdal.Open(dataset_name,gdal.GA_ReadOnly)
        the_ret = list()
        if _the_ds.RasterCount > 0:
            _the_filename = _the_ds.GetFileList()[0]
            _the_driver_name = _the_ds.GetDriver().ShortName.upper()
            _the_name = _the_filename #f"{_the_driver_name}:\"{_the_filename}\""
            _the_description = _the_ds.GetDescription()
            the_ret.append((_the_name,_the_description))
        the_ret.extend(_the_ds.GetSubDatasets())
        return the_ret
        
    def _gdal_set_netcdf_options(self):
        gdal.UseExceptions()
        the_version = gdal.VersionInfo()
        # IGNORE_XY_AXIS_NAME_CHECKS=[YES/NOA]: (GDAL >= 3.4.2) 
        if int(the_version) < int('3040002'):
            self.label_3.hide()
            self.comboBox_2.hide()
        # VARIABLES_AS_BANDS=[YES/NO]: (GDAL >= 3.5)
        if int(the_version) < int('3050000'):
            self.label_4.hide()
            self.comboBox_3.hide()
        # ASSUME_LONGLAT=[YES/NO]: (GDAL >= 3.7) 
        if int(the_version) < int('3070000'):
            self.label_5.hide()
            self.comboBox_4.hide()
        # ASSUME_LONGLAT=[YES/NO]: (GDAL >= 3.8) 
        if int(the_version) < int('3080000'):
            self.label_6.hide()
            self.comboBox_5.hide()




