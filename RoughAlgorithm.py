#-*- coding : utf-8 -*-

import time, threading, math, fileinput
from datetime import timedelta
from Kiwoom import *
from KiwoomUtil import *
import sqlite3Util as sUtil
from pandas import Series, DataFrame

class RoughAlgorithm(threading.Thread):
    def __init__(self, kiwoom):
        super().__init__()

        # testFlag == True 이면 테스트 로그를 콘솔에 print
        self.testFlag = False
        
        self.kiwoom = kiwoom
        self.KUtil = KiwoomUtil(kiwoom)

        self.timeInterval = 0.2

        # 세마포
        # 자원이 점유되지 않으면 False, 사용중이면 True
        self.semaphore = False

        # 시간 관련
        self.today = sUtil.now(False)
        self.beforetime = self.KUtil.getNow()
        self.nowtime = self.beforetime

        # 알고리즘 테스트인지 실제 매매인지 구분
        self.trading = False
        self.realtimetesting = False

        # 테스트 모드에서 얻은 데이터의 realpool 형태, partitions에서 제거할 코드 임시 저장
        self.tmprealpool = {}
        self.removelist = []

        # 관심종목 지정
        self.interest = self.KUtil.queryByMargin(20)

        # 1초 간격의 데이터를 120개씩 저장할 DataFrame
        self.datapool = DataFrame(columns = self.interest)

        # 종목들의 계산된 점수 dic, 점수가 큰 순서로 정렬된 list, 초과해야 할 한계 점수
        self.score = {}
        self.ranking = []
        self.limitscore = 0.002

        # 자금
        self.money = 5000000

        # 수익
        self.earning = 0
        self.limitloss = -200000

        # 분할 종목 지정
        # {code : [buyprice, quantity]...}
        self.partitionCount = 2
        self.partitions = {}

        # 주문 pool
        # {주문번호 : [종목코드, 매수/매도, 가격, 수량, 체결량, 시간]...}
        self.orderpool = {}

        # 파일, 테이블 이름
        self.algorithmName = 'roughAlgorithm'  # 알고리즘마다 각자의 이름으로 변경
        
        self.logDirectory = 'algorithm log'
        self.logFile = self.algorithmName + '.db'
        self.tradingLogTable = 'trading_log'
        self.gainLogTable = 'earning_rate_log'

        self.realtimeDirectory = 'realtime data'


    def run(self):
        
        while True:
            if not(self.semaphore):
                self.nowtime = self.KUtil.getNow()
                
                if self.nowtime>152000: break

                if self.limitloss>self.earning: break

                if self.nowtime<90000: pass
                
                elif self.nowtime>self.beforetime:

                    #if self.nowtime%100==0:
                    print(self.nowtime)
                    
                    self.semaphore = True

                    self.algorithm()
                    
                    self.beforetime = self.nowtime
                    self.semaphore = False
        
            time.sleep(0.2)
            

    # abstract method
    def algorithm(self):

        realpool = self.getRealpool()
        self.adjustTime()
        
        for code, l in realpool.items():
            self.datapool.set_value(self.nowtime, code, abs(int(l[0])))

        if len(self.datapool.index)>120:
            print('len>120')
            
            self.datapool.drop(self.datapool.index[[0]], inplace=True)

            for code in self.datapool.columns:
                
                data = list(self.datapool[code])
                before = sum(data[0:60]) / 60
                after = sum(data[60:120]) / 60

                self.score[code] = (after - before) / before
                if math.isnan(self.score[code]): self.score[code] = -100

            self.ranking = sorted(self.score, key = self.score.__getitem__, reverse = True)

            # 체결 내역 확인
            self.checkOrder()

            # orderpool에 10초 이상 미체결 내역 처리
            if self.isTradingMode():
                for order, l in self.orderpool.items():
                    if l[5]<=self.secCalc(self.nowtime, -10):
                        if l[1]=='매수': self.buyCancel()
                        elif l[1]=='매도': self.sellCancel()

            # 매수 동작 체크
            if self.nowtime<150000:
                
                existingPartitions = len(self.partitions)

                if existingPartitions<self.partitionCount:

                    for code in self.ranking:

                        if self.score[code]<=0: break
                        
                        if self.partitions.get(code)==None:

                            if self.score[code]>self.limitscore:
                                quantity = self.money / (self.partitionCount - existingPartitions) / self.datapool.get_value(self.nowtime, code)
                                quantity = int(quantity)
                                self.buy(code, quantity)
                                
                            break

            # 매도 동작 체크
            for code, l in self.partitions.items():
                if self.nowtime>151000: self.sell(code)
                if self.ranking.index(code)>10: self.sell(code)
                if self.score[code]<=0: self.sell(code)

            # 실시간테스트나 테스트 모드에서는 sell 도중 partitions 내용을 제거해야 하므로
            # 이와 같은 별도의 제거 루프 필요
            if not(self.isTradingMode()):
                self.removelist = list(set(self.removelist))
                for code in self.removelist:
                    self.partitions.pop(code)
                self.removelist = []
                

    # self.beforetime과 self.nowtime을 비교하여 1초 넘게 차이나면 공백을 직전 row를 복사하여 메우고,
    # 120초(2분) 넘게 차이나면 아예 datapool을 비우고 새로 시작
    def adjustTime(self):

        timedifference = self.timeCalc(self.nowtime, -self.beforetime)
        
        if timedifference>200:
            
            self.datapool = self.datapool[0:0]
        
        elif timedifference>1:

            duplicate = list(self.datapool.loc[self.beforetime])
            
            for i in range(1,timedifference):
                self.datapool.loc[self.timeCalc(self.beforetime, i)] = duplicate
        
        
    # realpool 얻기
    def getRealpool(self):

        if (self.isTradingMode() or self.isRealtimetestingMode()):
            realpool = self.kiwoom.getRealpool()
        else:
            realpool = self.tmprealpool

        return realpool
    

    # timeA에서 timeB를 더하거나 뺀 값 얻기
    # 시간은 (h)hmmss 형식의 숫자
    # timeB의 부호로 덧셈/뺄셈 결정
    def timeCalc(self, timeA, timeB):
        
        a = timedelta(hours = int(timeA/10000),
                      minutes = int((timeA%10000)/100),
                      seconds = timeA%100)

        tmpB = abs(timeB)
        b = timedelta(hours = int(tmpB/10000),
                      minutes = int((tmpB%10000)/100),
                      seconds = tmpB%100)

        if timeB>0: calcdelta = a + b
        else: calcdelta = a - b

        l = str(calcdelta).split(':')
        ret = int(l[0]) * 10000 + int(l[1]) * 100 + int(l[2])
        
        return ret


    # 시간을 hh:mm:ss 형식으로 반환
    # time은 hhmmss 형식의 숫자
    def timeFormat(self, time):
        
        hour = int(time/10000)
        minute = int(time%10000/100)
        sec = time%100

        ret = '{:02d}:{:02d}:{:02d}'.format(hour, minute, sec)
        return ret
        


    # 매수 주문 넣기
    def buy(self, code, quantity):

        # 실제매매의 경우, 주문까지만 넣음.
        if self.isTradingMode():
            
            price = self.KUtil.getBuyPricePlus(code)
            self.money -= (price*quantity)
        
            orderNo = self.KUtil.buy(self.KUtil.getRqname(), code, price, quantity) ###

            self.orderpool[orderNo] = [code, '매수', price, quantity, 0, self.nowtime]
            self.partitions[code] = [price, 0]

        # 실시간테스트의 경우, 주문가는 실제매매와 같되 주문은 넣지 않고 체결된 것으로 취급.
        elif self.isRealtimetestingMode():
            
            price = self.KUtil.getBuyPricePlus(code)
            
            self.money -= (price*quantity)
            
            self.partitions[code] = [price, quantity]

            loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code), '매수',
                        price, quantity, price*quantity, self.score[code], self.ranking.index(code)]
            print(loglist)
            
            self.log('매매', loglist)

        # 테스트의 경우, 데이터 상 현재가를 그대로 주문가로 사용해 체결된 것으로 취급.
        elif self.isTestMode():

            price = self.datapool.get_value(self.nowtime, code)
            
            self.money -= (price*quantity)
            self.partitions[code] = [price, quantity]

            loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code), '매수',
                        price, quantity, price*quantity, self.score[code], self.ranking.index(code)]
            print(loglist)
            
            self.log('매매', loglist)
        

    # 매수 체결 (실제매매에서만 적용)
    def buyComplete(self, orderNo):

        if not(self.isTradingMode()): return

        code = self.orderpool[orderNo][0]
        price = self.orderpool[orderNo][2]
        quantity = self.orderpool[orderNo][3]
        self.partitions[code] = [price, quantity]
        
        self.orderpool.pop(orderNo)

        loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code), '매수',
                price, quantity, price*quantity, self.score[code], self.ranking.index(code)]
        print(loglist)
    
        self.log('매매', loglist)


    # 매수 미체결 (실제매매에서만 적용)
    # 10초 동안 체결되지 않는 경우 처리
    # 이미 매수한 것은 가지고 있고, 추가 매수는 안 함.
    # 재매수가 없으므로, 체결된 부분에 대해서 log
    def buyCancel(self, orderNo):

        if not(self.isTradingMode()): return

        code = self.orderpool[orderNo][0]
        price = self.orderpool[orderNo][2]
        notFinishedQuantity = self.orderpool[orderNo][3]-self.orderpool[orderNo][4]

        self.orderpool.pop(orderNo)

        self.KUtil.cancelBuy(self.KUtil.getRqname(), orderNo, code)
        self.money += price*notFinishedQuantity

        # 단위체결가와 체결량
        price = self.partitions[code][0]
        quantity = self.partitions[code][1]
        
        loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code), '매수',
                  price, quantity, price*quantity, self.score[code], self.ranking.index(code)]
        print(loglist)
    
        self.log('매매', loglist)


    # 매도 주문 넣기
    def sell(self, code, quantity=0):

        # 실제매매에서는 매도 주문까지만 넣음
        if self.isTradingMode():
            
            price = self.KUtil.getSellPriceMinus(code)
            if quantity==0: quantity = self.partitions[code][1]

            orderNo = self.KUtil.sell(self.KUtil.getRqname(), code, price, quantity) ###

            self.orderpool[orderNo] = [code, '매도', price, quantity, 0, self.KUtil.getNow()]

        # 실시간테스트에선 실제매매의 주문가와 같은 가격으로 체결된 것으로 취급
        # 가격 부분을 빼면 테스트 모드와 전부 같음
        elif self.isRealtimetestingMode():
            
            price = self.KUtil.getSellPriceMinus(code)

            # self.partitions 에서 제거할 목록
            self.removelist.append(code)
            
            l = self.partitions[code]
            buyprice = l[0]
            quantity = l[1]

            # 수수료 + 제세금은 매도금의 0.35% 로 계산
            totalprice = int(quantity*price*0.9965)
            gain = totalprice - buyprice * quantity
            investment = buyprice*quantity

            loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code), '매도',
                        price, quantity, totalprice, self.score[code], self.ranking.index(code)]
            print(loglist)
            
            self.log('매매', loglist)

            loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code),
                       investment, gain, gain/investment*100]
            print(loglist)
            
            self.log('수익률', loglist)

        # 테스트에선 데이터 상의 현재가와 같은 가격으로 체결된 것으로 취급
        # 가격 부분을 빼면 실시간테스트 모드와 전부 같음
        elif self.isTestMode():
            
            price = self.datapool.get_value(self.nowtime, code)

            # self.partitions 에서 제거할 목록
            self.removelist.append(code)
            
            l = self.partitions[code]
            buyprice = l[0]
            quantity = l[1]

            # 수수료 + 제세금은 매도금의 0.35% 로 계산
            totalprice = int(quantity*price*0.9965)
            gain = totalprice - buyprice * quantity
            investment = buyprice*quantity
            
            self.money += totalprice
            self.earning += gain

            loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code), '매도',
                        price, quantity, totalprice, self.score[code], self.ranking.index(code)]
            print(loglist)
            
            self.log('매매', loglist)

            loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code),
                       investment, gain, gain/investment*100]
            print(loglist)
            
            self.log('수익률', loglist)


    # 매도 체결
    def sellComplete(self, orderNo, totalprice):

        if not(self.isTradingMode()): return

        code = self.orderpool[orderNo][0]
        price = self.orderpool[orderNo][2]
        quantity = self.orderpool[orderNo][3]
        
        self.orderpool.pop(orderNo)
        
        l = self.partitions.pop(code)
        buyprice = l[0]
        quantity = l[1]

        gain = totalprice - buyprice * quantity
        investment = buyprice*quantity
        
        self.money += totalprice
        self.earning += gain

        loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code), '매도',
                    price, quantity, totalprice, self.score[code], self.ranking.index(code)]
        print(loglist)
        
        self.log('매매', loglist)

        loglist = [self.today, self.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(code),
                   investment, gain, gain/investment*100]
        print(loglist)
        
        self.log('수익률', loglist)
                

    # 매도 미체결
    # 10초 동안 체결되지 않는 경우 처리
    # 기존 주문 취소 후 재매도
    # 재매도가 있으므로 중간에 log 안 함.
    def sellCancel(self, orderNo):

        if not(self.isTradingMode()): return

        code = self.orderpool[orderNo][0]
        price = self.orderpool[orderNo][2]
        quantity = self.orderpool[orderNo][3]-self.orderpool[orderNo][4]

        self.orderpool.pop(orderNo)
        
        self.KUtil.cancelSell(self.KUtil.getRqname(), orderNo, code)

        self.sell(code, quantity)


    # 체결 확인 된 주문 처리
    # 매도는 다 팔릴 때까지 계속 다시 팔기 때문에,
    # 체결 완료 시 money, partitions 등 전부 해결.
    # 매수는 도중에 그만 둘 수도 있기 때문에,
    # 일부만 체결되어도 money, partitions 등 전부 갱신.
    def checkOrder(self):

        if not(self.isTradingMode()): return

        print('')
        print('checkOrder()')
        
        trcode = 'opt10075'
        inputdic = {'계좌번호' : self.kiwoom.account[0],
                    '체결구분' : '0',
                    '매매구분' : '0'}
        outputs = ['주문번호', '종목코드', '주문상태', '체결량', '체결가', '당일매매수수료', '당일매매세금']

        self.KUtil.testFlag = True

        df = self.KUtil.kiwoomRequest(self.KUtil.getRqname(), trcode, inputdic, outputs)

        print(df)

        checklist = []
        
        for i in df.index:
            
            orderNo = df.get_value(i, '주문번호')

            if self.orderpool.get(orderNo)==None: continue
            
            finishedQuantity = int(df.get_value(i, '체결량'))

            buysell = self.orderpool[orderNo][1]

            # 매도의 경우
            if buysell=='매도':

                if df.get_value(i, '주문상태')=='체결':

                    if self.orderpool.get(orderNo)==None: continue

                    price = int(df.get_value(i, '체결가'))
                    premium = int(df.get_value(i, '당일매매수수료'))
                    tax = int(df.get_value(i, '당일매매세금'))

                    totalprice = price * finishedQuantity - premium - tax
                    self.sellComplete(orderNo, totalprice)

                elif finishedQuantity>0:
                    
                    code = df.get_value(i, '종목코드')
                    
                    self.partitions[code] = [self.partitions[code][0], finishedQuantity]

                    self.orderpool[orderNo][4] = finishedQuantity

            # 매수의 경우             
            elif buysell=='매수':

                if df.get_value(i, '주문상태')=='체결':

                    if self.orderpool.get(orderNo)==None: continue

                    self.buyComplete(orderNo)

                elif finishedQuantity>0:

                    code = df.get_value(i, '종목코드')

                    beforeprice = self.partitions[code][0]
                    nowprice = int(df.get_value(i, '체결가'))
                    
                    self.partitions[code] = [nowprice, finishedQuantity]

                    self.money += finishedQuantity * (beforeprice - nowprice)

                    self.orderpool[orderNo][4] = finishedQuantity


    # trading_log : 매수/매도(날짜, 시간, 종목명, 구분, 금액, 수량, 정산금, 점수, 순위) -> 구분에 매수/매도
    # earning_rate_log : 수익률(날짜, 시간, 종목명, 투자액수, 수익액, 수익률)
    # logtype : '매매', '수익률'
    def log(self, logtype, loglist):
        
        if logtype=='매매':

            if len(loglist)!=9: return
            
            con = sqlite3.connect(self.logDirectory + '/' + self.logFile)
            tablename = self.tradingLogTable

            columnstr ='''date CHAR(8),
                          time CHAR(8),
                          stockname VARCHAR2(30),
                          type CHAR(6),
                          price NUMBER(7),
                          quantity NUMBER(7),
                          totalprice NUMBER(20),
                          score NUMBER(7),
                          ranking NUMBER(4)'''

            sUtil.create(tablename, con, columnstr)

            columns = ['date', 'time', 'stockname', 'type', 'price', 'quantity', 'totalprice', 'score', 'ranking']
            
            sUtil.insert(tablename, con, columns, loglist)
            con.close()

        elif logtype=='수익률':

            if len(loglist)!=6: return
            
            con = sqlite3.connect(self.logDirectory + '/' + self.logFile)
            tablename = self.gainLogTable

            columnstr ='''date CHAR(8),
                          time CHAR(8),
                          stockname VARCHAR2(30),
                          investment NUMBER(20),
                          earning NUMBER(20),
                          earningrate NUMBER(4)'''

            sUtil.create(tablename, con, columnstr)

            columns = ['date', 'time', 'stockname', 'investment', 'earning', 'earningrate']
            
            sUtil.insert(tablename, con, columns, loglist)
            con.close()


    # 알고리즘 테스트
    # realtime data / YYYY-MM-DD.txt 파일들을 참조
    # 매개변수 날짜 형식은 YYYYMMDD
    # 데이터에서 얻은 realpool은 self.tmprealpool로 참조
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
                
                self.today = strday
                notFirst = False
                
                with open(filename) as fileobject:
                    
                    for line in fileobject:

                        line = line.strip()
                        if line == '': continue

                        l = line.split('\t')
                        
                        if l[0]=='realtime':

                            if notFirst:
                                self.algorithm()
                                self.beforetime = self.nowtime
                                
                            else:
                                notFirst = True
                                self.beforetime = int(l[1])
                                
                            self.nowtime = int(l[1])
                            
                            if self.nowtime%100==0: print(self.nowtime)

                        else:
                            
                            self.tmprealpool[l[0]] = [abs(int(l[1])), int(l[2])]
                        
            except:
                pass

            day += 1


    def setTradingMode(self):
        self.trading = True
        self.realtimetesting = False


    def setRealtimetestingMode(self):
        self.trading = False
        self.realtimetesting = True


    def setTestMode(self):
        self.trading = False
        self.realtimetesting = False


    def isTradingMode(self):
        if (self.trading and not(self.realtimetesting)): return True
        else: return False


    def isRealtimetestingMode(self):
        if (not(self.trading) and self.realtimetesting): return True
        else: return False


    def isTestMode(self):
        if (not(self.trading) and not(self.realtimetesting)): return True
        else: return False




    




        
        
