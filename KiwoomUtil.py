#-*- coding : utf-8 -*-

import sys, threading, time
import sqlite3
import sqlite3Util as sUtil
import timeUtil as tUtil
from Kiwoom import *
from pandas import DataFrame



##############################################################
# ** 주의 **
#
# Kiwoom API 자체에서, 쿼리에 대한 응답을 받지 못하고
# 무한 대기하는 경우 존재.
# 자체적으로 커버할 수 있도록 처리해야 함.
# 쿼리 시 시간간격을 0.2초 정도는 두고 사용할 것.
# 주문 또한 초당 5회 제한이지만, 그보다는 여유를 두고 사용.
##############################################################


class KiwoomUtil(Kiwoom):
    
    def __init__(self):
        
        super().__init__()

        self.testFlag = False

        # 계좌
        self.account = ''

        # 종목의 차트 등 종목코드.db 파일 저장 경로
        self.stockDirectory = 'stock data'

        # 종목코드-종목명 db 파일 & 테이블
        self.stocksCodeNameFile = 'stocks.db'
        self.stocksCodeNameTable = 'stocks'

        # time.sleep 간격
        self.timeInterval = 0.2

        # rqname 용
        self.rqNo = 0

        # request pool
        # 쿼리 요청 시 rqname : outputlist
        # 쿼리 완료 시 rqname : outputdataframe
        self.rqpool = {}

        # 실시간 pool
        # 종목코드 : [현재가, 총거래량, 매수최우선호가, 매도최우선호가]
        self.realpool = {}

        # 체결/잔고 pool
        # pool 리스트 내에는 {fid의미 : 값} 형식의 dic 저장
        # 10개 이상이면 1개씩 비움
        self.chejanpool = []

        # 잔고 내역
        self.balance = {'총매입':0, '총평가':0, '총손익':0, '총수익률':0,
                        'D+1예수금':0, 'D+1정산금액':0, 'D+1추정인출가능금':0,
                        'D+2예수금':0, 'D+2정산금액':0, 'D+2추정인출가능금':0}

        # 잔고 pool
        # 종목코드 : [종목명, 손익율, 주문가능수량, 보유수량, 매입단가, 현재가]
        self.balancepool = {}

        # 주문 pool
        # 주문번호 : [코드, 종목명, 구분(매수/매도), 주문가격, 현재가,
        #             주문수량, 체결수량, 미체결수량, 주문/체결시간, 원주문번호]
        # 미체결수량이 0이 되면 제거
        self.orderpool = {}



