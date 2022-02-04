import os

from PyQt5 import QtGui
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, \
    QRadioButton, QCheckBox, QMessageBox, QFormLayout, QWidget, QPlainTextEdit, QComboBox
from PyQt5.QtGui import QPixmap, QIntValidator
from PyQt5.QtCore import Qt

import json

import DataFolderUtil
import Util


class OutputSettingsDialog(QDialog):

    def __init__(self, data_path, output_path):
        super(OutputSettingsDialog, self).__init__()

        self.setWindowTitle('Output')
        self.setWindowIcon(QtGui.QIcon(':/icons/settings.png'))
        self.data_path = data_path
        self.output_path = output_path

        self.outputDict = {}

        self.initUI()
        self.load()

    def initUI(self):
        self.nameEdit = QLineEdit()
        self.descriptionEdit = QPlainTextEdit()
        Util.setHeight(self.descriptionEdit, 4)

        #self.typeEdit = QLineEdit()
        self.typeBox = QComboBox()
        self.typeBox.addItem('Stalagmit')
        self.typeBox.addItem('Koralle')
        self.typeBox.addItem('Authigenes Karbonat')

        labNrRange = DataFolderUtil.getLabNrRange(self.data_path)

        self.minLabNrEdit = QLineEdit(str(labNrRange[0]))
        self.maxLabNrEdit = QLineEdit(str(labNrRange[1]))
        self.lonEdit = QLineEdit()
        self.latEdit = QLineEdit()

        minLabNrLayout = QHBoxLayout()
        minLabNrLayout.addWidget(QLabel('Erste Labornummer'))
        minLabNrLayout.addWidget(self.minLabNrEdit)
        firstLabNrWidget = QWidget()
        firstLabNrWidget.setLayout(minLabNrLayout)
        maxLabNrLayout = QHBoxLayout()
        maxLabNrLayout.addWidget(QLabel('Letzte Labornummer'))
        maxLabNrLayout.addWidget(self.maxLabNrEdit)
        lastLabNrWidget = QWidget()
        lastLabNrWidget.setLayout(maxLabNrLayout)

        lonLayout = QHBoxLayout()
        lonLayout.addWidget(QLabel('Längengrad'))
        lonLayout.addWidget(self.lonEdit)
        lonWidget = QWidget()
        lonWidget.setLayout(lonLayout)
        latLayout = QHBoxLayout()
        latLayout.addWidget(QLabel('Breitengrad'))
        latLayout.addWidget(self.latEdit)
        latWidget = QWidget()
        latWidget.setLayout(latLayout)

        layout = QFormLayout()
        layout.setLabelAlignment(Qt.AlignRight)

        layout.addRow(QLabel('Bezeichnung'), self.nameEdit)
        layout.addRow(QLabel('Art des Archivs'), self.typeBox)
        layout.addRow(firstLabNrWidget, lastLabNrWidget)
        layout.addRow(lonWidget, latWidget)
        layout.addRow(QLabel('Beschreibung'), self.descriptionEdit)

        saveButton = QPushButton('Save')
        saveButton.clicked.connect(self.save)
        layout.addRow(saveButton)

        self.setLayout(layout)

    def load(self):
        connectionsFilePath = os.path.join(self.output_path, 'connections.json')
        if os.path.exists(connectionsFilePath):
            with open(connectionsFilePath, 'r') as file:
                connectionsDict = json.loads(file.read().replace('\n', ''))
            dataBaseName = DataFolderUtil.baseName(self.data_path)
            if dataBaseName in connectionsDict:
                infoFilePath = os.path.join(os.path.join(self.output_path, connectionsDict[dataBaseName]), 'info.json')
                if os.path.exists(infoFilePath):
                    with open(infoFilePath, 'r') as file:
                        infoDict = json.loads(file.read().replace('\n', ''))
                    self.nameEdit.setText(infoDict['name'])
                    self.typeBox.setCurrentText(infoDict['type'])
                    self.minLabNrEdit.setText(infoDict['min_lab_nr'])
                    self.maxLabNrEdit.setText(infoDict['max_lab_nr'])
                    self.lonEdit.setText(infoDict['lon'])
                    self.latEdit.setText(infoDict['lat'])
                    self.descriptionEdit.setPlainText(infoDict['description'])

    def save(self):
        self.outputDict = {
            'name': self.nameEdit.text(),
            'type': self.typeBox.currentText(),
            'min_lab_nr': self.minLabNrEdit.text(),
            'max_lab_nr': self.maxLabNrEdit.text(),
            'lon': self.lonEdit.text(),
            'lat': self.latEdit.text(),
            'description': self.descriptionEdit.toPlainText()
        }

        if self.nameEdit.text() == '':
            QMessageBox.critical(self, 'Not valid', 'Please enter a name.', QMessageBox.Ok)
            return

        self.accept()