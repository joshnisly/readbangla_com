#!/usr/bin/python

import glob
import os
import PyQt4
import shutil
import sys
import zipfile

from distutils.core import setup
from distutils.cmd import Command
import py2exe #pylint: disable=F0401

def _zip_dir(path, rel_zip_path, output_path):
    assert os.path.isdir(path)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(path):
            for entry in files:
                full_path = os.path.join(root, entry)
                assert full_path.startswith(path + os.sep)
                rel_path = rel_zip_path + full_path[len(path):]
                zip_file.write(full_path, rel_path)

if __name__ == '__main__':
    pyqt_dir = os.path.dirname(PyQt4.__file__)
    setup(name = 'BanglaRecorder',
          version = '0.1',
          description = 'BanglaRecorder',
          author = 'Josh Nisly',
          options = {'py2exe':
                     {'excludes': ['pywin', 'pywin.debugger', 'pywin.debugger.dbgcon',
                                  'pywin.dialogs', 'pywin.dialogs.list',
                                  'Tkconstants','Tkinter','tcl'],
                      'includes': ['sip', 'pyaudio', 'PyQt4.QtSvg', 'PyQt4.QtXml'],
                      'dll_excludes': ['w9xpopen.exe', 'mswsock.dll'],
                      }},
          data_files = [
              ('', glob.glob('*.svg')),
              ('imageformats', [os.path.join(pyqt_dir, 'plugins', 'imageformats', 'qsvg4.dll')])
          ],
          windows = [{'script':'gui.py',
                      'dest_base':'BanglaRecorder',
                      #'icon_resources':[(1,'teamwrite.ico')],
                     }],
          zipfile = None
          )

    _zip_dir('dist', 'BanglaRecorder', 'BanglaRecorder.zip')


