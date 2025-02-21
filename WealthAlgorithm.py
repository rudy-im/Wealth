#-*- coding : utf-8 -*-

import time, threading
from Kiwoom import *
from KiwoomUtil import *
import sqlite3Util as sUtil

class WealthAlgorithm(threading.Thread):
    def __init__(self, kiwoom, infoUpdater):
        super().__init__()

        # testFlag == True 이면 테스트 로그를 콘솔에 print
        self.testFlag = False
        
        self.kiwoom = kiwoom
        self.KUtil = KiwoomUtil(kiwoom)
        
        self.stopflag = False
        self.disposeflag = False
        
        self.timeInterval = 0.5

        # 알고리즘 테스트인지 실제 매매인지 구분
        self.trading = False
        self.realtimetesting = False

        # 현재 시점 세팅
        self.phase = self.getNow()

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

        # 장 중 트레이딩 시간
        self.starttime = 9
        self.endtime = 3

        # 알고리즘 종료 시 동작
        # 전량매도, 전량보유
        self.finishMove = '전량매도'

        # 파일, 테이블 이름
        self.algorithmName = 'algorithm'  # 알고리즘마다 각자의 이름으로 변경
        
        self.logDirectory = 'algorithm log'
        self.logFilename = self.algorithmName + '.db'
        self.tradinglogTablename = 'trading_log'
        self.gainTablename = 'earning_rate_log'

        self.realtimeDirectory = 'realtime data'

                
    def run(self):
        
        while True:

            if self.testFlag:
                print("[run()] self.stopflag : " + str(self.stopflag) +
                      ",   self.disposeflag : " + str(self.disposeflag))
                
            if not(self.stopflag): self.algorithm()
                
            time.sleep(self.timeInterval)

            # todo
            #phase =
            
            if self.disposeflag: break
            

    # abstract method
    def algorithm(self):
        raise NotImplementedError

    
    # 루프 내에서 시점을 계속 변화시키며 알고리즘 테스트
    # date는 YYYYMMDD 형식
    def test(self, startdate, enddate):
        
        self.setTestMode()

        start = int(startdate)
        end = int(enddate)
        day = start
        
        while True:

            if day > end: break

            if day%100 > 31: day = (day/100)*100 + 101
            if day%10000 >= 1300 : day = (day/10000)*10000 + 10101

            try:
                strday = str(day)
                strday = strday[0:4] + '-' + strday[4:6] + '-' + strday[6:8]
                filename = self.realtimeDirectory + '/' + strday + '.txt'
                fp = open(filename, 'r')

                # todo
                
                fp.close()

            except:
                pass

            day += 1

    
    # trading / realtimetesting / test 에 따라 실제 주문을 넣거나
    # 데이터 상에서 해당 종목 가격에 따른 주문 계산
    # todo
    def order(self, buy1sell2, code, quantity, price):

        # 실제 매매 모드
        if trading:
            if self.testFlag:
                print("\n\n")
                print("[order()] trading : True")

            if buy1sell2 == 1:
                self.KUtil.buy()#todo
                
            elif buy1sell2 == 2:
                self.KUtil.sell()#todo

            else:
                print("\n\n")
                print("[order()] Order Type is wrong!!")
                return

        # 실시간 테스트
        elif realtimetesting:
            if self.testFlag:
                print("\n\n")
                print("[order()] realtimetesting : True")

            if buy1sell2 == 1:
                pass
                
            elif buy1sell2 == 2:
                pass

            else:
                print("\n\n")
                print("[order()] Order Type is wrong!!")
                return

        # DB를 이용한 테스트
        else:
            if self.testFlag:
                print("\n\n")
                print("[order()] test mode")

            if buy1sell2 == 1:
                pass
                
            elif buy1sell2 == 2:
                pass

            else:
                print("\n\n")
                print("[order()] Order Type is wrong!!")
                return
    


    def stop(self):
        self.stopflag = True


    def resume(self):
        self.stopflag = False


    def dispose(self):
        self.disposeflag = True


    def setTimeInterval(self, timeInterval):
        self.timeInterval = timeInterval


    def setTradingMode(self):
        self.trading = True
        self.realtimetesting = False


    def setRealtimetestingMode(self):
        self.trading = False
        self.realtimetesting = True


    def setTestMode(self):
        self.trading = False
        self.realtimetesting = False


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

    
        
