# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 09:38:07 2019

@author: hayden.flake
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import glowButton as custom
import datetime
import sigicomDataHandler2 as sigi
import sys
from matplotlib.widgets import Cursor
import traceback
import os
import pytz

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib

matplotlib.use('agg')
import matplotlib.pyplot as plt


def log_error(message):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    filename = str(month) + '_' + str(year) + '_Err_Log.txt'
    if not os.path.exists('./ErrorLogs'):
        os.mkdir('./ErrorLogs')
    with open('./ErrorLogs/' + filename, 'a') as file:
        file.write(str(datetime.datetime.now()) + '.........')
        file.write(message + '\n')


class MplFigure(object):
    def __init__(self, parent):
        self.figure = plt.figure(facecolor=(.195, .195, .195))
        self.canvas = FigureCanvas(self.figure)


class radio_btn(QRadioButton):
    state_changed = pyqtSignal(tuple)
    right_click = pyqtSignal(str)

    def __init__(self, id, name):
        super(radio_btn, self).__init__(id + " " + name)
        self.toggled.connect(self.emit_id_st)
        self.id = id

    def emit_id_st(self):
        self.state_changed.emit((self.id, self.isChecked()))

    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            super().mousePressEvent(QMouseEvent)
        elif QMouseEvent.button() == Qt.RightButton:
            # do what you want here
            print("Right Button Clicked")
            self.right_click.emit(self.id)


class instrum_stats(QGroupBox):
    def __init__(self):
        super(instrum_stats, self).__init__()
        mainLayout = QVBoxLayout()
        row0 = QHBoxLayout()
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        mainLayout.addLayout(row0)
        self.serLbl = QLabel('Serial Number: ')
        row0.addWidget(self.serLbl)
        self.bat = QLabel('Battery: ')
        self.humid = QLabel('Humidity: ')
        self.temp = QLabel('Board Temperature: ')
        row1.addWidget(self.bat)
        row1.addWidget(self.humid)
        row1.addWidget(self.temp)

        self.wait = QLabel('Total Wait Time: ')
        self.avg_time = QLabel('Average Wait Time: ')
        self.aborted = QLabel('Queries Aborted: ')
        row2.addWidget(self.wait)
        row2.addWidget(self.avg_time)
        row2.addWidget(self.aborted)

        mainLayout.addLayout(row1)
        mainLayout.addLayout(row2)
        self.setLayout(mainLayout)

    def update_stats(self, sn):
        try:
            print('Updating Stats')
            stats = sigi.get_all_instrum_stats(sn)
            self.serLbl.setText('Serial Number: ' + stats['serial'])
            self.bat.setText('Battery: ' + str(stats['bat'])[:4])
            self.humid.setText('Humidity: ' + str(stats['humid'])[:5])
            self.temp.setText('Board Temp: ' + str(stats['temp'])[:5])
            self.wait.setText('Total Wait Time: ' + str(stats['total_wait']))
            self.avg_time.setText('Average Wait Time: ' + str(stats['avg_q_time']))
            self.aborted.setText('Queries Aborted: ' + str(stats['aborted_q']))
        except Exception as e:
            log_error(str(e))


class operation_thread(QThread):
    finished = pyqtSignal()

    def __init__(self, func, params):
        super(operation_thread, self).__init__()
        self.func = func
        self.params = params

    def run(self):
        try:
            self.func(*self.params)
            self.finished.emit()
        except Exception as e:
            log_error(str(e))


