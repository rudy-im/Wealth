from KiwoomUtil import *
from PyQt5.QtCore import *
from pandas import DataFrame
import timeUtil as tUtil
import sqlite3
import sqlite3Util as sUtil




class WealthAlgorithm():

    def __init__(self, KUtil):
        
        self.KUtil = KUtil

        # 파일, 테이블 이름
        self.algorithmName = 'WealthAlgorithm'  # 알고리즘마다 각자의 이름으로 변경
        
        self.logDirectory = 'algorithm log'
        self.logFile = self.algorithmName + '.db'
        self.tradingLogTable = 'trading_log'
        self.gainLogTable = 'earning_rate_log'

        self.realtimeDirectory = 'realtime data'

        # 세마포
        # 자원 이용중이면 True
        self.semaphore = False

        # 시간 관련
        self.today = tUtil.getToday()
        self.nowtime = tUtil.getNowTime()
        self.beforetime = self.nowtime

        # 주문 미체결을 기다려주는 시간
        self.orderwaitsec = 20

        # 보유 종목 가짓수
        self.partitions = 2

        # 자본금과 수익
        self.money = 2000000   # 알고리즘에 따라 수정
        self.totalmoney = self.money
        self.earning = 0

        # earning이 limitloss 보다 아래이면 프로그램 종료
        self.limitloss = 200000

        # 1초 내에 sendOrder를 사용한 횟수.
        # 매뉴얼에 따르면 5까지 가능하며, 본 모듈에선 1까지만 허용
        self.sendOrderCount = 0

        # 잔고 pool
        # 종목코드 : [해당 알고리즘의 보유수량, 해당 알고리즘의 매수정산금, 해당 알고리즘의 매도정산금]
        # 자세한 내역은 KUtil 참조
        self.balancepool = {}

        # 주문 예정 pool
        # [ [종목코드, 단가, 수량, 매수or매도] ... ]
        # 주문 내역을 보관하다가 1초에 1번씩만 주문
        self.reservedorderpool = []

        # 주문 pool
        # 주문번호 : [코드, 구분(매수/매도), 주문수량, 체결수량, 미체결수량,
        #             최초주문시간(단, 처음 시작 시 최종 체결 시간), 원주문번호, 체결누계금액,
        #             rqname, 주문단가]
        # (KUtil과 같은 내역 + rqname, 주문단가)
        # (단, 주문 시간은 KUtil과 달리, 본 컴퓨터에서 주문을 보낸 시간)
        # 원주문번호, 체결누계금액은 사용 안 함
        self.orderpool = {}

        # 알고리즘에서 필요한 data pool
        # columns : 종목코드
        # index : 직전시가, 직전봉('+', '-')
        self.datapool = None

        # 본 알고리즘에서 차트를 체크하는 분 단위
        self.algMinute = 1

        # 알고리즘마다 계산한 방식에 의한 점수
        # 종목코드 : 점수
        self.score = {}

        # 관심종목들의 점수에 따른 순위
        # 앞에 있을수록 우선순위
        self.ranking = []
        


    # kiwoom API 함수는 외부 스레드에서 호출 시 컨텍스트 오류 발생.
    # 따라서 시그널을 보내 본 클래스에서 함수를 호출하도록 함.
    @pyqtSlot(str)
    def executeSignal(self, signal):
        #print(signal)
        exec(signal)


    # 시그널로 호출될, thread의 주요 동작 함수
    # 자동 매매 처리
    def run(self):

        # 자원 플래그 세우기
        self.semaphore = True

        # run은 1초마다 동작하므로, 본 코드는 1초마다 카운트 클리어.
        self.sendOrderCount = 0

        # orderpool을 KUtil.orderpool에 따라 업데이트.
        self.updateOrderpool()

        # 체결 완료된 주문 처리
        self.finishOrder()

        # orderwaitsec동안 미체결된 주문 처리
        # 매수는 그냥 취소, 매도는 재주문
        self.orderTimeOver()

        # reservedorderpool에서 주문 1개 보내기
        self.orderOne()

        # 알고리즘에 따른 자동 매매
        self.algorithm()

        # 자원 플래그 해제
        self.semaphore = False


    # nowtime 세팅
    def setNowtime(self, nowtime):
        self.nowtime = nowtime


    # beforetime 세팅
    def setBeforetime(self, beforetime):
        self.beforetime = beforetime


    # 세마포 체크
    def getSemaphore(self):
        return self.semaphore


    # 관심종목에 따라 datapool 초기화
    def initInterest(self, interest):

        # 실시간 데이터 등록
        self.KUtil.setRealtime(interest)

        # datapool 초기화
        self.datapool = DataFrame(columns=interest,
                                  index=['price', 'candle'])

        for j in self.datapool.columns:
            self.datapool.set_value('price', j, 0)
            self.datapool.set_value('candle', j, '')


    # earning보다 limitloss가 커서 프로그램을 종료해야 하는 경우, True 반환
    def isLossTooBig(self):

        if self.earning<-self.limitloss:
            
            print("")
            print("============================================")
            print("earning : ", self.earning)
            print("limitloss : ", self.limitloss)
            print("손실이 과도하므로, 프로그램을 종료합니다.")
            print("============================================")
            
            return True
        
        else: return False
        
                
    # 매수
    def buy(self, code, quantity=0):

        print('buy')

        price = self.KUtil.getBuyPricePlus(code)
        maxquantity = int(self.totalmoney / self.partitions / price)

        # quantity가 0이거나 최대 매수 수량을 넘으면
        # 최대 매수 수량만큼 주문.
        validquantity = quantity
        if (quantity==0 or quantity>maxquantity): validquantity = maxquantity

        self.reservedorderpool.append([code, price, validquantity, '매수'])

        print(self.reservedorderpool)


    # 매도
    def sell(self, code, quantity=0):

        print('sell')

        # 보유하고 있지 않으면 패스
        if self.balancepool.get(code)==None: return

        price = self.KUtil.getSellPriceMinus(code)
        maxquantity = self.balancepool[code][0]

        # quantity가 0이거나 최대 매도 수량을 넘으면
        # 최대 매도 수량만큼 주문
        validquantity = quantity
        if (quantity==0 or quantity>maxquantity): validquantity = maxquantity

        # 주문 예정 pool에 내용 등록
        self.reservedorderpool.append([code, price, validquantity, '매도'])

        print(self.reservedorderpool)


    # KUtil의 orderpool내용에 따라 orderpool 업데이트
    def updateOrderpool(self):

        print('updateOrderpool')

        # korderpool
        # 주문번호 : [코드, 구분(매수/매도), 주문수량, 체결수량, 미체결수량,
        #             최초주문시간(단, 처음 시작 시 최종 체결 시간), 원주문번호, 체결누계금액]
        korderpool = self.KUtil.getOrderpool()
        print('korderpool')
        print(korderpool)

        for orderNo, l in korderpool.items():

            # 본 알고리즘의 주문이 아니면 패스
            if self.orderpool.get(orderNo)==None: continue

            # 맞으면 업데이트
            self.orderpool[orderNo][3] = l[3]  # 체결수량
            self.orderpool[orderNo][4] = l[4]  # 미체결수량

            print(self.orderpool)
            

    # 체결 완료된 주문 처리
    def finishOrder(self):

        print('finishOrder')

        removeOrderList = []
        
        # orderpool
        # 주문번호 : [코드, 구분(매수/매도), 주문수량, 체결수량, 미체결수량,
        #             최초주문시간(단, 처음 시작 시 최종 체결 시간), 원주문번호, 체결누계금액,
        #             rqname, 주문단가]
        for orderNo, l in self.orderpool.items():

            # 체결 완료된 경우
            if self.KUtil.isOrderFinished(orderNo):
                print(l)

                removeOrderList.append(orderNo)

                # 로그에 등록할 점수, 랭킹 처리
                s = self.score.get(l[0])
                if s==None: s = 0

                if self.ranking.count(l[0])==0: r = 0
                else: r = self.ranking.index(l[0])
                    

                # 매수의 경우
                if l[1]=='매수':

                    # 매수정산금 얻기
                    totalprice = self.KUtil.getTotalBuyPrice(l[0])
                    print(totalprice)

                    # 본 알고리즘의 잔고에 등록
                    if self.balancepool.get(l[0])!=None:
                        
                        self.balncepool[l[0]][0] += l[2]
                        self.balancepool[l[0]][1] += totalprice
                        
                    else:
                        
                        self.balancepool[l[0]] = [l[2], totalprice, 0]

                    print(self.balancepool)

                    # 잔금 등록
                    self.money -= totalprice

                    print(self.money)
                    
                    # 로그                    
                    loglist = [self.today, tUtil.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(l[0]), '매수',
                               l[2], totalprice, s, r]

                    print('')
                    print("-----------------------------------------")
                    print("  [매수 체결]")
                    print(loglist)
                    print("-----------------------------------------")
                    
                    self.log('매매', loglist)

                    

                # 매도의 경우
                elif l[1]=='매도':
                    
                    # 매도정산금 얻기
                    totalsellprice = self.KUtil.getTotalSellPrice(l[0])

                    # 잔금 등록
                    self.money += totalsellprice

                    # 본 알고리즘의 잔고에 등록
                    self.balancepool[l[0]][0] -= l[2]
                    self.balancepool[l[0]][2] += totalsellprice

                    print(self.balancepool)
                    
                    # 로그
                    loglist = [self.today, tUtil.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(l[0]), '매도',
                               l[2], totalsellprice, s, r]
                    
                    print('')
                    print("-----------------------------------------")
                    print("  [매도 체결]")
                    print(loglist)
                    
                    self.log('매매', loglist)

                    # 보유 수량이 0이 된 경우, 수익률까지 정리
                    if self.balancepool[l[0]][0]==0:
                        
                        # 수익 관련 계산
                        totalbuyprice = self.balancepool[l[0]][1]
                        
                        gain = totalsellprice - totalbuyprice
                        self.earning += gain
                        self.totalmoney += gain

                        print(totalbuyprice, gain, self.earning, self.totalmoney)

                        # 본 알고리즘의 잔고에서 제거
                        self.balancepool.pop[l[0]]

                        print(self.balancepool)

                        # 로그
                        loglist = [self.today, tUtil.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(l[0]),
                                   totalbuyprice, gain, gain/totalbuyprice*100]
                        
                        self.log('수익률', loglist)
                        
                        print(loglist)
                        
                    print("-----------------------------------------")                                

        # 위 루프가 orderpool에 대해 돌아가고 있었으므로,
        # 제거할 orderNo를 따로 빼서 루프 밖에서 제거
        for orderNo in removeOrderList:

            self.orderpool.pop(orderNo)


    # orderwaitsec 동안 처리되지 않은 주문 처리
    # 매수는 그냥 취소, 매도는 재주문
    def orderTimeOver(self):

        # 이미 1개의 주문을 사용한 경우, 함수 종료
        if self.sendOrderCount>0: return

        removeOrder = ''
        
        # orderpool
        # 주문번호 : [코드, 구분(매수/매도), 주문수량, 체결수량, 미체결수량,
        #             최초주문시간(단, 처음 시작 시 최종 체결 시간), 원주문번호, 체결누계금액,
        #             rqname, 주문단가]
        for orderNo, l in self.orderpool.items():

            if self.nowtime<l[5]: continue
            elif tUtil.timeCalc(self.nowtime, -l[5])>self.orderwaitsec:

                removeOrder = orderNo

                # 로그에 등록할 점수, 랭킹 처리
                s = self.score.get(l[0])
                if s==None: s = 0

                if self.ranking.count(l[0])==0: r = 0
                else: r = self.ranking.index(l[0])

                # 매수의 경우
                if l[1]=='매수':

                    print('')
                    print("-----------------------------------------")
                    print("  [매수 취소] :: ", orderNo)
                    print(l)
                    print("-----------------------------------------")

                    # 주문 취소
                    self.KUtil.cancelBuy(self.KUtil.getRqname(), orderNo, l[0])

                    # 매수정산금 얻기
                    totalprice = self.KUtil.getTotalBuyPrice(l[0])

                    # 본 알고리즘의 잔고에 등록
                    if l[3]==0: pass
                    
                    elif self.balancepool.get(l[0])!=None:

                        self.balncepool[l[0]][0] += l[3]
                        self.balancepool[l[0]][1] += totalprice
                                         
                    else:

                        self.balancepool[l[0]] = [l[3], totalprice, 0]

                    print(self.balancepool)

                    # 잔금 등록
                    self.money -= totalprice

                    # 로그
                    if l[3]!=0:
                        loglist = [self.today, tUtil.timeFormat(self.nowtime), self.KUtil.convertCodeOrName(l[0]), '매수',
                                   l[3], totalprice, s, r]
                        
                        print('')
                        print("-----------------------------------------")
                        print("  [매수 취소 전 체결]")
                        print(loglist)
                        print("-----------------------------------------")
                                             
                        self.log('매매', loglist)

                    # 주문 루프 종료
                    break

                # 매도의 경우
                elif l[1]=='매도':

                    print('')
                    print("-----------------------------------------")
                    print("  [매도 취소] :: ", orderNo)
                    print(l)
                    print("-----------------------------------------")

                    # 주문 취소
                    self.KUtil.cancelSell(self.KUtil.getRqname(), orderNo, l[0])

                    # 매도정산금 얻기
                    totalprice = self.KUtil.getTotalSellPrice(l[0])

                    # 본 알고리즘의 잔고에 등록
                    self.balancepool[l[0]][0] -= l[3]
                    self.balancepool[l[0]][2] += totalprice

                    print(self.balancepool)

                    # 잔금 등록
                    self.money += totalprice

                    # 재주문 대기
                    # 미체결 수량만큼 재 매도 하므로, 주문이 체결 완료로 끝난 경우에만 몰아서 로그
                    self.sell(l[0], l[4])

                    # 주문 루프 종료
                    break

        # 위 루프가 orderpool에 대해 돌아가고 있었으므로,
        # 제거할 orderNo를 따로 빼서 루프 밖에서 제거.
        # 제거하는 orderNo가 있는 경우, 주문 1회를 이미 완료한 것이므로 함수 종료.
        if removeOrder!='':
            self.orderpool.pop(removeOrder)
            return
            

    # 주문을 1초에 1개씩만 넣도록 함
    # (원래의 thread가 1초에 1회씩 체크하므로)
    def orderOne(self):

        # 이미 1개의 주문을 사용한 경우, 함수 종료
        if self.sendOrderCount>0: return

        # reservedorderpool에 내용이 없으면, 함수 종료
        if len(self.reservedorderpool)==0: return

        print('orderOne')

        # reservedorderpool
        # [종목코드, 단가, 수량, 매수or매도]
        l = self.reservedorderpool[0]

        # 매수/매도 공통 부분
        rqname = self.KUtil.getRqname()

        print('')
        print("-----------------------------------------")

        # orderpool
        # 주문번호 : [코드, 구분(매수/매도), 주문수량, 체결수량, 미체결수량,
        #             최초주문시간(단, 처음 시작 시 최종 체결 시간), 원주문번호, 체결누계금액,
        #             rqname, 주문단가]

        # 매수의 경우
        if l[3]=='매수':

            # 주문 넣기
            orderNo = self.KUtil.buy(rqname, l[0], l[1], l[2])
            self.orderpool[orderNo] = [l[0], '매수', l[2], 0, l[2],
                                       self.nowtime, '', 0,
                                       rqname, l[1]]

            print("  [매수 주문] :: ", orderNo)
            
        # 매도의 경우
        elif l[3]=='매도':

            # 주문 넣기
            orderNo = self.KUtil.sell(rqname, l[0], l[1], l[2])
            self.orderpool[orderNo] = [l[0], '매도', l[2], 0, l[2],
                                       self.nowtime, '', 0,
                                       rqname, l[1]]

            print("  [매도 주문] :: ", orderNo)

        print(l)
        print("-----------------------------------------")

        # reservedorderpool에서 삭제
        self.reservedorderpool = self.reservedorderpool[1:]


    # trading_log : 매수/매도(날짜, 시간, 종목명, 구분, 수량, 정산금, 점수, 순위) -> 구분에 매수/매도
    # earning_rate_log : 수익률(날짜, 시간, 종목명, 투자액수, 수익액, 수익률)
    # logtype : '매매', '수익률'
    def log(self, logtype, loglist):
        print('log')
        
        if logtype=='매매':

            if len(loglist)!=8: return
            
            con = sqlite3.connect(self.logDirectory + '/' + self.logFile)
            tablename = self.tradingLogTable

            columnstr ='''date CHAR(8),
                          time CHAR(8),
                          stockname VARCHAR2(30),
                          type CHAR(6),
                          quantity NUMBER(7),
                          totalprice NUMBER(20),
                          score NUMBER(7),
                          ranking NUMBER(4)'''

            sUtil.create(tablename, con, columnstr)

            columns = ['date', 'time', 'stockname', 'type', 'quantity', 'totalprice', 'score', 'ranking']
            
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


    # 알고리즘 동작
    def algorithm(self):

        nowmin = int(self.nowtime/100)
        nowmin %= 100

        nowsec = self.nowtime%100

        # algMinute마다 차트 체크
        if (nowmin%self.algMinute == 0 and nowsec==0):

            print('work')

            for code in self.datapool.columns:

                # 현재 가격과 직전 가격 체크
                beforeprice = self.datapool.get_value('price', code)
                nowprice = self.KUtil.getNowPrice(code)

                # 현재 가격을 직전 가격에 등록
                self.datapool.set_value('price', code, nowprice)

                # 주가 측정이 처음인 경우
                # 현재 가격을 등록하기만 하고, 기타 체크는 패스
                if beforeprice==0: continue

                # 현재 봉과 직전 봉 체크
                beforecandle = self.datapool.get_value('candle', code)
                nowcandle = ''
                if beforeprice>nowprice: nowcandle = '-'
                elif beforeprice<nowprice: nowcandle = '+'

                # 직전 봉이 없거나 음봉이고, 현재 봉이 양봉이면 매수
                if (beforecandle=='' or beforecandle=='-'):
                    if nowcandle=='+':
                        self.buy(code)

                # 현재 봉이 음봉이면 매도
                if nowcandle=='-':
                    self.sell(code)

                # 현재 봉을 직전 봉에 등록
                self.datapool.set_value('candle', code, nowcandle)

                print(self.datapool)
                

                
                        
