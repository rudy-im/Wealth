#-*- coding : utf-8 -*-

import time, threading
from Kiwoom import *

class WealthAlgorithm(threading.Thread):
    def __init__(self, kiwoom, infoUpdater):
        super().__init__()
        
        self.kiwoom = kiwoom
        self.infoUpdater = infoUpdater
        
        self.stopflag = False
        self.disposeflag = False
        
        self.timeInterval = 0.5
        self.testflag = False

        # 타 알고리즘에서의 종목과 중복 가능 여부
        self.duplicationflag = False

        # limitPortion : 예수금 내에서의 한도 비율
        # limitMoney : 한도 금액
        # 한도 비율이 우선적으로 고려됨
        self.limitPortion = 100
        self.limitMoney = 5000000

        # partitions : 분할 종목 수
        # partitionPortion : 분할 %
        self.setUniformPartitions(2)

        # todo : dataframe으로 해당 알고리즘 보유 종목, 수량 등

        # evaluatedMoney : 현재 보유중인 종목들의 평가금액 합
        self.evaluatedMoney = 0

                
    def run(self):
        while True:
            print(str(self.kiwoom))
            if self.stopflag :
                time.sleep(self.timeInterval)

            else :
                self.algorithm()
                time.sleep(self.timeInterval)
                
            if self.disposeflag :
                self.disposeflag = False
                break
            

    # abstract method
    def algorithm(self):
        raise NotImplementedError

    
    # 루프 내에서 시점을 계속 변화시키며 알고리즘 테스트
    # todo
    def test(self, starttime, endtime):
        pass

    
    # testflag에 따라 실제 주문을 넣거나
    # 데이터 상에서 해당 종목 가격에 따른 주문 계산
    # todo
    def order(self, buy1sell2, code, quantity, price):
        pass
    


    def stop(self):
        self.stopflag = True


    def resume(self):
        self.stopflag = False


    def dispose(self):
        self.disposeflag = True


    def setTimeInterval(self, timeInterval):
        self.timeInterval = timeInterval


    # 분할 종목 수에 따라 같은 비율이 되게 지정
    def setUniformPartitions(self, count):
        self.partitions = count
        self.partitionPortion = []
        for i in range(count):
            self.partitionPortion.append(100/i)

    # 매수(시간, 금액, 수량), 매도(시간, 금액, 수량),
    # 수익율(투자액수, 수익액, 수익율)
    # todo
    def log(self):
        pass

    
        