class auto_update(QWidget):
    radio_button_changed = pyqtSignal()

    def __init__(self, parent, projectName):
        super().__init__()
        self.parent = parent
        self.projectName = projectName
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)
        self.stats_widget = instrum_stats()
        radLayout = self.init_radio()
        radScroll = QScrollArea()
        radWidget = QWidget()
        radWidget.setFixedWidth(250)
        radWidget.setLayout(radLayout)
        radScroll.setWidget(radWidget)
        radScroll.setMaximumWidth(290)
        radScroll.setMaximumHeight(250)
        mainLayout.addWidget(radScroll)
        rightCol = QVBoxLayout()
        rightCol.addWidget(self.stats_widget)
        tmLayout = QGridLayout()
        mainLayout.addLayout(rightCol)
        rightCol.addLayout(tmLayout)
        mainLayout.setStretchFactor(radScroll, 3)
        mainLayout.setStretchFactor(rightCol, 5)
        pathLbl = QLabel('Export Path: ')
        self.pathEdt = QLineEdit()
        self.pathEdt.editingFinished.connect(self.path_edt_changed)
        self.pathEdt.setText(sigi.get_project_path(projectName))
        self.dialogBtn = QPushButton('Browse')
        self.dialogBtn.clicked.connect(self.folder_dia)
        tmLayout.setRowStretch(0, 2)
        tmLayout.addWidget(pathLbl, 1, 0)
        tmLayout.addWidget(self.pathEdt, 1, 1)
        print('Added pathEdt')
        tmLayout.addWidget(self.dialogBtn, 1, 2)
        radWidget.setObjectName('radWidget')
        self.setStyleSheet('QWidget{color:rgb(140,140,140); background-color:rgb(77,78,79); font: 10pt Tw Cen MT; font-weight: bold; border-radius: 4px; padding:5px}\
                           QScrollBar::handle:vertical{border-radius: 2px; background-color:white} QScrollBar::add-page:vertical{background:none;} QScrollBar::sub-page:vertical{background:none;}\
                           QScrollBar::add-line:vertical{background-color:transparent; border-radius:5px; image: url(.//down.png)}\
                           QScrollBar::sub-line:vertical{background-color:transparent; border-radius:5px; image: url(.//up.png)}\
                                    QPushButton{color: white; padding: 5px; background-color:rgb(66,134,244); border-radius: 4px; font: Wide Latin; font-weight: bold}\
                                    QPushButton:hover{background-color:rgb(100,175,255)} QPushButton:pressed{background-color:rgb(17, 66, 122)}')
        print('finished tab init')

    def folder_dia(self):
        try:
            self.parent.parent.update_status('Selecting new path for current project', 'Yellow')
            self.folderDia = QFileDialog()
            options = self.folderDia.Options()
            options |= self.folderDia.ShowDirsOnly
            text = self.folderDia.getExistingDirectory(self, options=options)
            text += '/'
            text = text.replace('//', '/')
            self.pathEdt.setText(text)
            self.path_edt_changed()
            self.parent.parent.update_status('New Path Selected', 'Green')
        except Exception as e:
            log_error(str(e))
            self.parent.parent.update_status(str(e), 'red')

    def path_edt_changed(self):
        try:
            print('path edt changed...........')
            text = self.pathEdt.text()
            text = text.replace('//', '/')
            sigi.update_project_path(self.projectName, text)
        except Exception as e:
            log_error(str(e))
            self.parent.parent.update_status(str(e), 'Red')

    def init_radio(self):
        try:
            insts = sigi.get_sensors_by_project(self.projectName)
            radLayout = QVBoxLayout()
            self.radioGroup = QButtonGroup()
            self.radioGroup.setExclusive(False)
            radLayout = QVBoxLayout()

            for inst in insts:
                radioBt = radio_btn(*inst)
                self.radioGroup.addButton(radioBt)
                radioBt.setAutoExclusive(False)
                radioBt.setFixedHeight(20)
                radLayout.addWidget(radioBt)
                if inst[0] in sigi.get_auto_record_instrums():
                    radioBt.toggle()
                radioBt.state_changed.connect(self.radio)
                radioBt.right_click.connect(self.stats_widget.update_stats)
            radLayout.addStretch(1)
            return radLayout
        except Exception as e:
            log_error(str(e))
            self.parent.parent.update_status(
                'Error initiating radio buttons on project tab {} '.format(self.projectName) + str(e), 'Red')

    def radio(self, tup):
        try:
            sigi.update_auto_record(tup[0], tup[1])
        except Exception as e:
            log_error(str(e))
            self.parent.parent.update_status('Error updating auto record status for {} '.format(tup[0]) + str(e), 'Red')