######################################################################################
# Event 함수 overriding
######################################################################################



    # (이벤트) 로그인 성공 시 알림
    def eventConnect(self, err_code):
        
        self.account = self.getAccountList()[0]
        self.saveStocksInfo()
        self.initBalance()
        self.initBalancepool()
        self.initOrderpool()


    # (이벤트) 받은 쿼리 결과에 따른 처리
    # GetCommData() 사용
    def receiveTrData(self, screen_no, rqname, trcode, record_name):

        # rqpool에 저장되어 있는, 얻고자 하는 출력 리스트 얻기
        # rqpool에 등록되지 않은 경우, 즉 KiwoomUtil의 전용 쿼리 함수를 사용하지 않았는데
        # 데이터가 도착한 경우, return
        outputs = self.rqpool.get(rqname)
        if outputs==None: return

        # 전달 받은 데이터의 행 수만큼 반복
        repeatCnt = self.getRepeatCnt(trcode, rqname)
        indices = range(repeatCnt)
        if repeatCnt==0: indices = [0]

        if self.testFlag:
            print("\n\n")
            print("[receiveTrData()] repeatCnt : " + str(repeatCnt))
            print("[receiveTrData()] indices : " + str(indices))
            print("[receiveTrData()] outputs : " + str(outputs))

        # 행 이름은 그냥 숫자, 열 이름은 output 이름인 DataFrame 객체에 데이터 넣기
        df = DataFrame(index = indices, columns = outputs)

        for i in indices:
            for o in outputs:
                data = self.getCommData(trcode, rqname, i, o)
                df.set_value(i, o, data)

        if self.testFlag:
            print("")
            print("[receiveTrData()] df : ")
            print(df)

        # 쿼리가 완료된 경우, rqpool에 해당 데이터프레임 세팅
        self.rqpool[rqname] = df

        # rqpool이 10개 초과인 경우, 가장 오래된 항목 삭제
        if len(self.rqpool)>20: self.rqpool.pop(list(self.rqpool.keys())[0])
        

    # (이벤트) 실시간 데이터 수신. SetRealReg()로 등록한 실시간 데이터 포함.
    # realType : '주식체결' 등... 문자열. 
    # realData : getRealIndex() 참조. 문자열.
    # GetCommRealData(), getRealData() 사용
    # realpool 에 종목코드 : [현재가, 누적거래량, 최우선매수호가, 최우선매도호가] 저장
    def receiveRealData(self, code, realType, realData):

        # realpool에 등록되지 않은 종목은 무시
        if self.realpool.get(code)==None: return
        
        if realType == '주식체결':

            realdata = self.getRealData(code, realType, ['현재가', '누적거래량'])
            
            if self.realpool.get(code)!=None:
                
                self.realpool[code][0] = abs(int(realdata['현재가']))
                self.realpool[code][1] = int(realdata['누적거래량'])
                
            else:
                
                self.realpool[code] = [abs(int(realdata['현재가'])), int(realdata['누적거래량']), 0, 0]
                
        elif realType == '주식우선호가':

            realdata = self.getRealData(code, realType, [])

            if self.realpool.get(code)!=None:
                
                self.realpool[code][2] = abs(int(realdata['(최우선)매수호가']))
                self.realpool[code][3] = abs(int(realdata['(최우선)매도호가']))
                
            else:
                
                self.realpool[code] = [0, 0, abs(int(realdata['(최우선)매수호가'])), abs(int(realdata['(최우선)매도호가']))]

        if self.testFlag:
            print("\n\n")
            print('[receiveRealData()] self.realpool[code] : ', self.realpool[code])


    # (이벤트) 주문 접수, 체결 통보, 잔고 통보
    # GetChejanData() 사용
    # gubun은 체결 접수 및 체결 시 '0', 국내주식 잔고전달은 '1', 파생잔고전달은 '4'
    # gubun의 데이터 타입은 str
    # fidListStr : fid를 세미콜론(;) 으로 구분. fid는 int형으로 사용할 것.
    # fid 사용 시 self.convertFid()로 fid <-> 의미 변환
    def receiveChejanData(self, gubun, itemCnt, fidListStr):
        fidList = fidListStr.split(';')
        fidList = [int(fidList[i]) for i in range(itemCnt)]

        # {fid의미:값} 의 dic 세팅
        chejanResult = {}

        for fid in fidList:
            fidMeaning = self.convertFid(fid)
            tmp = self.getChejanData(fid)
            if fidMeaning!=None: chejanResult[fidMeaning] = tmp

        print('')
        print(chejanResult)
        
        if self.testFlag:
            print("\n")
            print('[receiveChejanData()] chejanResult : ')
            print(chejanResult)

        # chejanpool 채우기
        self.chejanpool.append(chejanResult)

        # chejanpool이 10개 이상이면 오래된 것부터 1개씩 비우기
        if len(self.chejanpool)>10:
            self.chejanpool = self.chejanpool[1:]

        # orderpool 채우기
        if gubun == '0':
            self.updateOrderpool(chejanResult)

        # balance, balancepool 채우기
        elif gubun == '1':
            self.updateBalancepool(chejanResult)
            self.updateBalance()
            
        

