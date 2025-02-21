#-*- coding : utf-8 -*-

# 사용 방법
#----------------------------------
#if __name__ == "__main__":
#    app = QApplication(sys.argv)
#    kiwoom = Kiwoom()
#    kiwoom.commConnect()
#----------------------------------

from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from pandas import Series, DataFrame

class Kiwoom(QAxWidget):
    
    def __init__(self):
        
        super().__init__()

        # testFlag == True 이면 테스트 로그를 콘솔에 print
        self.testFlag = False
        
        self._create_kiwoom_instance()
        self._set_signal_slots()

        # market 번호
        self.marketGubun = {"장내"         : '0',
                            "ELW"          : '3',
                            "뮤추얼펀드"   : '4',
                            "신주인수권"   : '5',
                            "리츠"         : '6',
                            "ETF"          : '8',
                            "하이일드펀드" : '9',
                            "코스닥"       : '10',
                            "제3시장"      : '30',
                            "전체"         : ''}

        # 주문 시 orderType
        self.orderType = {'신규매수' : 1,
                          '신규매도' : 2,
                          '매수취소' : 3,
                          '매도취소' : 4,
                          '매수정정' : 5,
                          '매도정정' : 6}

        # 주문 시 gubun
        self.orderGubun = {'지정가' : '00',
                           '시장가' : '03',
                           '조건부지정가' : '05',
                           '최유리지정가' : '06',
                           '최우선지정가' : '07',
                           '지정가IOC' : '10',
                           '시장가IOC' : '13',
                           '최유리IOC' : '16',
                           '지정가FOK' : '20',
                           '시장가FOK' : '23',
                           '최유리FOK' : '26',
                           '장전시간외종가' : '61',
                           '시간외단일가매매' : '62',
                           '장후시간외종가' : '81'}
        
        # 쿼리 시 남은 데이터가 있는지 여부 표시
        self.remainedData = False


    # COM 객체 생성
    def _create_kiwoom_instance(self):

        if self.testFlag:
            print("\n\n")
            print("[_create_kiwoom_instance()]")
            
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")


    # 이벤트 연결
    def _set_signal_slots(self):
        
        if self.testFlag:
            print("\n\n")
            print("[_set_signal_slots()]")
            
        self.OnEventConnect.connect(self._event_connect)
        #self.OnReceiveMsg.connect(self._receive_msg)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveRealData.connect(self._receive_real_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)
        #self.OnReceiveConditionVer.connect(self._receive_condition_ver)
        #self.OnReceiveTrCondition.connect(self._receive_tr_condition)
        #self.OnReceiveRealCondition.connect(self._receive_real_condition)


    # (이벤트) 로그인 성공 시 알림
    def _event_connect(self, err_code):

        if self.testFlag:
            print('')
            print("[_event_connect()] err_code = " + str(err_code))
        
        if err_code == 0:
            print('\n\n')
            print("[_event_connect()] connected")
            self.eventConnect(err_code)

        else:
            print('\n\n')
            print("[_event_connect()] disconnected")

        self.login_event_loop.exit()


    # (이벤트) 서버 통신 후 수신한 메시지를 알려 줌.
    def _receive_msg(self, screenNo, rqname, trcode, msg):
        
        if self.testFlag:
            print('\n\n')
            print("[_receive_msg()] screenNo : ", screenNo)
            print("[_receive_msg()] rqname : ", rqname)
            print("[_receive_msg()] trcode : ", trcode)
            print("[_receive_msg()] msg : ", msg)

        try:
            self.receiveMsg(screenNo, rqname, trcode, msg)
        except:
            pass


    # (이벤트) 받은 쿼리 결과에 따른 처리
    # GetCommData() 사용
    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        
        if next == '2':
            self.remainedData = True
        else:
            self.remainedData = False

        if self.testFlag:
            print("\n\n")
            print("[_receive_tr_data()] screen_no : ", screen_no)
            print("[_receive_tr_data()] rqname : ", rqname)
            print("[_receive_tr_data()] trcode : ", trcode)
            print("[_receive_tr_data()] record_name : ", record_name)
            print("[_receive_tr_data()] self.remainedData : ", self.remainedData)
            
        try:
            self.receiveTrData(screen_no, rqname, trcode, record_name)
        except:
            pass
        
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass


    # (이벤트) 실시간 데이터 수신. SetRealReg()로 등록한 실시간 데이터 포함.
    # realType : '주식체결' 등... 문자열. 
    # realData : getRealIndex() 참조. 문자열.
    # GetCommRealData(), getRealData() 사용
    def _receive_real_data(self, code, realType, realData):
        
        if self.testFlag:
            print("\n\n")
            print('[_receive_real_data()] code : ' + str(code))
            print('[_receive_real_data()] realType : ' + str(realType))
            print('[_receive_real_data()] realData : ' + str(realData))

        try:
            self.receiveRealData(code, realType, realData)
        except:
            pass
                                                   
        
    # (이벤트) 주문 접수, 체결 통보, 잔고 통보
    # GetChejanData() 사용
    # gubun은 체결 접수 및 체결 시 '0', 국내주식 잔고전달은 '1', 파생잔고전달은 '4'
    # gubun의 데이터 타입은 str
    # fidListStr : fid를 세미콜론(;) 으로 구분. fid는 int형으로 사용할 것.
    # fid 사용 시 self.convertFid()로 fid <-> 의미 변환
    def _receive_chejan_data(self, gubun, itemCnt, fidListStr):
                
        if self.testFlag:
            print("\n\n")
            print('[_receive_chejan_data()] gubun : ' + str(gubun))
            print('[_receive_chejan_data()] itemCnt : ' + str(itemCnt))
            print('[_receive_chejan_data()] fidListStr : ' + fidListStr)

        try:
            self.receiveChejanData(gubun, itemCnt, fidListStr)
        except:
            pass
        
        try:
            self.chejan_event_loop.exit()
        except AttributeError:
            pass



    # (이벤트) 사용자 조건식 요청에 대한 응답
    # getConditionNameList() 사용
    # ret : 1이면 성공, 나머지는 실패
    def _receive_condition_ver(self, ret, msg):

        if self.testFlag:
            print("\n\n")
            print("[_receive_condition_ver()] ret : ", ret)
            print("[_receive_condition_ver()] msg : ", msg)

        try:
            self.receiveConditionVer(ret, msg)
        except:
            pass
            

    # (이벤트) 조건 검색 요청으로 검색된 종목코드 리스트 전달
    # codeList : 종목코드를 세미콜론(;)으로 구분한 문자열
    # next : 연속조회 여부
    def _receive_tr_condition(self, screenNo, codeList, conditionIndex, next):
        
        if next == '2':
            self.remainedData = True
        else:
            self.remainedData = False

        if self.testFlag:
            print("\n\n")
            print("[_receive_tr_condition()] screenNo : ", screenNo)
            print("[_receive_tr_condition()] codeList : ")
            print(codeList)
            print("[_receive_tr_condition()] conditionIndex : ")
            print(conditionIndex)

        try:
            self.receiveTrCondition(screenNo, codeList, conditionIndex)
        except:
            pass
            

    # (이벤트) 실시간 조건검색 요청 종목이 변경될 때 호출
    # insertOrDelete : I는 종목 편입, D는 종목 이탈
    def _receive_real_condition(self, code, insertOrDelete, conditionName, conditionIndex):

        if self.testFlag:
            print("\n\n")
            print("[_receive_real_condition()] code : ", code)
            print("[_receive_real_condition()] insertOrDelete : ", insertOrDelete)
            print("[_receive_real_condition()] conditionName : ", conditionName)
            print("[_receive_real_condition()] conditionIndex : ", conditionIndex)

        try:
            self.receiveRealCondition(code, insertOrDelete, conditionName, conditionIndex)
        except:
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
        ret = self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
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
    # trcode는 OPTKWFID로 처리
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


    # 실시간 데이터를 얻어오는 함수.
    # 반드시 OnReceiveRealData() 이벤트 함수 내에서 사용.
    # fid : 실시간 타입에 포함된 FID.
    #       10 : 현재가, 13 : 누적거래량, 228 : 체결강도, 20 : 체결시간 등...
    #       self.getRealIndex() 사용
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

    

    # 국내주식 주문. 0을 리턴하면 성공.
    # 1초에 5회만 가능. 그 이상 요청 시 에러 -308
    # orderType :  1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
    #              self.orderType 사용
    # gubun  :  00:지정가, 03:시장가, 05:조건부지정가, 06:최유리지정가, 07:최우선지정가
    #           10:지정가IOC, 13:시장가IOC, 16:최유리IOC, 20:지정가FOK, 23:시장가FOK
    #           26:최유리FOK, 61:장전시간외종가, 62:시간외단일가매매, 81:장후시간외종가
    #           self.orderGubun 사용
    # originalOrder : 신규주문은 공백, 정정/취소 시 원주문번호
    # 주문 취소 시, price 부분이 반드시 ''이어야 함
    # 2017.7.10 :: 주문 정정은 이벤트가 오지 않아 불가능
    def sendOrder(self, rqname, screenNo, account, orderType, code, quantity, price, gubun, originalOrder):
        # dynamicCall에서 인자가 8개를 초과하는 경우 다음과 같은 리스트 처리 필요
        ret = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                               [rqname, screenNo, account, orderType, code, quantity, price, gubun, originalOrder])

        if ret==0:

            if (orderType == self.orderType['신규매수'] or
                orderType == self.orderType['신규매도'] or
                orderType == self.orderType['매수정정'] or
                orderType == self.orderType['매도정정']):
                
                self.chejan_event_loop = QEventLoop()
                self.chejan_event_loop.exec_()
            
        return ret


    # 코스피지수200 선물옵션, 주식선물 주문 함수.
    # orderKind  :  1:신규매매, 2:정정, 3:취소
    # sellbuy  :  1:매도, 2:매수
    # orderType  :  1:지정가, 2:조건부지정가, 3:시장가, 4:최유리지정가, 5:지정가(IOC), 
    #               6:지정가(FOK), 7:시장가(IOC), 8:시장가(FOK), 9:최유리지정가(IOC), A:최유리지정가(FOK)
    def sendOrderFO(self, rqname, screenNo, account, code, orderKind, sellbuy, orderType, quantity, price, originalOrder):
        # dynamicCall에서 인자가 8개를 초과하는 경우 다음과 같은 리스트 처리 필요
        ret = self.dynamicCall("SendOrderFO(QString, QString, QString, QString, int, QString, QString, int, QString, QString)",
                               [rqname, screenNo, account, code, orderKind, sellbuy, orderType, quantity, price, originalOrder])

        ### 왜 이렇게????  ###
        # 테스트해보고, 잘 돌아가면 그냥 삭제 #
        '''
        if orderKind!=3:
            self.chejan_event_loop = QEventLoop()
            self.chejan_event_loop.exec_()
        '''
        
        return ret


    ### NOT TESTED
    # 국내주식 신용주문. 대주거래 지원 안함.
    # orderType :  1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
    # gubun  :  00:지정가, 03:시장가, 05:조건부지정가, 06:최유리지정가, 07:최우선지정가
    #           10:지정가IOC, 13:시장가IOC, 16:최유리IOC, 20:지정가FOK, 23:시장가FOK
    #           26:최유리FOK, 61:장전시간외종가, 62:시간외단일가매매, 81:장후시간외종가
    # creditgubun  :  03:신용매수 - 자기융자, 33:신용매도 - 자기융자, 99:신용매도 자기융자 합
    # loandate : "YYYYMMDD" 형식. 신용매도-자기융자일 때엔 종목별 대출일, 신용매도-융자합일 때엔 "99991231"
    # originalOrder : 신규주문은 공백, 정정/취소 시 원주문번호
    def sendOrderCredit(self, rqname, screenNo, account, orderType, code, quantity, price, gubun, creditgubun, loandate, originalOrder):
        # dynamicCall에서 인자가 8개를 초과하는 경우 다음과 같은 리스트 처리 필요
        ret = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString, QString, QString)",
                               [rqname, screenNo, account, orderType, code, quantity, price, gubun, creditgubun, loandate, originalOrder])

        ### 왜 이렇게????  ###
        # 테스트해보고, 잘 돌아가면 그냥 삭제 #
        '''
        self.chejan_event_loop = QEventLoop()
        self.chejan_event_loop.exec_()
        '''
        
        return ret


    # 체결 정보, 잔고 정보 얻기
    # 반드시 OnReceiveChejan() 이벤트 함수 내에서 사용
    def getChejanData(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret.strip()



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
    # {조건명 인덱스 : 조건식 이름} 의 dic 으로 반환
    # 반드시 OnReceiveConditionVer() 이벤트 함수 내에서 사용
    def getConditionNameList(self):
        conditionStr = self.dynamicCall("GetConditionNameList()")

        conditionList = conditionStr.split(';')

        ret = {}
        for c in condiationList:
            kv = c.split('^')
            ret[kv[0]] = kv[1]

        if self.testFlag:
            print("[getConditionNameList()] ret : ")
            print(ret)
            
        return ret


    # 서버에 조건 검색 요청
    # 반환값이 1이면 성공, 0이면 실패
    # 조건식이 없거나, 조건명 인덱스와 조건식이 안 맞거나, 조회횟수 초과 시 실패
    # conditionIndex : 조건명 인덱스. GetConditionNameList() 함수에서 전달받은 대로 사용.
    # option : 기본값은 0, 실시간 조건검색 시 1
    def sendCondition(self, screenNo, conditionName, conditionIndex, option):
        ret = self.dynamicCall("SendCondition(QString, QString, int, int)",
                               screenNo, conditionName, conditionIndex, option)
        return ret


    # 조건 검색 중지
    def sendConditionStop(self, screenNo, conditionName, conditionIndex):
        ret = self.dynamicCall("SendConditionStop(QString, QString, int)",
                               screenNo, conditionName, conditionIndex)
        return ret


    # 실시간 시세 등록. 한 번에 100개까지 가능.
    # option : 0이면 기존 등록 종목들은 실시간 해지, 1이면 유지.
    def setRealReg(self, screenNo, codeList, fidList, option):
        ret = self.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                               screenNo, codeList, fidList, option)
        return ret


    # 실시간 시세 해지
    # screenNo, code는 각각 해당 번호만 쓰거나 'ALL' 사용 가능.
    # 2017.7.10. :: 테스트 결과, 코드 하나만 해지하는 것은 안 됨. 'ALL'은 가능.
    #               세미콜론(;)으로 구분한 코드 여러 개 지정 시, 아예 오류로 프로그램 정지.
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
    #              self.marketNo 사용
    def getCodeListByMarket(self, market):
        codeList = self.dynamicCall("GetCodeListByMarket(QString)", market)
        codeList = codeList.split(';')

        if self.testFlag:
            print("[getCodeListByMarket()] codeList : ")
            print(codeList)
            print("\n\n")
            
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


    # 해당 종목코드의 증거금 비율, 거래정지, 관리종목, 감리종목, 투자유의종목, 담보대출, 액면분할, 신용가능 여부 반환
    # 파이프(|)로 구분.
    # 리턴값 예) 증거금40%|담보대출|신용가능
    def getMasterStockState(self, code):
        stockState = self.dynamicCall("GetMasterStockState(QString)", code)
        return stockState


    # 지수선물 종목코드 리스트 반환
    def getFutureList(self):
        futureList = self.dynamicCall("GetFutureList()")
        futureList = futureList.split(';')

        if self.testFlag:
            print("[getFutureList()] futureList : ")
            print(futureList)
            print("\n\n")
            
        return futureList[:-1]


    # 지수옵션 행사가에 100을 곱해서 소수점이 없는 값의 리스트로 반환
    def getActPriceList(self):
        actPriceList = self.dynamicCall("GetActPriceList()")
        actPriceList = actPriceList.split(';')
        
        if self.testFlag:
            print("[getActPriceList()] actPriceList : ")
            print(actPriceList)
            print("\n\n")
            
        return actPriceList[:-1]


    # 지수옵션 월물정보 리스트 반환
    # 순서는 콜 11월물 ~ 콜 최근월물, 풋 11월물 ~ 풋 최근월물.
    def getMonthList(self):
        monthList = self.dynamicCall("GetMonthList()")
        monthList = monthList.split(';')

        if self.testFlag:
            print("[getMonthList()] monthList : ")
            print(monthList)
            print("\n\n")
            
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
# TR 목록
# SetInputValue() 로 INPUT 세팅 후 CommRqData() 사용
######################################################################################



    # 주식 기본 정보 요청
    # INPUT : 종목코드
    def _opt10001(self):
        
        # 싱글데이터 [주식기본정보]
        outputS = ["종목코드", "종목명", "결산월", "액면가", "자본금", "상장주식", "신용비율",
                   "연중최고", "연중최저", "시가총액", "시가총액비중", "외인소진률", "대용가",
                   "PER", "EPS", "ROE", "PBR", "EV", "BPS", "매출액", "영업이익", "당기순이익",
                   "250최고", "250최저", "시가", "고가", "저가", "상한가", "하한가", "기준가",
                   "예상체결가", "예상체결수량", "250최고가일", "250최고가대비율", "250최저가일",
                   "250최저가대비율", "현재가", "대비기호", "전일대비", "등락율", "거래량",
                   "거래대비", "액면가단위"]
        
        return outputS


    # OPT10002 : 주식거래원요청


    # 체결 정보 요청
    # INPUT : 종목코드
    def _opt10003(self):
        
        # 멀티데이터 [체결정보]
        outputM = ["시간", "현재가", "전일대비", "대비율", "우선매도호가단위", "우선매수호가단위",
                   "체결거래량", "sign", "누적거래량", "누적거래대금", "체결강도"]

        return outputM


    # opt10004 : 주식호가요청
    # INPUT : 종목코드
    def _opt10004(self):
        
        # 멀티데이터 [주식호가]
        outputM = ["호가잔량기준시간", "매도10차선잔량대비", "매도10차선잔량", "매도10차선호가",
                   "매도9차선잔량대비", "매도9차선잔량", "매도9차선호가", "매도8차선잔량대비", "매도8차선잔량", "매도8차선호가",
                   "매도7차선잔량대비", "매도7차선잔량", "매도7차선호가", "매도6차선잔량대비", "매도6차선잔량", "매도6차선호가",
                   "매도5차선잔량대비", "매도5차선잔량", "매도5차선호가", "매도4차선잔량대비", "매도4차선잔량", "매도4차선호가",
                   "매도3차선잔량대비", "매도3차선잔량", "매도3차선호가", "매도2차선잔량대비", "매도2차선잔량", "매도2차선호가",
                   "매도1차선잔량대비", "매도최우선잔량", "매도최우선호가", "매수최우선호가", "매수최우선잔량",
                   "매수1차선잔량대비", "매수2차선호가", "매수2차선잔량", "매수2차선잔량대비",
                   "매수3차선호가", "매수3차선잔량", "매수3차선잔량대비", "매수4차선호가", "매수4차선잔량", "매수4차선잔량대비",
                   "매수5차선호가", "매수5차선잔량", "매수5차선잔량대비", "매수6차선호가", "매수6차선잔량", "매수6차선잔량대비",
                   "매수7차선호가", "매수7차선잔량", "매수7차선잔량대비", "매수8차선호가", "매수8차선잔량", "매수8차선잔량대비",
                   "매수9차선호가", "매수9차선잔량", "매수9차선잔량대비", "매수10차선호가", "매수10차선잔량", "매수10차선잔량대비",
                   "총매도잔량직전대비", "총매도잔량", "총매수잔량", "총매수잔량직전대비",
                   "시간외매도잔량대비", "시간외매도잔량", "시간외매수잔량", "시간외매수잔량대비"]
                   
        return outputM
    

    # opt10005 : 주식일주월시분요청

    # OPT10006 : 주식시분요청

    # opt10007 : 시세표성정보요청
    
    # opt10008 : 주식외국인요청
    
    # OPT10009 : 주식기관요청
    
    # OPT10010 : 업종프로그램요청

    
    # 주문 체결 요청
    # INPUT : 계좌번호
    def _opt10012(self):

        # 멀티데이터 [주문체결]
        outputM = ["주문수량", "주문가격", "미체결수량", "체결누계금액", "원주문번호", "주문구분",
                   "매매구분", "매도수구분", "주문/체결시간", "체결가", "체결량", "주문상태",
                   "단위체결가", "대출일", "신용구분", "만기일", "보유수량", "매입단가", "총매입가",
                   "주문가능수량", "당일매도수량", "당일매도금액", "당일매수수량", "당일매수금액",
                   "당일매매수수료", "당일매매세금", "당일hts매도수수료", "당일hts매수수수료",
                   "당일매도손익", "당일순매수량", "매도/매수구분", "당일총매도손일", "예수금",
                   "사용가능현금", "사용가능대용", "전일재사용", "당일재사용", "담보현금", "신용금액",
                   "신용이자", "담보대출수량", "현물주문체결이상유무", "현물잔고이상유무",
                   "현물예수금이상유무", "선물주문체결이상유무", "선물잔고이상유무", "D+1추정예수금",
                   "D+2추정예수금", "D+1매수/매도정산금", "D+2매수/매도정산금", "D+1연체변제소요금",
                   "D+2연체변제소요금", "D+1추정인출가능금", "D+2추정인출가능금", "현금증거금",
                   "대용잔고", "대용증거금", "수표금액", "현금미수금", "신용설정보증금", "인출가능금액"]

        return outputM
    
        
    # opt10013 : 신용매매동향요청
        
    # opt10014 : 공매도추이요청
        
    # opt10015 : 일별거래상세요청
        
    # OPT10016 : 신고저가요청
        
    # OPT10017 : 상하한가요청
        
    # OPT10018 : 고저가근접요청

    
    # 가격 급등락 요청
    # INPUT : 시장구분, 등락구분, 시간구분, 시간, 거래량구분, 종목조건, 신용조건, 가격조건, 상하한포함
    # 시장구분  :  000:전체, 001:코스피, 101:코스닥, 201:코스피200
    # 등락구분  :  1:급등, 2:급락
    # 시간구분  :  1:분전, 2:일전
    # 시간  :  분 혹은 일
    # 거래량구분  :  00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상,
    #                00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상
    # 종목조건  :  0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기
    # 신용조건  :  0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 9:신용융자전체
    # 가격조건  :  0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~3천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상
    # 상하한포함  :  0:미포함, 1:포함
    def _OPT10019(self):

        # 멀티데이터 [가격급등락]
        outputM = ["종목코드", "종목분류", "종목명", "전일대비기호", "전일대비", "등락률", "기준가", "현재가",
                   "기준대비", "거래량", "급등률"]

        return outputM
        
        
    # OPT10020 : 호가잔량상위요청
        
    # OPT10021 : 호가잔량급증요청
        
    # OPT10022 : 잔량율급증요청

    
    # 거래량 급증 요청
    # INPUT : 시장구분, 정렬구분, 시간구분, 거래량구분, 시간, 종목조건, 가격구분
    # 시장구분  :  000:전체, 001:코스피, 101:코스닥
    # 정렬구분  :  1:급증량, 2:급증률
    # 시간구분  :  1:분, 2:전일
    # 거래량구분  :  5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상,
    #                500:50만주이상, 1000:백만주이상
    # 시간  :  분 기준
    # 종목조건  :  0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기
    # 가격구분  :  0:전체조회, 2:5만원이상, 5:1만원이상, 6:5천원이상, 8:1천원이상, 9:10만원이상
    def _OPT10023(self, rqname):

        # 멀티데이터 [거래량급증]
        outputM = ["종목코드", "종목명", "현재가", "전일대비기호", "전일대비", "등락률", "이전거래량", "현재거래량",
                   "급증량", "급증률"]

        return outputM
        
        
    # OPT10024 : 거래량갱신요청
        
    # OPT10025 : 매물대집중요청
        
    # opt10026 : 고저PER요청
        
    # opt10027 : 전일대비등락률상위요청
        
    # opt10028 : 시가대비등락률요청
        
    # OPT10029 : 예상체결등락률상위요청

    
    # 당일 거래량 상위 요청
    # INPUT : 시장구분, 정렬구분, 관리종목포함
    # 시장구분  :  000:전체, 001:코스피, 101:코스닥
    # 정렬구분  :  1:거래량, 2:거래회전율, 3:거래대금
    # 관리종목포함  :  0:관리종목 포함, 1:관리종목 미포함
    def _OPT10030(self):

        # 멀티데이터 [당일거래량상위]
        outputM = ["종목코드", "종목명", "현재가", "전일대비기호", "전일대비", "등락률", "거래량", "전일비",
                   "거래회전율", "거래금액"]

        return outputM
        
    
    # 전일 거래량 상위 요청
    # INPUT : 시장구분, 조회구분, 순위시작, 순위끝
    # 시장구분  :  000:전체, 001:코스피, 101:코스닥
    # 조회구분  :  1:전일거래량 상위100종목, 2:전일거래대금 상위100종목
    # 순위시작  :  0 ~ 100 값 중에  조회를 원하는 순위 시작값
    # 순위끝  :  0 ~ 100 값 중에  조회를 원하는 순위 끝값
    def _OPT10031(self):

        # 멀티데이터 [전일거래량상위]
        outputM = ["종목코드", "종목명", "현재가", "전일대비기호", "전일대비", "거래량"]

        return outputM
        
        
    # OPT10032 : 거래대금상위요청
        
    # OPT10033 : 신용비율상위요청
        
    # OPT10034 : 외인기간별매매상위요청
        
    # OPT10035 : 외인연속순매매상위요청
        
    # OPT10036 : 매매상위요청
        
    # opt10037 : 외국계창구매매상위요청
        
    # opt10038 : 종목별증권사순위요청
        
    # OPT10039 : 증권사별매매상위요청
        
    # opt10040 : 당일주요거래원요청
        
    # opt10041 : 조기종료통화단위요청
        
    # OPT10042 : 순매수거래원순위요청
        
    # OPT10043 : 거래원매물대분석요청
        
    # OPT10044 : 일별기관매매종목요청
        
    # opt10045 : 종목별기관매매추이요청
        
    # OPT10048 : ELW일별민감도지표요청
        
    # OPT10049 : ELW투자지표요청
        
    # OPT10050 : ELW민감도지표요청
        
    # OPT10051 : 업종별투자자순매수요청
        
    # opt10053 : 당일상위이탈원요청
        
    # OPT10058 : 투자자별일별매매종목요청
        
    # opt10059 : 종목별투자자기관별요청
        
    # opt10060 : 종목별투자자기관별차트요청
        
    # opt10061 : 종목별투자자기관별합계요청
        
    # opt10062 : 동일순매매순위요청
        
    # opt10063 : 장중투자자별매매요청
        
    # opt10064 : 장중투자자별매매차트요청
        
    # OPT10065 : 장중투자자별매매상위요청
        
    # opt10066 : 장중투자자별매매차트요청
        
    # OPT10067 : 대차거래내역요청
        
    # OPT10068 : 대차거래추이요청
        
    # OPT10069 : 대차거래상위10종목요청
        
    # opt10070 : 당일주요거래원요청
        
    # OPT10071 : 시간대별전일비거래비중요청
        
    # OPT10072 : 일자별종목별실현손익요청
        
    # OPT10073 : 일자별종목별실현손익요청
        
    # opt10074 : 일자별실현손익요청

    
    # 실시간 미체결 요청
    # INPUT : 계좌번호, 체결구분, 매매구분
    # 체결구분  :  0:체결+미체결조회, 1:미체결조회, 2:체결조회
    # 매매구분  :  0:전체, 1:매도, 2:매수
    # 
    # OUTPUT
    # 주문구분 : +매수, -매도, 매수취소, 매도취소 등..
    def _opt10075(self):

        # 멀티데이터 [실시간미체결]
        outputM = ["계좌번호", "주문번호", "관리사번", "종목코드", "업무구분", "주문상태", "종목명",
                   "주문수량", "주문가격", "미체결수량", "체결누계금액", "원주문번호", "주문구분",
                   "매매구분", "시간", "체결번호", "체결가", "체결량", "현재가", "매도호가", "매수호가",
                   "단위체결가", "단위체결량", "당일매매수수료", "당일매매세금", "개인투자자"]

        return outputM


    # 실시간 체결 요청
    # INPUT : 종목코드, 조회구분, 모름2, 계좌번호, 비밀번호, 모름3
    # 조회구분  :  0:전체, 1:종목
    # 비밀번호  :  사용안함(공백)
    def _OPT10076(self):

        # 멀티데이터 [실시간체결]
        outputM = ["주문번호", "종목명", "주문구분", "주문가격", "주문수량", "체결가", "체결량",
                   "미체결수량", "당일매매수수료", "당일매매세금", "주문상태", "매매구분", "원주문번호",
                   "시간", "계좌번호"]

        return outputM
    

    # 당일 실현손익 상세 요청
    # INPUT : 계좌번호, 비밀번호, 종목코드
    # 비밀번호  :  사용안함(공백)
    def _opt10077(self):

        # 싱글데이터 [당일실현손익]
        outputS = ["당일실현손익"]
        
        # 멀티데이터 [당일실현손익상세]
        outputM = ["종목명", "체결량", "매입단가", "체결가", "당일매도손익", "손익율", "당일매매수수료",
                   "당일매매세금", "종목코드"]

        return outputS + outputM

        
    # OPT10078 : 증권사별종목매매동향요청

    
    # 주식 틱차트 조회 요청
    # INPUT : 종목코드, 틱범위, 수정주가구분
    # 틱범위  :  1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱
    # 수정주가구분  :  0 or 1
    # (수신)수정주가구분  :  1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락
    def _opt10079(self):

        # 싱글데이터 [주식틱차트]
        outputS = ["종목코드", "마지막틱갯수"]
        
        # 멀티데이터 [주식틱차트조회]
        outputM = ["현재가", "거래량", "체결시간", "시가", "고가", "저가", "수정주가구분", "수정비율",
                   "대업종구분", "소업종구분", "종목정보", "수정주가이벤트", "전일종가"]

        return outputS + outputM
    
    
        
    # 주식 분봉차트 조회 요청
    # INPUT : 종목코드, 틱범위, 수정주가구분
    # 틱범위  :  1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분
    # 수정주가구분  :  0 or 1
    # (수신)수정주가구분  :  1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락
    def _opt10080(self):
        
        # 싱글데이터 [주식분차트]
        outputS = ["종목코드"]
        
        # 멀티데이터 [주식분봉차트조회]
        outputM = ["현재가", "거래량", "체결시간", "시가", "고가", "저가", "수정주가구분", "수정비율",
                   "대업종구분", "소업종구분", "종목정보", "수정주가이벤트", "전일종가"]

        return outputS + outputM


    # 주식 일봉차트 조회 요청
    # INPUT : 종목코드, 기준일자, 수정주가구분
    # 기준일자  :  "YYYYMMDD"
    # 수정주가구분  :  0 or 1
    # (수신)수정주가구분  :  1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락
    def _opt10081(self):
        
        # 싱글데이터 [주식일봉차트]
        outputS = ["종목코드"]
        
        # 멀티데이터 [주식일봉차트조회]
        outputM = ["종목코드", "현재가", "거래량", "거래대금", "일자", "시가", "고가", "저가", "수정주가구분",
                   "수정비율", "대업종구분", "소업종구분", "종목정보", "수정주가이벤트", "전일종가"]

        return outputS + outputM


    # 주식 주봉차트 조회 요청
    # INPUT : 종목코드, 기준일자, 끝일자, 수정주가구분
    # 기준일자, 끝일자  :  "YYYYMMDD"
    # 수정주가구분  :  0 or 1
    # (수신)수정주가구분  :  1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락
    def _opt10082(self):

        # 싱글데이터 [주식주봉차트]
        outputS = ["종목코드"]
        
        # 멀티데이터 [주식주봉차트조회]
        outputM = ["현재가", "거래량", "거래대금", "일자", "시가", "고가", "저가", "수정주가구분", "수정비율",
                   "대업종구분", "소업종구분", "종목정보", "수정주가이벤트", "전일종가"]

        return outputS + outputM

    
    # 주식 월봉차트 조회 요청
    # INPUT : 종목코드, 기준일자, 끝일자, 수정주가구분
    # 기준일자, 끝일자  :  "YYYYMMDD"
    # 수정주가구분  :  0 or 1
    # (수신)수정주가구분  :  1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락
    def _opt10083(self):

        # 싱글데이터 [주식월봉차트]
        outputS = ["종목코드"]
        
        # 멀티데이터 [주식월봉차트조회]
        outputM = ["현재가", "거래량", "거래대금", "일자", "시가", "고가", "저가", "수정주가구분", "수정비율",
                   "대업종구분", "소업종구분", "종목정보", "수정주가이벤트", "전일종가"]

        return outputS + outputM

    
    # 당일전일 체결 요청
    # INPUT : 종목코드, 당일전일, 틱분, 시간
    # 당일전일  :  당일:1, 전일:2
    # 틱분  :  틱:0 , 분:1
    # 시간  :  조회시간 4자리 (예 : 오전 9시일 경우 '0900', 오후 2시 30분일 경우 '1430')
    def _opt10084(self):

        # 멀티데이터 [당일전일체결]
        outputM = ["시간", "현재가", "전일대비", "대비율", "우선매도호가단위", "우선매수호가단위", "체결거래량",
                   "sign", "누적거래량", "누적거래대금", "체결강도"]

        return outputM

    
    # 계좌 수익률 요청
    # INPUT : 계좌번호
    def _opt10085(self):

        # 멀티데이터 [계좌수익률]
        outputM = ["일자", "종목코드", "종목명", "현재가", "매입가", "매입금액", "보유수량", "당일매도손익",
                   "당일매매수수료", "당일매매세금", "신용구분", "대출일", "결제잔고", "청산가능수량", "신용금액",
                   "신용이자", "만기일"]

        return outputM
    
        
    # opt10086 : 일별주가요청
        
    # opt10087 : 시간외단일가요청
        
    # opt10094 : 주식년봉차트조회요청
        
    # opt20001 : 업종현재가요청
        
    # OPT20002 : 업종별주가요청
        
    # opt20003 : 전업종지수요청
        
    # OPT20004 : 업종틱차트조회요청
        
    # OPT20005 : 업종분봉조회요청
        
    # OPT20006 : 업종일봉조회요청
        
    # OPT20007 : 업종주봉조회요청
        
    # OPT20008 : 업종월봉조회요청
        
    # opt20009 : 업종현재가일별요청
        
    # opt20019 : 업종년봉조회요청
        
    # opt20068 : 대차거래추이요청(종목별)
        
    # OPT30001 : ELW가격급등락요청
        
    # OPT30002 : 거래원별ELW순매매상위요청
        
    # OPT30003 : ELWLP보유일별추이요청
        
    # OPT30004 : ELW괴리율요청
        
    # opt30005 : ELW조건검색요청
        
    # opt30006 : ELW종목상세요청
        
    # OPT30007 : ELW종목상세요청
        
    # OPT30008 : ELW민감도지표요청
        
    # OPT30009 : ELW등락율순위요청
        
    # OPT30010 : ELW잔량순위요청
        
    # OPT30011 : ELW근접율요청
        
    # OPT40001 : ETF수익율요청
        
    # OPT40002 : ETF종목정보요청
        
    # OPT40003 : ETF일별추이요청
        
    # opt40004 : ETF전체시세요청
        
    # OPT40005 : ETF일별추이요청
        
    # opt40006 : ETF시간대별추이요청
        
    # OPT40007 : ETF시간대별체결요청
        
    # opt40008 : ETF시간대별체결요청
        
    # OPT40009 : ETF시간대별체결요청
        
    # opt40010 : ETF시간대별추이요청
        
    # opt50001 : 선옵현재가정보요청
        
    # opt50002 : 선옵일자별체결요청
        
    # OPT50003 : 선옵시고저가요청
        
    # opt50004 : 콜옵션행사가요청
        
    # OPT50005 : 선옵시간별거래량요청
        
    # OPT50006 : 선옵체결추이요청
        
    # opt50007 : 선물시세추이요청
        
    # opt50008 : 프로그램매매추이차트요청
        
    # OPT50009 : 선옵시간별잔량요청
        
    # OPT50010 : 선옵호가잔량추이요청
        
    # OPT50011 : 선옵호가잔량추이요청
        
    # OPT50012 : 선옵타임스프레드차트요청
        
    # OPT50013 : 선물가격대별비중차트요청
        
    # OPT50014 : 선물가격대별비중차트요청
        
    # opt50015 : 선물미결제약정일차트요청
        
    # OPT50016 : 베이시스추이차트요청
        
    # OPT50017 : 베이시스추이차트요청
        
    # OPT50018 : 풋콜옵션비율차트요청
        
    # OPT50019 : 선물옵션현재가정보요청
        
    # opt50020 : 복수종목결제월별시세요청
        
    # OPT50021 : 콜종목결제월별시세요청
        
    # OPT50022 : 풋종목결제월별시세요청
        
    # opt50023 : 민감도지표추이요청
        
    # OPT50024 : 일별변동성분석그래프요청
        
    # OPT50025 : 시간별변동성분석그래프요청
        
    # OPT50026 : 선옵주문체결요청
        
    # OPT50027 : 선옵잔고요청
        
    # opt50028 : 선물틱차트요청
        
    # OPT50029 : 선물옵션분차트요청
        
    # OPT50030 : 선물옵션일차트요청
        
    # OPT50031 : 선옵잔고손익요청
        
    # OPT50032 : 선옵당일실현손익요청
        
    # OPT50033 : 선옵잔존일조회요청
        
    # OPT50034 : 선옵전일가격요청
        
    # OPT50035 : 지수변동성차트요청
        
    # OPT50036 : 주요지수변동성차트요청
        
    # OPT50037 : 코스피200지수요청
        
    # OPT50038 : 투자자별만기손익차트요청
        
    # OPT50039 : 투자자별포지션종합요청
        
    # OPT50040 : 선옵시고저가요청
        
    # OPT50043 : 주식선물거래량상위종목요청
        
    # OPT50044 : 주식선물시세표요청
        
    # opt50062 : 선물미결제약정분차트요청
        
    # opt50063 : 옵션미결제약정일차트요청
        
    # opt50064 : 옵션미결제약정분차트요청
        
    # opt50065 : 풋옵션행사가요청
        
    # opt50066 : 옵션틱차트요청
        
    # opt50067 : 옵션분차트요청
        
    # opt50068 : 옵션일차트요청
        
    # opt50071 : 선물주차트요청
        
    # opt50072 : 선물월차트요청
        
    # opt50073 : 선물년차트요청
        
    # OPT90001 : 테마그룹별요청
        
    # opt90002 : 테마구성종목요청
        
    # opt90003 : 프로그램순매수상위50요청
        
    # OPT90004 : 종목별프로그램매매현황요청
        
    # OPT90005 : 프로그램매매추이요청
        
    # OPT90006 : 프로그램매매차익잔고추이요청
        
    # OPT90007 : 프로그램매매누적추이요청
        
    # opt90008 : 종목시간별프로그램매매추이요청
        
    # opt90009 : 외국인기관매매상위요청
        
    # OPT90010 : 차익잔고현황요청
        
    # opt90011 : 차익잔고현황요청
        
    # OPT90012 : 대차거래내역요청
        
    # opt90013 : 종목일별프로그램매매추이요청
        
    # opt99999 : 대차거래상위10종목요청
    


