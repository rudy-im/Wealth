import sys, time, threading, sched
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from Kiwoom import *
from KiwoomUtil import *
from GetKiwoomChart import *
from Wealth import *
import sqlite3Util as sUtil
from pandas import Series, DataFrame
from AlgorithmThread import *

kiwoom = None
KUtil = None

def checkOrder():
    trcode = 'opt10075'
    inputdic = {'계좌번호' : kiwoom.account[0],
                '체결구분' : '0',
                '매매구분' : '0'}
    outputs = ['주문번호', '종목코드', '주문상태', '매매구분', '주문수량', '체결량', "미체결수량",
               '단위체결가', '당일매매수수료', '당일매매세금', "원주문번호", "업무구분"]

    outputs = ['종목코드']

    df = KUtil.kiwoomRequest(KUtil.getRqname(), trcode, inputdic, outputs)

    return df


def opt10075Test():
    trcode = 'opt10075'
    inputdic = {'계좌번호' : kiwoom.account[0],
                '체결구분' : '0',
                '매매구분' : '0'}
    outputs = ['주문번호', '종목코드', '주문상태', '매매구분', '주문수량', '체결량', "미체결수량",
               '단위체결가', '당일매매수수료', '당일매매세금', "원주문번호", "업무구분"]

    outputs = ['종목코드']

    next = 0
    screen_no = '1010'
    rqname = KUtil.getRqname()

    for k, v in inputdic.items():
        kiwoom.setInputValue(k, v)
    
    kiwoom.commRqData(rqname, trcode, next, screen_no, outputs)


def opw00001Test():
    
    rqname = KUtil.getRqname()
    trcode = 'opw00001'
    inputdic = {'계좌번호' : KUtil.account,
                '비밀번호' : '',
                '비밀번호입력매체구분' : '00',
                '조회구분' : '2'}
    outputs = ["d+1추정예수금", "d+1매도매수정산금", "d+1출금가능금액",
               "d+2추정예수금", "d+2매도매수정산금", "d+2출금가능금액"]

    next = 0
    screen_no = '1010'

    for k, v in inputdic.items():
        KUtil.setInputValue(k, v)
    
    KUtil.commRqData(rqname, trcode, next, screen_no)


def OPT10019Test():
    trcode = 'OPT10019'
    inputdic = {'시장구분' : '000',
                '등락구분' : '1',
                '시간구분' : '1',
                '시간' : '10',
                '거래량구분' : '00100',
                '종목조건' : '5',
                '신용조건' : '0',
                '가격조건' : '0',
                '상하한포함' : '1'}
    outputs = ["종목코드", "등락률"]

    next = 0
    screen_no = '1010'
    rqname = KUtil.getRqname()

    for k, v in inputdic.items():
        kiwoom.setInputValue(k, v)
                
    kiwoom.commRqData(rqname, trcode, next, screen_no, outputs)


def buytest():
    rqname = KUtil.getRqname()
    screenNo = '0101'
    code = '000020'
    quantity = 10
    price = KUtil.getBuyPricePlus(code)

    print(rqname)
    print(price)
    
    KUtil.buy(rqname, code, price, quantity)


def selltest():
    rqname = KUtil.getRqname()
    screenNo = '0101'
    code = '000020'
    quantity = 10
    price = KUtil.getSellPriceMinus(code)

    print(rqname)
    print(price)
    
    KUtil.sell(rqname, code, price, quantity)


def sutiltest():
    con = sqlite3.connect('stocks.db')
    selected = sUtil.select('stocks', con, 'code', limit=100)
    codes = list(selected['code'])
    con.close()
    ret = KUtil.findByMargin(codes, withName=True)
    print(ret)


def trtest():
    code = '000020'
    tick = 5
    modified = 1
    
    rqname = KUtil.getRqname()
    trcode = 'opt10080'
    inputdic = {'종목코드' : code, '틱범위' : tick, '수정주가구분' : modified}
    outputs = ['체결시간', '시가', '고가', '저가', '종가', '거래량']

    df = KUtil.kiwoomRequest(rqname, trcode, inputdic, outputs)
    print(df)


def trtest2():

    code = '000020'

    rqname = KUtil.getRqname()
    trcode = 'opw00001'
    inputdic = {'계좌번호' : KUtil.account,
                '비밀번호' : '',
                '비밀번호입력매체구분' : '00',
                '조회구분' : '1'}
    outputs = ["d+1추정예수금", "d+1매도매수정산금", "d+1출금가능금액",
                   "d+2추정예수금", "d+2매도매수정산금", "d+2출금가능금액"]

    df = KUtil.kiwoomRequest(rqname, trcode, inputdic, outputs)
    print(df)
    

def wait():
    for i in range(5):
        time.sleep(1)
        print('buy')
        buytest()
        time.sleep(1)
        print('sell')
        selltest()
        
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    #KUtil = KiwoomUtil()
    #KUtil.commConnect()

    gkc = GetKiwoomChart()
    gkc.commConnect()
    gkc.saveDayChart('217480')
    
    

    
    
    





    