######################################################################################
# 기타 내부 위주 함수
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

    
    # 종목코드-종목명, 주식 상태 DB 생성
    # columns : 종목코드, 종목명, 수정날짜, 시장구분(코스닥_D/코스피_P),
    #           증거금 비율, 거래정지, 관리종목, 감리종목, 투자유의종목, 담보대출, 액면분할, 신용가능
    def saveStocksInfo(self):

        print('\n\n')
        print("[saveStocksInfo()] Now Saving Stocks' Information....*")

        con = sqlite3.connect(self.stocksCodeNameFile)
        tablename = self.stocksCodeNameTable
        now = tUtil.getToday(withDateFunc=True)

        # 테이블이나 db가 없으면 새로운 테이블 생성
        columnstr ='''code CHAR(6) NOT NULL UNIQUE,
                      name VARCHAR2(30) NOT NULL,
                      modified_date DATE NOT NULL,
                      market CHAR(1),
                      margin NUMBER(3),
                      suspension CHAR(1),
                      administration CHAR(1),
                      surveillance CHAR(1),
                      attention CHAR(1),
                      loan CHAR(1),
                      split CHAR(1),
                      credit CHAR(1)'''

        sUtil.create(tablename, con, columnstr)

        # 오늘자 정보가 이미 업데이트 되어 있으면 패스
        checkDate = sUtil.select(tablename, con, 'modified_date', limit=1)

        if len(checkDate.index) != 0:
            date = 'date("' + checkDate.get_value(0, 'modified_date') + '")'
                
            if now == date:
                if self.testFlag:
                    print("\n\n")
                    print("[saveStocksCodeName()] now == date : True")
                
                return
        
        columns = ['code', 'name', 'modified_date', 'market']
        
        # 장내(코스피) 종목코드-이름을 self.stocksCodeNameTable 에 저장
        marketStocks = self.getCodeListByMarket(self.marketGubun["장내"])

        if self.testFlag:
            print("\n\n")
            print("[saveStocksCodeName()] marketStocks : ")
            print(marketStocks)
                
        for code in marketStocks:
            name = self.getMasterCodeName(code)
            sUtil.insert(tablename, con, columns, [code, name, [now], 'P'])


        # 코스닥 종목코드-이름을 self.stocksCodeNameTable 에 저장
        kosdaqStocks = self.getCodeListByMarket(self.marketGubun["코스닥"])

        if self.testFlag:
            print("\n\n")
            print("[saveStocksCodeName()] kosdaqStocks : ")
            print(kosdaqStocks)
            
        for code in kosdaqStocks:
            name = self.getMasterCodeName(code)
            sUtil.insert(tablename, con, columns, [code, name, [now], 'D'])

        # 수정 날짜가 오늘이 아닌 것들, 즉 사라진 종목들 정보 삭제
        wherestr = 'modified_date!=' + now
        sUtil.delete(tablename, con, wherestr)

        # 주식 증거금 비율, 상태 등 등록
        allStocks = marketStocks + kosdaqStocks
        columns = ['margin', 'suspension', 'administration', 'surveillance', 'attention',
                   'loan', 'split', 'credit']
        
        for code in allStocks:
            
            values = [100, 'X', 'X', 'X', 'X', 'X', 'X', 'X']
            stockState = self.getMasterStockState(code).split('|')
            
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


    # 잔고 내역 중 D+1, D+2 예수금 관련 내용 세팅
    # 최초 프로그램 시작 시 수행
    def initBalance(self):

        rqname = 'initBalance'
        trcode = 'opw00001'
        inputdic = {'계좌번호' : self.account,
                    '비밀번호' : '',
                    '비밀번호입력매체구분' : '00',
                    '조회구분' : '1'}
        outputs = ["d+1추정예수금", "d+1매도매수정산금", "d+1출금가능금액",
                   "d+2추정예수금", "d+2매도매수정산금", "d+2출금가능금액"]
        
        df = self.kiwoomRequest(rqname, trcode, inputdic, outputs)

        if len(df.index)!=0:
            self.balance['D+1예수금'] = int(df.get_value(0, "d+1추정예수금"))
            self.balance['D+1정산금액'] = int(df.get_value(0, "d+1매도매수정산금"))
            self.balance['D+1추정인출가능금'] = int(df.get_value(0, "d+1출금가능금액"))
            self.balance['D+2예수금'] = int(df.get_value(0, "d+2추정예수금"))
            self.balance['D+2정산금액'] = int(df.get_value(0, "d+2매도매수정산금"))
            self.balance['D+2추정인출가능금'] = int(df.get_value(0, "d+2출금가능금액"))

        if self.testFlag:
            print('\n\n')
            print('[initBalance()] self.balance : ')
            print(self.balance)
        

    # 잔고 내역 중 총매입, 총평가, 총손익, 총수익률 세팅
    # query 결과로 얻은 DataFrame을 balancepool에 세팅
    # balancepool = { 종목코드 : [종목명, 손익율, 주문가능수량, 보유수량, 매입단가, 현재가] ... }
    # 최초 프로그램 시작 시 수행.
    def initBalancepool(self):
        
        rqname = 'initBalancepool'
        trcode = 'OPW00004'
        inputdic = {'계좌번호' : self.account,
                    '비밀번호' : '',
                    '상장폐지조회구분' : '0',
                    '비밀번호입력매체구분' : '00'}
        outputs = ["총매입금액", "추정예탁자산", "당일투자손익", "당일손익율",  # single data
                   "종목코드", "종목명", "손익율", "결제잔고", "보유수량", "평균단가", "현재가"] # multi data

        df = self.kiwoomRequest(rqname, trcode, inputdic, outputs)

        if len(df.index)!=0:
            self.balance['총매입'] = int(df.get_value(0, "총매입금액"))
            self.balance['총평가'] = int(df.get_value(0, "추정예탁자산"))
            self.balance['총손익'] = int(df.get_value(0, "당일투자손익"))
            self.balance['총수익률'] = int(df.get_value(0, "당일손익율"))

        self.balancepool = {}

        for i in df.index:
            
            code = df.get_value(i, '종목코드')
            if code=='': break
            
            self.balancepool[code[1:]] = [df.get_value(i, '종목명'),
                                         int(df.get_value(i, '손익율')),
                                         int(df.get_value(i, '결제잔고')),
                                         int(df.get_value(i, '보유수량')),
                                         int(df.get_value(i, '평균단가')),
                                         int(df.get_value(i, '현재가'))]

        if self.testFlag:
            print('\n\n')
            print('[initBalancepool()] self.balance : ')
            print(self.balance)
            print('')
            print('[initBalancepool()] self.balancepool : ')
            print(self.balancepool)
    

    # query 결과로 얻은 DataFrame을 orderpool에 세팅
    # orderpool = { 주문번호 : [코드, 종목명, 구분(매수/매도), 주문가격, 현재가, 
    #                           주문수량, 체결수량, 미체결수량, 주문/체결시간, 원주문번호] ... }
    # 최초 프로그램 시작 시 수행.
    def initOrderpool(self):

        rqname = 'initOrderpool'
        trcode = 'opt10075'
        inputdic = {'계좌번호' : self.account,
                    '체결구분' : '0',
                    '매매구분' : '0'}
        outputs = ['주문번호', '종목코드', '종목명', '주문구분', '주문가격', '현재가',
                   '주문수량', '체결량', '미체결수량', '시간', '원주문번호']

        df = self.kiwoomRequest(rqname, trcode, inputdic, outputs)

        self.orderpool = {}

        for i in df.index:

            orderNo = df.get_value(i, '주문번호')
            if orderNo=='': break

            notFinishedQuantity = int(df.get_value(i, '미체결수량'))
            if notFinishedQuantity==0: continue

            ordertype = df.get_value(i, '주문구분')
            if ordertype=='+매수' : ordertype = '매수'
            elif ordertype=='-매도' : ordertype = '매도'
            
            self.orderpool[orderNo] = [df.get_value(i, '종목코드'),
                                       df.get_value(i, '종목명'),
                                       ordertype,
                                       int(df.get_value(i, '주문가격')),
                                       int(df.get_value(i, '현재가')),
                                       int(df.get_value(i, '주문수량')),
                                       int(df.get_value(i, '체결량')),
                                       notFinishedQuantity,
                                       int(df.get_value(i, '시간')),
                                       df.get_value(i, '원주문번호')]

        if self.testFlag:
            print('\n\n')
            print('[initOrderpool()] self.orderpool : ')
            print(self.orderpool)


    # 잔고 내역 업데이트
    def updateBalance(self):

        # query 1
        trcode = 'OPW00004'
        inputdic = {'계좌번호' : self.account,
                    '비밀번호' : '',
                    '상장폐지조회구분' : '0',
                    '비밀번호입력매체구분' : '00'}
        outputs = ["총매입금액", "추정예탁자산", "당일투자손익", "당일손익율",  # single data
                   "종목코드", "종목명", "평균단가", "손익금액", "손익율",      # 이하는 multi data
                   "결제잔고", "보유수량", "현재가", "매입금액", "평가금액"]

        df = self.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs)
        
        if len(df.index)!=0:
            self.balance['총매입'] = int(df.get_value(0, "총매입금액"))
            self.balance['총평가'] = int(df.get_value(0, "추정예탁자산"))
            self.balance['총손익'] = int(df.get_value(0, "당일투자손익"))
            self.balance['총수익률'] = int(df.get_value(0, "당일손익율"))

        # query 2
        trcode = 'opw00001'
        inputdic = {'계좌번호' : self.account,
                    '비밀번호' : '',
                    '비밀번호입력매체구분' : '00',
                    '조회구분' : '1'}
        outputs = ["d+1추정예수금", "d+1매도매수정산금", "d+1출금가능금액",
                   "d+2추정예수금", "d+2매도매수정산금", "d+2출금가능금액"]
        
        df = self.KUtil.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs)

        if len(df.index)!=0:
            self.balance['D+1예수금'] = int(df.get_value(0, "d+1추정예수금"))
            self.balance['D+1정산금액'] = int(df.get_value(0, "d+1매도매수정산금"))
            self.balance['D+1추정인출가능금'] = int(df.get_value(0, "d+1출금가능금액"))
            self.balance['D+2예수금'] = int(df.get_value(0, "d+2추정예수금"))
            self.balance['D+2정산금액'] = int(df.get_value(0, "d+2매도매수정산금"))
            self.balance['D+2추정인출가능금'] = int(df.get_value(0, "d+2출금가능금액"))
        

    # chejan event 에서 얻은 결과로 balancepool 갱신
    # balancepool = { 종목코드 : [종목명, 손익율, 주문가능수량, 보유수량, 매입단가, 현재가] ... }
    # chejan event 구분이 국내주식 잔고전달('1') 인 경우
    def updateBalancepool(self, chejanResult):

        code = chejanResult['종목코드'][1:]

        self.balancepool[code] = [chejanResult['종목명'],
                                  int(chejanResult['손익율']),
                                  int(chejanResult['주문가능수량']),
                                  int(chejanResult['보유수량']),
                                  int(chejanResult['매입단가']),
                                  abs(int(chejanResult['현재가']))]

        if self.testFlag:
            print('\n\n')
            print('[updateBalancepool()] self.balancepool : ')
            print(self.balancepool)


    # chejan event 에서 얻은 결과로 orderpool 갱신
    # orderpool = { 주문번호 : [코드, 종목명, 구분(매수/매도), 주문가격, 현재가, 
    #                           주문수량, 체결수량, 미체결수량, 주문/체결시간, 원주문번호] ... }
    # chejan event 구분이 체결 접수 및 체결 ('0') 인 경우
    def updateOrderpool(self, chejanResult):

        orderNo = chejanResult['주문번호']

        finishedQuantity = self.int(chejanResult['체결량'])
        notFinishedQuantity = self.int(chejanResult['미체결수량'])

        code = chejanResult['종목코드'][1:]

        if self.orderpool.get(orderNo)!=None:

            # 미체결수량이 0이고 orderpool에 있으면 체결 완료이고 아직 안 지워진 것
            # 체결이 완료되었으므로 orderpool에서 제거
            if notFinishedQuantity == 0:
                self.orderpool.pop(orderNo)
                return

            # 미체결수량이 남아있는 경우, orderpool 업데이트
            self.orderpool[orderNo][4] = int(chejanResult['현재가'])
            self.orderpool[orderNo][6] = finishedQuantity
            self.orderpool[orderNo][7] = notFinishedQuantity

        else:

            # 미체결수량이 0이고 orderpool에 없으면 이미 지워진 것
            if notFinishedQuantity == 0: return

            # 미체결수량이 0이 아니고 orderpool에 없으면 새로운 주문
            ordertype = chejanResult['주문구분']
            if ordertype=='+매수' : ordertype = '매수'
            elif ordertype=='-매도' : ordertype = '매도'

            self.orderpool[orderNo] = [code,
                                       chejanResult['종목명'],
                                       ordertype,
                                       int(chejanResult['주문가격']),
                                       int(chejanResult['현재가']),
                                       int(chejanResult['주문수량']),
                                       finishedQuantity,
                                       notFinishedQuantity,
                                       int(chejanResult['주문/체결시간']),
                                       chejanResult['원주문번호']]

        if self.testFlag:
            print('\n\n')
            print('[updateOrderpool()] self.orderpool : ')
            print(self.orderpool)
            

    # 문자열을 int로 변환하되, 공백이면 0으로 변환
    def int(self, value):

        if value.strip() == '': return 0
        else: return int(value)

    