######################################################################################


    
    # OPTFOFID : 선물전체시세요청


    # 관심종목 정보 요청
    # INPUT : 종목코드
    # commKwRqData() 사용
    def _OPTKWFID(self):

        # 멀티데이터 [관심종목정보]
        outputM = ["종목코드", "종목명", "현재가", "기준가", "전일대비", "전일대비기호", "등락율",
                   "거래량", "거래대금", "체결량", "체결강도", "전일거래량대비", "매도호가", "매수호가",
                   "매도1차호가", "매도2차호가", "매도3차호가", "매도4차호가", "매도5차호가",
                   "매수1차호가", "매수2차호가", "매수3차호가", "매수4차호가", "매수5차호가",
                   "상한가", "하한가", "시가", "고가", "저가", "종가", "체결시간", "예상체결가",
                   "예상체결량", "자본금", "액면가", "시가총액", "주식수", "호가시간", "일자",
                   "우선매도잔량", "우선매수잔량", "우선매도건수", "우선매수건수", "총매도잔량",
                   "총매수잔량", "총매도건수", "총매수건수", "패리티", "기어링", "손익분기", "자본지지",
                   "ELW행사가", "전환비율", "ELW만기일", "미결제약정", "미결제전일대비", "이론가",
                   "내재변동성", "델타", "감마", "쎄타", "베가", "로"]

        return outputM
    
            
    # OPTKWINV : 관심종목투자자정보요청
            
    # OPTKWPRO : 관심종목프로그램정보요청