class treeCombo(QComboBox):
    def __init__(self, items):
        super(treeCombo, self).__init__()
        model = QStandardItemModel()
        rootNode = model.invisibleRootItem()
        for proj in items.keys():
            newProj = QStandardItem(proj)
            if not proj == 'LIST':
                newProj.setSelectable(False)
            rootNode.appendRow(newProj)
            for sn in items[proj]:
                new_sn = QStandardItem(sn[0])
                new_sn.setData(sn[0])
                newProj.appendRow(new_sn)
        view = QTreeView()
        self.setView(view)
        self.setModel(model)
        view.header().hide()
        self.setModel(model)


class plot_widget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        mainLayout = QVBoxLayout()
        self.main_figure = MplFigure(self)
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.main_figure.canvas)
        mainLayout.addLayout(topLayout)
        self.setLayout(mainLayout)
        self.ax1 = self.main_figure.figure.add_subplot(1, 1, 1)
        self.main_figure.figure.tight_layout()
        self.main_figure.figure.subplots_adjust(bottom=0.2, top=1)
        self.ax1.set_facecolor((0.2, 0.2, 0.2))
        self.main_figure.canvas.draw()
        controlLayout = QHBoxLayout()
        mainLayout.addLayout(controlLayout)
        self.sns = sigi.get_sensors_by_project_dict()
        self.sns.update({'LIST': []})
        self.snCombo = treeCombo(self.sns)
        maxDt = datetime.datetime.now()
        minDt = datetime.datetime.now() - datetime.timedelta(days=1)
        self.dateBegin = QDateTimeEdit(QDateTime(minDt))
        self.dateBegin.setDisplayFormat('dd/MM/yyyy HH:mm:ss')
        self.dateBegin.setCalendarPopup(True)
        self.dateEnd = QDateTimeEdit(QDateTime(maxDt))
        self.dateEnd.setDisplayFormat('dd/MM/yyyy HH:mm:ss')
        self.dateEnd.setCalendarPopup(True)
        controlLayout.addWidget(self.dateBegin)
        controlLayout.addWidget(self.dateEnd)
        self.dateEnd.setMinimumDateTime(self.dateBegin.dateTime())
        self.dateBegin.setMaximumDateTime(self.dateEnd.dateTime())
        self.dateBegin.dateTimeChanged.connect(self.update_min_max)
        self.dateEnd.dateTimeChanged.connect(self.update_min_max)
        controlLayout.addWidget(self.snCombo)
        self.snCombo.currentIndexChanged.connect(self.update_min_max)
        radLayout = self.init_radio()
        topLayout.addLayout(radLayout)
        topLayout.setStretchFactor(radLayout, 0)
        topLayout.setStretchFactor(self.main_figure.canvas, 1)
        manualBtn = QPushButton('Manual API Query')
        manualBtn.clicked.connect(self.manual_from_db_threaded)
        controlLayout.addWidget(manualBtn)
        manualExp = QPushButton('Manual Export')
        manualExp.clicked.connect(self.manual_export_threaded)
        controlLayout.addWidget(manualExp)
        self.setStyleSheet('QWidget{color:rgb(140,140,140); background-color:rgb(77,78,79); font: 10pt Tw Cen MT; font-weight: bold; border-radius: 4px; padding: 5px}\
                                    QPushButton{color: white; padding: 5px; background-color:rgb(66,134,244); border-radius: 8px; font: Wide Latin; font-weight: bold}\
                                    QPushButton:hover{background-color:rgb(100,175,255)} QPushButton:pressed{background-color:rgb(17, 66, 122)}\
                                    QComboBox::down-arrow{image: url(.//down.png)}\
                                    QDateTimeEdit::down-arrow{image: url(.//down.png)}\
                                    QWidget::drop-down:button{border-radius:3px; width: 25px}\
                                    QWidget::drop-down\
                                    QScrollBar::handle:vertical{border-radius: 2px; background-color:white} QScrollBar::add-page:vertical{background:none;} QScrollBar::sub-page:vertical{background:none;}\
                                    QScrollBar::add-line:vertical{background-color:transparent; border-radius:5px; image: url(.//down.png)}\
                                    QScrollBar::sub-line:vertical{background-color:transparent; border-radius:5px; image: url(.//up.png)}')

    def manual_export(self):
        try:
            sn = self.snCombo.currentText()
            if sn == "LIST":
                sns = sigi.get_all_sensors()
                sn = self.parent.snList.toPlainText().split()
                sn = [x for x in sn if x in sns]
                print(sn)
                if len(sn) == 0:
                    self.parent.update_status('No recognizable serial numbers in LIST', 'Red')
                    return
            self.parent.update_status('Exporting Data for instruments {}'.format(str(sn)), 'Yellow')
            start_timestamp = self.dateBegin.dateTime().toPyDateTime()
            end_timestamp = self.dateEnd.dateTime().toPyDateTime()
            sigi.manual_export(sn, start_timestamp, end_timestamp)
            self.parent.update_status('Data export completed for instruments {}'.format(str(sn)), 'Green')
        except Exception as e:
            log_error(str(e))
            self.parent.update_status(str(e), 'Red')

    def manual_export_threaded(self):
        self.export_worker = operation_thread(self.manual_export, [])
        self.export_worker.start()

    def manual_from_db_threaded(self):
        self.worker = operation_thread(self.manual_get_data, [])
        self.worker.finished.connect(self.plot)
        self.worker.start()

    def plot(self):
        sn = self.snCombo.currentText()
        if sn == "LIST":
            return
        self.plot_preview(sn, self.dateBegin.dateTime().toPyDateTime(), self.dateEnd.dateTime().toPyDateTime())

    def manual_get_data(self):
        try:
            sn = self.snCombo.currentText()
            if sn == "LIST":
                sn = self.parent.snList.toPlainText().split()
                sns = sigi.get_all_sensors()
                sn = [x for x in sn if x in sns]

                if len(sn) == 0:
                    self.parent.update_status('No recognizable serial numbers in LIST', 'Red')
                    return
            self.parent.update_status('Querying Data for instruments {}'.format(str(sn)), 'Yellow')
            start_time = self.dateBegin.dateTime().toPyDateTime()
            end_time = self.dateEnd.dateTime().toPyDateTime()
            print('Manual Get Data Start: ', start_time)
            print('Manual Get Data End: ', end_time)
            sigi.manual_get_data(sn, start_time, end_time)
            self.parent.update_status('Data acquisition completed for instruments {}'.format(str(sn)), 'Green')
        except Exception as e:
            log_error(e)
            self.parent.update_status(str(e), 'Red')

    def init_radio(self):
        bts = ['intervals_R', 'intervals_L', 'intervals_V', 'intervals_T', 'transients_L', 'transients_T',
               'transients_V']
        print(bts)
        self.radioGroup = QButtonGroup()
        self.radioGroup.setExclusive(False)
        radLayout = QVBoxLayout()
        radLayout.addStretch(1)
        for bt in bts:
            radioBt = radio_btn(bt, '')
            self.radioGroup.addButton(radioBt)
            radioBt.setAutoExclusive(False)
            radioBt.toggle()
            radioBt.state_changed.connect(self.radio)
            radLayout.addWidget(radioBt)
        radLayout.addStretch(5)
        return radLayout

    def radio(self, tup):
        if tup[0] in self.lineDict.keys():
            self.lineDict[tup[0]].set_visible(tup[1])
        self.main_figure.canvas.draw()

    def update_min_max(self):
        print('update_min_max')
        self.dateEnd.setMinimumDateTime(self.dateBegin.dateTime())
        self.dateBegin.setMaximumDateTime(self.dateEnd.dateTime())
        if self.snCombo.currentText() == "LIST":
            return
        self.plot_preview(self.snCombo.currentText(), self.dateBegin.dateTime().toPyDateTime(),
                          self.dateEnd.dateTime().toPyDateTime())
        for btn in self.radioGroup.buttons():
            btn.state_changed.emit((btn.id, btn.isChecked()))

    def retreive_data(self, SN, date_st, date_end):
        self.worker = operation_thread(self.plot_preview, [SN, date_st, date_end])
        self.worker.start()

    def plot_preview(self, SN, date_st, date_end):
        try:
            self.parent.update_status('Plotting {} from {} to {}...'.format(SN, date_st, date_end), 'Yellow')
            print('Date_start_Plot: ', date_st)
            print('Date_end_Plot: ', date_end)
            inD, tD = sigi.data_to_plot(SN, date_st, date_end)
            self.parent.status.setText('Plotting in progress...')
            print('plotting for {}'.format(SN))
            self.ax1.clear()
            self.lineDict = {}
            if len(inD['L']) > 0:
                self.inter_val_R, = self.ax1.plot(*zip(*inD['R']), color='teal', label='intervals_R', alpha=0.7)
                self.inter_val_L, = self.ax1.plot(*zip(*inD['L']), color='purple', label='intervals_L', alpha=0.7)
                self.inter_val_T, = self.ax1.plot(*zip(*inD['T']), color='red', label='intervals_T', alpha=0.7)
                self.inter_val_V, = self.ax1.plot(*zip(*inD['V']), color='blue', label='intervals_V', alpha=0.7)
                # self.cursor=SnaptoCursor(self.ax1, data[0],data[4])
                # self.main_figure.canvas.mpl_connect('motion_notify_event', self.cursor.mouse_move)
            if len(tD['L']) > 0:
                self.trans_val_L = self.ax1.scatter(*zip(*tD['L']), color='purple', label='transients_L', alpha=0.7)
                self.trans_val_T = self.ax1.scatter(*zip(*tD['T']), color='red', label='transients_T', alpha=0.7)
                self.trans_val_V = self.ax1.scatter(*zip(*tD['V']), color='blue', label='transients_V', alpha=0.7)
        except Exception as e:
            log_error(str(e))
            self.parent.update_status(str(e), 'Red')
        lines = self.ax1.get_lines()
        lines.extend(self.ax1.collections)
        for lin in lines:
            self.lineDict[lin.get_label()] = lin
        self.ax1.set_xlim([self.dateBegin.dateTime().toPyDateTime(), self.dateEnd.dateTime().toPyDateTime()])
        bottom, top = self.ax1.get_ylim()
        if top < 0.2:
            self.ax1.set_ylim(top=0.2)
        try:
            self.ax1.legend(prop={'size': 8})
        except:
            pass
        self.ax1.grid()
        for x in self.ax1.get_xticklabels():
            x.set_rotation(15)
        self.main_figure.canvas.draw()
        self.parent.update_status('Finished plotting {}'.format(SN), 'Green')


