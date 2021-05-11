# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 09:39:59 2019

@author: hayden.flake
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class dragView(QGraphicsView):
    def __init__(self,parent):
        super(dragView,self).__init__()
        self.parent=parent
    
    def mousePressEvent(self,event):
        self.m_old_pos = event.globalPos();
        self.m_mouse_down = event.button()== Qt.LeftButton;

    def mouseMoveEvent(self,event):
        if event.buttons()==Qt.LeftButton:
            currPos=self.parent.mapToGlobal(self.parent.pos())
            globalPos=event.globalPos()
            diff=globalPos-self.m_old_pos
            newPos=self.parent.mapFromGlobal(currPos+diff)
            self.m_old_pos=event.globalPos()
            self.parent.move(newPos)

    def mouseReleaseEvent(self,event):
        self.m_mouse_down=False;




class coolButton(QPushButton):
    def __init__(self,text):
        super(coolButton,self).__init__()
        self.setText(text)
        self.setObjectName('coolButton')
        self.setStyleSheet('#coolButton{border-radius:4px; padding: 5px; \
                           color: white; selection-color: rgb(30,70,120);background-color:rgb(66,134,244)} #coolButton:hover{background-color:rgb(75,150,250)}')
        self.effect=QGraphicsDropShadowEffect()
        self.effect.setColor(QColor(66,134,244))
        self.effect.setOffset(0,0)
        self.effect.setBlurRadius(20)
        self.setGraphicsEffect(self.effect)
        #self.update()
        
    def update(self):
        if not self.isEnabled():
            self.effect.setBlurRadius(0)
        else:
            self.effect.setBlurRadius(20)
    
    def changeEvent(self,event):
        if event.type()==98:
            if not self.isEnabled():
                self.effect.setBlurRadius(0)
                self.setStyleSheet('#coolButton:disabled{background-color: rgb(87,88,89); color:grey} #coolButton:hover{background-color:rgb(75,150,250)}')
            else:
                self.effect.setBlurRadius(20)
                self.setStyleSheet('#coolButton:enabled{background-color:rgb(66,134,244);color: white} #coolButton:hover{background-color:rgb(75,150,250)}')
    
    def mousePressEvent(self,event):
        if self.isEnabled():
            self.effect.setColor(QColor(247, 34, 73))
            #self.setStyleSheet('#coolButton:pressed{background-color:rgb(33,70,120)}')

            
    def mouseReleaseEvent(self,event):
        if self.isEnabled():
            self.effect.setColor(QColor(66,134,244))
            #self.setStyleSheet('#colorButton:!pressed{background-color:rgb(66,134,244)}')
            self.clicked.emit()
        


class glowButton(QLabel):
    def __init__(self,pixmap,pixHeight,color):
        super(glowButton,self).__init__()
        self.pixmap=pixmap
        #self.pixmap=QImage(pixmap)
        self.pixHeight=pixHeight
        self.color=QColor(color[0],color[1],color[2])
        self.partner=None
        self.negative()
        self.initWidget()
        self.state=True
    
    def initWidget(self):
        self.pixmap=self.pixmap.scaledToHeight(self.pixHeight)
        #self.setCentralWidget(self.pixmap)
        self.setPixmap(self.pixmap)
        
        self.effect = QGraphicsDropShadowEffect()
        self.effect.setColor(self.color)
        self.effect.setOffset(0, 0)
        self.effect.setBlurRadius(20)
        self.setGraphicsEffect(self.effect)
        self.setMask(self.pixmap.mask())
        
    def setChecked(self,val):
        if self.isChecked()==val:
            return
        self.toggle()
            
        
    def negative(self):
        img=QImage(self.pixmap)
        img.invertPixels()
        self.pixmap=QPixmap(img)
    
    def mousePressEvent(self,event):
        self.toggle()
        print('glowButton state is: {}'.format(str(self.state)))
    
    def isChecked(self):
        return self.state
    
    def toggle(self):
        if not self.partner:
            if self.state:
                self.state=False
            else:
                self.state=True
            self.update()
        else:
            if self.state and not self.partner.state:
                self.state=False
                self.partner.state=True
            else:
                if self.state:
                    self.state=False
                else:
                    self.state=True
            self.update()
            self.partner.update()
        
    def update(self):
        if self.state:
            self.effect.setBlurRadius(20)
        else:
            self.effect.setBlurRadius(0)
            
    def pairWith(self,partner):
        self.partner=partner
        self.partner.partner=self

        
class fontWindow(QMainWindow):
    def __init__(self):
        super(fontWindow,self).__init__()
        self.view=QWidget()
        self.scrollView=QScrollArea()
        self.scrollView.setWidget(self.view)
        self.scrollView.setWidgetResizable(True)
        self.setCentralWidget(self.scrollView)
        self.mainLayout=QVBoxLayout()
        self.view.setLayout(self.mainLayout)
        lbl=QLabel('Here are the fonts:')
        self.mainLayout.addWidget(lbl)
        name='a'
        for font in QFontDatabase().families():
        #for font in range(0,20):
            print(font)
            self.newLabel=QLabel(str(font))
            self.newLabel.setMinimumHeight(15)
            #newName=font.replace(' ','')
            self.newLabel.setObjectName(name)
            self.newLabel.setStyleSheet('#'+name+'{font: '+font+'}')
            name+='a'
            self.mainLayout.addWidget(self.newLabel)
        #self.view.setStyleSheet('QLabel{font: Vladimir Script}')
            
    def show_window(self):
        self.show()
                