######################################################################################



    # 예수금 상세 현황 요청
    # INPUT : 계좌번호, 비밀번호, 비밀번호입력매체구분, 조회구분
    # 비밀번호 : 사용안함(공백)
    # 비밀번호입력매체구분 : 00
    # 조회구분  :  1 : 추정조회, 2 : 일반조회
    def _opw00001(self):

        # 싱글데이터 [예수금상세현황]
        outputS = ["예수금", "주식증거금현금", "수익증권증거금현금", "익일수익증권매도정산대금",
                   "해외주식원화대용설정금", "신용보증금현금", "신용담보금현금", "추가담보금현금",
                   "기타증거금", "미수확보금", "공매도대금", "신용설정평가금", "수표입금액",
                   "기타수표입금액", "신용담보재사용", "코넥스기본예탁금", "ELW예탁평가금",
                   "신용대주권리예정금액", "생계형가입금액", "생계형입금가능금액", "대용금평가금액(합계)",
                   "잔고대용평가금액", "위탁대용잔고평가금액", "수익증권대용평가금액", "위탁증거금대용",
                   "신용보증금대용", "신용담보금대용", "추가담보금대용", "권리대용금", "출금가능금액",
                   "랩출금가능금액", "주문가능금액", "수익증권매수가능금액", "20%종목주문가능금액",
                   "30%종목주문가능금액", "40%종목주문가능금액", "100%종목주문가능금액", "현금미수금",
                   "현금미수연체료", "현금미수금합계", "신용이자미납", "신용이자미납연체료",
                   "신용이자미납합계", "기타대여금", "기타대여금연체료", "기타대여금합계", "미상환융자금",
                   "융자금합계", "대주금합계", "신용담보비율", "중도이용료", "최소주문가능금액",
                   "대출총평가금액", "예탁담보대출잔고", "매도담보대출잔고", "d+1추정예수금",
                   "d+1매도매수정산금", "d+1매수정산금", "d+1미수변제소요금", "d+1매도정산금", "d+1출금가능금액",
                   "d+2추정예수금", "d+2매도매수정산금", "d+2매수정산금", "d+2미수변제소요금", "d+2매도정산금",
                   "d+2출금가능금액", "출력건수"]
        
        # 멀티데이터 [종목별예수금현황]
        outputM = ["통화코드", "외화예수금", "원화대용평가금", "해외주식증거금", "출금가능금액(예수금)",
                   "주문가능금액(예수금)", "외화미수(합계)", "외화현금미수금", "연체료",
                   "d+1외화예수금", "d+2외화예수금", "d+3외화예수금", "d+4외화예수금"]

        return outputS + outputM
    
          
    # 일별 추정예탁자산 현황 요청
    # INPUT : 계좌번호, 비밀번호, 시작조회기간, 종료조회기간
    # 비밀번호 : 사용안함(공백)
    # 시작조회기간, 종료조회기간 : YYYYMMDD
    def _OPW00002(self):

        # 싱글데이터 [출력건수]
        outputS = ["출력건수"]
        
        # 멀티데이터 [일별추정예탁자산현황]
        outputM = ["일자", "예수금", "담보대출금", "신용융자금", "대주담보금", "대용금",
                   "추정예탁자산", "추정예탁자산수익증권제외"]
        
        return outputS + outputM
    


    # 추정자산 조회 요청
    # INPUT : 계좌번호, 비밀번호, 상장폐지조회구분
    # 비밀번호 : 사용안함(공백)
    # 상장폐지조회구분  :  0 : 전체, 1 : 상장폐지종목제외
    def _OPW00003(self):

        # 싱글데이터 [추정자산조회]
        outputS = ["추정예탁자산"]
        
        return outputS + outputM
    
    

    # 계좌평가 현황 요청
    # INPUT : 계좌번호, 비밀번호, 상장폐지조회구분, 비밀번호입력매체구분
    # 비밀번호 : 사용안함(공백)
    # 상장폐지조회구분  :  0 : 전체, 1 : 상장폐지종목제외
    # 비밀번호입력매체구분 : 00
    def _OPW00004(self):

        # 싱글데이터 [계좌평가현황]
        outputS = ["계좌명", "지점명", "예수금", "D+2추정예수금", "유가잔고평가액", "예탁자산평가액",
                   "총매입금액", "추정예탁자산", "매도담보대출금", "당일투자원금", "당월투자원금",
                   "누적투자원금", "당일투자손익", "당월투자손익", "누적투자손익", "당일손익율",
                   "당월손익율", "누적손익율", "출력건수"]
        
        # 멀티데이터 [종목별계좌평가현황]
        outputM = ["종목코드", "종목명", "보유수량", "평균단가", "현재가", "평가금액", "손익금액", "손익율",
                   "대출일", "매입금액", "결제잔고", "전일매수수량", "전일매도수량",
                   "금일매수수량", "금일매도수량"]
        
        return outputS + outputM
    

    # 체결 잔고 요청
    # INPUT : 계좌번호, 비밀번호, 비밀번호입력매체구분
    # 비밀번호 : 사용안함(공백)
    # 비밀번호입력매체구분 : 00
    def _opw00005(self):

        # 싱글데이터 [체결잔고]
        outputS = ["예수금", "예수금D+1", "예수금D+2", "출금가능금액", "미수확보금", "대용금", "권리대용금",
                   "주문가능현금", "현금미수금", "신용이자미납금", "기타대여금", "미상환융자금", "증거금현금",
                   "증거금대용", "주식매수총액", "평가금액합계", "총손익합계", "총손익률", "총재매수가능금액",
                   "20주문가능금액", "30주문가능금액", "40주문가능금액", "50주문가능금액", "60주문가능금액",
                   "100주문가능금액", "신용융자합계", "신용융자대주합계", "신용담보비율", "예탁담보대출금액",
                   "매도담보대출금액", "조회건수"]
        
        # 멀티데이터 [종목별체결잔고]
        outputM = ["신용구분", "대출일", "만기일", "종목번호", "종목명", "결제잔고", "현재잔고", "현재가",
                   "매입단가", "매입금액", "평가금액", "평가손익", "손익률"]
        
        return outputS + outputM
    
            
    # OPW00006 : 관리자별주문체결내역요청


    # 계좌별 주문체결내역 상세 요청
    # INPUT : 주문일자, 계좌번호, 비밀번호, 비밀번호입력매체구분, 조회구분, 주식채권구분, 매도수구분,
    #         종목코드, 시작주문번호
    # 주문일자 : YYYYMMDD
    # 비밀번호 : 사용안함(공백)
    # 비밀번호입력매체구분 : 00
    # 조회구분  :  1:주문순, 2:역순, 4:체결내역만
    # 주식채권구분  :  0:전체, 1:주식, 2:채권
    # 매도수구분  :  0:전체, 1:매도, 2:매수
    def _OPW00007(self):

        # 싱글데이터 [출력건수]
        outputS = ["출력건수"]
        
        # 멀티데이터 [계좌별주문체결내역상세]
        outputM = ["주문번호", "종목번호", "매매구분", "신용구분", "주문수량", "주문단가", "확인수량",
                   "접수구분", "반대여부", "주문시간", "원주문", "종목명", "주문구분", "대출일",
                   "체결수량", "체결단가", "주문잔량", "통신구분", "정정취소", "확인시간"]
        
        return outputS + outputM
    
            
    # opw00008 : 계좌별익일결제예정내역요청


    # 계좌별 주문체결 현황 요청
    # INPUT : 주문일자, 계좌번호, 비밀번호, 비밀번호입력매체구분, 주식채권구분, 시장구분, 매도수구분, 조회구분,
    #         종목코드, 시작주문번호
    # 주문일자 : YYYYMMDD
    # 비밀번호 : 사용안함(공백)
    # 비밀번호입력매체구분 : 00
    # 주식채권구분  :  0:전체, 1:주식, 2:채권
    # 시장구분  :  0:전체, 1:장내, 2:코스닥, 3:OTCBB, 4:ECN
    # 매도수구분  :  0:전체, 1:매도, 2:매수
    # 조회구분  :  0:전체, 1:체결
    def _opw00009(self):

        # 싱글데이터 [계좌별주문체결현황]
        outputS = ["매도약정금액", "매수약정금액", "약정금액", "조회건수"]
        
        # 멀티데이터 [계좌별주문체결현황배열]
        outputM = ["주식채권구분", "주문번호", "종목번호", "매매구분", "주문유형구분", "주문수량", "주문단가",
                   "확인수량", "예약반대", "체결번호", "접수구분", "원주문번호", "종목명", "결제구분",
                   "신용거래구분", "체결수량", "체결단가", "통신구분", "정정취소구분", "체결시간"]
        
        return outputS + outputM
    
            
    # 주문 인출 가능 금액 요청
    # INPUT : 계좌번호, 비밀번호, 비밀번호입력매체구분, 입출금금액, 종목번호, 매매구분, 매매수량,
    #         매수가격, 예상매수단가
    # 비밀번호 : 사용안함(공백)
    # 비밀번호입력매체구분 : 00
    # 매매구분  :  1:매도, 2:매수
    def _opw00010(self):
        
        # 싱글데이터 [주문인출가능금액]
        outputS = ["증거금20주문가능금액", "증거금20주문가능수량", "증거금30주문가능금액", "증거금30주문가능수량",
                   "증거금40주문가능금액", "증거금40주문가능수량", "증거금50주문가능금액", "증거금50주문가능수량",
                   "증거금60주문가능금액", "증거금60주문가능수량", "증거금100주문가능금액", "증거금100주문가능수량",
                   "전일재사용가능금액", "금일재사용가능금액", "예수금", "대용금", "미수금", "주문가능대용",
                   "주문가능현금", "인출가능금액", "익일인출가능금액", "매입금액", "수수료", "매입정산금",
                   "D2추정예수금"]

        return outputS
    
            
    # opw00011 : 증거금율별주문가능수량조회요청
            
    # OPW00012 : 신용보증금율별주문가능수량조회요청
            
    # 증거금 세부내역 조회 요청
    # INPUT : 계좌번호, 비밀번호
    # 비밀번호 : 사용안함(공백)
    def _opw00013(self):
        
        # 싱글데이터 [증거금세부내역조회]
        outputS = ["금일재사용대상금액", "금일재사용사용금액", "금일재사용가능금액", "금일재사용제한금액",
                   "금일재사용가능금액최종", "전일재사용대상금액", "전일재사용사용금액", "전일재사용가능금액",
                   "전일재사용제한금액", "전일재사용가능금액최종", "현금금액", "현금증거금", "사용가능현금",
                   "현금사용제한금액", "사용가능현금최종", "대용금액", "대용증거금", "사용가능대용",
                   "대용사용제한금액", "사용가능대용최종", "신용보증금현금", "신용보증금대용", "신용담보금현금",
                   "신용담보금대용", "미수금", "대주담보금재사용금", "20주문가능금액", "30주문가능금액",
                   "40주문가능금액", "50주문가능금액", "60주문가능금액", "100주문가능금액", "금일신용상환손실금액",
                   "전일신용상환손실금액", "금일대주상환손실대용증거금", "전일대주상환손실대용증거금"]

        return outputS
    
            
    # OPW00014 : 비밀번호일치여부요청
            
    # OPW00015 : 위탁종합거래내역요청
            
    # 일별 계좌 수익률 상세 현황 요청
    # INPUT : 계좌번호, 비밀번호, 평가시작일, 평가종료일, 비밀번호입력매체구분
    # 비밀번호 : 사용안함(공백)
    # 비밀번호입력매체구분 : 00
    def _OPW00016(self):
        
        # 싱글데이터 [일별계좌수익률상세현황]
        outputS = ["관리사원번호", "관리자명", "관리자지점", "예수금_초", "예수금_말",
                   "유가증권평가금액_초", "유가증권평가금액_말",
                   "대주담보금_초", "대주담보금_말", "신용융자금_초", "신용융자금_말", "현금미수금_초", "현금미수금_말",
                   "원화대용금_초", "원화대용금_말", "대주평가금_초", "대주평가금_말", "권리평가금_초", "권리평가금_말",
                   "대출금_초", "대출금_말", "기타대여금_초", "기타대여금_말", "신용이자미납금_초", "신용이자미납금_말",
                   "신용이자_초", "신용이자_말", "순자산액계_초", "순자산액계_말", "투자원금평잔",
                   "평가손익", "수익률", "회전율", "기간내총입금", "기간내총출금", "기간내총입고", "기간내총출고",
                   "선물대용매도금액", "위탁대용매도금액"]

        return outputS


    # 계좌별 당일 현황 요청
    # INPUT : 계좌번호, 비밀번호, 비밀번호입력매체구분
    # 비밀번호 : 사용안함(공백)
    # 비밀번호입력매체구분 : 00
    def _OPW00017(self):
        
        # 싱글데이터 [계좌별당일현황]
        outputS = ["D+2추정예수금", "신용이자미납금", "기타대여금", "일반주식평가금액D+2", "예탁담보대출금D+2",
                   "예탁담보주식평가금액D+2", "신용융자금D+2", "신용융자평가금D+2", "신용대주담보금D+2",
                   "신용대주평가금D+2", "입금금액", "출금금액", "입고금액", "출고금액", "매도금액", "매수금액",
                   "수수료", "세금", "주식매입자금대출금", "RP평가금액", "채권평가금액", "ELS평가금액",
                   "신용이자금액", "매도대금담보대출이자금액", "배당금액"]

        return outputS
    

    # 계좌평가잔고 내역 요청
    # INPUT : 계좌번호, 비밀번호, 비밀번호입력매체구분, 조회구분
    # 비밀번호 : 사용안함(공백)
    # 비밀번호입력매체구분 : 00
    # 조회구분  :  1:합산, 2:개별
    def _opw00018(self):
        
        # 싱글데이터 [계좌평가결과]
        outputS = ["총매입금액", "총평가금액", "총평가손익금액", "총수익률(%)", "추정예탁자산", "총대출금",
                   "총융자금액", "총대주금액", "조회건수"]
        
        # 멀티데이터 [계좌평가잔고개별합산]
        outputM = ["종목번호", "종목명", "평가손익", "수익률(%)", "매입가", "전일종가", "보유수량", "매매가능수량",
                   "현재가", "전일매수수량", "전일매도수량", "금일매수수량", "금일매도수량", "매입금액", "매입수수료",
                   "평가금액", "평가수수료", "세금", "수수료합", "보유비중(%)", "신용구분", "신용구분명", "대출일"]
        
        return outputS + outputM
    
            
    # OPW20001 : 선물옵션청산주문위탁증거금가계산요청
            
    # OPW20002 : 선옵당일매매변동현황요청
            
    # opw20003 : 선옵기간손익조회요청
            
    # OPW20004 : 선옵주문체결내역상세요청
            
    # OPW20005 : 선옵주문체결내역상세평균가요청
            
    # OPW20006 : 선옵잔고상세현황요청
            
    # OPW20007 : 선옵잔고현황정산가기준요청
            
    # OPW20008 : 계좌별결제예상내역조회요청
            
    # opw20009 : 선옵계좌별주문가능수량요청
            
    # OPW20010 : 선옵예탁금및증거금조회요청
            
    # OPW20011 : 선옵계좌예비증거금상세요청
            
    # opw20012 : 선옵증거금상세내역요청
            
    # OPW20013 : 계좌미결제청산가능수량조회요청
            
    # OPW20014 : 선옵실시간증거금산출요청
            
    # opw20015 : 옵션매도주문증거금현황요청
            
    # opw20016 : 신용융자 가능종목요청
            
    # opw20017 : 신용융자 가능문의



