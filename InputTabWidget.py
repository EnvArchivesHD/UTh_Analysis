import json

from PyQt5.QtWidgets import QWidget, QGridLayout, QGroupBox, QLineEdit, QLabel, QPushButton, QFileIconProvider, \
    QMessageBox, QSlider, \
    QTableWidget, QTableWidgetItem, QHeaderView, QListWidget, QListWidgetItem, QFileDialog, QHBoxLayout, QCheckBox, \
    QTableView, QStyle
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from pyqtgraph import QtGui
from PyQt5 import QtWidgets
import os
from ConstantsDialog import ConstantsDialog
import DataFolderUtil
import numpy as np
import MathUtil
from DataFrameModel import DataFrameModel
import pandas as pd
import Util
from DetectorLayoutDialog import DetectorLayoutDialog
import Globals
from DetectorLayoutDialogOld import DetectorLayoutDialogOld
import resources
from OutputSettingsDialog import OutputSettingsDialog


class InputTabWidget(QWidget):

    def __init__(self, window, ratioBuilder):
        super(InputTabWidget, self).__init__()
        self.window = window

        self.ratioBuilder = ratioBuilder

        self.initSettingsBox()
        self.initOverviewBox()
        self.initRatiosBox()

        self.runListeners = []

        layout = QGridLayout()
        layout.addWidget(self.settingsBox, 0, 0)
        layout.addWidget(self.overviewBox, 1, 0)
        layout.addWidget(self.ratiosBox, 2, 0)

        self.setLayout(layout)


    ''' +-----------------------------+ '''
    ''' |       Settings-Code         | '''
    ''' +-----------------------------+ '''

    def initSettingsBox(self):
        self.settingsBox = QGroupBox("Settings")
        self.settingsBox.setMaximumHeight(400)

        # Specific constants section
        constantsWidget = QWidget()
        constantsHLayout = QHBoxLayout()
        self.constantsFileEdit = QLineEdit()
        self.constantsFileEdit.setText(self.window.settings[Globals.DEFAULT_CONSTANTS_KEY])
        self.constantsFileEdit.textChanged.connect(self.updateSettings)
        self.constantsFileEdit.setEnabled(False)
        self.newConstantsButton = QPushButton('New')
        self.editConstantsButton = QPushButton('Edit')
        self.loadConstantsButton = QPushButton('Load')
        self.newConstantsButton.clicked.connect(self.newConstants)
        self.editConstantsButton.clicked.connect(self.editConstants)
        self.loadConstantsButton.clicked.connect(self.loadConstants)

        constantsHLayout.addWidget(QLabel('Constants'))
        constantsHLayout.addWidget(self.constantsFileEdit)
        constantsHLayout.addWidget(self.newConstantsButton)
        constantsHLayout.addWidget(self.loadConstantsButton)
        constantsHLayout.addWidget(self.editConstantsButton)
        constantsWidget.setLayout(constantsHLayout)

        # Detector layout section
        # detectorWidget = QWidget()
        # detectorHLayout = QHBoxLayout()
        # self.detectorFileEdit = QLineEdit()
        # self.detectorFileEdit.setText(self.window.settings[Globals.LAYOUT_KEY])
        # self.detectorFileEdit.setEnabled(False)
        # self.newLayoutButton = QPushButton('New')
        # self.editLayoutButton = QPushButton('Edit')
        # self.loadLayoutButton = QPushButton('Load')
        # self.newLayoutButton.clicked.connect(self.newDLayout)
        # self.newLayoutButton.clicked.connect(self.updateSettings)
        # self.editLayoutButton.clicked.connect(self.editLayout)
        # self.loadLayoutButton.clicked.connect(self.loadLayout)
        # self.editLayoutButton.clicked.connect(self.editConstants)
        # self.loadLayoutButton.clicked.connect(self.loadConstants)
        # self.defaultConstantsButton.clicked.connect(self.setConstantsAsDefault)
        # self.defaultConstantsButton.setEnabled(False)
        #
        # detectorHLayout.addWidget(QLabel('Detector layout:'))
        # detectorHLayout.addWidget(self.detectorFileEdit)
        # detectorHLayout.addWidget(self.newLayoutButton)
        # detectorHLayout.addWidget(self.loadLayoutButton)
        # detectorHLayout.addWidget(self.editLayoutButton)
        # detectorWidget.setLayout(detectorHLayout)

        # Directory label and edit widget
        dirHLayout = QHBoxLayout()
        self.dirNameEdit = QLineEdit()
        dirNameLabel = QLabel('&Directory path')
        dirNameLabel.setBuddy(self.dirNameEdit)
        # Directory button
        self.dirButton = QPushButton()
        self.dirButton.setIcon(QtGui.QIcon(":/icons/folder.png"))
        self.dirButton.clicked.connect(self.setDirectory)
        # Run button
        runButton = QPushButton('Run')
        runButton.clicked.connect(self.runEvent)
        dirHLayout.addWidget(dirNameLabel)
        dirHLayout.addWidget(self.dirNameEdit)
        dirHLayout.addWidget(self.dirButton)
        dirHLayout.addWidget(runButton)
        dirHLayoutWidget = QWidget()
        dirHLayoutWidget.setLayout(dirHLayout)

        # Save label and edit widget
        outputLayout = QHBoxLayout()
        self.outputDirNameEdit = QLineEdit()
        self.outputDirNameEdit.setText(self.window.settings[Globals.OUTPUT_KEY])
        self.outputDirNameEdit.textChanged.connect(self.updateSettings)
        self.outputDirNameEdit.setEnabled(False)
        outputDirNameLabel = QLabel('&Output path')
        outputDirNameLabel.setBuddy(self.outputDirNameEdit)
        self.outputDirButton = QPushButton()
        self.outputDirButton.setIcon(QtGui.QIcon(":/icons/folder.png"))
        self.outputDirButton.clicked.connect(self.setOutputDirectory)
        self.openOutputDirButton = QPushButton()
        self.openOutputDirButton.setIcon(QtGui.QIcon(":/icons/open_folder.png"))
        self.openOutputDirButton.clicked.connect(self.openOutputDirectory)
        self.statusOutputDir = QPushButton()
        self.statusOutputDir.setIcon(QtGui.QIcon(":/icons/cross.png"))
        self.statusOutputDir.clicked.connect(self.openStatusMessage)
        #self.statusOutputDir.setEnabled(False)
        self.settingsOutputDirButton = QPushButton()
        self.settingsOutputDirButton.setIcon(QtGui.QIcon(":/icons/settings.png"))
        self.settingsOutputDirButton.clicked.connect(self.openOutputSettings)
        outputLayout.addWidget(outputDirNameLabel)
        outputLayout.addWidget(self.outputDirNameEdit)
        outputLayout.addWidget(self.outputDirButton)
        outputLayout.addWidget(self.openOutputDirButton)
        outputLayout.addWidget(self.settingsOutputDirButton)
        outputLayout.addWidget(self.statusOutputDir)
        outputDirHLayoutWidget = QWidget()
        outputDirHLayoutWidget.setLayout(outputLayout)

        # Connect output status listeners
        self.dirNameEdit.textChanged.connect(self.checkOutputStatus)
        self.outputDirNameEdit.textChanged.connect(self.checkOutputStatus)

        # Custom constants label and table
        tablesLayout = QGridLayout()

        customTable = QTableWidget()
        customTable.setRowCount(3)
        customTable.setColumnCount(2)
        yieldUItem = QTableWidgetItem('Yield (U)')
        yieldUItem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        yieldUItem.setFlags(Qt.ItemIsEditable)
        yieldThItem = QTableWidgetItem('Yield (Th)')
        yieldThItem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        yieldThItem.setFlags(Qt.ItemIsEditable)
        gainItem = QTableWidgetItem('Gain (13 Ohm)')
        gainItem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        gainItem.setFlags(Qt.ItemIsEditable)
        customTable.setItem(0, 0, yieldUItem)
        customTable.setItem(1, 0, yieldThItem)
        customTable.setItem(2, 0, gainItem)
        customTable.setItem(0, 1, QTableWidgetItem('1'))
        customTable.setItem(1, 1, QTableWidgetItem('1'))
        customTable.setItem(2, 1, QTableWidgetItem('1'))
        customTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        customTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        customTable.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        customTable.horizontalHeader().setVisible(False)
        customTable.verticalHeader().setVisible(False)
        self.customTable = customTable

        font = QtGui.QFont()
        font.setPixelSize(12)

        tailShiftLabel = QLabel('Tailshift von 228.5 zu 227.5?')
        tailShiftLabel.setFont(font)
        tailShiftLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        blankLabel = QLabel('Blank abziehen?')
        blankLabel.setFont(font)
        blankLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tailShiftCheckBox = QCheckBox()
        self.blankCheckBox = QCheckBox()
        self.blankCheckBox.setChecked(True)

        customBox = QGroupBox('Custom constants')
        customLayout = QGridLayout()
        customLayout.setVerticalSpacing(15)
        customLayout.addWidget(customTable, 0, 0, 1, 2)
        customLayout.addWidget(blankLabel, 1, 0, 1, 1)
        customLayout.addWidget(tailShiftLabel, 2, 0, 1, 1)
        customLayout.addWidget(self.blankCheckBox, 1, 1, 1, 1)
        customLayout.addWidget(self.tailShiftCheckBox, 2, 1, 1, 1)
        customLayout.addItem(QtWidgets.QSpacerItem(0, 15, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum), 4, 1, 1, 1)
        customBox.setLayout(customLayout)

        # File stats overview
        filesBox = QGroupBox('File overview')

        dataFilesLabel = QLabel('Data files:')
        dataFilesLabel.setAlignment(Qt.AlignRight)
        blankFilesLabel = QLabel('Blank Files:')
        blankFilesLabel.setAlignment(Qt.AlignRight)
        yhasuFilesLabel = QLabel('Yhas_u Files:')
        yhasuFilesLabel.setAlignment(Qt.AlignRight)
        yhasthFilesLabel = QLabel('Yhas_th Files:')
        yhasthFilesLabel.setAlignment(Qt.AlignRight)
        hfFilesLabel = QLabel('Hf Files:')
        hfFilesLabel.setAlignment(Qt.AlignRight)

        self.dataFilesNumber = QLabel('0')
        self.hfFilesNumber = QLabel('0')
        self.yhas_uFilesNumber = QLabel('0')
        self.yhas_thFilesNumber = QLabel('0')
        self.blankFilesNumber = QLabel('0')

        self.filesList = QListWidget()
        self.filesList.addItem(QListWidgetItem('No files'))
        self.filesList.itemDoubleClicked.connect(lambda item: Util.openFileItem(self.get_path(), item))
        # self.filesList.setVerticalScrollBar(QScrollBar())
        # self.filesList.setHorizontalScrollBar(QScrollBar())

        filesLayout = QGridLayout()
        filesLayout.addWidget(dataFilesLabel, 0, 0)
        filesLayout.addWidget(blankFilesLabel, 1, 0)
        filesLayout.addWidget(yhasuFilesLabel, 2, 0)
        filesLayout.addWidget(yhasthFilesLabel, 3, 0)
        filesLayout.addWidget(hfFilesLabel, 4, 0)
        filesLayout.addWidget(self.dataFilesNumber, 0, 1)
        filesLayout.addWidget(self.blankFilesNumber, 1, 1)
        filesLayout.addWidget(self.yhas_uFilesNumber, 2, 1)
        filesLayout.addWidget(self.yhas_thFilesNumber, 3, 1)
        filesLayout.addWidget(self.hfFilesNumber, 4, 1)
        filesLayout.addWidget(self.filesList, 5, 0, 1, 2)
        filesBox.setLayout(filesLayout)

        # Set table layout
        tablesLayout.addWidget(customBox, 1, 0)
        tablesLayout.addWidget(filesBox, 1, 1)
        tablesLayoutWidget = QWidget()
        tablesLayoutWidget.setLayout(tablesLayout)

        # Set main settings layout
        layout = QGridLayout()
        layout.addWidget(dirHLayoutWidget, 0, 0, 1, 2)
        layout.addWidget(constantsWidget, 1, 0, 1, 2)
        layout.addWidget(outputDirHLayoutWidget, 2, 0)
        #layout.addWidget(detectorWidget, 2, 1)
        layout.addWidget(tablesLayoutWidget, 3, 0, 1, 2)

        self.settingsBox.setLayout(layout)

    # called when the 'Run' button is clicked
    def runEvent(self):
        path = self.dirNameEdit.text()
        if not os.path.isdir(path):
            QMessageBox.critical(self, 'Not valid', 'Please select a valid directory.', QMessageBox.Ok)
        elif not os.path.isfile(self.constantsFileEdit.text()) or not self.constantsFileEdit.text().endswith('.cfg'):
            QMessageBox.critical(self, 'Not valid', 'Please load the constants first.', QMessageBox.Ok)
        else:
            if (DataFolderUtil.willFilesBeMoved(path) and not DataFolderUtil.willFilesBeDeleted(path) and QMessageBox.question(
                    self, 'Run', 'This will move files in "{}". Are you sure you want to proceed?'.format(path),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No) == QMessageBox.Yes) \
                    or (not DataFolderUtil.willFilesBeMoved(path) and DataFolderUtil.willFilesBeDeleted(path) and QMessageBox.question(
                    self, 'Run', 'This will delete files in "{}". Are you sure you want to proceed?'.format(path),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No) == QMessageBox.Yes) \
                    or (DataFolderUtil.willFilesBeDeleted(path) and DataFolderUtil.willFilesBeMoved(path) and QMessageBox.question(
                    self, 'Run', 'This will move and delete files in "{}". Are you sure you want to proceed?'.format(path),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No) == QMessageBox.Yes) or (not DataFolderUtil.willFilesBeDeleted(path) and not DataFolderUtil.willFilesBeMoved(path)):

                self.window.calcRatios(path)
                self.addRatios()
                self.setFilesBox(path)
                if len(self.runListeners) > 0:
                    for listener in self.runListeners:
                        listener.notify()

    def addRunListener(self, listener):
        self.runListeners.append(listener)

    def get_path(self):
        return self.dirNameEdit.text()

    def setDirectory(self):
        path = str(QFileDialog.getExistingDirectory(self, 'Select data directory'))
        if not os.path.isdir(path):
            return

        if path != self.dirNameEdit.text():
            self.clear()
            self.dirNameEdit.setText(path)
            self.setFilesBox(path)

    def setOutputDirectory(self):
        path = str(QFileDialog.getExistingDirectory(self, 'Select output saving directory'))
        if not os.path.isdir(path):
            return

        self.outputDirNameEdit.setText(path)

    def openOutputDirectory(self):
        path = self.outputDirNameEdit.text()
        if not os.path.isdir(path):
            QMessageBox.critical(self, 'Not valid', 'Please select a valid directory.', QMessageBox.Ok)
            return
        os.startfile(path)

    def openOutputSettings(self):
        data_path = self.dirNameEdit.text()
        output_path = self.outputDirNameEdit.text()
        if not os.path.isdir(data_path):
            QMessageBox.critical(self, 'Not valid', 'Please select a valid data directory.', QMessageBox.Ok)
            return
        if not os.path.isdir(output_path):
            QMessageBox.critical(self, 'Not valid', 'Please select a valid output directory.', QMessageBox.Ok)
            return
        dialog = OutputSettingsDialog(data_path, output_path)
        if dialog.exec_():
            try:
                DataFolderUtil.tryCreateOutputFolder(data_path, output_path, dialog.outputDict)
                self.checkOutputStatus()
            except PermissionError:
                error_dialog = QtWidgets.QMessageBox()
                error_dialog.setIcon(QMessageBox.Critical)
                error_dialog.setWindowTitle('Permission error')
                error_dialog.setText(
                    'Could not save output settings. Please close all related files or folders.')
                error_dialog.exec_()

    def getDataOutputPath(self):
        outputPath = self.outputDirNameEdit.text()
        connectionsPath = os.path.join(outputPath, 'connections.json')
        if os.path.exists(connectionsPath):
            with open(connectionsPath, 'r') as file:
                connectionsDict = json.loads(file.read().replace('\n', ''))
                baseName = DataFolderUtil.baseName(self.dirNameEdit.text())
                if baseName in connectionsDict:
                    return os.path.join(outputPath, connectionsDict[baseName])
        return None

    def openStatusMessage(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        if self.checkOutputStatus():
            msg.setText("Die Output-Einstellungen sind richtig konfiguriert.")
        else:
            msg.setText("Die Output-Einstellungen sind nicht richtig konfiguriert.")
        msg.setWindowTitle("Status des Output-Ordners")
        msg.exec_()

    def checkOutputStatus(self):
        outputPath = self.outputDirNameEdit.text()
        connectionsPath = os.path.join(outputPath, 'connections.json')
        if os.path.exists(connectionsPath):
            with open(connectionsPath, 'r') as file:
                connectionsDict = json.loads(file.read().replace('\n', ''))
                baseName = DataFolderUtil.baseName(self.dirNameEdit.text())
                if baseName in connectionsDict:
                    self.statusOutputDir.setIcon(QtGui.QIcon(':icons/checkmark.png'))
                    return True
        self.statusOutputDir.setIcon(QtGui.QIcon(':icons/cross.png'))
        return False

    def updateSettings(self):
        self.window.settings[Globals.DEFAULT_CONSTANTS_KEY] = self.constantsFileEdit.text()
        self.window.settings[Globals.OUTPUT_KEY] = self.outputDirNameEdit.text()
        #self.window.settings[Globals.LAYOUT_KEY] = self.detectorFileEdit.text()

    def setFilesBox(self, path):
        self.filesList.clear()

        files = DataFolderUtil.getFiles(path)
        self.dataFilesNumber.setText(str(len(files['data'])))
        self.blankFilesNumber.setText(str(len(files['blank'])))
        self.yhas_uFilesNumber.setText(str(len(files['yhasu'])))
        self.yhas_thFilesNumber.setText(str(len(files['yhasth'])))
        self.hfFilesNumber.setText(str(len(files['hf'])))

        for file in files['data'] + files['blank'] + files['yhasu'] + files['yhasth'] + files['hf']:
            self.filesList.addItem(QListWidgetItem(file))

    def loadConstants(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Load constants", "",
                                                  "Config files (*.cfg)", options=options)
        if not os.path.isfile(fileName):
            return

        self.constantsFileEdit.setText(fileName)

    def newConstants(self):
        dialog = ConstantsDialog(self)
        dialog.exec_()

    def newDLayout(self):
        dialog = DetectorLayoutDialog(self)
        dialog.exec_()

    def newD2Layout(self):
        dialog = DetectorLayoutDialogOld(self)
        dialog.exec_()

    def loadLayout(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "Load layout", "",
                                                  "Layout files (*.layout)", options=options)
        if not os.path.isfile(fileName):
            return

        self.detectorFileEdit.setText(fileName)

    def editConstants(self):
        dialog = ConstantsDialog(self, self.constantsFileEdit.text())
        dialog.exec_()

    def editLayout(self):
        dialog = DetectorLayoutDialog(self, self.detectorFileEdit.text())
        dialog.exec_()

    def get_specific_constants(self):
        specific = {
            'Blank': self.blankCheckBox.isChecked(),
            'Yield_U': float(self.customTable.item(0, 1).text()),
            'Yield_Th': float(self.customTable.item(1, 1).text()),
            'Gain': float(self.customTable.item(2, 1).text()),
            'Tail shift': self.tailShiftCheckBox.isChecked()
        }
        return specific

    def get_constants_path(self):
        return self.constantsFileEdit.text()

    #def get_layout_path(self):
    #    return self.detectorFileEdit.text()

    ''' +-----------------------------+ '''
    ''' |       Overview-Code         | '''
    ''' +-----------------------------+ '''

    def initOverviewBox(self):
        self.overviewBox = QGroupBox("Overview")
        self.overviewBox.setMaximumHeight(350)

        # set graph below settings box
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        # pg.setConfigOption('leftButtonPan', False)

        # U Tailing Graph
        self.uTailGraph = pg.PlotWidget()

        self.uTailGraph.setTitle('Tailing U-238')
        self.uTailGraph.setXRange(228, 238)
        self.uTailGraph.setYRange(0, 400)
        self.uTailGraph.getPlotItem().showGrid(True, True, 0.1)
        self.uTailGraph.getPlotItem().showAxis('top')
        self.uTailGraph.getPlotItem().showAxis('right')
        self.uTailGraph.getPlotItem().getAxis('top').setHeight(0)
        self.uTailGraph.getPlotItem().getAxis('top').setTicks([])
        self.uTailGraph.getPlotItem().getAxis('right').setWidth(0)
        #self.uTailGraph.resize(50, 200)
        #self.uTailGraph.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.uTailGraph.setMaximumWidth(300)

        self.u_ySlider = QSlider(Qt.Vertical)
        self.u_ySlider.setValue(99)
        self.u_ySlider.setEnabled(False)
        self.u_ySlider.valueChanged[int].connect(self.setUGraphRange)
        self.u_ySlider.setMaximumHeight(300)

        # Th Tailing Graph
        self.thTailGraph = pg.PlotWidget()

        self.thTailGraph.setTitle('Tailing Th-232')
        self.thTailGraph.setXRange(228, 231.8)
        self.thTailGraph.setYRange(0, 400)
        self.thTailGraph.getPlotItem().showGrid(True, True, 0.1)
        self.thTailGraph.getPlotItem().showAxis('top')
        self.thTailGraph.getPlotItem().showAxis('right')
        self.thTailGraph.getPlotItem().getAxis('top').setHeight(0)
        self.thTailGraph.getPlotItem().getAxis('top').setTicks([])
        self.thTailGraph.getPlotItem().getAxis('right').setWidth(0)
        self.thTailGraph.setMaximumWidth(300)

        self.th_ySlider = QSlider(Qt.Vertical)
        self.th_ySlider.setValue(99)
        self.th_ySlider.setEnabled(False)
        self.th_ySlider.valueChanged[int].connect(self.setThGraphRange)
        self.th_ySlider.setMaximumHeight(300)

        #uTailTable
        self.uTailTable = QTableView()
        self.uTailTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.uTailTable.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.uTailTable.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        #uThTailTable
        self.thTailTable = QTableView()
        self.thTailTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.thTailTable.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.thTailTable.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        #hPlusTable
        self.factorsTable = QTableView()

        self.factorsTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.factorsTable.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.factorsTable.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        self.setEmptyOverviewTables()

        layout = QGridLayout()
        layout.addWidget(self.uTailGraph, 0, 0, 3, 1)
        layout.addWidget(self.u_ySlider, 0, 1, 3, 1)
        layout.addWidget(self.thTailGraph, 0, 2, 3, 1)
        layout.addWidget(self.th_ySlider, 0, 3, 3, 1)
        layout.addWidget(self.uTailTable, 0, 4)
        layout.addWidget(self.thTailTable, 1, 4)
        layout.addWidget(self.factorsTable, 2, 4)
        #layout.addItem(QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding), 0, 5, 3, 1)

        self.overviewBox.setLayout(layout)

    def setEmptyOverviewTables(self):
        emptyUTailFrame = pd.DataFrame(
            {'229': '', '230': '', '230': '', '231': '', '232': '', '233': '', '234': '', '235': '', '236': '',
             '237': ''},
            index=['Tailing U SEM', 'Tailing U Cup'])
        self.uTailTable.setModel(DataFrameModel(emptyUTailFrame))
        emptyThTailFrame = pd.DataFrame({'229': '', '230': ''}, index=['Tailing Th SEM', 'Tailing Th Cup'])
        self.thTailTable.setModel(DataFrameModel(emptyThTailFrame))
        emptyFactorsFrame = pd.DataFrame({'UH+': '', 'ThH+': ''},
                                         index=['Factors'])
        self.factorsTable.setModel(DataFrameModel(emptyFactorsFrame))

    def setUGraphRange(self, value):
        norm_value = value/100/0.99
        self.uTailGraph.setYRange(0, MathUtil.interp(100, np.max(self.interp_u_tail), norm_value))

    def setThGraphRange(self, value):
        norm_value = value / 100 / 0.99
        self.thTailGraph.setYRange(0, MathUtil.interp(100, np.max(self.interp_th_tail), norm_value))

    def addRatios(self):
        self.addRatiosToTable(self.ratioBuilder.ratios.copy())
        self.fillTailingTables()

        self.plot()
        self.u_ySlider.setEnabled(True)
        self.th_ySlider.setEnabled(True)
        self.setUGraphRange(self.u_ySlider.value())
        self.setThGraphRange(self.th_ySlider.value())

    def plot(self):
        self.uTailGraph.clear()
        self.thTailGraph.clear()

        # Plot U-238 Tailing
        xnew = np.linspace(228.5, 237.5, num=200)
        x_axis_tail_u = self.ratioBuilder.x_axis_tail_u
        aatsu = self.ratioBuilder.aatsu
        f_u238 = self.ratioBuilder.f_u238
        self.interp_u_tail = f_u238(xnew)
        self.uTailGraph.plot(xnew, self.interp_u_tail, pen=pg.mkPen(color=(150,150,150), style=Qt.DashLine))
        self.uTailGraph.plot(x_axis_tail_u, aatsu, symbol='o', pen=None)

        # Plot U-232 Tailing
        xnew = np.linspace(228, 231.8, num=200)
        x_axis_tail_th = self.ratioBuilder.x_axis_tail_th
        aats = self.ratioBuilder.aats
        g_th232 = self.ratioBuilder.g_th232
        self.interp_th_tail = g_th232(xnew)
        self.thTailGraph.plot(xnew, self.interp_th_tail, pen=pg.mkPen(color=(150, 150, 150), style=Qt.DashLine))
        self.thTailGraph.plot(x_axis_tail_th, aats, symbol='o', pen=None)

    def fillTailingTables(self):
        self.uTailTable.setModel(DataFrameModel(self.ratioBuilder.uTailData))
        self.uTailTable.resizeColumnsToContents()

        self.thTailTable.setModel(DataFrameModel(self.ratioBuilder.thTailData))
        self.thTailTable.resizeColumnsToContents()

        factorsData = pd.DataFrame({'UhH+': self.ratioBuilder.UH_plus, 'ThH+': self.ratioBuilder.ThH_plus}, index=['Factors'])
        self.factorsTable.setModel(DataFrameModel(factorsData))
        self.factorsTable.resizeColumnsToContents()

    ''' +-----------------------------+ '''
    ''' |        Ratios-Code          | '''
    ''' +-----------------------------+ '''

    def initRatiosBox(self):
        self.ratiosBox = QGroupBox('Ratios')

        self.ratiosTable = QTableView()
        self.ratiosTable.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.ratiosTable.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        layout = QGridLayout()
        layout.addWidget(self.ratiosTable)

        self.ratiosBox.setLayout(layout)

    def addRatiosToTable(self, ratios):
        model = DataFrameModel(ratios, DataFolderUtil.findStandardNumber(self.dirNameEdit.text()))
        self.ratiosTable.setModel(model)
        self.ratiosTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def clear(self):
        self.ratioBuilder.ratios = None
        self.filesList.clear()
        self.uTailGraph.clear()
        self.thTailGraph.clear()
        self.u_ySlider.setEnabled(False)
        self.th_ySlider.setEnabled(False)
        self.u_ySlider.setValue(100)
        self.th_ySlider.setValue(100)
        self.ratiosTable.setModel(None)
        self.setEmptyOverviewTables()