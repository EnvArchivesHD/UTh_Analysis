from PyQt5 import QtGui
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, \
    QRadioButton, QCheckBox, QMessageBox
from PyQt5.QtGui import QPixmap, QIntValidator
from PyQt5.QtCore import Qt

import json


class DetectorLayoutDialog(QDialog):

    def __init__(self, inputTab, path=None):
        super(DetectorLayoutDialog, self).__init__()

        self.inputTab = inputTab
        self.path = path

        self.isotopes = ['229Th', '230Th', '232Th', '233U', '234U', '235U', '236U', '238U']
        self.column_dict = {}
        self.sem_dict = {}

        if path is None:
            self.setWindowTitle('Create new layout')
        else:
            self.setWindowTitle('Edit layout')

        self.initUI()
        self.setElements()
        # self.save()

    def initUI(self):
        layout = QGridLayout()

        headerFont = QtGui.QFont('Arial', 16)
        headerFont.setBold(True)

        isotopeHeaderLabel = QLabel('Isotope', font=headerFont)
        isotopeHeaderLabel.setAlignment(Qt.AlignCenter)
        columnHeaderLabel = QLabel('Column', font=headerFont)
        columnHeaderLabel.setAlignment(Qt.AlignCenter)
        semHeaderLabel = QLabel('SEM?', font=headerFont)
        semHeaderLabel.setAlignment(Qt.AlignCenter)

        layout.addWidget(isotopeHeaderLabel, 0, 0)
        layout.addWidget(columnHeaderLabel, 0, 1)
        layout.addWidget(semHeaderLabel, 0, 2)

        for i, isotope in enumerate(self.isotopes):

            font = QtGui.QFont()
            font.setBold(True)
            isotopeLabel = QLabel(isotope)
            isotopeLabel.setFont(font)
            isotopeLabel.setAlignment(Qt.AlignCenter)

            columnEdit = QLineEdit()
            columnEdit.setValidator(QIntValidator())
            self.column_dict[isotope] = columnEdit

            semBox = QCheckBox()
            self.sem_dict[isotope] = semBox
            semBox.setStyleSheet("margin-left:50%; margin-right:50%;")

            layout.addWidget(isotopeLabel, i+1, 0)
            layout.addWidget(columnEdit, i+1, 1)
            layout.addWidget(semBox, i+1, 2)


        self.saveButton = QPushButton('Save')
        self.saveButton.clicked.connect(self.save)
        layout.addWidget(self.saveButton, 1+len(self.isotopes), 0, 1, 3)

        self.setLayout(layout)

    def setElements(self):
        if self.path is None:
            return

        layout = {}
        with open(self.path, 'r') as file:
            layout = json.loads(file.read().replace('\n', ''))

        for isotope in self.isotopes:
            self.column_dict[isotope].setText(str(layout[isotope][0]))
            self.sem_dict[isotope].setChecked(layout[isotope][1])

    def save(self):
        for isotope in self.isotopes:
            try:
                test = int(self.column_dict[isotope].text())
            except:
                QMessageBox.critical(self, 'Not valid', 'Every text fields requires a number.', QMessageBox.Ok)
                return

        if self.path is None:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "detector.layout",
                                                      "Layout file (*.layout)", options=options)
            try:
                open(fileName, 'w')
            except OSError:
                return
        else:
            fileName = self.path

        layoutDict = {}

        for isotope in self.isotopes:
            layoutDict[isotope] = [int(self.column_dict[isotope].text()), self.sem_dict[isotope].isChecked()]

        with open(fileName, 'w') as file:
            json.dump(layoutDict, file, indent=4)

        self.inputTab.detectorFileEdit.setText(fileName)

        self.close()