######################################################################################



    # 매수 주문 시 자동 수신
    def _KOA_NORMAL_BUY_KP_ORD(self):

        outputS = []

        return outputS


    # 매도 주문 시 자동 수신
    def _KOA_NORMAL_SELL_KP_ORD(self):

        outputS = []

        return outputS


    # 매수 주문 (언제 오는지는???)
    def _KOA_NORMAL_BUY_KQ_ORD(self):

        print('KOA_NORMAL_BUY_KQ_ORD')
        outputS = []

        return outputS


    # 매도 주문 (언제 오는지는???)
    def _KOA_NORMAL_SELL_KQ_ORD(self):

        print('KOA_NORMAL_SELL_KQ_ORD')
        outputS = []

        return outputS
    

    # 매수 주문 변경 시 자동 수신
    def _KOA_NORMAL_KP_MODIFY(self):

        outputS = []

        return outputS


    # 매도 주문 변경 시 자동 수신
    def _KOA_NORMAL_KQ_MODIFY(self):

        outputS = []

        return outputS


    # 매수 주문 취소 시 자동 수신
    def _KOA_NORMAL_KP_CANCEL(self):

        outputS = []

        return outputS


    # 매도 주문 취소 시 자동 수신
    def _KOA_NORMAL_KQ_CANCEL(self):

        outputS = []

        return outputS