######################################################################################
# Util 함수
######################################################################################



    # rqname 자동 부여
    def getRqname(self):
        self.rqNo += 1
        return 'rq' + str(self.rqNo)
    
        
    # 데이터 조회 요청
    # outputs==[] 이면 모든 가능한 output 얻기
    # 관심종목 조회의 경우 inputdic은 사용하지 않고, codelist를 입력해야 함
    # 5회까지 쿼리 요청 보내고, 그 이상 실패 시 경고문
    # 단순 루프를 돌고 있으면 이벤트가 도착하지 않으므로, thread 내에서 루프를 돌며 대기
    def kiwoomRequest(self, rqname, trcode, inputdic, outputs=[], next=0, screenNo="0101", codelist=[]):

        self.rqpool[rqname] = self.getValidOutputs(trcode, outputs)

        for i in range(5):

            # 한 번에 100종목까지 조회하는 관심종목 조회의 경우
            if trcode=='OPTKWFID':

                codeCount = len(codelist)
                if (codeCount<=0 or codeCount>100): return                

                self.commKwRqData(';'.join(codelist), next, codeCount, 0, rqname, screenNo)
                

            # 일반 조회의 경우
            else:
                for k, v in inputdic.items():

                    self.setInputValue(k, v)
                    
                    if self.testFlag:
                        print("")
                        print("[kiwoomRequest()] setInputValue(" + str(k) + ", " + str(v) + ")")
                
                self.commRqData(rqname, trcode, next, screenNo)

            wait = threading.Thread(target=self.waitDuringQuery, args=[rqname])
            wait.start()
            wait.join()

            df = self.rqpool.pop(rqname)
            if type(df)==type(DataFrame()): return df

        # 루프를 다 도는 동안 쿼리 결과를 반환하지 못한 경우
        print("\n\n")
        print("[kiwoomRequest()] Query is failed!!!")
        
        self.rqpool.pop(rqname)
        

    # kiwoomRequest() 에서 데이터 조회가 완료될 때까지 기다리는 thread 전용
    def waitDuringQuery(self, rqname):
        
        for j in range(5):

            df = self.rqpool.get(rqname)
            if type(df)==type(DataFrame()): break

            time.sleep(0.05)



