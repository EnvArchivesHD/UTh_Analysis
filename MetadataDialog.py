import os

from PyQt5.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QWidget, QGridLayout, \
    QTableView, QHeaderView, QFileIconProvider, QHBoxLayout, QMessageBox
from PyQt5 import QtGui
from MetadataFrameModel import MetadataFrameModel

import json
import pandas as pd


class MetadataDialog(QDialog):

    def __init__(self, analysisTab, folderPath=None, filePath=None):
        super(MetadataDialog, self).__init__()

        self.analysisTab = analysisTab

        self.folderPath = folderPath
        self.filePath = filePath
        self.currentData = self.getDataFromPath(filePath)

        self.setWindowTitle('Create Metadata File')
        self.initUI()

        self.setLayout(self.tableLayout)

    def initUI(self):
        directoryLabel = QLabel('Data directory')
        self.directoryEdit = QLineEdit()
        if self.folderPath is not None:
            self.directoryEdit.setText(self.folderPath)
        directoryLabel.setBuddy(self.directoryEdit)
        self.dirButton = QPushButton()
        self.dirButton.setIcon(QFileIconProvider().icon(QFileIconProvider.Folder))
        self.dirButton.clicked.connect(self.getDir)

        self.addRowButton = QPushButton('New row')
        self.addRowButton.clicked.connect(self.addRow)

        hBoxLayout = QHBoxLayout()
        hBoxLayout.addWidget(directoryLabel)
        hBoxLayout.addWidget(self.directoryEdit)
        hBoxLayout.addWidget(self.dirButton)
        hBoxWidget = QWidget()
        hBoxWidget.setLayout(hBoxLayout)

        self.saveButton = QPushButton('Save')
        self.saveButton.clicked.connect(self.save)

        if self.currentData is not None:
            metadataFrame = self.currentData
        else:
            metadataFrame = pd.DataFrame({
                'Lab. #': '',
                'Bezeich.': '',
                'Art der Probe': '',
                'Mess. Dat.': '',
                'Tiefe (cm)': '',
                'Einwaage (g)': '',
                'TriSp13 (g)': ''
            }, index=[])
        self.dataModel = MetadataFrameModel(metadataFrame)

        self.table = QTableView()
        self.table.setModel(self.dataModel)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.table.setMinimumSize(800, self.table.minimumHeight())

        self.tableLayout = QGridLayout()
        self.tableLayout.addWidget(hBoxWidget, 0, 0)
        self.tableLayout.addWidget(self.addRowButton, 1, 0)
        self.tableLayout.addWidget(self.table, 2, 0)
        self.tableLayout.addWidget(self.saveButton, 3, 0)

    def getDataFromPath(self, path):
        if path is None or not os.path.isfile(path) or not path.endswith('.csv'):
            return None
        return pd.read_csv(path, sep=';', na_filter=False)

    def getDir(self):
        path = str(QFileDialog.getExistingDirectory(self, 'Select data directory'))
        if not os.path.isdir(path):
            return

        self.folderPath = os.path.normpath(path)
        self.filePath = None
        self.directoryEdit.setText(self.folderPath)

    def addRow(self):
        self.dataModel.insertRows(1, 1)

    def save(self):
        if not os.path.isdir(self.directoryEdit.text()):
            QMessageBox.critical(self, 'Not valid', 'Please select a valid directory.', QMessageBox.Ok)
            return
        if self.filePath is not None:
            path = self.filePath
        else:
            path = os.path.normpath(os.path.join(self.directoryEdit.text(), 'Metadata.csv'))

        self.dataModel.getData().to_csv(path, sep=';', index=False)

        self.analysisTab.metadataFileEdit.setText(path)

        self.close()
