from PyQt5.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QWidget, QGridLayout
from PyQt5 import QtGui

import json
import os

from Util import path_leaf

ratiosConstants = {
    'mf48': ('Mf 234 / 238', 'float'), 'mf36': ('Mf 233 / 236', 'float'), 'mf56': ('Mf 235 / 236', 'float'),
    'mf68': ('Mf 236 / 238', 'float'), 'mf92': ('Mf 229 / 232', 'float'), 'mf38': ('Mf 233 / 238', 'float'),
    'mf35': ('Mf 233 / 235', 'float'), 'mf43': ('Mf 234 / 233', 'float'), 'mf45': ('Mf 234 / 235', 'float'),
    'mf09': ('Mf 230 / 229', 'float'), 'mf29': ('Mf 232 / 239', 'float'), 'mf34': ('Mf 233 / 234', 'float'),
    'mf58': ('Mf 235 / 238', 'float'), 'mf02': ('Mf 230 / 232', 'float'), 'l230': ('\u03BB<sub>230</sub>', 'float'),
    'l232': ('\u03BB<sub>232</sub>', 'float'), 'l234': ('\u03BB<sub>234</sub>', 'float'), 'l238': ('\u03BB<sub>238</sub>', 'float'),
    'NA': ('NA', 'float'), 'NR85': ('NR85', 'float'), 'cps': ('Counts per second', 'float'),
    'R3433': ('R34_33', 'float'), 'R3533': ('R35_33', 'float'),
    'R3029': ('R30_29', 'float'), 'th229SubU238': ('229Th - k * 238U', 'float'), 'th230SubU238': ('230Th - k * 238U', 'float')
}
analysisConstants = {
    'tri229': ('TRI-13 Th229 (ng/g)', 'float'), 'tri233': ('TRI-13 U233 (ng/g)', 'float'), 'tri236': ('TRI-13 U236 (ng/g)', 'float'),
    'blank232': ('Blank 232 Non-Standard (ng)', 'float'), 'blank232S': ('Blank 232 Standard (ng)', 'float'),
    'blank234': ('Blank 234 Non-Standard (fg)', 'float'), 'blank234S': ('Blank 234 Standard (fg)', 'float'),
    'blank238': ('Blank 238 Non-Standard (ng)', 'float'), 'blank238S': ('Blank 238 Standard (ng)', 'float'),
    'sp_blank230': ('Spikeblank 230 (fg/g)', 'float'),
    'ch_blank230': ('Ch. Bl. 230 Non-Standard (fg)', 'float'), 'ch_blank230S': ('Ch. Bl. 230 Standard (fg)', 'float'),
    'a230232_init': ('A230Th232Th Init.', 'float'), 'a230232_init_err': ('A230Th232Th Init. Error (abs.)', 'float'),
    'a230232_init_sst': ('A230Th232Th Init. Sst', 'float'), 'a230232_init_err_sst': ('A230Th232Th Init. Sst. Error (abs.)', 'float')
}
standardConstants = {
    'standardDenom': ('Denomination', 'string'), 'standardSampleMass': ('Sample mass (g)', 'float'), 'standardTriSp13': ('TriSp13 (g)', 'float')
}

def loadConstants(path):
    constants = {}
    if os.path.isfile(path):
        with open(path, 'r') as file:
            constants = json.loads(file.read().replace('\n', ''))

    allConstants = {**ratiosConstants, **analysisConstants, **standardConstants}
    for key in allConstants:
        if key not in constants:
            if allConstants[key][1] == 'float':
                constants[key] = 0.0
            elif allConstants[key][1] == 'string':
                constants[key] = ''

    fileName = path_leaf(path)
    if 'coral' in fileName:
        constants['type'] = 'coral'
    elif 'stalag' in fileName:
        constants['type'] = 'stalag'
    else:
        constants['type'] = 'stalag'
    return constants


class ConstantsDialog(QDialog):

    def __init__(self, inputTab, path=None):
        super(ConstantsDialog, self).__init__()

        self.inputTab = inputTab
        self.path = path
        self.edits = {}
        self.constants = {}

        if path is None:
            self.setWindowTitle('Set new constants')
            self.setWindowIcon(QtGui.QIcon(':/icons/file.png'))
        else:
            self.setWindowTitle('Edit constants')
            self.setWindowIcon(QtGui.QIcon(':/icons/edit.png'))

        self.initUI()
        self.setEdits()

    def initUI(self):
        font = QtGui.QFont()
        font.setBold(True)

        ratiosLayout1 = QFormLayout()
        ratiosLayout2 = QFormLayout()
        ratiosLabel = QLabel('For Ratios:')
        ratiosLabel.setFont(font)
        ratiosLayout1.addRow(ratiosLabel)
        
        i = 0
        for constant in ratiosConstants:
            
            self.edits[constant] = QLineEdit()
            if i < 14:
                ratiosLayout1.addRow(QLabel(ratiosConstants[constant][0]), self.edits[constant])
            else:
                ratiosLayout2.addRow(QLabel(ratiosConstants[constant][0]), self.edits[constant])
            i+=1

        analysisLayout = QFormLayout()
        analysisLabel = QLabel('For Analysis:')
        analysisLabel.setFont(font)
        analysisLayout.addRow(analysisLabel)

        for constant in analysisConstants:
            self.edits[constant] = QLineEdit()
            analysisLayout.addRow(QLabel(analysisConstants[constant][0]), self.edits[constant])

        standardLabel = QLabel('Standard')
        standardLabel.setFont(font)
        analysisLayout.addRow(standardLabel)

        for constant in standardConstants:
            self.edits[constant] = QLineEdit()
            analysisLayout.addRow(QLabel(standardConstants[constant][0]), self.edits[constant])

        self.saveButton = QPushButton('Save')
        self.saveButton.clicked.connect(self.save)

        layout = QGridLayout()
        ratios1Widget = QWidget()
        ratios1Widget.setLayout(ratiosLayout1)
        ratios2Widget = QWidget()
        ratios2Widget.setLayout(ratiosLayout2)
        analysisWidget = QWidget()
        analysisWidget.setLayout(analysisLayout)
        layout.addWidget(ratios1Widget, 0, 0)
        layout.addWidget(ratios2Widget, 0, 1)
        layout.addWidget(analysisWidget, 0, 2)
        layout.addWidget(self.saveButton, 1, 0, 1, 3)

        self.setLayout(layout)

    def setEdit(self, key):
        if self.constants is not None and key in self.constants:
            self.edits[key].setText(str(self.constants[key]))
        else:
            self.edits[key].setText('0.0')

    def setEdits(self):

        if self.path is not None:
            self.constants = loadConstants(self.path)

        for constant in {**ratiosConstants, **analysisConstants, **standardConstants}:
            self.setEdit(constant)

    def save(self):

        if self.path is None:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "constants.cfg",
                                                      "Config files (*.cfg)", options=options)
            try:
                open(fileName, 'w')
            except OSError:
                return
        else:
            fileName = self.path

        fileDict = {}
        allConstants = {**ratiosConstants, **analysisConstants, **standardConstants}
        for constant in allConstants:
            if allConstants[constant][1] == 'float':
                fileDict[constant] = float(self.edits[constant].text())
            elif allConstants[constant][1] == 'string':
                fileDict[constant] = self.edits[constant].text()

        with open(fileName, 'w') as file:
            json.dump(fileDict, file, indent=4)

        self.inputTab.constantsFileEdit.setText(fileName)

        self.close()