######################################################################################
        

    
    # 주문번호를 알아낼 때까지 대기하는 thread 전용
    def getOrderNo(self):

        for i in range(10):
            print(i)
            
            time.sleep(0.05)

            chejan = self.getOneFromChejanpool()
            print(chejan)

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
            
        if self.testFlag:
            print("\n\n")
            print("[buy()]")
        
        # price = 0 이면 시장가에 매수. 아니면 지정가 매수.
        gubun = self.orderGubun["지정가"]
        if price==0: gubun = self.orderGubun["시장가"]

        for i in range(5):

            print('sendorder')
            ret = self.sendOrder(rqname, screenNo, self.account, self.orderType["신규매수"],
                                 code, quantity, price, gubun, '')

            print(ret)

            self.tmpOrderNo = ''

            # 주문 성공 시
            if ret==0:
                wait = threading.Thread(target=self.getOrderNo)
                wait.start()
                wait.join()

            if self.tmpOrderNo!='': return self.tmpOrderNo

        # 루프를 다 도는 동안 쿼리 결과를 반환하지 못한 경우
        print("\n\n")
        print("[buy()] Order is failed!!!")



    # 종목 매도 후 주문번호 반환
    def sell(self, rqname, code, price, quantity, screenNo = "0101"):

        if self.testFlag:
            print("\n\n")
            print("[sell()]")
            
        # price = 0 이면 시장가에 매도. 아니면 지정가 매도.
        gubun = self.orderGubun["지정가"]
        if price==0: gubun = self.orderGubun["시장가"]

        for i in range(5):
        
            ret = self.sendOrder(rqname, screenNo, self.account, self.orderType["신규매도"],
                                 code, quantity, price, gubun, '')

            self.tmpOrderNo = ''
            
            # 주문 성공 시
            if ret==0:
                wait = threading.Thread(target=self.getOrderNo)
                wait.start()
                wait.join()

            if self.tmpOrderNo!='': return self.tmpOrderNo

        # 루프를 다 도는 동안 쿼리 결과를 반환하지 못한 경우
        print("\n\n")
        print("[sell()] Order is failed!!!")


    # 매수 취소 (price 부분이 반드시 ''이어야 함)
    # '매수 취소' 주문이 온 뒤, 원주문과 매수 취소 주문의 미체결수량을 0으로 만듬
    def cancelBuy(self, rqname, originalOrder, code, screenNo = "0101"):
        
        if self.testFlag:
            print("\n\n")
            print("[cancelBuy()]")
            
        ret = self.sendOrder(rqname, screenNo, self.account, self.orderType["매수취소"],
                             code, 0, '', '', originalOrder)

        return ret


    # 매도 취소 (price 부분이 반드시 ''이어야 함)
    # '매도 취소' 주문이 온 뒤, 원주문과 매도 취소 주문의 미체결수량을 0으로 만듬
    def cancelSell(self, rqname, originalOrder, code, screenNo = "0101"):
        
        if self.testFlag:
            print("\n\n")
            print("[cancelSell()]")
            
        ret = self.sendOrder(rqname, screenNo, self.account, self.orderType["매도취소"],
                             code, 0, '', '', originalOrder)

        return ret