class edit_tab_bar(QTabBar):
    def __init__(self, parent=None):
        super(edit_tab_bar, self).__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def mouseDoubleClickEvent(self, event):
        try:
            idx = self.currentIndex()
            self.edit_tab = idx
            rect = self.tabRect(idx)
            top_margin = 3
            left_margin = 6
            self.edit_line = QLineEdit(self)
            self.edit_line.show()
            self.edit_line.move(rect.left() + left_margin, rect.top() + top_margin)
            self.edit_line.resize(rect.width() - 2 * left_margin, rect.height() - 2 * top_margin)
            self.edit_line.setText(self.tabText(idx))
            self.edit_line.selectAll()
            self.edit_line.setFocus()
            self.edit_line.editingFinished.connect(self.finished_edit)
        except Exception as e:
            print(e)

    def finished_edit(self):
        try:
            self.setTabText(self.edit_tab, self.edit_line.text())
            self.parent().widget(self.edit_tab).project_name_changed(self.edit_line.text())
            self.edit_line.deleteLater()
        except Exception as e:
            print(e)


class project_tabs(QTabWidget):
    def __init__(self, parent):
        super(project_tabs, self).__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setTabBar(edit_tab_bar(self))
        self.parent = parent
        self.setStyleSheet('QTabBar::tab{color:rgb(140,140,140); background-color:rgb(77,78,79); font-size: 6pt; font-weight: bold; border-top-right-radius: 3px; border-top-left-radius: 3px; padding: 8px;}\
         QTabBar::tab:selected{background-color:rgb(40,40,40)}\
         QLineEdit{color:rgb(140,140,140); background-color:rgb(77,78,79); font: 8pt Tw Cen MT; font-weight: bold; border-radius: 2px}\
         QTabBar::tab:!selected:hover{background-color:rgb(60,60,60)}\
         QTabBar{qproperty-drawBase:0}\
         QTabWidget::pane{background-color:rgb(40,40,40); border-bottom-right-radius:5px; border-bottom-left-radius:5px}\
         QPushButton{color: white; padding: 5px; background-color:rgb(66,134,244);\ border-radius: 8px; font: Wide Latin; font-weight: bold}')
        self.init_from_API()

    def init_from_API(self):
        try:
            sigi.get_sensors()
            sigi.get_project_info()
            sigi.update_sensor_parameters()
            projects = sigi.get_project_names()
            for proj in projects:
                print('adding project tab: ', proj)
                newTabWidget = auto_update(self, proj)
                self.addTab(newTabWidget, proj)
        except Exception as e:
            log_error(str(e))
            self.parent.update_status(str(e), 'Red')

    def tabInserted(self, tabNum):
        try:
            new_tab = self.widget(tabNum)
            self.setCurrentIndex(tabNum)
        except Exception as e:
            log_error(str(e))
            self.parent.update_status(str(e), 'Red')


