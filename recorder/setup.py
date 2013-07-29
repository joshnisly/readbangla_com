#!/usr/bin/python

import glob
import os
import shutil
import sys

from distutils.core import setup
from distutils.cmd import Command
import py2exe #pylint: disable=F0401

if __name__ == '__main__':
    setup(name = 'BanglaRecorder',
          version = '0.1',
          description = 'BanglaRecorder',
          author = 'Josh Nisly',
          options = {'py2exe':
                     {'excludes': ['pywin', 'pywin.debugger', 'pywin.debugger.dbgcon',
                                  'pywin.dialogs', 'pywin.dialogs.list',
                                  'Tkconstants','Tkinter','tcl'],
                      'includes': ['sip'],
                      'dll_excludes': ['w9xpopen.exe', 'mswsock.dll'],
                      'bundle_files': 1}},
          console = [{'script':'gui.py',
                      'dest_base':'BanglaRecorder',
                      #'icon_resources':[(1,'teamwrite.ico')],
                     }],
          zipfile = None
          )


