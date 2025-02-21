import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from Kiwoom import *
from WealthUI import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.commConnect()
    wealthUI = WealthUI(kiwoom)
    wealthUI.show()