######################################################################################



    # 받은 종목 리스트 중 지정 증거금 이하인 것들만 반환
    # withName이 True이면 {종목코드:종목명} 의 dic 반환
    def findByMargin(self, codelist, marginLimit=40, withName=False):

        con = sqlite3.connect(self.stocksCodeNameFile)
        
        selectstr = 'code, '
        if withName: selectstr = selectstr + 'name, '
        selectstr = selectstr + 'margin'

        if withName: ret = {}
        else: ret = []
        
        for code in codelist:
            
            wherestr = 'code = "' + code + '"'
            selected = sUtil.select(self.stocksCodeNameTable, con, selectstr, wherestr)

            if int(selected.get_value(0, 'margin'))<=marginLimit:
                
                if withName: ret[code] = selected.get_value(0, 'name')
                else: ret.append(code)

        con.close()

        if self.testFlag:
            print("\n\n")
            print("[findByMargin()] ret : ")
            print(ret)

        return ret
        

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



######################################################################################



    # 실시간 시세 처음 등록 시 realpool에 trcode 로 쿼리한 결과 적용
    def setRealpool(self, codelist, append):

        if not(append): self.realpool = {}

        trcode = 'OPTKWFID'
        inputdic = {}
        outputs = ["종목코드", "현재가", "거래량", "매수호가", "매도호가"]

        # 한 번에 100개까지 등록 가능
        left = codelist
        df = DataFrame()

        while True:
            
            if len(left)>100:

                time.sleep(0.2)
                ret = self.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs, codelist=left[:100])
                left = left[100:]
                df = df.append(ret)
                
            else:
                
                time.sleep(0.2)
                ret = self.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs, codelist=left)
                df = df.append(ret)
                break

        for i in  df.index:
            self.realpool[df.get_value(i, '종목코드')] = [abs(int(df.get_value(i, '현재가'))),
                                                          int(df.get_value(i, '거래량')),
                                                          abs(int(df.get_value(i, '매수호가'))),
                                                          abs(int(df.get_value(i, '매도호가')))]

        if self.testFlag:
            print("\n\n")
            print("[setRealpool()] self.realpool : ")
            print(self.realpool)
            
    
    # 실시간 시세 등록
    def setRealtime(self, codelist, fidlist=None, append=False, screenNo='0101'):

        if self.testFlag:
            print("\n\n")
            print("[setRealtime()]")
        
        if fidlist==None:
            fidlist = [str(self.convertFid("현재가")), str(self.convertFid("(최우선)매도호가")),
                       str(self.convertFid("(최우선)매수호가"))]

        # realpool을 쿼리로 채우기
        self.setRealpool(codelist, append)

        option = '0'
        if append: option = '1'

        # 한 번에 100개까지 등록 가능
        left = codelist
        
        while True:
            
            if len(codelist)>100:
                
                self.setRealReg(screenNo, ';'.join(left[:100]), ';'.join(fidlist), option)
                left = left[100:]
                
            else:
                
                self.setRealReg(screenNo, ';'.join(left), ';'.join(fidlist), option)
                break


    # 실시간 시세 해지 시 realpool에서 해당 항목 제거
    def removeRealpool(self, codestr):

        if codestr=='ALL':

            self.realpool = {}

        else:

            if self.realpool.get(codestr)!=None:
                self.realpool.pop(codestr)
            

    # 실시간 시세 해지
    # codestr은 코드 하나이거나 'ALL' (코드 여러 개 지정은 안 됨)
    # (코드 하나만 해지 시, Kiwoom API 자체 오류로 실시간 데이터 자체는 수신됨.
    #  다만 realpool에서 제거하여 값을 저장하지 않고 패스)
    # screenNo 도 'ALL' 가능
    def clearRealtime(self, codestr='ALL', screenNo='0101'):

        ret = self.setRealRemove(screenNo, codestr)
        print(ret)

        time.sleep(0.2)
        self.removeRealpool(codestr)

        if self.testFlag:
            print("\n\n")
            print("[clearRealtime()]")



