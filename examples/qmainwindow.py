#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Custom QMainWindow Widget."""


import os
import sys
from random import randint
from webbrowser import open_new_tab

from PyQt5.QtCore import Qt, QTimer

from PyQt5.QtGui import QColor, QCursor, QIcon, QPainter, QPalette, QPen

from PyQt5.QtWidgets import (QDesktopWidget, QFileDialog, QFontDialog,
                             QGraphicsDropShadowEffect, QLabel, QMainWindow,
                             QMenu, QMessageBox, QShortcut, QSystemTrayIcon,
                             QToolBar, QWidget)

try:
    import resource
except ImportError:
    resource = None
try:
    import qdarkstyle  # https://github.com/ColinDuquesnoy/QDarkStyleSheet
except ImportError:    # sudo pip3 install qdarkstyle
    qdarkstyle = None  # 100% optional


##############################################################################


class MainWindow(QMainWindow):

    """Main Window."""

    def __init__(self, parent=None):
        """Initialize MainWindow."""
        super(MainWindow, self).__init__(parent)
        self.ram_info, self.ram_timer = QLabel(self), QTimer(self)
        self.menubar, self.tray = QMenu(self), QSystemTrayIcon(self)
        self.ram_timer.timeout.connect(self.update_statusbar)
        self.ram_timer.start(60000)  # Every 60 seconds
        self.statusBar().insertPermanentWidget(0, self.ram_info)
        self.setMinimumSize(800, 600)
        self.setMaximumSize(QDesktopWidget().screenGeometry().width() * 2,
                            QDesktopWidget().screenGeometry().height() * 2)
        self.palette().setBrush(QPalette.Base, Qt.transparent)
        self.setPalette(self.palette())  # Transparent palette
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)  # no opaque paint
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # translucent
        QShortcut("Ctrl+q", self, activated=self.close)
        self.make_toolbar()
        self.make_menubar()
        self.update_statusbar()
        self.make_trayicon()
        if qdarkstyle:
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def paintEvent(self, event):
        """Paint transparent background,animated pattern,background text."""
        painter, font = QPainter(self), self.font()
        painter.fillRect(event.rect(), Qt.transparent)  # fill transparent rect
        painter.setPen(QPen(QColor(randint(9, 255), randint(9, 255), 255)))
        painter.rotate(30)  # Rotate painter ~30 Degree
        font.setBold(True)  # Set painter Font for text
        font.setPixelSize(100)
        painter.setFont(font)
        painter.drawText(99, 99, "Python Qt")  # draw the background text
        painter.rotate(-30)  # Rotate -30 the QPen back
        painter.setPen(Qt.NoPen)  # set the pen to no pen
        painter.setBrush(QColor("black"))  # Background Color
        painter.setOpacity(0.9)  # Background Opacity
        painter.drawRoundedRect(self.rect(), 25, 25)  # Back Rounded Borders
        for i in range(2048):  # animated random dots background pattern
            x = randint(10, self.size().width() - 10)
            y = randint(10, self.size().height() - 10)
            painter.setPen(QPen(QColor(randint(9, 255), randint(9, 255), 255)))
            painter.drawPoint(x, y)
        QMainWindow.paintEvent(self, event)

    def make_toolbar(self, list_of_actions=None):
        """Make or Update the main Tool Bar."""
        self.toolbar = QToolBar(self)
        self.left_spacer, self.right_spacer = QWidget(self), QWidget(self)
        self.left_spacer.setSizePolicy(1 | 2, 1 | 2)  # Expanding, Expanding
        self.right_spacer.setSizePolicy(1 | 2, 1 | 2)  # Expanding, Expanding
        self.toolbar.addAction("Menu",
                               lambda: self.menubar.exec_(QCursor.pos()))
        self.toolbar.addWidget(self.left_spacer)
        self.toolbar.addSeparator()
        self.toolbar.addAction(QIcon.fromTheme("help-contents"),
                               "Help and Docs", lambda: open_new_tab(__url__))
        self.toolbar.addAction(QIcon.fromTheme("help-about"), "About Qt 5",
                               lambda: QMessageBox.aboutQt(self))
        self.toolbar.addAction(QIcon.fromTheme("help-about"), "About Python 3",
                               lambda: open_new_tab('http://python.org/about'))
        self.toolbar.addAction(QIcon.fromTheme("application-exit"),
                               "Quit", self.close)
        self.toolbar.addSeparator()
        if list_of_actions and len(list_of_actions):
            for action in list_of_actions:  # if list_of_actions, add actions.
                self.toolbar.addAction(action)
            self.toolbar.addSeparator()
        self.toolbar.addWidget(self.right_spacer)
        self.addToolBar(self.toolbar)
        if sys.platform.startswith("win"):
            self.toolbar.hide()  # windows dont have QIcon.fromTheme,so hide.
        return self.toolbar

    def make_menubar(self, list_of_actions=None):
        """Make or Update the main Tool Bar."""
        self.menuBar().addMenu("&File").addAction("Exit", self.close)
        self.menubar.addMenu("&File").addAction("Exit", self.close)
        viewMenu = self.menuBar().addMenu("&View")
        viewMenu.addAction(
            "Toggle ToolBar", lambda:
                self.toolbar.setVisible(not self.toolbar.isVisible()))
        viewMenu.addAction(
            "Toggle StatusBar", lambda:
                self.statusBar().setVisible(not self.statusBar().isVisible()))
        viewMenu.addAction(
            "Toggle MenuBar", lambda:
                self.menuBar().setVisible(not self.menuBar().isVisible()))
        viewMenu2 = self.menubar.addMenu("&View")
        for action in viewMenu.actions():
            viewMenu2.addAction(action)
        windowMenu = self.menuBar().addMenu("&Window")
        windowMenu.addAction("Minimize", lambda: self.showMinimized())
        windowMenu.addAction("Maximize", lambda: self.showMaximized())
        windowMenu.addAction("Restore", lambda: self.showNormal())
        windowMenu.addAction("Full-Screen", lambda: self.showFullScreen())
        windowMenu.addAction("Center", lambda: self.center())
        windowMenu.addAction("Top-Left", lambda: self.move(0, 0))
        windowMenu.addAction("To Mouse", lambda: self.move(QCursor.pos()))
        windowMenu.addSeparator()
        windowMenu.addAction("Increase size", lambda: self.resize(
            self.size().width() * 1.5, self.size().height() * 1.5))
        windowMenu.addAction("Decrease size", lambda: self.resize(
            self.size().width() // 1.5, self.size().height() // 1.5))
        windowMenu.addAction("Minimum size", lambda:
                             self.resize(self.minimumSize()))
        windowMenu.addAction("Maximum size", lambda:
                             self.resize(self.maximumSize()))
        windowMenu.addAction("Horizontal Wide", lambda: self.resize(
            self.maximumSize().width(), self.minimumSize().height()))
        windowMenu.addAction("Vertical Tall", lambda: self.resize(
            self.minimumSize().width(), self.maximumSize().height()))
        windowMenu.addSeparator()
        windowMenu.addAction("Disable Resize", lambda:
                             self.setFixedSize(self.size()))
        windowMenu2 = self.menubar.addMenu("&Window")
        for action in windowMenu.actions():
            windowMenu2.addAction(action)
        optionMenu = self.menuBar().addMenu("&Options")
        optionMenu.addAction("Set Interface Font...", lambda:
                             self.setFont(QFontDialog.getFont(self)[0]))
        optionMenu.addAction("Load CSS Skin...", lambda:
                             self.setStyleSheet(self.skin()))
        optionMenu.addAction("Take ScreenShoot...", lambda: self.grab().save(
            QFileDialog.getSaveFileName(self, "Save", os.path.expanduser("~"),
                                        "(*.png) PNG image file", "png")[0]))
        optionMenu2 = self.menubar.addMenu("&Options")
        for action in optionMenu.actions():
            optionMenu2.addAction(action)
        helpMenu = self.menuBar().addMenu("&Help")
        helpMenu.addAction("About Qt 5", lambda: QMessageBox.aboutQt(self))
        helpMenu.addAction("About Python 3", lambda:
                           open_new_tab('https://www.python.org/about'))
        helpMenu.addSeparator()
        if sys.platform.startswith('linux'):
            helpMenu.addAction("View Source Code",
                               lambda: open_new_tab(__file__))
        helpMenu.addAction("View GitHub Repo", lambda: open_new_tab(__url__))
        helpMenu.addAction("Report Bugs", lambda:
                           open_new_tab(__url__ + '/issues?state=open'))
        helpMenu2 = self.menubar.addMenu("&Help")
        for action in helpMenu.actions():
            helpMenu2.addAction(action)
        return self.menuBar()

    def update_statusbar(self, custom_message=None):
        """Make or Update the Status Bar."""
        statusbar = self.statusBar()
        if resource:
            ram_use = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
                          resource.getpagesize() / 1024 / 1024)
            ram_byt = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
            ram_all = int(ram_byt / 1024 / 1024)
            self.ram_info.setText("{0} / {1} Mb".format(ram_use, ram_all))
            self.ram_info.setToolTip(
                "{0} of {1} MegaBytes of RAM Memory.".format(ram_use, ram_all))
        if custom_message and len(custom_message):
            return statusbar.showMessage(custom_message)
        return statusbar.showMessage(__doc__)

    def make_trayicon(self):
        """Make a Tray Icon."""
        if self.windowIcon() and __doc__ and self.menubar:
            self.tray.setIcon(self.windowIcon())
            self.tray.setToolTip(__doc__)
            self.tray.setContextMenu(self.menubar)
            self.tray.activated.connect(lambda evnt: self.menubar.exec_(
                QCursor.pos()) if evnt == self.tray.Trigger else evnt)
            return self.tray.show()

    def must_have_tooltip(self, widget_list):
        """Force widget tuple passed as argument should have Tool Tips."""
        if not widget_list and not len(widget_list):
            return
        for each_widget in widget_list:
            if hasattr(each_widget, "text"):
                each_widget.setToolTip(each_widget.text())
            elif hasattr(each_widget, "currentText"):
                each_widget.setToolTip(each_widget.currentText())
            elif hasattr(each_widget, "value"):
                each_widget.setToolTip(str(each_widget.value()))

    def toggle_autofillbackground(self, widget_list):
        """Widget tuple passed as argument should have filled background."""
        if not widget_list and not len(widget_list):
            return
        for a_widget in widget_list:
            a_widget.setAutoFillBackground(not a_widget.autoFillBackground())

    def must_glow(self, widget_list):
        """force apply an glow effect to the widget."""
        if not widget_list and not len(widget_list):
            return
        for glow, each_widget in enumerate(widget_list):
            if each_widget.graphicsEffect() is None:
                glow = QGraphicsDropShadowEffect(self)
                glow.setOffset(0)
                glow.setBlurRadius(99)
                glow.setColor(QColor(99, 255, 255))
                each_widget.setGraphicsEffect(glow)
            each_widget.graphicsEffect().setEnabled(
                not each_widget.graphicsEffect().isEnabled())

    def skin(self, filename=None):
        """Open QSS from filename,if no QSS return None,if no filename ask."""
        if not filename:
            filename = str(QFileDialog.getOpenFileName(
                self, __doc__ + " - Open QSS Skin", os.path.expanduser("~"),
                "CSS Cascading Style Sheet for Qt 5 (*.qss);;All (*.*)")[0])
        if filename and os.path.isfile(filename):
            with open(filename, 'r', encoding="utf-8-sig") as file_to_read:
                text = file_to_read.read().strip()
        if text:
            return text

    def center(self):
        """Center and resize the window."""
        self.showNormal()
        self.resize(QDesktopWidget().screenGeometry().width() // 1.25,
                    QDesktopWidget().screenGeometry().height() // 1.25)
        qr = self.frameGeometry()
        qr.moveCenter(QDesktopWidget().availableGeometry().center())
        return self.move(qr.topLeft())

    def closeEvent(self, event):
        """Ask to Quit."""
        return event.accept() if QMessageBox.question(
            self, "Close", "<h1>Quit ?.", QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No) == QMessageBox.Yes else event.ignore()


##############################################################################


if __name__ in '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    gui = MainWindow()
    gui.show()
    exit(app.exec_())