class readyTimer(QTimer):
    def __init__(self):
        super(readyTimer, self).__init__()
        self.ready = False


class ConfWindow(QWidget):
    def __init__(self):
        super(ConfWindow, self).__init__()
        try:
            self.setWindowTitle("Configuration")
            self.setBaseSize(400, 200)
            self.mainLayout=QVBoxLayout()
            self.setLayout(self.mainLayout)
            tokenLbl=QLabel("API Token: ")
            self.tokenEdt=QLineEdit()
            tokenLayout=QHBoxLayout()
            tokenLayout.addWidget(tokenLbl)
            tokenLayout.addWidget(self.tokenEdt)
            self.mainLayout.addLayout(tokenLayout)
            apiButton=QPushButton("Apply")
            apiButton.clicked.connect(self.update_token)
            tokenLayout.addWidget(apiButton)
            self.timezoneCombo=QComboBox()
            self.timezoneCombo.addItems(pytz.all_timezones)
            self.timezoneCombo.setCurrentText(sigi.get_base_timezone())
            timezoneLbl=QLabel("Base Time Zone")
            timezoneLayout=QHBoxLayout()
            timezoneLayout.addWidget(timezoneLbl)
            timezoneLayout.addWidget(self.timezoneCombo)
            self.mainLayout.addLayout(timezoneLayout)
            self.show()
        except Exception as e:
            print(e)

    def update_token(self):
        try:
            sigi.set_token(self.tokenEdt.text())
            sigi.set_base_timezone(self.timezoneCombo.currentText())
            self.close()
        except Exception as e:
            print(e)




