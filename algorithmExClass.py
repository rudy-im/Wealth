#-*- coding : utf-8 -*-

import time, threading
from WealthAlgorithm import *

class algorithmExClass(WealthAlgorithm):
    def __init__(self, kiwoom, infoUpdater):
        super().__init__(kiwoom, infoUpdater)
        
    def algorithm(self):
        print('algorithm')

    