######################################################################################



    # 입력받은 outputs 중 trcode에서 실제로 얻을 수 있는 출력 반환.
    # outputs = [] 이면 trcode에서 얻을 수 있는 모든 출력 반환.
    def getValidOutputs(self, trcode, outputs):

        # TR별 함수 수행
        try:
            ret = []
            evalstr = 'self._' + trcode + '()'
            ret = eval(evalstr)
            
            if self.testFlag:
                print("[getValidOutputs()] evalstr : " + evalstr)
                print("[getValidOutputs()] ret : ")
                print(ret)
            
        except:
            print("[getValidOutputs()] " + trcode + " function doesn't exist")
            return

        if outputs==[]: return ret
        
        validOutputs = [i for i in outputs if i in ret]

        if self.testFlag:
                print("[getValidOutputs()] validOutputs : ")
                print(validOutputs)
                print("\n\n")
                
        return validOutputs



######################################################################################
# 실시간 목록
######################################################################################


    # getCommRealData()로 얻을 수 있는 값들의 인덱스를 {인덱스:값이름} dic으로 반환
    # valuelist가 [] 이면 얻을 수 있는 모든 값들 dic 반환
    def getRealIndex(self, realtype, valuelist):
        dic = {}
        
        if realtype == '주식시세':
            dic = {'현재가':10, '전일대비':11, '등락율':12, '(최우선)매도호가':27,
                   '(최우선)매수호가':28, '누적거래량':13, '누적거래대금':14,
                   '시가':16, '고가':17, '저가':18, '전일대비기호':25,
                   '전일거래량대비(계약,주)':26, '거래대금증감':29, '전일거래량대비(비율)':30,
                   '거래회전율':31, '거래비용':32, '시가총액(억)':311,
                   '상한가발생시간':567, '하한가발생시간':568}

        elif realtype == '주식체결':
            dic = {'체결시간':20, '현재가':10, '전일대비':11, '등락율':12, '(최우선)매도호가':27,
                   '(최우선)매수호가':28, '거래량':15, '누적거래량':13, '누적거래대금':14,
                   '시가':16, '고가':17, '저가':18, '전일대비기호':25,
                   '전일거래량대비(계약,주)':26, '거래대금증감':29, '전일거래량대비(비율)':30,
                   '거래회전율':31, '거래비용':32, '체결강도':228, '시가총액(억)':311,
                   '장구분':290, 'KO접근도':691, '상한가발생시간':567, '하한가발생시간':568}

        elif realtype == '주식우선호가':
            dic = {'(최우선)매도호가':27, '(최우선)매수호가':28}

        elif realtype == '주식호가잔량':
            dic = {'호가시간':21, '매도호가1':41, '매도호가수량1':61, '매도호가직전대비1':81, '매수호가1':51,
                   '매수호가수량1':71, '매수호가직전대비1':91, '매도호가2':42, '매도호가수량2':62,
                   '매도호가직전대비2':82, '매수호가2':52, '매수호가수량2':72, '매수호가직전대비2':92,
                   '매도호가3':43, '매도호가수량3':63, '매도호가직전대비3':83, '매수호가3':53,
                   '매수호가수량3':73, '매수호가직전대비3':93, '매도호가4':44, '매도호가수량4':64,
                   '매도호가직전대비4':84, '매수호가4':54, '매수호가수량4':74, '매수호가직전대비4':94,
                   '매도호가5':45, '매도호가수량5':65, '매도호가직전대비5':85, '매수호가5':55,
                   '매수호가수량5':75, '매수호가직전대비5':95, '매도호가6':46, '매도호가수량6':66,
                   '매도호가직전대비6':86, '매수호가6':56, '매수호가수량6':76, '매수호가직전대비6':96,
                   '매도호가7':47, '매도호가수량7':67, '매도호가직전대비7':87, '매수호가7':57,
                   '매수호가수량7':77, '매수호가직전대비7':97, '매도호가8':48, '매도호가수량8':68,
                   '매도호가직전대비8':88, '매수호가8':58, '매수호가수량8':78, '매수호가직전대비8':98,
                   '매도호가9':49, '매도호가수량9':69, '매도호가직전대비9':89, '매수호가9':59,
                   '매수호가수량9':79, '매수호가직전대비9':99, '매도호가10':50, '매도호가수량10':70,
                   '매도호가직전대비10':90, '매수호가10':60, '매수호가수량10':80, '매수호가직전대비10':100,
                   '매도호가총잔량':121, '매도호가총잔량직전대비':122, '매수호가총잔량':125,
                   '매수호가총잔량직전대비':126, '예상체결가':23, '예상체결수량':24, '순매수잔량':128,
                   '매수비율':129, '순매도잔량':138, '매도비율':139, '예상체결가전일종가대비':200,
                   '예상체결가전일종가대비등락율':201, '예상체결가전일종가대비기호':238, '예상체결가':291,
                   '예상체결량':292, '예상체결가전일대비기호':293, '예상체결가전일대비':294,
                   '예상체결가전일대비등락율':295, 'LP매도호가수량1':621, 'LP매수호가수량1':631,
                   'LP매도호가수량2':622, 'LP매수호가수량2':632, 'LP매도호가수량3':623, 'LP매수호가수량3':633,
                   'LP매도호가수량4':624, 'LP매수호가수량4':634, 'LP매도호가수량5':625, 'LP매수호가수량5':635,
                   'LP매도호가수량6':626, 'LP매수호가수량6':636, 'LP매도호가수량7':627, 'LP매수호가수량7':637,
                   'LP매도호가수량8':628, 'LP매수호가수량8':638, 'LP매도호가수량9':629, 'LP매수호가수량9':639,
                   'LP매도호가수량10':630, 'LP매수호가수량10':640, '누적거래량':13, '전일거래량대비예상체결률':299,
                   '장운영구분':215, '투자자별ticker':216}

        elif realtype == '주식시간외호가':
            pass

        elif realtype == '주식당일거래원':
            pass

        elif realtype == 'ETF NAV':
            pass

        elif realtype == 'ELW 지표':
            pass

        elif realtype == 'ELW 이론가':
            pass

        elif realtype == '주식예상체결':
            dic = {'체결시간':20, '현재가':10, '전일대비':11, '등락율':12, '거래량':15, '누적거래량':13,
                   '전일대비기호':25}

        elif realtype == '주식종목정보':
            dic = {'임의연장':297, '장전임의연장':592, '장후임의연장':593, '상한가':305, '하한가':306,
                   '기준가':307, '조기종료ELW발생':689, '통화단위':594, '증거금율표시':382, '종목정보':370,
                   '종목분류필드':330}

        elif realtype == '임의연장정보':
            pass

        elif realtype == '시간외종목정보':
            pass

        elif realtype == '주식거래원':
            pass

        elif realtype == '선물옵션우선호가':
            pass

        elif realtype == '선물시세':
            pass

        elif realtype == '선물호가잔량':
            pass
        
        elif realtype == '선물이론가':
            pass

        elif realtype == '옵션시세':
            pass

        elif realtype == '옵션호가잔량':
            pass

        elif realtype == '옵션이론가':
            pass

        elif realtype == '선물옵션우선호가':
            pass

        elif realtype == '업종지수':
            pass

        elif realtype == '업종등락':
            pass

        elif realtype == '장시작시간':
            dic = {'장운영구분':215, '체결시간':20, '장시작예상잔여시간':214}
        
        elif realtype == '투자자별매매':
            dic = {'체결시간':20, '이전순매수수량':217, '매도수량':202, '매도증감':203, '매도금액':204,
                   '매도금액증감':205, '매수수량':206, '매수증감':207, '매수금액':208, '매수금액증감':209,
                   '순매수수량':210, '순매수수량증감':211, '순매수금액':212, '순매수금액증감':213,
                   '누적순매수금액':561, '누적순매수수량':562}

        elif realtype == '주문체결':
            dic = {'계좌번호':9201, '주문번호':9203, '관리자사번':9205, '종목코드,업종코드':9001,
                   '주문업무분류':912, '주문상태':913, '종목명':302, '주문수량':900, '주문가격':901,
                   '미체결수량':902, '체결누계금액':903, '원주문번호':904, '주문구분':905, '매매구분':906,
                   '매도수구분':907, '주문/체결시간':908, '체결번호':909, '체결가':910, '체결량':911,
                   '현재가':10, '(최우선)매도호가':27, '(최우선)매수호가':28, '단위체결가':914, '단위체결량':915,
                   '당일매매수수료':938, '당일매매세금':939, '거부사유':919, '화면번호':920, '터미널번호':921,
                   '신용구분(실시간 체결용)':922, '대출일(실시간 체결용)':923}

        elif realtype == '파생잔고':
            pass

        elif realtype == '잔고':
            dic = {'계좌번호':9201, '종목코드,업종코드':9001, '신용구분':917, '대출일':916, '종목명':302, '현재가':10,
                   '보유수량':930, '매입단가':931, '총매입가':932, '주문가능수량':933, '당일순매수량':945, '매도/매수구분':946,
                   '당일총매도손일':950, '예수금':951, '(최우선)매도호가':27, '(최우선)매수호가':28, '기준가':307,
                   '손익율':8019, '신용금액':957, '신용이자':958, '만기일':918, '당일실현손익(유가)':990, '당일실현손익률(유가)':991,
                   '당일실현손익(신용)':992, '당일실현손익률(신용)':993, '담보대출수량':959, 'Extra Item':924}

        elif realtype == '순간체결량':
            pass

        elif realtype == '선물옵션합계':
            pass

        elif realtype == '파생실시간상하한':
            pass

        elif realtype == '종목프로그램매매':
            dic = {'체결시간':20, '현재가':10, '전일대비기호':25, '전일대비':11, '등락율':12, '누적거래량':13,
                   '매도수량':202, '매도금액':204, '매수수량':206, '매수금액':208, '순매수수량':210, '순매수금액':212,
                   '순매수금액증감':213, '장시작예상잔여시간':214, '장운영구분':215, '투자자별ticker':216}

        if dic=={}: return {}

        ret = {}

        if valuelist == []:
            ret = {v:k for k, v in dic.items()}
            
        else:
            for i in valuelist:
                j = dic.get(i)
                if j!=None: ret[j] = i

        if self.testFlag:
            print("\n\n")
            print("[getRealIndex()] dic : ")
            print(dic)
            print("[getRealIndex()] ret : ")
            print(ret)
            
        return ret


    # 지정한 값들을 getCommRealData()로 얻어 {값이름:값} dic으로 반환
    # valuelist가 [] 이면 얻을 수 있는 모든 값 반환
    def getRealData(self, code, realtype, valuelist):
        valuedic = self.getRealIndex(realtype, valuelist)

        if valuedic=={}: return

        ret = {}
        
        for k, v in valuedic.items():
            i = self.getCommRealData(code, k)
            ret[v] = i

        if self.testFlag:
            print("\n\n")
            print("[getRealData()] ret : ")
            print(ret)

        return ret



