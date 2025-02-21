from KiwoomUtil import *
from PyQt5.QtCore import *
import time, threading


# 시그널 전용 클래스
# thread 내에서 바로 kiwoom 호출 시 컨텍스트 문제 발생
# 따라서, 시그널을 보내 kiwoom 함수를 다른 클래스에서 호출하게 함
class SignalClass(QObject):
    signal = pyqtSignal(str)


class TmpSignal(threading.Thread):

    def __init__(self, slot):

        super().__init__()

        # 시그널 객체 처리
        # self.signal.emit('알고리즘클래스 내에서 함수 사용 형식')
        self.sc = SignalClass()
        
        self.signal = self.sc.signal
        self.signal.connect(slot.executeSignal)

    def run(self):

        self.signal.emit('self.changetest()')

        
        

class TmpSlot():

    def __init__(self, KUtil):
        
        self.KUtil = KUtil


    # kiwoom 함수는 외부 스레드에서 호출 시 컨텍스트 오류 발생.
    # 따라서 시그널을 보내 본 클래스에서 함수를 호출하도록 함.
    @pyqtSlot(str)
    def executeSignal(self, signal):
        print(signal)
        exec(signal)


    def buytest(self):
        rqname = self.KUtil.getRqname()
        code = '000020'
        quantity = 10
        price = self.KUtil.getBuyPricePlus(code)
        
        self.KUtil.buy(rqname, code, price, quantity)


    def selltest(self):
        rqname = self.KUtil.getRqname()
        code = '000020'
        quantity = 10
        price = self.KUtil.getSellPriceMinus(code)
        
        self.KUtil.sell(rqname, code, price, quantity)


    def canceltest(self):
        rqname = self.KUtil.getRqname()
        code = '000020'
        quantity = 10
        price = self.KUtil.getBuyPricePlus(code)
        
        orderNo = self.KUtil.sell(rqname, code, price, quantity)
        print(orderNo)
        print('cancel')
        print(self.KUtil.balancepool)
        rqname = self.KUtil.getRqname()

        self.KUtil.cancelSell(rqname, orderNo, code)


    def changetest(self):
        rqname = self.KUtil.getRqname()
        code = '000020'
        quantity = 10
        price = self.KUtil.getBuyPricePlus(code)-100
        
        orderNo = self.KUtil.buy(rqname, code, price, quantity)
        print(orderNo)
        print('change')
        print(self.KUtil.balancepool)
        
        rqname = self.KUtil.getRqname()
        price = 0
        quantity = 100

        self.KUtil.changeBuy(rqname, orderNo, code, price, quantity)
        time.sleep(3)
        print(self.KUtil.orderpool)
        
        
        
