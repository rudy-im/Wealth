#-*- coding : utf-8 -*-

# 사용 방법
#----------------------------------
#if __name__ == "__main__":
#    app = QApplication(sys.argv)
#    kiwoom = Kiwoom()
#    kiwoom.commConnect()
#----------------------------------

import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from pandas import Series, DataFrame
import time

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

        # market 번호
        self.noMarket = '0'     # 장내
        self.noElw = '3'        # ELW
        self.noMutual = '4'     # 뮤추얼펀드
        self.noBw = '5'         # 신주인수권
        self.noReits = '6'      # 리츠
        self.noEtf = '8'        # ETF
        self.noHighyield = '9'  # 하이일드펀드
        self.noKosdaq = '10'    # 코스닥
        self.noThird = '30'     # 제 3 시장

        # Tr 코드
        self.trMin = 'opt10080'   # 분봉
        self.trDay = 'opt10081'   # 일봉
        self.trWeek = 'opt10082'  # 주봉
        self.trMonth = 'opt10083' # 월봉

        # 쿼리 결과 데이터 관련
        self.TR_REQ_TIME_INTERVAL = 0.2
        self.dataChart = DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

        # 계좌
        self.account = self.getAccount()


    # COM 객체 생성
    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")


    # 이벤트 연결
    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        #self.OnReceiveMsg.connect(self._receive_msg)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        #self.OnReceiveRealData.connect(self._receive_real_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)
        self.OnReceiveConditionVer.connect(self._receive_condition_ver)
        #self.OnReceiveTrCondition.connect(self._receive_tr_condition)
        #self.OnReceiveRealCondition.connect(self._receive_real_condition)


    # (이벤트) 로그인 성공 여부 출력
    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    # (이벤트) 서버 통신 후 수신한 메시지를 알려 줌.
    # OnReceiveMsg 에 연결해야 사용 가능
    def _receive_msg(self, screenNo, rqname, trcode, msg):
        pass


    # (이벤트) 받은 쿼리 결과에 따른 처리
    # GetCommData() 사용
    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remainedData = True
        else:
            self.remainedData = False

        # TR별 함수 수행
        try:
            execStr = 'self._' + trcode + '("' + rqname + '")'
            exec(execStr)
        except:
            print(trcode + " function doesn't exist")

        
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass


    # (이벤트) 실시간 데이터 수신. SetRealReg()로 등록한 실시간 데이터 포함.
    # GetCommRealData() 사용
    # OnReceiveRealData() 에 연결해야 사용 가능
    def _receive_real_data(self, code, realType, realData):
        pass
    

    ###
    # (이벤트) 주문 접수, 체결 통보, 잔고 통보
    # GetChejanData() 사용
    # gubun은 체결 접수 및 체결 시 '0', 국내주식 잔고전달은 '1', 파생잔고전달은 '4'
    def _receive_chejan_data(self, gubun, itemCnt, fidList):
        # self.getChejanData(fid) 사용
        print(gubun + "   " + str(type(gubun)))
        print(itemCnt + "   " + str(type(itemCnt)))
        print(fidList)

        for fid in fidList:
            print(self.getChejanData(fid))
        
        try:
            self.chejan_event_loop.exit()
        except:
            pass


    # (이벤트) 사용자 조건식 요청에 대한 응답
    # getConditionNameList() 사용
    # ret : 1이면 성공, 나머지는 실패
    def _receive_condition_ver(self, ret, msg):
        print(str(self.getConditionNameList()))
        

    # (이벤트) 조건 검색 요청으로 검색된 종목코드 리스트를 세미콜론(;)으로 구분하여 반환
    # OnReceiveTrCondition() 에 연결해야 사용 가능
    # next : 연속조회 여부
    def _receive_tr_condition(self, screenNo, codeList, conditionIndex, next):
        pass

    # (이벤트) 실시간 조건검색 요청 종목이 변경될 때 호출
    # OnReceiveRealCondition() 에 연결해야 사용 가능
    # type : I는 종목 편입, D는 종목 이탈
    def _receive_real_condition(self, code, type, conditionName, conditionIndex):
        pass


