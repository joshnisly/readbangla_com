#!/usr/bin/python

import glob
import os
import shutil
import sys

from distutils.core import setup
from distutils.cmd import Command
import py2exe #pylint: disable=F0401
import win32com

# Hack the python path so that py2exe can find win32com.shell
# TODO: not sure if this is even needed for Bangla stuff...
import py2exe.mf as modulefinder #pylint: disable=F0401
for p in win32com.__path__[1:]:
    modulefinder.AddPackagePath('win32com', p)
    for extra in ['win32com.shell']:
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)

if __name__ == '__main__':
    setup(name = 'LaunchBangla',
          version = '0.1',
          description = 'LaunchBangla',
          author = 'Josh Nisly',
          options = {'py2exe':
                     {'excludes': ['pywin', 'pywin.debugger', 'pywin.debugger.dbgcon',
                                  'pywin.dialogs', 'pywin.dialogs.list',
                                  'Tkconstants','Tkinter','tcl'],
                      'dll_excludes': ['w9xpopen.exe', 'mswsock.dll'],
                      'bundle_files': 1}},
          console = [{'script':'main.py',
                      'dest_base':'LaunchBangla',
                      #'icon_resources':[(1,'teamwrite.ico')],
                     }],
          zipfile = None
          )


