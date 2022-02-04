import os

from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QGroupBox, QGridLayout, QListWidget, QListWidgetItem, QLabel, QComboBox, \
    QPushButton, QTableView, QHeaderView
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import Util
import DataFolderUtil
from DataFrameModel import DataFrameModel


class InspectTabWidget(QWidget):
    mean_option_dict = {
        'Arithmetic mean': 'mean',
        'Median': 'median'
    }

    dev_option_dict = {
        'Standard deviation': 'std',
        'Median absolute deviation': 'mad',
        'Interquartile range': 'iqr'
    }

    scale_option_dict = {
        'Relative': 'rel',
        'Absolute': 'abs'
    }

    def __init__(self, window, inspector):
        super(InspectTabWidget, self).__init__()
        self.window = window
        self.window.inputTab.addRunListener(self)

        self.data_root_folder = None
        self.mean_option = 'median'
        self.dev_option = 'std'
        self.scale_option = 'rel'

        self.inspector = inspector

        self.initRatiosBox()
        self.initOverviewBox()
        self.initVisualizeBox()

        layout = QGridLayout()
        layout.addWidget(self.ratiosBox, 0, 0)
        layout.addWidget(self.overviewBox, 1, 0)
        layout.addWidget(self.visualizeBox, 2, 0)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 2)
        layout.setRowStretch(2, 3)

        self.setLayout(layout)

    def set_path(self, data_root_folder):
        self.clear()
        self.data_root_folder = data_root_folder
        self.setFilesBox(self.data_root_folder)
        self.ratioButton.setEnabled(True)

    def get_path(self):
        return self.data_root_folder

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

    def addRatiosToTable(self):
        model = DataFrameModel(self.window.ratioBuilder.ratios, DataFolderUtil.findStandardNumber(self.data_root_folder))
        self.ratiosTable.setModel(model)
        self.ratiosTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    ''' +-----------------------------+ '''
    ''' |       Overview-Code         | '''
    ''' +-----------------------------+ '''

    def initOverviewBox(self):
        self.overviewBox = QGroupBox('Overview')

        self.filesList = QListWidget()
        self.filesList.addItem(QListWidgetItem('No files'))
        self.filesList.itemClicked.connect(self.fileClicked)
        self.filesList.itemEntered.connect(self.fileClicked)
        self.filesList.itemDoubleClicked.connect(lambda item: Util.openFileItem(self.get_path(), item))
        self.pathLabel = QLabel('')
        self.pathLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.dateLabel = QLabel('')
        self.dateLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.timeLabel = QLabel('')
        self.timeLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.labNrLabel = QLabel('')
        self.labNrLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)

        infoLayout = QGridLayout()
        infoLayout.addWidget(QLabel('Path:'), 0, 0)
        infoLayout.addWidget(self.pathLabel, 0, 1)
        infoLayout.addWidget(QLabel('Lab. Nr.:'), 1, 0)
        infoLayout.addWidget(self.labNrLabel, 1, 1)
        infoLayout.addWidget(QLabel('Mess. Dat.:'), 2, 0)
        infoLayout.addWidget(self.dateLabel, 2, 1)
        infoLayout.addWidget(QLabel('Time:'), 3, 0)
        infoLayout.addWidget(self.timeLabel, 3, 1)
        infoLayout.setAlignment(Qt.AlignTop)
        infoWidget = QWidget()
        infoWidget.setLayout(infoLayout)

        layout = QGridLayout()
        layout.addWidget(self.filesList, 0, 0)
        layout.addWidget(infoWidget, 0, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 3)
        self.overviewBox.setLayout(layout)

    def setFilesBox(self, path):
        self.filesList.clear()

        files = DataFolderUtil.getFiles(path)
        # self.dataFilesNumber.setText(str(len(files['data'])))
        # self.blankFilesNumber.setText(str(len(files['blank'])))
        # self.yhas_uFilesNumber.setText(str(len(files['yhasu'])))
        # self.yhas_thFilesNumber.setText(str(len(files['yhasth'])))
        # self.hfFilesNumber.setText(str(len(files['hf'])))

        for file in files['data'] + files['blank'] + files['yhasu'] + files['yhasth'] + files['hf']:
            self.filesList.addItem(QListWidgetItem(file))

    def setFileInfo(self, path):
        self.inspector.inspect(path)
        self.pathLabel.setText(path)
        self.labNrLabel.setText(self.inspector.labNr)
        self.dateLabel.setText(self.inspector.date)
        self.timeLabel.setText(self.inspector.time)

    def fileClicked(self, item):
        if self.data_root_folder is None:
            return
        path = os.path.join(self.data_root_folder, item.text())
        if not os.path.isfile(path):
            return
        self.setFileInfo(path)
        self.draw()

    ''' +-----------------------------+ '''
    ''' |      Visualize-Code         | '''
    ''' +-----------------------------+ '''

    def initVisualizeBox(self):
        self.visualizeBox = QGroupBox('Visualize')
        self.optionsBox = QGroupBox('Options')

        self.isotopeDropdown = QComboBox()
        font = self.isotopeDropdown.font()
        font.setPointSize(16)
        self.isotopeDropdown.setFont(font)
        for isotope in self.inspector.desc.keys():
            self.isotopeDropdown.addItem(isotope)
        self.isotopeDropdown.currentIndexChanged.connect(self.settingChanged)

        self.meanDropdown = QComboBox()
        self.meanDropdown.setFont(font)
        self.meanDropdown.addItem('Median')
        self.meanDropdown.addItem('Arithmetic mean')
        self.meanDropdown.currentIndexChanged.connect(self.settingChanged)

        self.devDropdown = QComboBox()
        self.devDropdown.setFont(font)
        self.devDropdown.addItem('Standard deviation')
        self.devDropdown.addItem('Median absolute deviation')
        self.devDropdown.addItem('Interquartile range')
        self.devDropdown.currentIndexChanged.connect(self.settingChanged)

        self.scaleDropdown = QComboBox()
        self.scaleDropdown.setFont(font)
        self.scaleDropdown.addItem('Relative')
        self.scaleDropdown.addItem('Absolute')
        self.scaleDropdown.currentIndexChanged.connect(self.settingChanged)

        self.ratioButton = QPushButton('Calculate ratios')
        self.ratioButton.setEnabled(False)
        self.ratioButton.clicked.connect(self.window.inputTab.runEvent)

        optionsLayout = QGridLayout()
        optionsLayout.addWidget(QLabel('Isotope'), 0, 0)
        optionsLayout.addWidget(self.isotopeDropdown, 0, 1)
        optionsLayout.addWidget(QLabel('Mean'), 1, 0)
        optionsLayout.addWidget(self.meanDropdown, 1, 1)
        optionsLayout.addWidget(QLabel('Deviation'), 2, 0)
        optionsLayout.addWidget(self.devDropdown, 2, 1)
        optionsLayout.addWidget(QLabel('Scaling'), 3, 0)
        optionsLayout.addWidget(self.scaleDropdown, 3, 1)
        optionsLayout.addItem(QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 4, 0, 1, 2)
        optionsLayout.addWidget(self.ratioButton, 5, 0, 1, 2)
        optionsLayout.setAlignment(Qt.AlignTop)
        self.optionsBox.setLayout(optionsLayout)

        self.plot = pg.PlotWidget()
        self.plot.getPlotItem().showGrid(True, True, 0.1)
        self.plot.getPlotItem().showAxis('top')
        self.plot.getPlotItem().showAxis('right')
        self.plot.getPlotItem().getAxis('top').setHeight(0)
        self.plot.getPlotItem().getAxis('top').setTicks([])
        self.plot.getPlotItem().getAxis('right').setWidth(0)
        self.plot.setMouseEnabled(x=False, y=False)

        layout = QGridLayout()
        layout.addWidget(self.optionsBox, 0, 0)
        layout.addWidget(self.plot, 0, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 3)
        self.visualizeBox.setLayout(layout)

    def draw(self):
        if self.inspector.data_dict is None:
            return

        self.plot.clear()

        isotope = self.isotopeDropdown.currentText()

        mean, std = self.inspector.get_stats(isotope, mean_option=self.mean_option, dev_option=self.dev_option)

        X = self.inspector.data_dict[isotope].copy()


        if self.scale_option == 'rel':
            std = abs(std/mean)
            X /= mean
            mean = 1

        linePen = pg.mkPen(color=(0, 0, 150), style=Qt.DashLine)
        topLine = pg.InfiniteLine(pos=mean + 2 * std, angle=0, pen=linePen)
        meanLine = pg.InfiniteLine(pos=mean, angle=0, pen=linePen)
        bottomLine = pg.InfiniteLine(pos=mean - 2 * std, angle=0, pen=linePen)

        inRangeIndices = np.where(np.logical_and(X >= mean - 2 * std, X <= mean + 2 * std))[0]
        mask = np.ones(len(X), np.bool)
        mask[inRangeIndices] = 0
        cycleNr = np.arange(len(X))
        scatterOut = pg.ScatterPlotItem(cycleNr[mask], X[mask], brush=pg.mkBrush(color=(150, 0, 0)))
        scatterIn = pg.ScatterPlotItem(cycleNr[inRangeIndices], X[inRangeIndices], brush=pg.mkBrush(color=(0, 150, 0)))

        self.plot.plot(X, pen=pg.mkPen(color=(150, 150, 150, 100), style=Qt.DashLine))
        self.plot.addItem(scatterIn)
        self.plot.addItem(scatterOut)
        self.plot.addItem(topLine)
        self.plot.addItem(meanLine)
        self.plot.addItem(bottomLine)

    def settingChanged(self, item):
        self.mean_option = self.mean_option_dict[self.meanDropdown.currentText()]
        self.dev_option = self.dev_option_dict[self.devDropdown.currentText()]
        self.scale_option = self.scale_option_dict[self.scaleDropdown.currentText()]
        self.ratioButton.setEnabled(True)
        self.draw()

    def clear(self):
        self.ratioButton.setEnabled(False)
        self.pathLabel.clear()
        self.labNrLabel.clear()
        self.timeLabel.clear()
        self.dateLabel.clear()
        self.plot.clear()
        self.inspector.data_dict = None

    # notified when ratios are successfully calculated
    def notify(self):
        self.ratioButton.setEnabled(False)
        self.addRatiosToTable()