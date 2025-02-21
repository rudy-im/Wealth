#-*- coding : utf-8 -*-

import sys, threading, time
from pandas import Series, DataFrame
import sqlite3
import sqlite3Util as sUtil
from Kiwoom import *

class KiwoomUtil():
    def __init__(self, kiwoom):
        super().__init__()
        self.kiwoom = kiwoom
        self.account = self.kiwoom.account[0]

        # testFlag == True 이면 테스트 로그를 콘솔에 print
        self.testFlag = False

        # 종목의 차트 등 종목코드.db 파일 저장 경로
        self.stockDirectory = 'stock data'

        # 종목코드-종목명 db 파일 & 테이블
        self.stocksCodeNameFile = 'stocks.db'
        self.stocksCodeNameTable = 'stocks'

        # time.sleep 간격
        self.timeInterval = 0.2

        # rqname 용
        self.rqNo = 0



######################################################################################
# Util 함수
######################################################################################


    # 데이터 조회 요청
    # outputs==[] 이면 모든 가능한 output 얻기
    def kiwoomRequest(self, rqname, trcode, inputdic, outputs=[], next=0, screen_no="0101"):
        
        for k, v in inputdic.items():
            
            try:
                self.kiwoom.setInputValue(k, v)
                
                if self.testFlag:
                    print("\n\n")
                    print("[kiwoomRequest()] setInputValue(" + str(k) + ", " + str(v) + ")")
                                        
            except:
                print("\n\n")
                print("[kiwoomRequest()] Failed to setInputValue()!!!")
                print("[kiwoomRequest()] k : " + str(k))
                print("[kiwoomRequest()] v : " + str(v))

        self.kiwoom.commRqData(rqname, trcode, next, screen_no, outputs)

        wait = threading.Thread(target=self.waitDuringQuery, args=[rqname])
        wait.start()
        wait.join()

        df = self.kiwoom.getRqResult(rqname)
        
        if self.testFlag:
            print("\n")
            print("[kiwoomRequest()] df = ")
            print(str(df))
        
        return df
    

    # kiwoomRequest() 에서 데이터 조회가 완료될 때까지 기다리는 thread 전용
    def waitDuringQuery(self, rqname):
        
        while True:
            
            time.sleep(self.timeInterval)
            
            if self.testFlag:
                print("\n")
                print("[waitDuringQuery()]")
                
            if self.kiwoom.isQueryFinished(rqname):
                
                if self.testFlag:
                    print("\n")
                    print("[waitDuringQuery()] Query is finished!!")
                    
                break
            

    # rqname 자동 부여
    def getRqname(self):
        self.rqNo += 1
        return 'rq' + str(self.rqNo)


    # 종목코드-종목명, 주식 상태 DB 생성
    # columns : 종목코드, 종목명, 수정날짜,
    #           증거금 비율, 거래정지, 관리종목, 감리종목, 투자유의종목, 담보대출, 액면분할, 신용가능
    def saveStocksInfo(self):
        
        con = sqlite3.connect(self.stocksCodeNameFile)
        tablename = self.stocksCodeNameTable
        now = sUtil.now()

        columnstr ='''code CHAR(6) NOT NULL UNIQUE,
                      name VARCHAR2(30) NOT NULL,
                      modified_date DATE NOT NULL,
                      margin NUMBER(3),
                      suspension CHAR(1),
                      administration CHAR(1),
                      surveillance CHAR(1),
                      attention CHAR(1),
                      loan CHAR(1),
                      split CHAR(1),
                      credit CHAR(1)'''

        sUtil.create(tablename, con, columnstr)

        checkDate = sUtil.select(tablename, con, 'modified_date', limit=1)

        if len(checkDate.index) != 0:
            date = 'date("' + checkDate.get_value(0, 'modified_date') + '")'
                
            if now == date:
                if self.testFlag:
                    print("\n\n")
                    print("[saveStocksCodeName()] now == date : True")
                
                return
        
        columns = ['code', 'name', 'modified_date']
        
        # 장내&코스닥 종목코드-이름을 self.stocksCodeNameTable 에 저장
        marketStocks = self.kiwoom.getCodeListByMarket(self.kiwoom.marketGubun["장내"])

        if self.testFlag:
            print("\n\n")
            print("[saveStocksCodeName()] marketStocks : ")
            print(marketStocks)
                
        for code in marketStocks:
            name = self.kiwoom.getMasterCodeName(code)
            sUtil.insert(tablename, con, columns, [code, name, [now]])


        kosdaqStocks = self.kiwoom.getCodeListByMarket(self.kiwoom.marketGubun["코스닥"])

        if self.testFlag:
            print("\n\n")
            print("[saveStocksCodeName()] kosdaqStocks : ")
            print(kosdaqStocks)
            
        for code in kosdaqStocks:
            name = self.kiwoom.getMasterCodeName(code)
            sUtil.insert(tablename, con, columns, [code, name, [now]])

        wherestr = 'modified_date!=' + now
        sUtil.delete(tablename, con, wherestr)

        allStocks = marketStocks + kosdaqStocks
        columns = ['margin', 'suspension', 'administration', 'surveillance', 'attention',
                   'loan', 'split', 'credit']
        
        for code in allStocks:
            
            values = [100, 'X', 'X', 'X', 'X', 'X', 'X', 'X']
            stockState = self.kiwoom.getMasterStockState(code).split('|')

            if self.testFlag:
                print("\n")
                print("[saveStocksCodeName()] stockState : ")
                print(stockState)
            
            for j in stockState:
                if j.startswith('증거금'):
                    margin = j.replace('증거금', '')
                    margin = margin.replace('%', '')
                    values[0] = int(margin)
                if j.startswith('거래정지'): values[1] = 'O'
                if j.startswith('관리종목'): values[2] = 'O'
                if j.startswith('감리종목'): values[3] = 'O'
                if j.startswith('투자유의종목'): values[4] = 'O'
                if j.startswith('담보대출'): values[5] = 'O'
                if j.startswith('액면분할'): values[6] = 'O'
                if j.startswith('신용가능'): values[7] = 'O'

            sUtil.update(tablename, con, columns, values, 'code = "' + code + '"')
        
        con.close()


    # 1초 간격의 실시간 데이터 저장
    # 파일명 : realtime data/YYYYMMDD.db
    # 테이블명 : r종목코드
    # 칼럼명 : realtime, price, volume
    # realtime은 hhmmss 형식의 6자리 문자열
    def saveRealtimeData(self, fp, dataFrame, realtime):

        dfcolumns = list(dataFrame.columns)
        
        if self.testFlag:
            print("\n\n")
            print("[saveRealtimeData()] dfcolumns : ")
            print(dfcolumns)

        if (dfcolumns.count('code')==0 or
           dfcolumns.count('price')==0 or
           dfcolumns.count('volume')==0):

            print("[saveRealtimeData()] dataFrame column is wrong!!")
            return
        
        try:
            fp.write('\n')
            fp.write('realtime\t' + str(realtime) + '\n')

            for i in dataFrame.index:
                fp.write(dataFrame.get_value(i, 'code') + '\t' +
                         dataFrame.get_value(i, 'price') + '\t' +
                         dataFrame.get_value(i, 'volume') + '\n')
            
        except:
            print("\n\n")
            print("[saveRealtimeData()] Failed to saveRealtimeData()!!!")
        


    # 지정한 파일의 지정한 테이블에 데이터 저장
    # dataFrame 의 칼럼은 반드시 candleTime, open, high, low, close, volume 포함
    def saveChart(self, filename, tablename, dataFrame):
        
        dfcolumns = list(dataFrame.columns)

        if self.testFlag:
            print("\n\n")
            print("[saveChart()] dfcolumns : ")
            print(dfcolumns)

        if (dfcolumns.count('candleTime')==0 or
           dfcolumns.count('open')==0 or
           dfcolumns.count('high')==0 or
           dfcolumns.count('low')==0 or
           dfcolumns.count('close')==0 or
           dfcolumns.count('volume')==0):

            print("[saveChart()] dataFrame column is wrong!!")
            return
        
        try:
            con = sqlite3.connect(filename)

            columstr = '''candleTime CHAR(25) NOT NULL UNIQUE,
                          open NUMBER(10) NOT NULL,
                          high NUMBER(10) NOT NULL,
                          low NUMBER(10) NOT NULL,
                          close NUMBER(10) NOT NULL,
                          volume NUMBER(20) NOT NULL'''
            sUtil.create(tablename, con, columnstr)
            
            sUtil.insertDataFrame(tablename, con, dataFrame)

            con.close()
            
        except:
            print("\n\n")
            print("[saveChart()] Failed to saveChart()!!!")
        
    
    # 분봉 데이터를 stockDirectory의 종목코드.db 파일에 저장
    # 테이블 이름은 min(분단위숫자)
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    def saveMinChart(self, rqname, code, tick, maxIteration = -1, modified = 1, screenNo = "0101"):
        
        trcode = 'opt10080'
        inputdic = {'종목코드' : code, '틱범위' : tick, '수정주가구분' : modified}
        outputs = ['체결시간', '시가', '고가', '저가', '현재가', '거래량']
        filename = stockDirectory + '/' + code + '.db'
        tablename = 'min' + str(tick)
        
        # 데이터 900개 요청
        df = self.kiwoomRequest(rqname, trcode, inputdic, outputs, 0)

        if self.testFlag:
            print("\n\n")
            print("[saveMinChart()] df : ")
            print(df)
        
        self.saveChart(filename, tablename, df)

        # 데이터 900개씩 추가 요청
        iteration = maxIteration
        
        while self.kiwoom.remainedData == True:
            
            iteration -= 1
            if iteration == 0 : break
            time.sleep(self.timeInterval)
            
            df = self.kiwoomRequest(rqname, trcode, inputdic, outputs, 2)

            if self.testFlag:
                print("\n")
                print("[saveMinChart()] df : ")
                print(df)
            
            self.saveChart(filename, tablename, df)
    

    # 일봉 데이터를 stockDirectory의 종목코드.db 파일에 저장
    # 테이블 이름은 day
    # date : YYYYMMDD 형식 (예 : "20170404")
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    def saveDayChart(self, rqname, code, date, maxIteration = -1, modified = 1, screenNo = "0101"):
        
        trcode = 'opt10081'
        inputdic = {'종목코드' : code, '기준일자' : date, '수정주가구분' : modified}
        outputs = ['일자', '시가', '고가', '저가', '현재가', '거래량']
        filename = stockDirectory + '/' + code + '.db'
        tablename = 'day'
        
        # 데이터 900개 요청
        df = self.kiwoomRequest(rqname, trcode, inputdic, outputs, 0)

        if self.testFlag:
            print("\n\n")
            print("[saveDayChart()] df : ")
            print(df)
        
        self.saveChart(filename, tablename, df)
        

        # 데이터 900개씩 추가 요청
        iteration = maxIteration
        
        while self.kiwoom.remainedData == True:
            
            iteration -= 1
            if iteration == 0 : break
            time.sleep(self.timeInterval)
            
            df = self.kiwoomRequest(rqname, trcode, inputdic, outputs, 2)

            if self.testFlag:
                print("\n")
                print("[saveDayChart()] df : ")
                print(df)
            
            self.saveChart(filename, tablename, df)


    # TODO
    # 해당 trcode에 맞춰 나머지 양식 작성해야 함
    # 주봉 데이터를 stockDirectory의 종목코드.db 파일에 저장
    # 테이블 이름은 week
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    def saveWeekChart(self, rqname, code, date, maxIteration = -1, modified = 1, screenNo = "0101"):
        pass


    # TODO
    # 해당 trcode에 맞춰 나머지 양식 작성해야 함
    # 월봉 데이터를 stockDirectory의 종목코드.db 파일에 저장
    # 테이블 이름은 month
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    def saveMonthChart(self, rqname, code, date, maxIteration = -1, modified = 1, screenNo = "0101"):
        pass


    # 주문번호를 알아낼 때까지 대기하는 thread 전용
    def getOrderNo(self):
        
        while True:
            
            time.sleep(self.timeInterval)

            chejan = self.kiwoom.getOneFromChejanpool()

            if self.testFlag:
                print("\n")
                print("[getOrderNo()] chejan : ")
                print(chejan)
            
            if chejan!=None:
                
                if chejan.get('주문상태')=='접수':

                    self.tmpOrderNo = chejan.get('주문번호')
                    
                    if self.testFlag:
                        print("\n")
                        print("[getOrderNo()] self.tmpOrderNo : " + self.tmpOrderNo)
                        
                    break
    

    # 종목 매수 후 주문번호 반환
    def buy(self, rqname, code, price, quantity, screenNo = "0101"):

        self.testFlag = True

        if self.testFlag:
            print("\n\n")
            print("[buy()]")
        
        # price = 0 이면 시장가에 매수. 아니면 지정가 매수.
        gubun = self.kiwoom.orderGubun["지정가"]
        if price==0: gubun = self.kiwoom.orderGubun["시장가"]

        ret = self.kiwoom.sendOrder(rqname, screenNo, self.account, self.kiwoom.orderType["신규매수"],
                                    code, quantity, price, gubun, '')

        self.tmpOrderNo = ''

        # 주문 성공 시
        if ret==0:
            wait = threading.Thread(target=self.getOrderNo)
            wait.start()
            wait.join()

        self.testFlag = False


        return self.tmpOrderNo


    # 종목 매도
    def sell(self, rqname, code, price, quantity, screenNo = "0101"):

        self.testFlag = True

        if self.testFlag:
            print("\n\n")
            print("[sell()]")
            
        # price = 0 이면 시장가에 매도. 아니면 지정가 매도.
        gubun = self.kiwoom.orderGubun["지정가"]
        if price==0: gubun = self.kiwoom.orderGubun["시장가"]
        
        ret = self.kiwoom.sendOrder(rqname, screenNo, self.account, self.kiwoom.orderType["신규매도"],
                                    code, quantity, price, gubun, '')

        self.tmpOrderNo = ''

        # 주문 성공 시
        if ret==0:
            wait = threading.Thread(target=self.getOrderNo)
            wait.start()
            wait.join()

        self.testFlag = False

        return self.tmpOrderNo


    # 매수 취소 (price 부분이 반드시 ''이어야 함)
    # 미체결수량을 0으로 만듬
    def cancelBuy(self, rqname, originalOrder, code, screenNo = "0101"):
        
        if self.testFlag:
            print("\n\n")
            print("[cancelBuy()]")
            
        ret = self.kiwoom.sendOrder(rqname, screenNo, self.account, self.kiwoom.orderType["매수취소"],
                                    code, 0, '', '', originalOrder)

        return ret


    # 매도 취소 (price 부분이 반드시 ''이어야 함)
    # 미체결수량을 0으로 만듬
    def cancelSell(self, rqname, originalOrder, code, screenNo = "0101"):
        
        if self.testFlag:
            print("\n\n")
            print("[cancelSell()]")
            
        self.kiwoom.sendOrder(rqname, screenNo, self.account, self.kiwoom.orderType["매도취소"],
                              code, 0, '', '', originalOrder)


    # 매수 정정
    # 사용하지 말 것
    def changeBuy(self, rqname, originalOrder, code, price, quantity, screenNo = "0101"):

        self.testFlag = True


        if self.testFlag:
            print("\n\n")
            print("[changeBuy()]")
            
        # price = 0 이면 시장가에 매도. 아니면 지정가 매도.
        gubun = self.kiwoom.orderGubun["지정가"]
        if price==0: gubun = self.kiwoom.orderGubun["시장가"]
        
        ret = self.kiwoom.sendOrder(rqname, screenNo, self.account, self.kiwoom.orderType["매수정정"],
                                    code, quantity, price, gubun, originalOrder)

        return ret


    # 매도 정정
    # 사용하지 말 것
    def changeSell(self, rqname, originalOrder, code, price, quantity, screenNo = "0101"):

        self.testFlag = True


        if self.testFlag:
            print("\n\n")
            print("[changeSell()]")
            
        # price = 0 이면 시장가에 매도. 아니면 지정가 매도.
        gubun = self.kiwoom.orderGubun["지정가"]
        if price==0: gubun = self.kiwoom.orderGubun["시장가"]
        
        
        ret = self.sendOrder(rqname, screenNo, self.account, self.kiwoom.orderType["매도정정"],
                             code, quantity, price, gubun, originalOrder)

        self.tmpOrderNo = ''

        # 주문 성공 시
        if ret==0:
            wait = threading.Thread(target=self.getOrderNo)
            wait.start()
            wait.join()

        self.testFlag = False

        return self.tmpOrderNo


    # 지정 증거금 이하 종목 코드를 리스트로 반환
    # withName이 True이면 {종목코드:종목명} 의 dic 반환
    def queryByMargin(self, marginLimit=20, withName=False):
        
        con = sqlite3.connect(self.stocksCodeNameFile)

        selectstr = 'code, '
        if withName: selectstr = selectstr + 'name, '
        selectstr = selectstr + 'margin'
        
        selected = sUtil.select(self.stocksCodeNameTable, con, selectstr, 'margin <= ' + str(marginLimit))
        
        codeList = list(selected['code'])

        if withName:
            nameList = list(selected['name'])
            ret = dict((codeList[i], nameList[i]) for i in range(len(codeList)))
            return ret 
            
        return codeList


    # 종목코드 <-> 종목명 변환
    def convertCodeOrName(self, codeOrName):
        
        con = sqlite3.connect(self.stocksCodeNameFile)
        ret = sUtil.select(self.stocksCodeNameTable, con, 'code, name', 'code = "' + codeOrName + '"')

        if self.testFlag:
            print("\n\n")
            print("[convertCodeOrName()] ret :")
            print(ret)

        if len(ret.index)==0:
            ret2 = sUtil.select('stocks', con, 'code, name', 'name = "' + codeOrName + '"')

            if self.testFlag:
                print("[convertCodeOrName()] ret2 :")
                print(ret2)
            
            if len(ret2.index)!=0:
                return ret2.get_value(0, 'code')
            else:
                return ''
        
        else:
            return ret.get_value(0, 'name')


    # 실시간 시세 등록
    def setRealtime(self, codelist, fidlist=None, option='0'):

        if self.testFlag:
            print("\n\n")
            print("[setRealtime()]")
        
        if fidlist==None:
            fidlist = [str(self.kiwoom.convertFid("현재가"))]
        
        while True:
            if len(codelist)>100:
                self.kiwoom.setRealReg('0101', ';'.join(codelist[0:100]), ';'.join(fidlist), option)
                codelist = codelist[100:]
            else:
                self.kiwoom.setRealReg('0101', ';'.join(codelist), ';'.join(fidlist), option)
                break



    # 실시간 시세 해지
    def clearRealtime(self, code='ALL'):
        
        ret = self.kiwoom.setRealRemove('0101', code)

        if self.testFlag:
            print("\n\n")
            print("[clearRealtime()] ret : " + str(ret))
            
        return ret


    # 해당 종목의 현재가 반환
    def getNowPrice(self, code):
        
        trcode = 'opt10003'
        inputdic = {"종목코드" : code}
        outputs = ["현재가"]
        
        df = self.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs)

        ret = abs(int(df.get_value(0, '현재가')))
        
        return ret


    # 해당 종목의 매수호가+1 반환
    def getBuyPricePlus(self, code):
        
        trcode = 'opt10004'
        inputdic = {"종목코드" : code}
        outputs = ["매수최우선호가", "매수2차선호가"]
        
        df = self.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs)

        ret = 2 * abs(int(df.get_value(0, '매수최우선호가'))) - abs(int(df.get_value(0, '매수2차선호가')))
        
        return ret


    # 해당 종목의 매도호가-1 반환
    def getSellPriceMinus(self, code):
        
        trcode = 'opt10004'
        inputdic = {"종목코드" : code}
        outputs = ["매도최우선호가", "매도2차선호가"]
        
        df = self.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs)

        ret = 2 * abs(int(df.get_value(0, '매도최우선호가'))) - abs(int(df.get_value(0, '매도2차선호가')))
        
        return ret


    # 현재 시간을 hhmmss 형식으로 반환.
    # rettype이 str이면 문자열, 그 외엔 int로 반환.
    # TODO :: str 변환 시 6자리로 고정(예 : 093241)
    def getNow(rettype='int'):
        localtime = time.localtime()
        now = localtime.tm_hour * 10000 + localtime.tm_min * 100 + localtime.tm_sec

        #print("[getNow()] now : " + str(now))

        if rettype == 'str':
            return str(now)
        else:
            return now
