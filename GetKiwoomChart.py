#-*- coding : utf-8 -*-

import time, threading
import sqlite3
import sqlite3Util as sUtil
import timeUtil as tUtil
from Kiwoom import *
from pandas import DataFrame



##############################################################
# ** 차트 저장 전용 모듈 **
#
# 
##############################################################


class GetKiwoomChart(Kiwoom):
    
    def __init__(self):
        
        super().__init__()

        self.testFlag = False

        # 계좌
        self.account = ''

        # 종목코드-종목명 db 파일 & 테이블
        self.stocksCodeNameFile = 'stocks.db'
        self.stocksCodeNameTable = 'stocks'

        # 종목의 차트 등 종목코드.db 파일 저장 경로
        self.stockDirectory = 'stock data'

        # db connect
        self.con = None
        self.connectFlag = False

        # 오늘 날짜
        # 차트 기준 날짜 미입력 시 사용
        self.today = tUtil.getToday('%Y%m%d')

        # 쿼리 데이터가 올 때까지 기다리는 플래그
        self.waitFlag = False

        # 'Once' 함수를 위한 데이터프레임
        self.df = None



######################################################################################
# Event 함수 overriding
######################################################################################



    # (이벤트) 로그인 성공 시 알림
    def eventConnect(self, err_code):
        
        self.account = self.getAccountList()[0]


    # (이벤트) 받은 쿼리 결과에 따른 처리
    # GetCommData() 사용
    def receiveTrData(self, screen_no, rqname, trcode, record_name):

        l = rqname.split('&')
        if len(l)<3: return

        code = l[0]
        tablename = l[1]
        funcname = l[2]

        minFlag = False
        if tablename.startswith('min'): minFlag = True

        onceFlag = False
        if funcname.endswith('Once'):
            onceFlag = True
            self.df = DataFrame(columns=['candleTime', 'open', 'high', 'low', 'close', 'volume'])


        # 전달 받은 데이터의 행 수만큼 반복
        repeatCnt = self.getRepeatCnt(trcode, rqname)

        for i in range(repeatCnt):

            if minFlag: candleTime = candleTime = self.getCommData(trcode, rqname, i, '체결시간')
            else: candleTime = self.getCommData(trcode, rqname, i, '일자')

            open = self.getCommData(trcode, rqname, i, '시가')
            high = self.getCommData(trcode, rqname, i, '고가')
            low = self.getCommData(trcode, rqname, i, '저가')
            close = self.getCommData(trcode, rqname, i, '현재가')
            volume = self.getCommData(trcode, rqname, i, '거래량')

            if onceFlag:
                self.df.loc[i] = [candleTime, open, high, low, close, volume]

            else:
                self.insertChart(tablename, candleTime, open, high, low, close, volume)

        self.waitFlag = False



######################################################################################
# 내부에서 사용하는 함수
######################################################################################



    # 보유 계좌 리스트 얻기
    def getAccountList(self):
        
        account = self.getLoginInfo("ACCLIST")
        account = account.split(';')

        if self.testFlag:
            print("[getAccount()] account : ")
            print(account)
            print("\n\n")
            
        return account[:-1]

    
    def dbconnect(self, filename):

        self.con = sqlite3.connect(filename)
        self.connectFlag = True


    def dbclose(self):

        if self.connectFlag: self.con.close()
        self.connectFlag = False


    def waitRun(self):

        for i in range(10):
            
            time.sleep(0.2)
            if not(self.waitFlag): break


    def wait(self):
        
        wt = threading.Thread(target = self.waitRun)
        wt.start()
        wt.join()


    # 지정 증거금 이하 종목 코드를 리스트로 반환
    # withName이 True이면 {종목코드:종목명} 의 dic 반환
    def queryByMargin(self, marginLimit=20, withName=False):
        
        con = sqlite3.connect(self.stocksCodeNameFile)

        selectstr = 'code, '
        if withName: selectstr = selectstr + 'name, '
        selectstr = selectstr + 'margin'

        wherestr = 'margin <= ' + str(marginLimit)
        
        selected = sUtil.select(self.stocksCodeNameTable, con, selectstr, wherestr)

        con.close()
        
        codeList = list(selected['code'])

        if withName:
            nameList = list(selected['name'])
            ret = dict((codeList[i], nameList[i]) for i in range(len(codeList)))
            return ret
            
        return codeList