######################################################################################
# 기타 모듈 내부에서 사용하는 함수
######################################################################################

            
            
    # FID 값을 주면 의미를, 의미를 주면 FID를 반환.
    # OnReceiveChejan() 이벤트 함수에서 사용.
    def convertFid(self, fidOrMeaning):
        
        fidList = { 9201 : "계좌번호", 
                    9203 : "주문번호", 
                    9001 : "종목코드",
                    913 : "주문상태", 
                    302 : "종목명", 
                    900 : "주문수량", 
                    901 : "주문가격", 
                    902 : "미체결수량", 
                    903 : "체결누계금액", 
                    904 : "원주문번호", 
                    905 : "주문구분", 
                    906 : "매매구분", 
                    907 : "매도수구분", 
                    908 : "주문/체결시간", 
                    909 : "체결번호", 
                    910 : "체결가", 
                    911 : "체결량", 
                    10 : "현재가", 
                    27 : "(최우선)매도호가", 
                    28 : "(최우선)매수호가", 
                    914 : "단위체결가", 
                    915 : "단위체결량", 
                    919 : "거부사유", 
                    920 : "화면번호", 
                    917 : "신용구분", 
                    916 : "대출일", 
                    930 : "보유수량", 
                    931 : "매입단가", 
                    932 : "총매입가", 
                    933 : "주문가능수량", 
                    945 : "당일순매수수량", 
                    946 : "매도/매수구분", 
                    950 : "당일총매도손일", 
                    951 : "예수금", 
                    307 : "기준가", 
                    8019 : "손익율", 
                    957 : "신용금액", 
                    958 : "신용이자", 
                    918 : "만기일", 
                    990 : "당일실현손익(유가)", 
                    991 : "당일실현손익률(유가)", 
                    992 : "당일실현손익(신용)", 
                    993 : "당일실현손익률(신용)", 
                    397 : "파생상품거래단위", 
                    305 : "상한가", 
                    306 : "하한가"}
                    
        res = fidList.get(fidOrMeaning)

        if self.testFlag:
            print("[convertFid()] res : " + str(res))
            print("\n\n")

        if res!=None: return res

        for k, v in fidList.items():
            if v == fidOrMeaning:
                
                if self.testFlag:
                    print("[convertFid()] 반환값 k : " + str(k))
                    print("\n\n")
                    
                return k

    
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

        try:
            errorComment = "[ERROR]" + errors[errCode]
            
        except:
            errorComment = "[ERROR]" + str(errCode) + " : unknown error"

        if self.testFlag:
            print("[getErrorComment()] errorComment : " + errorComment)
            print("\n\n")

        return errorComment



