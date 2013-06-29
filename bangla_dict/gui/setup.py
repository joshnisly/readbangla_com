#!/usr/bin/python

import os
import re
import sys

from distutils.core import setup
from distutils.cmd import Command
import py2exe

if __name__ == '__main__':
    setup(name = 'BanglaLauncher',
          version = '0.2',
          description = 'ReadBangla.com Launcher',
          author = 'Josh Nisly',
          options = {'py2exe':
                     {'excludes': ['pywin', 'pywin.debugger', 'pywin.debugger.dbgcon',
                                  'pywin.dialogs', 'pywin.dialogs.list',
                                  'Tkconstants','Tkinter','tcl'],
                      #'packages': ['encodings'],
                      'includes': ['sip'],
                      'dll_excludes': ['w9xpopen.exe', 'mswsock.dll'],
                      'bundle_files': 1}},
          data_files = [('', ['Microsoft.VC90.CRT.manifest', 'msvcr90.dll'])],
          windows = [{'script':'main.py',
                      'dest_base':'LaunchBangla',
                      #'icon_resources':[(1,'TODO.ico')],
                     }],
          zipfile = None
          )
    