######################################################################################
# 로그인 버전처리
######################################################################################


    # 로그인
    def commConnect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()


    # 로그인 상태 확인
    # 1 : 연결됨, 0 : 연결안됨.
    def getConnectState(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    # 로그인 정보 얻기
    # infoType  :
    #      "ACCOUNT_CNT" : 보유계좌 수를 반환합니다.
    #      "ACCLIST" 또는 "ACCNO" : 구분자 ';'로 연결된 보유계좌 목록을 반환합니다.
    #      "USER_ID" : 사용자 ID를 반환합니다.
    #      "USER_NAME" : 사용자 이름을 반환합니다.
    #      "KEY_BSECGB" : 키보드 보안 해지여부를 반환합니다.(0 : 정상, 1 : 해지)
    #      "FIREW_SECGB" : 방화벽 설정여부를 반환합니다.(0 : 미설정, 1 : 설정, 2 : 해지)
    #      "GetServerGubun" : 접속서버 구분을 반환합니다.(0 : 모의투자, 나머지 : 실서버)
    def getLoginInfo(self, infoType):
        ret = self.dynamicCall("GetLoginInfo(QString)", infoType)
        return ret
    

######################################################################################
# 조회와 실시간데이터처리
######################################################################################


    # 쿼리 요청
    # next : 연속조회여부. 0이면 연속조회X
    # 빈번하게 조회 요청 시 과부하에러값 -200, 조회전문작성 에러값 -201
    # 0을 반환하면 정상처리
    def commRqData(self, rqname, trcode, next, screen_no):
        ret = self.dynamicCall("CommRqData(QString, QString, int, QString", rqname, trcode, next, screen_no)
        if ret!=0 : return ret
        
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()


    # 쿼리 조건 세팅
    # id : "종목코드", "계좌번호", "기준일자", "수정주가구분" 등...
    def setInputValue(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)


    # 쿼리 결과 얻기 (구형)
    # 반드시 OnReceiveTRData() 이벤트 함수 내에서 사용
    # realType : ""
    # itemName : "종목명", "거래량", "종목코드" 등...
    def commGetData(self, trcode, realType, rqname, index, itemName):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)",
                               trcode, realType, rqname, index, itemName)
        return ret.strip()


    ###
    # 화면번호를 설정한 실시간 데이터 해지
    def disconnectRealData(self, screenNo):
        self.dynamicCall("DisconnectRealData(QString)", screenNo)


    # 받은 쿼리 결과 개수 얻기
    def getRepeatCnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret


    # 한 번에 100종목을 조회할 수 있는 관심종목 조회 함수.
    # codeList : 종목코드를 세미콜론(;)으로 구분한 문자열
    # next : 0이면 기본값, 1이면 연속조회
    # typeFlag : 0이면 주식, 3이면 선물옵션
    def commKwRqData(self, codeList, next, codeCount, typeFlag, rqname, screenNo):
        ret = self.dynamicCall("CommKwRqData(QString, bool, int, int, QString, QString)",
                               codeList, next, codeCount, typeFlag, rqname, screenNo)
        if ret!=0 : return ret
        
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()


    # 쿼리 결과 얻기 (신형)
    # 반드시 OnReceiveTrData() 이벤트 함수 내에서 사용
    # item_name : "종목명", "거래량", "종목코드" 등...
    def getCommData(self, trcode, rqname, index, itemName):
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString)",
                               trcode, rqname, index, itemName)
        return ret.strip()

    ###
    # 실시간 데이터를 얻어오는 함수.
    # 반드시 OnReceiveRealData() 이벤트 함수 내에서 사용.
    # fid : 실시간 타입에 포함된 FID.
    #       10 : 현재가, 13 : 누적거래량, 228 : 체결강도, 20 : 체결시간 등...
    def getCommRealData(self, code, fid):
        ret = self.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return ret.strip()


    # 크기가 큰 데이터 (차트 등..) 를 한 번에 가져오기 위한 전용 함수.
    def getCommDataEx(self, trcode, rqname):
        ret = self.dynamicCall("GetCommDataEx(QString, QString)", trcode, rqname)
        return ret