######################################################################################
# 차트 저장 함수
######################################################################################



    # 데이터 조회 요청
    # 5회까지 쿼리 요청 보내고, 그 이상 실패 시 경고문
    # 단순 루프를 돌고 있으면 이벤트가 도착하지 않으므로, thread 내에서 루프를 돌며 대기
    def chartRequest(self, rqname, trcode, inputdic, next=0, screenNo="0101"):
        
        for i in range(5):
            
            for k, v in inputdic.items():

                self.setInputValue(k, v)

            self.waitFlag = True
            
            self.commRqData(rqname, trcode, next, screenNo)

            print('')
            print("[chartRequest()] request!")

            self.wait()
            if not(self.waitFlag): return

        # 루프를 다 도는 동안 쿼리 결과를 반환하지 못한 경우
        print("\n\n")
        print("[chartRequest()] Query is failed!!!")


    # 차트 테이블이 없는 경우, 생성
    def makeChartTable(self, tablename):

        if not(self.connectFlag): return

        candleTime = '20'
        if tablename.startswith('min'): candleTime = '14'
        elif tablename.startswith('day'): candleTime = '8'
        elif tablename.startswith('week'): candleTime = '8'
        elif tablename.startswith('month'): candleTime = '8'

        try:

            columnstr = '''candleTime CHAR(''' + candleTime + ''') NOT NULL UNIQUE,
                          open NUMBER(10) NOT NULL,
                          high NUMBER(10) NOT NULL,
                          low NUMBER(10) NOT NULL,
                          close NUMBER(10) NOT NULL,
                          volume NUMBER(20) NOT NULL'''

            sUtil.create(tablename, self.con, columnstr)

        except:
            
            print("\n\n")
            print("[makeChartTable()] Failed to makeChartTable()!!!")


    # 차트 데이터 insert
    def insertChart(self, tablename, candleTime, open, high, low, close, volume):

        if not(self.connectFlag): return

        columns = ['candleTime', 'open', 'high', 'low', 'close', 'volume']
        values = [candleTime, open, high, low, close, volume]

        sUtil.insert(tablename, self.con, columns, values)


    # 차트 데이터를 정렬된 상태로 insert
    # 기존 저장 부분과 맞물리면 True, 빈틈이 생기면 False 반환
    def insertChartOnce(self, tablename):

        if not(self.connectFlag): return

        columns = ['candleTime', 'open', 'high', 'low', 'close', 'volume']
        indexlen = len(self.df.index)

        lasttime = 0
        selected = sUtil.select(tablename, self.con, limit=1, ordercolumn='candleTime', asc=False)
        if len(selected.index)!=0: lasttime = int(selected.get_value(0, 'candleTime'))

        remainFlag = True
        
        for i in range(indexlen-1, -1, -1):

            candleTime = self.df.get_value(i, 'candleTime')
            if lasttime==int(candleTime):
                print('')
                print("[insertChartOnce()] candleTime " + candleTime + " exists")
                remainFlag = False

            values = [candleTime,
                      self.df.get_value(i, 'open'),
                      self.df.get_value(i, 'high'),
                      self.df.get_value(i, 'low'),
                      self.df.get_value(i, 'close'),
                      self.df.get_value(i, 'volume')]

            sUtil.insert(tablename, self.con, columns, values)

        self.df = None

        return not(remainFlag)
            

    # 차트 데이터 테이블 정렬
    def orderChartTable(self, tablename):

        sUtil.orderTable(tablename, self.con, 'candleTime')


    # 분봉 데이터 900개 이하를 stockDirectory의 종목코드.db 파일에 한번에 저장
    # 테이블 이름은 min(분단위숫자)
    # 분 단위는 1, 3, 5, 10, 15, 30, 45, 60 가능
    # 기존 저장 부분과 맞물리면 True, 빈틈이 생기면 False 반환
    def saveMinChartOnce(self, code, tick, modified = 1, screenNo = "0101"):

        filename = self.stockDirectory + '/' + code + '.db'
        tablename = 'min' + str(tick)

        rqname = code + '&' + tablename + '&saveMinChartOnce'
        trcode = 'opt10080'
        inputdic = {'종목코드' : code, '틱범위' : tick, '수정주가구분' : modified}        

        print('\n\n')
        print("-----------------------------------------------")
        print("[saveMinChartOnce()]    " + rqname)
        print("-----------------------------------------------")

        self.dbconnect(filename)

        self.makeChartTable(tablename)
        
        self.chartRequest(rqname, trcode, inputdic)

        ret = self.insertChartOnce(tablename)

        self.dbclose()

        return ret


    # 일봉 데이터를 900개 이하를 stockDirectory의 종목코드.db 파일에 한번에 저장
    # 테이블 이름은 day
    # date : YYYYMMDD 형식 (예 : "20170404")
    # 기존 저장 부분과 맞물리면 True, 빈틈이 생기면 False 반환
    def saveDayChartOnce(self, code, date='', modified = 1, screenNo = "0101"):

        date_ = date
        if date=='': date_ = self.today

        filename = self.stockDirectory + '/' + code + '.db'
        tablename = 'day'

        rqname = code + '&' + tablename + '&saveDayChartOnce'
        trcode = 'opt10081'
        inputdic = {'종목코드' : code, '기준일자' : date_, '수정주가구분' : modified}
        outputs = ['일자', '시가', '고가', '저가', '현재가', '거래량']
        
        print('\n\n')
        print("-----------------------------------------------")
        print("[saveDayChartOnce()]    " + rqname)
        print("-----------------------------------------------")

        self.dbconnect(filename)

        self.makeChartTable(tablename)
        
        self.chartRequest(rqname, trcode, inputdic)

        ret = self.insertChartOnce(tablename)

        self.dbclose()

        return ret


    # 주봉 데이터 900개 이하를 stockDirectory의 종목코드.db 파일에 한번에 저장
    # 테이블 이름은 week
    # date, enddate : YYYYMMDD 형식 (예 : "20170404")
    # 기존 저장 부분과 맞물리면 True, 빈틈이 생기면 False 반환
    def saveWeekChartOnce(self, code, date='', enddate='', modified = 1, screenNo = "0101"):

        date_ = date
        if date=='': date_ = self.today

        enddate_ = enddate
        if enddate=='': enddate_ = self.today

        filename = self.stockDirectory + '/' + code + '.db'
        tablename = 'week'

        rqname = code + '&' + tablename + '&saveWeekChartOnce'
        trcode = 'opt10082'
        inputdic = {'종목코드' : code, '기준일자' : date_, '끝일자' : enddate_, '수정주가구분' : modified}
        outputs = ['일자', '시가', '고가', '저가', '현재가', '거래량']
        
        print('\n\n')
        print("-----------------------------------------------")
        print("[saveWeekChartOnce()]    " + rqname)
        print("-----------------------------------------------")

        self.dbconnect(filename)

        self.makeChartTable(tablename)
        
        self.chartRequest(rqname, trcode, inputdic)

        ret = self.insertChartOnce(tablename)

        self.dbclose()

        return ret


    # 월봉 데이터 900개 이하를 stockDirectory의 종목코드.db 파일에 한번에 저장
    # 테이블 이름은 month
    # 기존 저장 부분과 맞물리면 True, 빈틈이 생기면 False 반환
    def saveMonthChartOnce(self, code, date='', enddate='', modified = 1, screenNo = "0101"):

        date_ = date
        if date=='': date_ = self.today

        enddate_ = enddate
        if enddate=='': enddate_ = self.today

        filename = self.stockDirectory + '/' + code + '.db'
        tablename = 'month'
        
        rqname = code + '&' + tablename + '&saveMonthChartOnce'
        trcode = 'opt10083'
        inputdic = {'종목코드' : code, '기준일자' : date_, '끝일자' : enddate_, '수정주가구분' : modified}
        outputs = ['일자', '시가', '고가', '저가', '현재가', '거래량']
        
        print('\n\n')
        print("-----------------------------------------------")
        print("[saveMonthChartOnce()]    " + rqname)
        print("-----------------------------------------------")

        self.dbconnect(filename)

        self.makeChartTable(tablename)
        
        self.chartRequest(rqname, trcode, inputdic)

        ret = self.insertChartOnce(tablename)

        self.dbclose()

        return ret

    
    # 분봉 데이터를 stockDirectory의 종목코드.db 파일에 저장
    # 테이블 이름은 min(분단위숫자)
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    # 분 단위는 1, 3, 5, 10, 15, 30, 45, 60 가능
    def saveMinChart(self, code, tick, maxIteration = -1, modified = 1, screenNo = "0101"):

        filename = self.stockDirectory + '/' + code + '.db'
        tablename = 'min' + str(tick)

        rqname = code + '&' + tablename + '&saveMinChart'
        trcode = 'opt10080'
        inputdic = {'종목코드' : code, '틱범위' : tick, '수정주가구분' : modified}        

        print('\n\n')
        print("-----------------------------------------------")
        print("[saveMinChart()]    " + rqname)
        print("-----------------------------------------------")

        self.dbconnect(filename)

        self.makeChartTable(tablename)
        
        self.chartRequest(rqname, trcode, inputdic)
        time.sleep(0.2)

        # 데이터 900개씩 추가 요청
        iteration = maxIteration
        
        while self.remainedData == True:

            iteration -= 1
            if iteration == 0 : break
            time.sleep(0.2)

            self.chartRequest(rqname, trcode, inputdic, 2)

        print('')
        print('[saveMinChart()] ordering...*')

        self.orderChartTable(tablename)

        self.dbclose()
    

    # 일봉 데이터를 stockDirectory의 종목코드.db 파일에 저장
    # 테이블 이름은 day
    # date : YYYYMMDD 형식 (예 : "20170404")
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    def saveDayChart(self, code, date='', maxIteration = -1, modified = 1, screenNo = "0101"):

        date_ = date
        if date=='': date_ = self.today

        filename = self.stockDirectory + '/' + code + '.db'
        tablename = 'day'

        rqname = code + '&' + tablename + '&saveDayChart'
        trcode = 'opt10081'
        inputdic = {'종목코드' : code, '기준일자' : date_, '수정주가구분' : modified}
        outputs = ['일자', '시가', '고가', '저가', '현재가', '거래량']
        
        print('\n\n')
        print("-----------------------------------------------")
        print("[saveDayChart()]    " + rqname)
        print("-----------------------------------------------")

        self.dbconnect(filename)

        self.makeChartTable(tablename)
        
        self.chartRequest(rqname, trcode, inputdic)
        time.sleep(0.2)

        # 데이터 900개씩 추가 요청
        iteration = maxIteration
        
        while self.remainedData == True:

            iteration -= 1
            if iteration == 0 : break
            time.sleep(0.2)

            self.chartRequest(rqname, trcode, inputdic, 2)

        print('')
        print('[saveDayChart()] ordering...*')

        self.orderChartTable(tablename)

        self.dbclose()


    # 주봉 데이터를 stockDirectory의 종목코드.db 파일에 저장
    # 테이블 이름은 week
    # date, enddate : YYYYMMDD 형식 (예 : "20170404")
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    def saveWeekChart(self, code, date='', enddate='', maxIteration = -1, modified = 1, screenNo = "0101"):

        date_ = date
        if date=='': date_ = self.today

        enddate_ = enddate
        if enddate=='': enddate_ = self.today

        filename = self.stockDirectory + '/' + code + '.db'
        tablename = 'week'

        rqname = code + '&' + tablename + '&saveWeekChart'
        trcode = 'opt10082'
        inputdic = {'종목코드' : code, '기준일자' : date_, '끝일자' : enddate_, '수정주가구분' : modified}
        outputs = ['일자', '시가', '고가', '저가', '현재가', '거래량']
        
        print('\n\n')
        print("-----------------------------------------------")
        print("[saveWeekChart()]    " + rqname)
        print("-----------------------------------------------")

        self.dbconnect(filename)

        self.makeChartTable(tablename)
        
        self.chartRequest(rqname, trcode, inputdic)
        time.sleep(0.2)

        # 데이터 900개씩 추가 요청
        iteration = maxIteration
        
        while self.remainedData == True:

            iteration -= 1
            if iteration == 0 : break
            time.sleep(0.2)

            self.chartRequest(rqname, trcode, inputdic, 2)

        print('')
        print('[saveWeekChart()] ordering...*')

        self.orderChartTable(tablename)

        self.dbclose()


    # 월봉 데이터를 stockDirectory의 종목코드.db 파일에 저장
    # 테이블 이름은 month
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    def saveMonthChart(self, code, date='', enddate='', maxIteration = -1, modified = 1, screenNo = "0101"):
        
        date_ = date
        if date=='': date_ = self.today

        enddate_ = enddate
        if enddate=='': enddate_ = self.today

        filename = self.stockDirectory + '/' + code + '.db'
        tablename = 'month'
        
        rqname = code + '&' + tablename + '&saveMonthChart'
        trcode = 'opt10083'
        inputdic = {'종목코드' : code, '기준일자' : date_, '끝일자' : enddate_, '수정주가구분' : modified}
        outputs = ['일자', '시가', '고가', '저가', '현재가', '거래량']
        
        print('\n\n')
        print("-----------------------------------------------")
        print("[saveMonthChart()]    " + rqname)
        print("-----------------------------------------------")

        self.dbconnect(filename)

        self.makeChartTable(tablename)
        
        self.chartRequest(rqname, trcode, inputdic)
        time.sleep(0.2)

        # 데이터 900개씩 추가 요청
        iteration = maxIteration
        
        while self.remainedData == True:

            iteration -= 1
            if iteration == 0 : break
            time.sleep(0.2)

            self.chartRequest(rqname, trcode, inputdic, 2)

        print('')
        print('[saveMonthChart()] ordering...*')

        self.orderChartTable(tablename)

        self.dbclose()



######################################################################################
# 여러 종목의 차트 저장 함수
######################################################################################



    # 받은 종목 코드 리스트에서 Flag가 세워진 차트 저장
    def saveCharts(self, codeList, minFlag, dayFlag, weekFlag, monthFlag, tick=5, date='', enddate=''):

        totalCodes = str(len(codeList))
        i = 0
        
        for code in codeList:

            i += 1

            print("\n\n")
            print("=============================================================================")
            print("[saveCharts()] " + code + "    (" + str(i) + "/" + totalCodes + ")")
            print("=============================================================================")

            if minFlag:
                self.saveMinChart(code, tick)

            if dayFlag:
                self.saveDayChart(code, date)

            if weekFlag:
                self.saveWeekChart(code, date, enddate)

            if monthFlag:
                self.saveMonthChart(code, date, enddate)


    # 지정 증거금률 이하의 종목 리스트에서 Flag가 세워진 차트 저장
    def saveChartsByMargin(self, marginLimit, minFlag, dayFlag, weekFlag, monthFlag, tick=5, date='', enddate=''):

        codeList = self.queryByMargint(marginLimit)
        self.saveCharts(codeList, minFlag, dayFlag, weekFlag, monthFlag, tick, date, enddate)
                
        


