from PyQt5.QtWidgets import QGridLayout, QGroupBox, QLineEdit, QLabel, QPushButton, \
    QMessageBox, QHBoxLayout, QFileDialog, QTableView, QHeaderView, QCheckBox, QWidget, QListWidget, QListWidgetItem
from PyQt5 import QtGui
import os

import Util
from DataFrameModel import DataFrameModel
from MetadataDialog import MetadataDialog
import Globals


class AnalysisTabWidget(QWidget):
    NO_HISTORY_STRING = 'No metadata history'

    def __init__(self, window, ratioBuilder, analyzer):
        super(AnalysisTabWidget, self).__init__()
        self.window = window

        self.ratioBuilder = ratioBuilder
        self.analyzer = analyzer

        self.currentRatiosFolder = None

        self.initSettingsBox()
        self.initResultsBox()

        layout = QGridLayout()
        layout.addWidget(self.settingsBox, 0, 0)
        layout.addWidget(self.resultsBox, 1, 0)

        self.setLayout(layout)

    ''' +-----------------------------+ '''
    ''' |       Settings-Code         | '''
    ''' +-----------------------------+ '''

    def initSettingsBox(self):
        self.settingsBox = QGroupBox('Settings')
        # self.settingsBox.setMaximumHeight(400)

        # Metadata file row
        self.metadataFileEdit = QLineEdit()
        self.loadFileButton = QPushButton('Load')
        self.loadFileButton.clicked.connect(self.selectMetadataFile)
        self.createButton = QPushButton('Create')
        self.createButton.clicked.connect(self.createMetadata)
        self.editButton = QPushButton('Edit')
        self.editButton.clicked.connect(self.editMetadata)
        self.runAnalysisButton = QPushButton('Start Analysis')
        self.runAnalysisButton.clicked.connect(self.runEvent)
        # Reanalyze multiple Results files button
        self.multipleAnalysesButton = QPushButton()
        self.multipleAnalysesButton.setIcon(QtGui.QIcon(":/icons/excel.png"))
        self.multipleAnalysesButton.clicked.connect(self.runMultipleEvent)

        # Metadata history
        metadataHistoryBox = QGroupBox('Metadata History')
        metadataHistoryGrid = QGridLayout()

        self.filesList = QListWidget()
        self.filesList.itemClicked.connect(lambda item: self.setMetadataFile(item.text()))
        self.setFilesList()

        self.searchFilesButton = QPushButton('Search')
        self.searchFilesButton.clicked.connect(lambda: self.selectAndSearchFolderForMetadataFiles())
        self.clearFilesListButton = QPushButton('Clear')
        self.clearFilesListButton.clicked.connect(self.clearFilesList)

        metadataHistoryGrid.addWidget(self.searchFilesButton, 0, 0, 1, 1)
        metadataHistoryGrid.addWidget(self.clearFilesListButton, 1, 0, 1, 1)
        metadataHistoryGrid.addItem(QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 2, 0, 1, 1)
        metadataHistoryGrid.addWidget(self.filesList, 0, 1, 3, 1)
        metadataHistoryBox.setLayout(metadataHistoryGrid)

        topLayout = QHBoxLayout()
        topLayout.addWidget(QLabel('Metadata:'))
        topLayout.addWidget(self.metadataFileEdit)
        topLayout.addWidget(self.loadFileButton)
        topLayout.addWidget(self.createButton)
        topLayout.addWidget(self.editButton)
        topLayout.addWidget(self.runAnalysisButton)
        topLayout.addWidget(self.multipleAnalysesButton)
        topLayoutWidget = QWidget()
        topLayoutWidget.setLayout(topLayout)

        layout = QGridLayout()
        layout.addWidget(topLayoutWidget, 0, 0, 1, 1)
        layout.addWidget(metadataHistoryBox, 1, 0, 2, 1)

        self.settingsBox.setLayout(layout)

    def selectMetadataFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        path, _ = QFileDialog.getOpenFileName(self, 'Select metadata file', "",
                                              "Metadata/Wägeprotokolle (*.csv *.xlsx)", options=options)

        self.setMetadataFile(path)

    def setMetadataFile(self, filePath):
        if not os.path.isfile(filePath):
            return

        if filePath not in self.window.settings[Globals.METADATA_HISTORY_KEY]:
            self.window.settings.append(Globals.METADATA_HISTORY_KEY, filePath, position=0)
            self.setFilesList()
        self.metadataFileEdit.setText(filePath)

    def clearFilesList(self):
        self.window.settings[Globals.METADATA_HISTORY_KEY] = []
        self.setFilesList()

    def setFilesList(self):
        self.filesList.clear()
        if len(self.window.settings[Globals.METADATA_HISTORY_KEY]) == 0:
            self.filesList.addItem(QListWidgetItem(self.NO_HISTORY_STRING))
        else:
            for metadataPath in self.window.settings[Globals.METADATA_HISTORY_KEY]:
                self.filesList.addItem(QListWidgetItem(metadataPath))

    def selectAndSearchFolderForMetadataFiles(self, parent=None):
        if parent is None:
            path = str(QFileDialog.getExistingDirectory(self, 'Select directory you want to search'))
        else:
            path = parent
        if not os.path.isdir(path):
            return

        for entry in os.listdir(path):
            self.searchMetadataFile(path)
            self.selectAndSearchFolderForMetadataFiles(os.path.join(path, entry))
        self.metadataFileEdit.clear()

    def searchMetadataFile(self, path):
        self.currentRatiosFolder = path
        for entry in os.listdir(path):
            entrypath = os.path.join(path, entry)
            if os.path.isfile(entrypath) and entry.endswith('.csv'):
                self.setMetadataFile(os.path.normpath(entrypath))
                return
            elif os.path.isfile(entrypath) and entry.endswith('.xlsx') and 'Wägeprotokoll' in entry:
                self.setMetadataFile(os.path.normpath(entrypath))
                return

    def createMetadata(self):
        dialog = MetadataDialog(self, folderPath=self.currentRatiosFolder)
        dialog.exec_()

    def editMetadata(self):
        path = self.metadataFileEdit.text()
        if os.path.isfile(path) and path.endswith('.xlsx'):
            QMessageBox.critical(self, 'Not valid', 'Can only edit .csv metadata files.')
            return
        elif not os.path.isfile(path) or not path.endswith('.csv'):
            QMessageBox.critical(self, 'Not valid', 'Please select a valid metadata file (*.csv).',
                                 QMessageBox.Ok)
            return
        dialog = MetadataDialog(self, folderPath=self.currentRatiosFolder, filePath=path)
        dialog.exec_()

    def runEvent(self):
        path = self.metadataFileEdit.text()
        if not os.path.isfile(path) or (not path.endswith('.csv') and not path.endswith('.xlsx')):
            QMessageBox.critical(self, 'Not valid', 'Please select a valid metadata file (*.csv or *.xlsx).',
                                 QMessageBox.Ok)
        elif self.ratioBuilder.ratios is None:
            QMessageBox.critical(self, 'Not so fast!', 'Please run the ratio calculation first.', QMessageBox.Ok)
        else:
            self.window.startAnalysis(path)

    def runMultipleEvent(self):
        ratioFiles = QFileDialog.getOpenFileNames(self, 'Select results files to analyze', '', 'Excel-Datei (*.xlsx)')[0]
        fileNames = [Util.path_leaf(file) for file in ratioFiles]

        if not len(ratioFiles):
            return

        if QMessageBox.question(self, 'Run', 'Are you sure you want to analyze: {}?'.format(', '.join(fileNames)),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No) == QMessageBox.Yes:
            self.window.startCombinedResultsAnalysis(ratioFiles)

    ''' +-----------------------------+ '''
    ''' |        Results-Code         | '''
    ''' +-----------------------------+ '''

    def initResultsBox(self):
        self.resultsBox = QGroupBox('Results')
        # self.resultsBox.setMaximumHeight(400)

        self.resultTable = QTableView()
        self.resultTable.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.resultTable.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        layout = QGridLayout()
        layout.addWidget(self.resultTable, 0, 0)

        self.resultsBox.setLayout(layout)

    def clearResultsTable(self):
        self.resultTable.setModel(None)

    def display(self, results, standards):
        self.resultTable.setModel(DataFrameModel(results, standards, showIndex=False))
        self.resultTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