######################################################################################
# 주문과 잔고처리
######################################################################################
    

    ###
    # 국내주식 주문. 0을 리턴하면 성공.
    # 1초에 5회만 가능. 그 이상 요청 시 에러 -308
    # orderType :  1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
    # gubun  :  00:지정가, 03:시장가, 05:조건부지정가, 06:최유리지정가, 07:최우선지정가
    #           10:지정가IOC, 13:시장가IOC, 16:최유리IOC, 20:지정가FOK, 23:시장가FOK
    #           26 : 최유리FOK, 61:장전시간외종가, 62:시간외단일가매매, 81:장후시간외종가
    # originalOrder : 신규주문은 공백, 정정/취소 시 원주문번호
    def sendOrder(self, rqname, screenNo, account, orderType, code, quantity, price, gubun, originalOrder):
        # dynamicCall에서 인자가 8개를 초과하는 경우 다음과 같은 리스트 처리 필요
        ret = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                               [rqname, screenNo, account, orderType, code, quantity, price, gubun, originalOrder])

        self.chejan_event_loop = QEventLoop()
        self.chejan_event_loop.exec_()
        
        return ret


    """SendOrderFO(
          BSTR sRQName,     // 사용자 구분명
          BSTR sScreenNo,   // 화면번호
          BSTR sAccNo,      // 계좌번호 10자리 
          BSTR sCode,       // 종목코드 
          LONG lOrdKind,    // 주문종류 1:신규매매, 2:정정, 3:취소
          BSTR sSlbyTp,     // 매매구분	1: 매도, 2:매수
          BSTR sOrdTp,      // 거래구분(혹은 호가구분)은 아래 참고
          LONG lQty,        // 주문수량 
          BSTR sPrice,      // 주문가격 
          BSTR sOrgOrdNo    // 원주문번호
          )
          
          코스피지수200 선물옵션, 주식선물 전용 주문함수입니다.
          
          [거래구분]
          1 : 지정가
          2 : 조건부지정가
          3 : 시장가
          4 : 최유리지정가
          5 : 지정가(IOC)
          6 : 지정가(FOK)
          7 : 시장가(IOC)
          8 : 시장가(FOK)
          9 : 최유리지정가(IOC)
          A : 최유리지정가(FOK) """


    """SendOrderCredit(
          BSTR sRQName,   // 사용자 구분명
          BSTR sScreenNo,   // 화면번호 
          BSTR sAccNo,    // 계좌번호 10자리 
          LONG nOrderType,    // 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
          BSTR sCode,   // 종목코드
          LONG nQty,    // 주문수량
          LONG nPrice,    // 주문가격
          BSTR sHogaGb,   // 거래구분(혹은 호가구분)은 아래 참고
          BSTR sCreditGb, // 신용거래구분
          BSTR sLoanDate,   // 대출일
          BSTR sOrgOrderNo    // 원주문번호
          )
          
          국내주식 신용주문 전용함수입니다. 대주거래는 지원하지 않습니다.

          [거래구분]
          모의투자에서는 지정가 주문과 시장가 주문만 가능합니다.
          
          00 : 지정가
          03 : 시장가
          05 : 조건부지정가
          06 : 최유리지정가
          07 : 최우선지정가
          10 : 지정가IOC
          13 : 시장가IOC
          16 : 최유리IOC
          20 : 지정가FOK
          23 : 시장가FOK
          26 : 최유리FOK
          61 : 장전시간외종가
          62 : 시간외단일가매매
          81 : 장후시간외종가
          
          [신용거래]
          신용거래 구분은 다음과 같습니다.
          03 : 신용매수 - 자기융자
          33 : 신용매도 - 자기융자
          99 : 신용매도 자기융자 합
          
          대출일은 YYYYMMDD형식이며 신용매도 - 자기융자 일때는 종목별 대출일을 입력하고 신용매도 - 융자합이면 "99991231"을 입력합니다."""


    ###
    # 체결 정보, 잔고 정보 얻기
    # 반드시 OnReceiveChejan() 이벤트 함수 내에서 사용
    def getChejanData(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret


######################################################################################
# 조건검색
######################################################################################


    # 조건검색 목록을 서버에 요청.
    # 성공 시 1, 실패 시 0 반환.
    def getConditionLoad(self):
        ret = self.dynamicCall("GetConditionLoad()")
        return ret


    # 서버에서 수신한 사용자 조건식 반환
    # 조건명 인덱스와 조건식 이름은 ^, 각 조건식은 ; 로 구분
    # 반드시 OnReceiveConditionVer() 이벤트 함수 내에서 사용
    def getConditionNameList(self):
        ret = self.dynamicCall("GetConditionNameList()")
        return ret


    ###
    # 서버에 조건 검색 요청
    # 반환값이 1이면 성공, 0이면 실패
    # 조건식이 없거나, 조건명 인덱스와 조건식이 안 맞거나, 조회횟수 초과 시 실패
    # conditionIndex : 조건명 인덱스. GetConditionNameList() 함수에서 전달받은 대로 사용.
    # option : 기본값은 0, 실시간 조건검색 시 1
    def sendCondition(self, screenNo, conditionName, conditionIndex, option):
        ret = self.dynamicCall("SendCondition(QString, QString, int, int)",
                               screenNo, conditionName, conditionIndex, option)
        return ret


    ###
    # 조건 검색 중지
    def sendConditionStop(self, screenNo, conditionName, conditionIndex):
        ret = self.dynamicCall("SendConditionStop(QString, QString, int)",
                               screenNo, conditionName, conditionIndex)
        return ret


    ###
    # 실시간 시세 등록. 한 번에 100개까지 가능.
    # option : 0이면 기존 등록 종목들은 실시간 해지, 1이면 유지.
    def setRealReg(self, screenNo, codeList, fidList, option):
        ret = self.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                               screenNo, codeList, fidList, option)
        return ret


    ###
    # 실시간 시세 해지
    # screenNo, code는 각각 해당 번호만 쓰거나 'ALL' 사용 가능.
    def setRealRemove(self, screenNo, code):
        ret = self.dynamicCall("SetRealRemove(QString, QString)", screenNo, code)
        return ret


