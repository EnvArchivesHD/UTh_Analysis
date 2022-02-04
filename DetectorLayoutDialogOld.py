from PyQt5 import QtGui
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

import json


class DetectorLayoutDialogOld(QDialog):
    stylesheet = """
        MainWindow {
            background-image: url("D:/_Qt/img/cat.jpg"); 
            background-repeat: no-repeat; 
            background-position: center;
        }
    """

    def __init__(self, inputTab, path=None):
        super(DetectorLayoutDialogOld, self).__init__()

        self.inputTab = inputTab
        self.path = path

        # if path is None:
        #    self.setWindowTitle('Set new constants')
        # else:
        #    self.setWindowTitle('Edit constants')

        self.layout = {'0': 9 * [''], '1': 9 * [''], '2': 9 * ['']}
        self.load('A:\\Github Repos\\BachelorGUI\\dist\\GUI\\UTh.layout')
        self.initUI()
        # self.save()

    def initUI(self):
        layout = QGridLayout()

        label = QLabel(self)
        pixmap = QPixmap('images/messprotokoll.png')
        label.setPixmap(pixmap)
        layout.addWidget(label)
        layout.setContentsMargins(0, 0, 0, 0)

        font = QtGui.QFont('Arial', 20)

        for row in range(3):
            for col in range(9):
                edit = QLineEdit('', self) # self.layout[str(row)][col]
                edit.setFont(font)
                edit.setAlignment(Qt.AlignCenter)
                edit.move(238 + 108 * col, 375 + 70 * row)

        self.setLayout(layout)

        self.setFixedSize(pixmap.width(), pixmap.height())

    def load(self, filename):
        with open(filename, 'r') as file:
            self.layout = json.loads(file.read().replace('\n', ''))

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

        layoutDict = {
            1: ['', '', '', '233U', '234U', '235U', '236U', '238U', ''],
            2: ['', '', '', '229Th', '230Th', '', '232Th', '', ''],
            3: ['', '', '', '', '229Th', '230Th', '', '', '']
        }

        with open(fileName, 'w') as file:
            json.dump(layoutDict, file, indent=4)
