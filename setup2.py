# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 17:55:17 2018

@author: hayden.flake
"""
import sys
import os.path
from cx_Freeze import setup, Executable
import requests.certs
import matplotlib
import datetime
import tkinter as tk

#os.environ['TCL_LIBRARY'] = r'C:\Users\hayden.flake\AppData\Local\Continuum\anaconda3\tcl\tcl8.6'
#os.environ['TK_LIBRARY'] = r'C:\Users\hayden.flake\AppData\Local\Continuum\anaconda3\tcl\tk8.6'
buildOptions = dict(include_msvcr=True,\
                    includes=['matplotlib.backends.backend_pdf','matplotlib.figure','numpy.core','matplotlib.backends.backend_tkagg'], \
                    include_files=[(requests.certs.where(), 'cacert.pem'), (matplotlib.get_data_path(), "mpl-data"),
                                   "sigicom2.db", 'sixenseLogo.png', 'down.png', 'up.png', 'splash.png'], \
                        namespace_packages=["mpl_toolkits"],\
                        excludes=["QtSql","PyQt5.QtSql","PyQt5.QtNetwork","pluggy","xml","html","curses","xlrd","cv2","pygame",\
                              "pyautogui","setuptools","PIL","scipy","jupyter_client","jupyter_core",'pandas'])

#base = "Console"
if sys.platform == "win32":
    base = "Win32GUI"

setup(name = "sigicom data handler v1.3",
      version = "1.3" ,
      description = "SDH1.3 Compiled on "+str(datetime.datetime.now()) ,
      options={"build_exe":buildOptions},
      executables = [Executable("sigicom2.py",icon='icon.ico')])




#import win32com.client as win32
##import openpyxl
#import os
#import pathlib
#from PyQt5.QtGui import *
#from PyQt5.QtWidgets import *
#from PyQt5.QtCore import *
#import sys

#'numpy.core._methods','numpy.lib.format',

#,excludes=["numpy","html","http","xml","xlrd","email","cv2","pyautogui","setuptools","matplotlib","PIL","scipy"]