######################################################################################
# 기타함수
######################################################################################

    
    # 해당 market에 속하는 종목코드 얻기
    # market   :   0 : 장내, 10 : 코스닥, 3 : ELW, 8 : ETF, 50 : KONEX
    #              4 :  뮤추얼펀드, 5 : 신주인수권, 6 : 리츠, 9 : 하이얼펀드, 30 : K-OTC
    #              NULL이면 전체 시장코드 반환.
    def getCodeListByMarket(self, market):
        codeList = self.dynamicCall("GetCodeListByMarket(QString)", market)
        codeList = codeList.split(';')
        return codeList[:-1]


    # 해당 종목코드의 종목명 반환
    def getMasterCodeName(self, code):
        codeName = self.dynamicCall("GetMasterCodeName(QString)", code)
        return codeName


    # 해당 종목코드의 상장주식수 반환
    def getMasterListedStockCnt(self, code):
        stockCnt = self.dynamicCall("GetMasterListedStockCnt(QString)", code)
        return stockCnt


    # 해당 종목코드의 감리구분(정상, 투자주의, 투자경고, 투자위험, 투자주의환기종목) 반환
    def getMasterConstruction(self, code):
        construction = self.dynamicCall("GetMasterConstruction(QString)", code)
        return construction


    # 해당 종목코드의 상장일 반환
    def getMasterListedStockDate(self, code):
        stockDate = self.dynamicCall("GetMasterListedStockDate(QString)", code)
        return stockDate


    # 해당 종목코드의 전일가 반환
    def getMasterLastPrice(self, code):
        lastPrice = self.dynamicCall("GetMasterLastPrice(QString)", code)
        return lastPrice


    # 해당 종목코드의 증거금 비율, 거래정지, 관리종목, 감리종목, 투자융의종목, 담보대출, 액면분할, 신용가능 여부 반환
    # 파이프(|)로 구분.
    # 리턴값 예) 증거금40%|담보대출|신용가능
    def getMasterStockState(self, code):
        stockState = self.dynamicCall("GetMasterStockState(QString)", code)
        return stockState


    # 지수선물 종목코드 리스트 반환
    def getFutureList(self):
        futureList = self.dynamicCall("GetFutureList()")
        futureList = futureList.split(';')
        return futureList[:-1]


    # 지수옵션 행사가에 100을 곱해서 소수점이 없는 값의 리스트로 반환
    def getActPriceList(self):
        actPriceList = self.dynamicCall("GetActPriceList()")
        actPriceList = actPriceList.split(';')
        return actPriceList[:-1]


    # 지수옵션 월물정보 리스트 반환
    # 순서는 콜 11월물 ~ 콜 최근월물, 풋 11월물 ~ 풋 최근월물.
    def getMonthList(self):
        monthList = self.dynamicCall("GetMonthList()")
        monthList = monthList.split(';')
        return monthList[:-1]


    # 해당 지수옵션 코드 반환
    # actPrice는 소수점을 포함한 행사가
    # call_put : 콜이면 2, 풋이면 3
    # month : 6자리 월물 ('YYYYMM')
    def getOptionCode(self, actPrice, call_put, month):
        optionCode = self.dynamicCall("GetOptionCode(QString, int, QString)",
                                      actPrice, call_put, month)
        return optionCode


    # 100을 곱해 지수옵션 소수점을 제거한 ATM값 반환
    def getOptionATM(self):
        atm = self.dynamicCall("GetOptionATM()")
        return atm

    