######################################################################################


    
    # 해당 종목의 현재가 반환
    def getNowPrice(self, code):

        # 실시간 데이터에 현재가가 있는 경우, rqpool에서 값을 얻어 반환
        l = self.realpool.get(code)
        if l!=None:
            if l[0]!=0: return l[0]

        # 실시간 데이터가 없으면 query 후 반환
        trcode = 'opt10003'
        inputdic = {"종목코드" : code}
        outputs = ["현재가"]

        time.sleep(0.2)
        df = self.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs)

        ret = abs(int(df.get_value(0, '현재가')))
        
        return ret


    # 해당 종목의 매수호가+1 반환
    def getBuyPricePlus(self, code):

        # 실시간 데이터가 있는 경우, rqpool에서 값을 얻어 반환
        l = self.realpool.get(code)
        if l!=None:
            if l[2]!=0:
                unitprice = self.getUnitPrice(l[2])
                return l[2] + unitprice

        # 실시간 데이터가 없으면 query 후 반환
        trcode = 'opt10004'
        inputdic = {"종목코드" : code}
        outputs = ["매수최우선호가"]

        time.sleep(0.2)
        df = self.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs)
        
        buyprice = abs(int(df.get_value(0, '매수최우선호가')))
        print(buyprice)
        unitprice = self.getUnitPrice(buyprice)
        
        return buyprice + unitprice
    

    # 해당 종목의 매도호가-1 반환
    def getSellPriceMinus(self, code):
        
        # 실시간 데이터가 있는 경우, realpool에서 값을 얻어 반환
        l = self.realpool.get(code)
        if l!=None:
            if l[3]!=0:
                unitprice = self.getUnitPrice(l[3])
                return l[3] - unitprice

        # 실시간 데이터가 없으면 query 후 반환
        trcode = 'opt10004'
        inputdic = {"종목코드" : code}
        outputs = ["매도최우선호가"]

        time.sleep(0.2)
        df = self.kiwoomRequest(self.getRqname(), trcode, inputdic, outputs)
        
        sellprice = abs(int(df.get_value(0, '매도최우선호가')))
        print(sellprice)
        unitprice = self.getUnitPrice(sellprice)
        
        return sellprice - unitprice


    # 해당 종목의 단위 호가 반환
    def getUnitPrice(self, price):
        
        if price<1000: return 1

        elif price<5000: return 5

        elif price<10000: return 10

        elif price<50000: return 50

        elif price<100000: return 100

        else:
            # stocks.db에서 거래소(코스피)/코스닥 구분 얻기
            con = sqlite3.connect(self.stocksCodeNameFile)
            wherestr = 'code = "' + code + '"'
            selected = sUtil.select(self.stocksCodeNameTable, con, 'market', wherestr)
            con.close()

            market = selected.get_value(0, 'market')

            if market == 'D': return 100

            elif market == 'P':
                
                if price<500000: return 500

                else: return 1000



######################################################################################



    # realpool의 복사본 반환
    def getRealpool(self):
        return self.realpool.copy()


    # chejanpool list 중 가장 오래된 것 반환 후 삭제
    def getOneFromChejanpool(self):
        
        if self.testFlag:
            print("[getOneFromChejanpool()]")
            print("\n\n")

        if len(self.chejanpool)>0:
            return self.chejanpool.pop(0)
        else:
            return None


    # realpool에서 해당 종목의 내역 리스트 반환
    def getOneFromRealpool(self, code):

        l = self.realpool[code].copy()
        return l


    # orderpool에 해당 주문이 존재하지 않으면 True, 아니면 False 반환
    def isOrderFinished(self, orderNo):

        l = self.orderpool.get(orderNo)

        if l==None: return True
        else: return False


    # 주문 pool 반환
    def getOrderpool(self):

        try:
            korderpool = self.orderpool.copy()
            return korderpool

        except:
            return dict()

    

        

        