WINDOW_SIZE = 1000, 700


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, *WINDOW_SIZE)
        self.setWindowTitle('Sigicom Data Handler')
        self.setMinimumHeight(550)
        self.setMinimumWidth(950)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        view = custom.dragView(self)
        mainLayout = QVBoxLayout()
        view.setLayout(mainLayout)
        sizeGrip = QSizeGrip(self)
        bannerLayout = QHBoxLayout()
        sixense = QPixmap('sixenseLogo.png')
        sixense = sixense.scaledToHeight(30)
        sixenseLbl = QLabel()
        sixenseLbl.setPixmap(sixense)
        sixenseLbl.setMask(sixense.mask())
        logoShine = QGraphicsDropShadowEffect()
        logoShine.setBlurRadius(10)
        logoShine.setOffset(0, 0)
        sixenseLbl.setGraphicsEffect(logoShine)
        sixenseLbl.setMaximumHeight(30)
        sixenseLbl.setMinimumHeight(30)
        logoShine.setColor(QColor(66, 134, 244))
        bannerLayout.addWidget(sixenseLbl)
        closeBtn = QPushButton('X')
        closeBtn.setObjectName('closeBtn')
        closeBtn.clicked.connect(self.close)
        minBtn = QPushButton('_')
        minBtn.setObjectName('minBtn')
        minBtn.clicked.connect(self.min_window)
        bannerLayout.addStretch(1)
        bannerLayout.addWidget(minBtn)
        bannerLayout.addWidget(closeBtn)
        resizeLayout = QVBoxLayout()
        resizeLayout.addWidget(sizeGrip, 0, Qt.AlignTop | Qt.AlignLeft)
        bannerLayout.addLayout(resizeLayout)
        bannerLayout.setStretchFactor(resizeLayout, 0)
        self.status = QLabel()
        mainLayout.addLayout(bannerLayout)
        mainLayout.setStretchFactor(bannerLayout, 0)
        self.plot_window = plot_widget(self)
        mainLayout.addWidget(self.plot_window)
        mainLayout.setStretchFactor(self.plot_window, 4)
        self.tabs = project_tabs(self)
        tabsLayout = QHBoxLayout()
        tabsLayout.addWidget(self.tabs)
        self.snList = QPlainTextEdit()
        tabsLayout.addWidget(self.snList)
        tabsLayout.setStretchFactor(self.tabs, 7)
        tabsLayout.setStretchFactor(self.snList, 1)
        mainLayout.addLayout(tabsLayout)
        mainLayout.setStretchFactor(tabsLayout, 3)
        self.clearBtn = QPushButton('Clear DB')
        self.clearBtn.clicked.connect(self.clear_db)
        self.clearBtn.setObjectName('closeBtn')
        bottomBannerLayout = QHBoxLayout()
        bottomBannerLayout.addWidget(self.status)
        bottomBannerLayout.addStretch(1)
        bottomBannerLayout.addWidget(self.clearBtn)
        mainLayout.addLayout(bottomBannerLayout)
        self.setStyleSheet(' QMainWindow{border-radius: 3px} QVBoxLayout{padding: 0px; background-color:red}'
                           'QPlainTextEdit{color:rgb(140,140,140); background-color:rgb(77,78,79); font: 10pt Tw Cen '
                           'MT; font-weight: bold; border-radius: 4px; padding: 5px} '
                           '#setupView{margin:0px; padding:0px} #taskList{background-color:rgb(77,78,'
                           '79)} QGraphicsView{background-color:rgb(50,50,50); border-radius: 3px} '
                           '#closeBtn{color: white; padding: 5px; background-color:rgb(247, 34, 73); border-radius: '
                           '8px; font: Wide Latin; font-weight: bold} '
                           '#closeBtn:hover{background-color:rgb(255, 54, 93)} #closeBtn::pressed{'
                           'background-color:rgb(168, 0, 0)} #minBtn::pressed{background-color:rgb(17, 66, 122)} '
                           '#minBtn{color: white; padding: 5px; background-color:rgb(66,134,244); border-radius: 8px; '
                           'font: Wide Latin; font-weight: bold} #minBtn:hover{background-color:rgb(75,150,250)} '
                           'QDateTimeEdit(color:rgb(140,140,140); background-color:rgb(77,78,79); font: 10pt Tw Cen '
                           'MT; font-weight: bold; border-radius: 8px; padding: 5px}')
        self.setCentralWidget(view)
        self.timer = readyTimer()
        self.timer.start(60000)
        self.timer.timeout.connect(self.check_time_threaded)
        qApp.aboutToQuit.connect(self.timer.stop)



    def clear_old_data(self):
        try:
            if self.clear_timer.ready and datetime.datetime.now().minute == 16:
                self.update_status('Clearing week old data to maintain data base performance', 'Yellow')
                sigi.clear_old_data()
                self.clear_timer.ready = False
            if not self.clear_timer.ready and datetime.datetime.now().minute != 16:
                self.clear_timer.ready = True
        except Exception as e:
            log_error('Error while clearing old data ' + str(e))
            self.update_status('Error while clearing week old data ' + str(e), 'Red')

    def update_status(self, text, color):
        self.status.setStyleSheet("color: {}".format(color))
        self.status.setText(text)

    def check_time_threaded(self):
        try:
            if not (hasattr(self, 'worker') and self.worker.isRunning()):
                self.update_status('Running auto acquisition process', 'Yellow')
                self.worker = operation_thread(sigi.auto_acq, [])
                self.worker.finished.connect(self.auto_acq_done)
                self.worker.start()
            else:
                print('Auto Acq is still running, no new instance created')
        except Exception as e:
            log_error(str(e))
            self.update_status(str(e), 'Red')

    def auto_acq_done(self):
        self.update_status('Auto acquisition process complete', 'Green')
        try:
            if self.timer.ready and datetime.datetime.now().hour == 12:
                self.update_status('Clearing week old data to maintain data base performance', 'Yellow')
                sigi.clear_old_data()
                self.timer.ready = False
            if not self.timer.ready and datetime.datetime.now().hour != 12:
                self.timer.ready = True
        except Exception as e:
            log_error('Error while clearing old data ' + str(e))
            self.update_status('Error while clearing week old data ' + str(e), 'Red')

    def clear_db(self):
        try:
            self.update_status('Re-initializing data base', 'Yellow')
            sigi.create_db()
            self.update_status('Re-loading data from the API', 'Yellow')
            sigi.get_sensors()
            sigi.get_project_info()
            sigi.update_sensor_parameters()
            self.update_status('Finished clearing the data base and loading data from the API', 'Green')
        except Exception as e:
            log_error(str(e))
            self.update_status(str(e), 'Red')

    def min_window(self):
        self.setWindowState(Qt.WindowMinimized)

    def keyPressEvent(self, event):
        print(event.key(), int(event.modifiers()))
        if event.key()==72 and int(event.modifiers())==Qt.CTRL:
            self.confWindow=ConfWindow()
        else:
            super(QMainWindow, self).keyPressEvent(event)

    def closeEvent(self,event):
        try:
            if hasattr(self,"confWindow"):
                self.confWindow.close()
            super(QMainWindow, self).closeEvent(event)
        except Exception as e:
            print(e)



if __name__ == '__main__':
    app = QApplication([])
    splash_pix = QPixmap('splash.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    splash.showMessage(
        "<h1><font color='white'>Sigicom Data Handler 1.3</font></h1><p></p><h3><font color='white'>Sixense</font></h3>")
    app.processEvents()

    window = MainWindow()
    window.show()
    splash.finish(window)
    app.exec_()
    sys.exit()