######################################################################################

    ###
    # 주식 기본 정보 처리
    def _opt10001(self, rqname):
        trcode = 'opt10001'
        repeatCnt = self.getRepeatCnt(trcode, rqname)

        for i in range(repeatCnt):
            code = self.getCommData(trcode, rqname, i, "종목코드")
            name = self.getCommData(trcode, rqname, i, "종목명")
            capital = self.getCommData(trcode, rqname, i, "자본금")
            nowprice = self.getCommData(trcode, rqname, i, "현재가")

        print([code, name, capital, nowprice])
            
        
    # 분봉 데이터 처리
    def _opt10080(self, rqname):
        trcode = 'opt10080'
        repeatCnt = self.getRepeatCnt(trcode, rqname)

        for i in range(repeatCnt):
            date = self.getCommData(trcode, rqname, i, "체결시간")
            open = self.getCommData(trcode, rqname, i, "시가")
            high = self.getCommData(trcode, rqname, i, "고가")
            low = self.getCommData(trcode, rqname, i, "저가")
            close = self.getCommData(trcode, rqname, i, "현재가")
            volume = self.getCommData(trcode, rqname, i, "거래량")

            self.dataChart.loc[date] = [int(open), int(high), int(low), int(close), int(volume)]


    # 일봉 데이터 처리
    def _opt10081(self, rqname):
        trcode = 'opt10081'
        repeatCnt = self.getRepeatCnt(trcode, rqname)

        for i in range(repeatCnt):
            date = self.getCommData(trcode, rqname, i, "일자")
            open = self.getCommData(trcode, rqname, i, "시가")
            high = self.getCommData(trcode, rqname, i, "고가")
            low = self.getCommData(trcode, rqname, i, "저가")
            close = self.getCommData(trcode, rqname, i, "현재가")
            volume = self.getCommData(trcode, rqname, i, "거래량")

            self.dataChart.loc[date] = [int(open), int(high), int(low), int(close), int(volume)]


