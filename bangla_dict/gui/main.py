#!/usr/bin/python

import os
from PyQt4 import QtGui, QtCore
import re
import sys
import urllib
import webbrowser

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, icon, parent)

        self._menu = QtGui.QMenu(parent)
        exit_action = self._menu.addAction("Exit")
        self.setContextMenu(self._menu)

        self.connect(exit_action, QtCore.SIGNAL('triggered()'), self._exit)

        self._timer = QtCore.QTimer(self)
        self.connect(self._timer, QtCore.SIGNAL('timeout()'), self._on_timer)
        self._timer.start(250)

        self._last_text = None

    def _exit(self):
        self.hide()
        sys.exit()

    def _on_timer(self):
        clipboard = QtGui.QApplication.clipboard();
        text = unicode(clipboard.text());

        if text == self._last_text:
            return

        self._last_text = text

        for char in text:
            if char >= u'\u0981' and char <= u'\u09FF':
                self._launch_text(text)
                break

    def _launch_text(self, text):
        text = re.sub('[()\r\n]', '', text)
        url_text = urllib.quote(text.encode('utf8'))
        url = 'http://bangla.joshnisly.com/lookup/%s/' % url_text
        webbrowser.open(url)


def main():
    app = QtGui.QApplication(sys.argv)
    style = app.style()
    icon = QtGui.QIcon(style.standardPixmap(QtGui.QStyle.SP_FileIcon))
    trayIcon = SystemTrayIcon(icon)

    trayIcon.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
