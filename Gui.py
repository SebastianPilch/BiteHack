from __future__ import annotations

import math
from typing import *
import sys
import os

from PyQt5.QtWidgets import QPushButton, QWidget, QApplication
from matplotlib import figure
from matplotlib.backends.qt_compat import QtCore, QtWidgets
# from PyQt5 import QtWidgets, QtCore

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib as mpl
import numpy as np
import serial
import re

idx = 0
rotate = False
distance = 0
ser = serial.Serial('COM7', 9600, timeout=1)
set_of_distance = []

class ApplicationWindow(QtWidgets.QMainWindow):
    '''
    The PyQt5 main window.

    '''

    def __init__(self):
        super().__init__()

        # Place buttons

        self.app = QApplication(sys.argv)
        self.widget = QWidget()
        self.button1 = QPushButton(self.widget)
        self.button1.setText("Button1")
        self.button1.clicked.connect(button1_clicked)
        self.button2 = QPushButton(self.widget)
        self.button2.setText("Button2")

        # Window settings
        self.setGeometry(300, 300, 800, 400)
        self.setWindowTitle("Control Panel")
        self.frm = QtWidgets.QFrame(self)
        self.frm.setStyleSheet("QWidget { background-color: #65738a; }")
        self.lyt = QtWidgets.QGridLayout()
        self.frm.setLayout(self.lyt)
        self.setCentralWidget(self.frm)

        # Place matplotlib figures
        self.myFig = JustPlot(x_len=200, y_range=[0, 300], interval=20, name='Distance', num=0)
        self.myFig2 = JustPlot(x_len=200, y_range=[-200, 200], interval=20, name='Temperature', num=1)
        self.Scatter = ScatterPlot(len = 180, range=300, name='Distance_Pole', num=2)
        self.Temp_Al = JustPlot(x_len=100, y_range=[-0.2, 1.2], interval=20, name='Temperature Alarm', num=3)
        self.lyt.addWidget(self.myFig, 0,0)
        self.lyt.addWidget(self.Scatter, 0, 1)
        self.lyt.addWidget(self.myFig2, 1, 0)
        self.lyt.addWidget(self.button1, 2,0)
        self.lyt.addWidget(self.button2, 3,0)
        self.lyt.addWidget(self.Temp_Al, 1, 1)

        # Show
        self.show()
        return

class JustPlot(FigureCanvas):
    '''
    This is the FigureCanvas in which the live plot is drawn.

    '''

    def __init__(self, x_len: int, y_range: List, interval: int, name: str, num: int) -> None:
        '''
        :param x_len:       The nr of data points shown in one plot.
        :param y_range:     Range on y-axis.
        :param interval:    Get a new datapoint every .. milliseconds.
        :param interval:    Name of the plot

        '''
        super().__init__(figure.Figure())
        # Range settings
        self._x_len_ = x_len
        self._y_range_ = y_range
        self._name_ = name
        self._num_ = num

        # Store two lists _x_ and _y_
        self._x_ = list(range(0, x_len))
        self._y_ = [0] * x_len
        self.figure.set_facecolor('#65738a')

        # Store a figure ax
        self._ax_ = self.figure.subplots()
        self._ax_.set_facecolor("#8997ad")

        # Initiate the timer
        self._timer_ = self.new_timer(interval, [(self._update_canvas_, (), {})])
        self._timer_.start()
        return

    def _update_canvas_(self) -> None:
        '''
        This function gets called regularly by the timer.

        '''
        if not rotate:
            self._y_.append(round(get_next_datapoint(), 2))  # Add new datapoint
            self._y_ = self._y_[-self._x_len_:]  # Truncate list _y_
            self._ax_.clear()  # Clear ax
            self._ax_.plot(self._x_, self._y_, color='k')  # Plot y(x)
            self._ax_.set_ylim(ymin=self._y_range_[0], ymax=self._y_range_[1])
            self._ax_.set_title(self._name_)
            self._ax_.grid()

            self.draw()
        return


class ScatterPlot(FigureCanvas):
    '''
        This is the FigureCanvas in which the live plot is drawn.

        '''

    def __init__(self, len: int, range: int, name: str, num: int) -> None:
        '''
            :param x_len:       The nr of data points shown in one plot.
            :param y_range:     Range on y-axis.
            :param interval:    Get a new datapoint every .. milliseconds.
            :param interval:    Name of the plot

            '''
        super().__init__(figure.Figure())
        # Range settings
        self._len_ = len
        self._range_ = range
        self._name_ = name
        self._num_ = num

        # Store two lists _x_ and _y_
        self._x_ = [0] * len
        self._y_ = [0] * len
        self.figure.set_facecolor('#65738a')

        # Store a figure ax
        self._ax_ = self.figure.subplots()
        self._ax_.set_facecolor("#8997ad")

        # Initiate the timer

        self._update_canvas2_()
        return

    # show data

    def _update_canvas2_(self) -> None:
        '''
            This function gets called regularly by the timer.

            '''
        global rotate
        if rotate:
            for i, elem in enumerate(set_of_distance):
                cord = coords(elem)
                self._y_.append(cord[1])
                self._x_.append(cord[0])
                self._y_ = self._y_[-self._len_:]  # Truncate list _y_
                self._x_ = self._x_[-self._len_:]
                self._ax_.clear()  # Clear ax
                self._ax_.plot(self._x_, self._y_, color='k', size = 2)  # Plot y(x)
                self._ax_.set_ylim(ymin=-self._range_, ymax=self._range_)
                self._ax_.set_xlim(xmin=-self._range_, xmax=self._range_)
                self._ax_.set_title(self._name_)
                self.draw()
            rotate = False
        return


def button1_clicked():
    global rotate
    global set_of_distance
    rotate = True
    # ser.write('r'.encode())
    ser.write('t'.encode())
    arduino_data = ser.readline()
    while len(arduino_data) < 100:
        arduino_data = ser.readline()
    str_data = str(arduino_data)
    if len(str_data) > 3:
        set_of_distance = [int(s) for s in re.findall(r'\b\d+\b', str_data)]
        print(len(set_of_distance))


def get_next_datapoint():
    global distance

    ser.write('m'.encode())
    arduino_data = ser.readline()
    str_data = str(arduino_data)
    if len(str_data) > 3:
        values = [int(s) for s in re.findall(r'\b\d+\b', str_data)]
        distance = values[0]

    return distance

def coords(current_distance):
    global idx
    round_angle = 2 * math.pi
    current_angle = round_angle / 180 * idx
    idx += 1
    x_ = np.sin(current_angle) * current_distance
    y_sin = np.cos(current_angle) * current_distance
    return x_, y_sin


if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    app = ApplicationWindow()
    qapp.exec_()
