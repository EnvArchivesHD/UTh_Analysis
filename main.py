from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QTabWidget, QMessageBox, QStyleFactory, QShortcut
from PyQt5.QtGui import QIcon, QKeySequence
import sys
import os
import pandas as pd

import Globals
from Analyzer import Analyzer
from Inspector import Inspector
from InputTabWidget import InputTabWidget
from AnalysisTabWidget import AnalysisTabWidget
from InspectTabWidget import InspectTabWidget

from RatioBuilding import RatioBuilder
import DataFolderUtil
import Util
import warnings
import webbrowser
from Settings import Settings

from ConstantsDialog import loadConstants

class Window(QtWidgets.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 1200, 1000)
        self.setWindowTitle("U/Th Data Analysis")
        self.setWindowIcon(QIcon(':/icons/PUA_logo.ico'))

        self.settings = Settings()

        self.tabWidget = QTabWidget()

        self.ratioBuilder = RatioBuilder()
        self.analyzer = Analyzer()
        self.inspector = Inspector()

        self.inputTab = InputTabWidget(self, self.ratioBuilder)
        self.inspectTab = InspectTabWidget(self, self.inspector)
        self.analysisTab = AnalysisTabWidget(self, self.ratioBuilder, self.analyzer)
        self.tabWidget.addTab(self.inputTab, 'Input')
        self.tabWidget.addTab(self.inspectTab, 'Inspect')
        self.tabWidget.addTab(self.analysisTab, 'Analysis')
        self.setCentralWidget(self.tabWidget)

        self.quitSc = QShortcut(QKeySequence('Ctrl+R'), self)
        self.quitSc.activated.connect(self.inputTab.runEvent)

        self.inputTab.dirNameEdit.textChanged.connect(lambda: self.setPaths(self.inputTab.dirNameEdit.text()))

        self.initMenu()
        self.change_style(self.settings['style'])

        self.show()

    def initMenu(self):
        # Open file action
        extractAction = QtWidgets.QAction('Open', self)
        extractAction.setShortcut('Ctrl+O')
        extractAction.setStatusTip('Open a file')
        extractAction.triggered.connect(self.inputTab.setDirectory)

        closeAction = QtWidgets.QAction('Exit', self)
        closeAction.setStatusTip('Closes the program')
        closeAction.triggered.connect(self.close_application)

        showHelpAction = QtWidgets.QAction('Nutzung', self)
        showHelpAction.setStatusTip('Shows, how to use the program.')
        showHelpAction.triggered.connect(self.showHelp)

        showAboutAction = QtWidgets.QAction('Info', self)
        showAboutAction.setStatusTip('Shows information about this program.')
        showAboutAction.triggered.connect(self.showAbout)

        openGitHubAction = QtWidgets.QAction('GitHub', self)
        openGitHubAction.setStatusTip('Opens the GitHub repository of this GUI')
        openGitHubAction.triggered.connect(self.openGitHub)

        fullscreenAction = QtWidgets.QAction('Toggle fullscreen', self)
        fullscreenAction.setShortcut('F11')
        fullscreenAction.triggered.connect(self.toggle_fullscreen)

        self.styleActions = {}
        for style in QStyleFactory.keys():
            styleAction = QtWidgets.QAction(style, self)
            styleAction.triggered.connect(self.get_change_style_action(style))
            styleAction.setCheckable(True)
            self.styleActions[style] = styleAction

        # menu
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(extractAction)
        fileMenu.addAction(closeAction)
        viewMenu = mainMenu.addMenu('&View')
        viewMenu.addAction(fullscreenAction)
        styleMenu = viewMenu.addMenu('&Style')
        for action in self.styleActions.values():
            styleMenu.addAction(action)
        helpMenu = mainMenu.addMenu('&Help')
        helpMenu.addAction(showHelpAction)
        helpMenu.addAction(openGitHubAction)
        helpMenu.addAction(showAboutAction)

    def setPaths(self, path):
        if not os.path.isdir(path):
            return

        self.inspectTab.set_path(path)
        self.analysisTab.searchMetadataFile(path)
        self.analyzer.set_path(path)

    def calcRatios(self, path):
        DataFolderUtil.createDataFolders(path)
        DataFolderUtil.removeUnnecessaryFiles(path)
        self.ratioBuilder.set_path(path)
        constants = loadConstants(self.inputTab.get_constants_path())
        self.ratioBuilder.set_constants(constants)
        #layout = Util.load_json(self.inputTab.get_layout_path())
        #self.ratioBuilder.set_layout(layout)
        self.ratioBuilder.set_options(mean_option=self.inspectTab.mean_option,
                                      dev_option=self.inspectTab.dev_option)
        self.ratioBuilder.set_specific_constants(self.inputTab.get_specific_constants())
        self.ratioBuilder.data_correction()

    def startAnalysis(self, metadatapath):
        self.analyzer.set_path(self.ratioBuilder.data_root_folder)
        constants = loadConstants(self.inputTab.get_constants_path())
        self.analyzer.set_constants(constants)
        self.analyzer.set_specific_constants(self.inputTab.get_specific_constants())
        self.analyzer.set_metadata(metadatapath, self.ratioBuilder.ratios)

        options_dict = {Globals.MEAN_METHOD: Util.keyByValue(self.inspectTab.mean_option_dict, self.ratioBuilder.mean_option),
                        Globals.DEV_METHOD: Util.keyByValue(self.inspectTab.dev_option_dict, self.ratioBuilder.dev_option)}

        try:
            self.analyzer.analyze(self.ratioBuilder.ratios,
                                  options_dict=options_dict,
                                  output_path=self.inputTab.getDataOutputPath())
            self.analysisTab.display(self.analyzer.results, self.analyzer.standard)
        except PermissionError:
            self.analysisTab.display()
            error_dialog = QtWidgets.QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle('Permission error')
            error_dialog.setText(
                'Could not save \"Results.xlsx\". Please close the related \"Results.xlsx\" file if it is open.')
            error_dialog.exec_()

    def startCombinedResultsAnalysis(self, resultsPaths):
        self.analyzer.set_path(Util.path_head(resultsPaths[0]), find_standard=False)
        constants = loadConstants(self.inputTab.get_constants_path())
        self.analyzer.set_constants(constants)
        self.analyzer.set_specific_constants(self.inputTab.get_specific_constants())

        results_dicts = []
        standards = []

        for file in resultsPaths:
            ratios, metadata = Util.get_ratios_and_metadata_from_results(file)
            ratios = ratios[ratios['Lab. #'].notna()]
            ratios.index = list(range(len(ratios)))

            self.analyzer.standard = Util.get_standard_number_from_df(ratios)
            self.analyzer.set_metadata_df(metadata)

            results_dict = self.analyzer.analyze(ratios, write_results_file=False, options_dict=None)
            results_dicts.append(results_dict)
            standards.append(self.analyzer.standard)

        all_inputs = pd.concat([entry['Input'] for entry in results_dicts])
        all_calcs = pd.concat([entry['Calc'] for entry in results_dicts])
        all_results = pd.concat([entry['Results'] for entry in results_dicts])
        all_constants = pd.concat([entry['Constants'] for entry in results_dicts])
        all_options = pd.concat([entry['Options'] for entry in results_dicts])

        all_dict = {
            'Input': all_inputs,
            'Calc': all_calcs,
            'Results': all_results,
            'Constants': all_constants
        }

        try:
            self.analyzer.writeToFile(all_dict, fileTitle='CombinedResults')
            self.analysisTab.display(all_results, standards)
        except PermissionError:
            self.analysisTab.display(all_results, standards)
            error_dialog = QtWidgets.QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle('Permission error')
            error_dialog.setText(
                'Could not save \"CombinedResults.xlsx\". Please close the related \"CombinedResults.xlsx\" file if it is open.')
            error_dialog.exec_()

    def showHelp(self):
        helpBox = QMessageBox()
        helpBox.setIcon(QMessageBox.Information)
        helpBox.setWindowTitle('How to use')
        helpBox.setText("Nutzung (Reihenfolge beachten):\n\n" +
                        "1. Im Input-Tab den Datenordner auswählen.\n" +
                        "2. Falls noch nicht vorhanden: Konstanten laden oder neu erstellen.\n" +
                        "3. Falls nötig messungsspezifische Konstanten einstellen.\n"
                        "4. Im Input-Tab auf \"Run\" klicken, um die Isotopenverhältnise zu berechnen.\n" +
                        "    Im Datenordner sollten nun die Dateien \"PrBlank.xlsx\", \"Ratios.xlsx\" und\n" +
                        "    \"Ratios_add.xlsx\" sein.\n" +
                        "5. Im Analysis-Tab eine Metadaten-Datei laden oder neu erstellen.\n" +
                        "6. Auf \"Start Analysis\" klicken.\n" +
                        "7. Im Datenordner sollte nun die Datei \"Results.xlsx\" erstellt sein.\n"
                        "\n" +
                        "Falls es Probleme beim Einlesen der Daten gibt, bitte den Beispiel"
                        "ordner als Vorlage nehmen. Bei weiteren Fragen oder Problemen bitte "
                        "@fabi anschreiben auf Mattermost oder Email an f.kontor@stud.uni-heidelberg.de.")
        helpBox.exec_()

    def showAbout(self):
        aboutBox = QMessageBox()
        aboutBox.setIcon(QMessageBox.Information)
        aboutBox.setWindowTitle('Info')
        aboutBox.setTextFormat(QtCore.Qt.RichText)
        aboutBox.setText('Programm: U/Th Data Analysis v1.0<br>' +
                         'Erstellt von: Fabian Kontor am Institut für Umweltphysik in Heidelberg (2021)<br>' +
                         'Ermöglicht durch: PyQt5, <a href="https://pypi.org/project/PyQt5/">https://pypi.org/project/PyQt5/</a>')
        aboutBox.exec_()

    def get_change_style_action(self, style):
        return lambda: self.change_style(style)

    def change_style(self, style):
        if style in QStyleFactory.keys():
            app = QtWidgets.QApplication.instance()
            app.setStyle(style)
            self.settings['style'] = style
            for action in self.styleActions.values():
                action.setChecked(False)
            self.styleActions[style].setChecked(True)
        else:
            style = QStyleFactory.keys()[0]
            app = QtWidgets.QApplication.instance()
            app.setStyle(style)
            self.settings['style'] = style
            for action in self.styleActions.values():
                action.setChecked(False)
            self.styleActions[style].setChecked(True)

    def toggle_fullscreen(self):
        if self.windowState() & QtCore.Qt.WindowFullScreen:
            self.showNormal()
        else:
            self.showFullScreen()

    def openGitHub(self):
        webbrowser.open('https://github.com/zebleck/BachelorGUI')

    def close_application(self):
        sys.exit()


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    app = QtWidgets.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
