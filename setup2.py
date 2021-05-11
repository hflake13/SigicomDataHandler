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




