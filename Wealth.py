#-*- coding : utf-8 -*-

import sys, threading, time
import sqlite3
import sqlite3Util as sUtil
import timeUtil as tUtil
from Kiwoom import *
from KiwoomUtil import *
from WealthUI import *
from pandas import DataFrame



class Wealth(KiwoomUtil):

    def __init__(self):
        
        super().__init__()

        # 테스트용 print 여부
        self.testFlag = False

        # 자동 로그인
        self.commConnect()



######################################################################################
# Event 함수 overriding
######################################################################################



    # (이벤트) 로그인 성공 시 알림
    def eventConnect(self, err_code):

        super().eventConnect(err_code)

        # UI 세팅
        self.ui = WealthUI()
        self.uiSetup()
        self.ui.show()



######################################################################################
# 
######################################################################################        



    # WealthUI에 balance, balancepool, orderpool 세팅
    def uiSetup(self):

        self.ui.showBalance(self.balance)
        self.ui.showBalancepool(self.balancepool)
        self.ui.showOrderpool(self.orderpool)

    

        

        
