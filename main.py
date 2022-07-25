import sys
import pyVideoSDK
from pyVideoSDK.methods import Methods
from pyVideoSDK.consts import EVENT, METHOD_RESPONSE
import pyVideoSDK.consts as C
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import screeninfo
import time
from enum import Enum
import wstyle
from datetime import datetime

# ========================
# Configuration
# ========================
ROOM_IP: str = "127.0.0.1"
ROOM_PORT: int = 2233
PIN: str = "123"

# ========================

BUTTON_WIDTH: int = 160
BUTTON_HEIGHT: int = 90
INDENT: int = 100

MONITOR: int = 0
CALL_ID: str = "azobov@team.trueconf.com"
IMAGE_BUTTON: str = "call.png"

sdk = pyVideoSDK.open_session(ip = ROOM_IP, port = ROOM_PORT, pin = PIN, debug = True)
methods = Methods(sdk)

class KioskButton(QWidget):
    def __init__(self, monitor: int):
        super().__init__()

        self.layout = None
        self.room = None
        self.displayName = ""
        self.buttonCall = None
        self.buttonCallTag = False
        if monitor >= len(screeninfo.get_monitors()) or monitor < 0:
            monitor = 0
        self.monitor = screeninfo.get_monitors()[monitor]
        self.state = 0
        self.initUI()

    def initUI(self):
        # Setting layout
        self.layout = QVBoxLayout(self)
        # Position
        self.setPosition()

        # Frameless window
        self.setWindowFlags(Qt.WindowStaysOnTopHint 
            | Qt.X11BypassWindowManagerHint | Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Show
        self.show()
        # connectToRoom
        self.connectToRoom()
        # Button
        self.buttonCall = self.addButton(style = wstyle.STYLE_GRAY_BUTTON, icon = IMAGE_BUTTON)
        # flashing timer
        self.timer = QTimer(self, interval = 500)
        self.timer.timeout.connect(self.flashing)
        self.timer.start()

    def setPosition(self):
        # calc window size & position
        width: int = 200
        height: int = 120
        leftCoord: int = self.monitor.x + self.monitor.width - width - INDENT
        topCoord: int = self.monitor.y + self.monitor.height - height - INDENT

        # set position
        print(f'{leftCoord=}, {topCoord=}, {width=}, {height=}')
        self.setGeometry(leftCoord, topCoord, width, height)

    def flashing(self):
        if self.state == 3:
            if self.buttonCallTag:
                self.buttonCall.setStyleSheet(wstyle.STYLE_GREEN_BUTTON_FLASH)
            else:
                self.buttonCall.setStyleSheet(wstyle.STYLE_GREEN_BUTTON)

        self.buttonCallTag = not self.buttonCallTag

    def addButton(self, style: str, icon: str):
        button = QPushButton()
        button.setStyleSheet(style)
        button.setFixedWidth(BUTTON_WIDTH)
        button.setFixedHeight(BUTTON_HEIGHT)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.layout.addWidget(button)
        self.layout.setAlignment(button, Qt.AlignRight | Qt.AlignBottom)

        if icon:
            button.setIcon(QIcon(icon))
            sizeIcon: int = 48
            button.setIconSize(QSize(sizeIcon, sizeIcon))

        button.clicked.connect(self.on_click_call)
        return button

    def connectToRoom(self):
        pass

    def on_state_change(self, response):
        try:
            self.state = response["appState"]
            print(f'onChangeState( {self.state} )')

            # Button color
            if self.state == 3:
                style = wstyle.STYLE_GREEN_BUTTON 
            elif self.state in [4, 5]:
                style = wstyle.STYLE_RED_BUTTON
            else:
                style = wstyle.STYLE_GRAY_BUTTON
            self.buttonCall.setStyleSheet(style)

            if self.state in [4, 5]:
                methods.showMainWindow(True, stayOnTop = False)  # Maximized
            else:
                methods.showMainWindow(False) # Minimized, Hiden
        except Exception as e:
            print(f'Exception "{e.__class__.__name__}" in {__file__}:{sys._getframe().f_lineno}: {e}')

    @pyqtSlot()
    def on_click_call(self):
        self.displayName = self.sender().text
        if self.state == 3:
            methods.call(CALL_ID)
        else:
            methods.hangUp(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    call_button = KioskButton(MONITOR)
    
    # Add handlers
    sdk.add_handler(EVENT[C.EV_appStateChanged], call_button.on_state_change)
    sdk.add_handler(METHOD_RESPONSE[C.M_getAppState], call_button.on_state_change)
    # Request the current state
    methods.getAppState()

    sys.exit(app.exec_())