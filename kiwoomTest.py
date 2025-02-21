import sys, time, threading
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from Kiwoom import *
from KiwoomUtil import *
import sqlite3Util as sUtil
from WealthUI import *
from pandas import Series, DataFrame

kiwoom = None
KUtil = None

def checkOrder():
    trcode = 'opt10075'
    inputdic = {'계좌번호' : kiwoom.account[0],
                '체결구분' : '0',
                '매매구분' : '0'}
    outputs = ['주문번호', '종목코드', '주문상태', '매매구분', '주문수량', '체결량', "미체결수량",
               '단위체결가', '당일매매수수료', '당일매매세금', "원주문번호", "업무구분"]

    outputs = []

    df = KUtil.kiwoomRequest(KUtil.getRqname(), trcode, inputdic, outputs)

    print(df)


def tmp():
    while True:
        checkOrder()
        time.sleep(1)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.commConnect()
    KUtil = KiwoomUtil(kiwoom)

    inputdic = {'계좌번호' : kiwoom.account[0],
                '비밀번호' : '',
                '비밀번호입력매체구분' : '00',
                '조회구분' : '2'}
                
    #df = KUtil.kiwoomRequest('rq', 'opw00001', inputdic)


    #KUtil.saveStocksCodeName()
    #print(len(KUtil.queryByMargin(20)))

    
    #KUtil.setRealtime(KUtil.queryByMargin(20))

    #print(KUtil.getNowPrice('000020'))
    
    
    code = '000020'
    price = KUtil.getSellPriceMinus(code)
    quantity = 1

    #kiwoom.sendOrder(KUtil.getRqname(), '0101', kiwoom.account[0], 1, code, quantity, price, '00', '')
    
    #orderNo = KUtil.sell(KUtil.getRqname(), code, price, quantity)

    #time.sleep(0.5)
    
    #print(KUtil.changeBuy(KUtil.getRqname(), orderNo, code, KUtil.getNowPrice(code), 10))

    #checkOrder(kiwoom, KUtil)

    #print(KUtil.cancelSell(KUtil.getRqname(), orderNo, code))

    #time.sleep(0.5)

    #checkOrder()

    th = threading.Thread(target = tmp)
    th.start()
    th.join()

    print('a')
    