######################################################################################
# abstract methods
######################################################################################



    # (이벤트) 로그인 성공 시 알림
    def eventConnect(self, err_code):
        pass


    # (이벤트) 서버 통신 후 수신한 메시지를 알려 줌.
    def receiveMsg(self, screenNo, rqname, trcode, msg):
        pass


    # (이벤트) 받은 쿼리 결과에 따른 처리
        # GetCommData() 사용
    def receiveTrData(self, screen_no, rqname, trcode, record_name):
        pass


    # (이벤트) 실시간 데이터 수신. SetRealReg()로 등록한 실시간 데이터 포함.
    # realType : '주식체결' 등... 문자열. 
    # realData : getRealIndex() 참조. 문자열.
    # GetCommRealData(), getRealData() 사용
    def receiveRealData(self, code, realType, realData):
        pass


    # (이벤트) 주문 접수, 체결 통보, 잔고 통보
    # GetChejanData() 사용
    # gubun은 체결 접수 및 체결 시 '0', 국내주식 잔고전달은 '1', 파생잔고전달은 '4'
    # gubun의 데이터 타입은 str
    # fidListStr : fid를 세미콜론(;) 으로 구분. fid는 int형으로 사용할 것.
    # fid 사용 시 self.convertFid()로 fid <-> 의미 변환
    def receiveChejanData(self, gubun, itemCnt, fidListStr):
        pass


    # (이벤트) 사용자 조건식 요청에 대한 응답
    # getConditionNameList() 사용
    # ret : 1이면 성공, 나머지는 실패
    def receiveConditionVer(self, ret, msg):
        pass


    # (이벤트) 조건 검색 요청으로 검색된 종목코드 리스트 전달
    # codeList : 종목코드를 세미콜론(;)으로 구분한 문자열
    # next : 연속조회 여부
    def receiveTrCondition(self, screenNo, codeList, conditionIndex):
        pass


    # (이벤트) 실시간 조건검색 요청 종목이 변경될 때 호출
    # insertOrDelete : I는 종목 편입, D는 종목 이탈
    def receiveRealCondition(self, code, insertOrDelete, conditionName, conditionIndex):
        pass