######################################################################################

            
    # 분봉 데이터 얻기
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    def getTrMin(self, rqname, code, tick, maxIteration = -1, modified = 1, screenNo = "0101"):
        # 기존 데이터 삭제
        self.dataChart = self.dataChart[0:0]
        
        # 데이터 900개 요청
        self.setInputValue("종목코드", code)
        self.setInputValue("틱범위", tick)
        self.setInputValue("수정주가구분", modified)
        self.commRqData(rqname, self.trMin, 0, screenNo)

        # 데이터 900개씩 추가 요청
        iteration = maxIteration
        while self.remainedData == True:
            iteration -= 1
            if iteration == 0 : break
            time.sleep(self.TR_REQ_TIME_INTERVAL)
            self.setInputValue("종목코드", code)
            self.setInputValue("틱범위", tick)
            self.setInputValue("수정주가구분", modified)
            self.commRqData(rqname, self.trMin, 2, screenNo)

        return self.dataChart
    

    # 일봉 데이터 얻기
    # date : YYYYMMDD 형식 (예 : "20170404")
    # maxIteration이 -1 이하이면 얻을 수 있는 모든 데이터를 얻음
    def getTrDay(self, rqname, code, date, maxIteration = -1, modified = 1, screenNo = "0101"):
        # 기존 데이터 삭제
        self.dataChart = self.dataChart[0:0]
        
        # 데이터 900개 요청
        self.setInputValue("종목코드", code)
        self.setInputValue("기준일자", date)
        self.setInputValue("수정주가구분", modified)
        self.commRqData(rqname, self.trDay, 0, screenNo)

        # 데이터 900개씩 추가 요청
        iteration = maxIteration
        while self.remainedData == True:
            iteration -= 1
            if iteration == 0 : break
            time.sleep(self.TR_REQ_TIME_INTERVAL)
            self.setInputValue("종목코드", code)
            self.setInputValue("기준일자", date)
            self.setInputValue("수정주가구분", modified)
            self.commRqData(rqname, self.trDay, 2, screenNo)

        return self.dataChart


    # 보유 계좌 리스트 얻기
    def getAccount(self):
        account = self.getLoginInfo("ACCLIST")
        account = account.split(';')
        return account[:-1]


    ###
    # 종목 매수
    def buy(self, rqname, code, price, quantity, screenNo = "0101"):
        # price = 0 이면 시장가에 매수. 아니면 지정가 매수.
        gubun = "00"
        if price==0: gubun = "03"
        
        self.sendOrder(rqname, screenNo, self.account[0], 1, code, quantity, price, gubun, '')


    ###
    # 종목 매도
    def sell(self, rqname, code, price, quantity, screenNo = "0101"):
        # price = 0 이면 시장가에 매도. 아니면 지정가 매도.
        gubun = "00"
        if price==0: gubun = "03"
        
        self.sendOrder(rqname, screenNo, self.account[0], 2, code, quantity, price, gubun, '')


    ###
    # 매수 취소
    def cancelBuy(self, rqname, originalOrder, screenNo = "0101"):     
        self.sendOrder(rqname, screenNo, self.account[0], 3, '', 0, 0, "00", originalOrder)


    ###
    # 매도 취소
    def cancelSell(self, rqname, originalOrder, screenNo = "0101"):
        self.sendOrder(rqname, screenNo, self.account[0], 4, '', 0, 0, "00", originalOrder)


    ###
    # 매수 정정
    def changeBuy(self, rqname, originalOrder, code, price, quantity, screenNo = "0101"):
        # price = 0 이면 시장가에 매수. 아니면 지정가 매수.
        gubun = "00"
        if price==0: gubun = "03"
        
        self.sendOrder(rqname, screenNo, self.account[0], 5, code, quantity, price, gubun, originalOrder)


    ###
    # 매도 정정
    def changeSell(self, rqname, originalOrder, code, price, quantity, screenNo = "0101"):
        # price = 0 이면 시장가에 매도. 아니면 지정가 매도.
        gubun = "00"
        if price==0: gubun = "03"
        
        self.sendOrder(rqname, screenNo, self.account[0], 6, code, quantity, price, gubun, originalOrder)


    # 주요 함수 반환값 코드 의미 반환
    def getErrorComment(self, errCode):
        errors = {0 : '정상처리',                                                                      
                -10 : '실패',                                                                          
                -100 : '사용자정보교환 실패',                                                          
                -101 : '서버 접속 실패',                                                               
                -102 : '버전처리 실패',                                                               
                -103 : '개인방화벽 실패',                                                           
                -104 : '메모리 보호실패',                                                             
                -105 : '함수입력값 오류',                                                             
                -106 : '통신연결 종료',                                                                 
                                                                                                        
                -200 : '시세조회 과부하',                                                               
                -201 : '전문작성 초기화 실패',                                                       
                -202 : '전문작성 입력값 오류',                                                        
                -203 : '데이터 없음',                                                                
                -204 : '조회가능한 종목수 초과. 한번에 조회 가능한 종목개수는 최대 100종목',         
                -205 : '데이터 수신 실패',                                                              
                -206 : '조회가능한 FID수 초과. 한번에 조회 가능한 FID개수는 최대 100개',            
                -207 : '실시간 해제오류',                                                               
                                                                                                        
                -300 : '입력값 오류',                                                                 
                -301 : '계좌비밀번호 없음',                                                         
                -302 : '타인계좌 사용오류',                                                       
                -303 : '주문가격이 20억원을 초과',                                                  
                -304 : '주문가격이 50억원을 초과',                                                
                -305 : '주문수량이 총발행주수의 1% 초과오류',                                       
                -306 : '주문수량은 총발행주수의 3% 초과오류',                                       
                -307 : '주문전송 실패',                                                                 
                -308 : '주문전송 과부하 ',                                                              
                -309 : '주문수량 300계약 초과',                                                    
                -310 : '주문수량 500계약 초과',                                                     
                -340 : '계좌정보 없음',                                                             
                -500 : '종목코드 없음'}

        return errors[errCode]

    
