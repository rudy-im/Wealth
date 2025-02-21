#-*- coding : utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import  *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic
import pickle
import datetime, time, threading
import sqlite3
from pandas import Series, DataFrame
from KiwoomUtil import *
import sqlite3Util as sUtil




mainWindow = uic.loadUiType("MainWindow.ui")[0]
buyOrSellDialog = uic.loadUiType("BuyOrSellDialog.ui")[0]
editDialog = uic.loadUiType("EditDialog.ui")[0]




class WealthUI(QMainWindow, mainWindow):
    
    def __init__(self, kiwoom):
        
        super().__init__()
        self.setupUi(self)
        self.kiwoom = kiwoom
        self.KUtil = KiwoomUtil(kiwoom)

        # testFlag == True 이면 테스트 로그를 콘솔에 print
        self.testFlag = False

        # UI 위젯 처리
        self.btnBuy.clicked.connect(self.buy)
        self.btnSell.clicked.connect(self.sell)
        self.btnEdit.clicked.connect(self.edit)
        self.btnCancel.clicked.connect(self.cancel)

        # 파일, 폴더 이름
        self.logDirectory = 'log'

        # 관심종목 dic
        self.interest = {}

        # 계좌 정보
        self.accountInfo = {'총매입':0, '총평가':0, '총손익':0, '총수익률':0,
                            'D+1예수금':0, 'D+1정산금액':0, 'D+1추정인출가능금':0,
                            'D+2예수금':0, 'D+2정산금액':0, 'D+2추정인출가능금':0}

        # 각 테이블의 column
        self.tblInterestCols = ['종목코드', '종목명', '현재가', '등락율']
        self.tblTodayCols = ['종목코드', '종목명', '손익금액', '수익률', '금일매도평균가', '금일매도수량', '금일매도금액',
                             '수수료+제세금', '이전매입가']
        self.tblHoldingsCols = ['종목코드', '종목명', '매입가', '평가손익', '수익률', '가능수량', '보유수량', '현재가',
                                '평가금액', '수수료', '세금', '보유비중', '손익분기매입가']
        self.tblOrderCols = ['종목코드', '종목명', '주문번호', '주문수량', '미체결수량', '구분', '주문가', '현재가',
                             '주문시간']

        # 초기화
        print("saveStocksInfo...")
        self.KUtil.saveStocksInfo()
        print("initialize...")
        self.initialize()


    # 초기화
    def initialize(self):

        # 계좌 정보, 금일 손익, 미체결 표시
        self.getAccInfo()
        self.getTodayOrder()
        
        # 증20이하 관심종목으로
        # 관심종목을 실시간 이벤트에 등록
        self.interest = self.KUtil.queryByMargin(20, True)
        self.showInterest()
        self.KUtil.setRealtime(list(self.interest.keys()))

        # 1초마다 체크하는 thread 시작
        self.timeInterval = 0.2
        
        filename = 'realtime data/' + sUtil.now(False) + '.txt'
        self.fp = open(filename, 'a')
        
        self.infoUpdater = threading.Thread(target = self.infoUpdate)
        self.infoUpdater.start()

        
    # 수동 매수
    def buy(self):

        code = '000020' # tblInterest에서 선택된 종목
        cash = int(self.accountInfo['D+2예수금'])
        totalEvaluation = int(self.accountInfo['총평가'])
        
        dialog = BuyOrSellDialog(1, code, self.KUtil, cash, totalEvaluation)
        dialog.exec_()
        
        # dialog 띄워서 입력 받을 것.
        # log 남길 것.

        
    # 수동 매도
    def sell(self):

        code = '000020' # tblHoldings에서 선택된 종목
        rest = 0  # tblHoldings에서 선택된 종목
        totalEvaluation = int(self.accountInfo['총평가'])
        
        dialog = BuyOrSellDialog(2, code, self.KUtil, rest, totalEvaluation)
        dialog.exec_()
        
        # dialog 띄워서 입력 받을 것.
        # log 남길 것.

        
    # 수동 정정
    def edit(self):
        
        originalOrder = '' # tblOrder에서 선택된 종목
        code = '000020' # tblOrder에서 선택된 종목
        rest = 0 # tblOrder에서 선택된 종목
        buy1sell2 = 1 # tblOrder에서 선택된 종목
        
        dialog = EditDialog(buy1sell2, code, originalOrder, self.KUtil, rest)
        dialog.exec_()
        
        # dialog 띄워서 입력 받을 것.
        # log 남길 것.

        
    # 수동 취소
    def cancel(self):
        originalOrder = '' # tblOrder에서 선택된 종목
        code = '000020' # tblOrder에서 선택된 종목
        buy1sell2 = 1 # tblOrder에서 선택된 종목

        if buy1sell2==1:
            self.KUtil.cancelBuy(self.KUtil.getRqname(), originalOrder, code)

        elif buy1sell2==2:
            self.KUtil.cancelSell(self.KUtil.getRqname(), originalOrder, code)

        # log 남길 것.

        
    # 시스템 로그
    def log(self, msg):
        
        if self.testFlag: print("[log()] msg : " + msg)
        
        self.txtLog.append(msg)

        try:
            filename = self.logDirectory + '/' + sUtil.now(False) + '.txt'
            fp = open(filename, 'a')
            fp.write('\n')
            fp.write(msg)
            fp.close()
            
        except:
            pass


    # 관심종목 표시 (가격/거래량 제외)
    def showInterest(self):
        # tblInterest 의 모든 행 제거
        self.tblInterest.setRowCount(0)
        
        for code, name in self.interest.items():
            self.insert(self.tblInterest, [code, name, None, None])


    # 관심종목의 현재가, 누적거래량 업데이트
    def updateInterest(self):
        realpool = self.kiwoom.getRealpool()
        print('\n\n\n updateInterest \n\n\n')

        for i in range(self.tblInterest.rowCount()):
            
            try:
                code = self.tblInterest.item(i, 0).text()
                self.tblInterest.setItem(i, 2, self.tableWidgetItem(realpool[code][0]))
                self.tblInterest.setItem(i, 3, self.tableWidgetItem(realpool[code][1]))
                
            except:
                pass


    # 계좌 정보 표시
    def showAccount(self):

        if self.testFlag:
            print("\n\n")
            print("[showAccount()] self.accountInfo : ")
            print(self.accountInfo)

        # tblAccount1
        
        self.tblAccount1.setItem(0, 0, self.tableWidgetItem(self.accountInfo['총매입']))
        self.tblAccount1.setItem(0, 1, self.tableWidgetItem(self.accountInfo['총평가']))
        self.tblAccount1.setItem(0, 2, self.tableWidgetItem(self.accountInfo['총손익']))
        self.tblAccount1.setItem(0, 3, self.tableWidgetItem(self.accountInfo['총수익률'] + '%'))

        # tblAccount2

        self.tblAccount2.setItem(0, 0, self.tableWidgetItem(self.accountInfo['D+1예수금']))
        self.tblAccount2.setItem(0, 1, self.tableWidgetItem(self.accountInfo['D+1정산금액']))
        self.tblAccount2.setItem(0, 2, self.tableWidgetItem(self.accountInfo['D+1추정인출가능금']))

        self.tblAccount2.setItem(1, 0, self.tableWidgetItem(self.accountInfo['D+2예수금']))
        self.tblAccount2.setItem(1, 1, self.tableWidgetItem(self.accountInfo['D+2정산금액']))
        self.tblAccount2.setItem(1, 2, self.tableWidgetItem(self.accountInfo['D+2추정인출가능금']))


    # 계좌 내역 얻고 표시
    def getAccInfo(self):
            
        trcode = 'opw00001'
        inputdic = {'계좌번호' : self.kiwoom.account[0],
                    '비밀번호' : '',
                    '비밀번호입력매체구분' : '00',
                    '조회구분' : '2'}
        outputs = ["d+1추정예수금", "d+1매도매수정산금", "d+1출금가능금액",
                   "d+2추정예수금", "d+2매도매수정산금", "d+2출금가능금액"]
        
        df = self.KUtil.kiwoomRequest(self.KUtil.getRqname(), trcode, inputdic, outputs)

        if self.testFlag:
            print("\n\n")
            print("[getAccInfo()] df : ")
            print(df)

        self.accountInfo['D+1예수금'] = str(int(df.get_value(0, "d+1추정예수금")))
        self.accountInfo['D+1정산금액'] = str(int(df.get_value(0, "d+1매도매수정산금")))
        self.accountInfo['D+1추정인출가능금'] = str(int(df.get_value(0, "d+1출금가능금액")))
        self.accountInfo['D+2예수금'] = str(int(df.get_value(0, "d+2추정예수금")))
        self.accountInfo['D+2정산금액'] = str(int(df.get_value(0, "d+2매도매수정산금")))
        self.accountInfo['D+2추정인출가능금'] = str(int(df.get_value(0, "d+2출금가능금액")))

        trcode = 'OPW00004'
        inputdic = {'계좌번호' : self.kiwoom.account[0],
                    '비밀번호' : '',
                    '상장폐지조회구분' : '0',
                    '비밀번호입력매체구분' : '00'}
        outputs = ["총매입금액", "추정예탁자산", "당일투자손익", "당일손익율",  # single data
                   "종목코드", "종목명", "평균단가", "손익금액", "손익율",      # 이하는 multi data
                   "결제잔고", "보유수량", "현재가", "매입금액", "평가금액"]

        df = self.KUtil.kiwoomRequest(self.KUtil.getRqname(), trcode, inputdic, outputs)

        if self.testFlag:
            print("\n")
            print("[getAccInfo()] df : ")
            print(df)

        self.accountInfo['총매입'] = str(int(df.get_value(0, "총매입금액")))
        self.accountInfo['총평가'] = str(int(df.get_value(0, "추정예탁자산")))
        self.accountInfo['총손익'] = str(int(df.get_value(0, "당일투자손익")))
        self.accountInfo['총수익률'] = str(int(df.get_value(0, "당일손익율")))

        if self.testFlag:
            print("\n")
            print("[getAccInfo()] self.accountInfo : ")
            print(self.accountInfo)

        self.showAccount()

        # tblHoldings의 모든 행 삭제
        self.tblHoldings.setRowCount(0)

        for i in df.index:
            code = df.get_value(i, "종목코드")
            if code=='': break

            row = []
            
            row.append(code)
            row.append(df.get_value(i, "종목명"))

            avgPrice = df.get_value(i, "평균단가")
            row.append(avgPrice)
            
            row.append(df.get_value(i, "손익금액"))
            row.append(df.get_value(i, "손익율"))
            row.append(df.get_value(i, "결제잔고"))
            row.append(df.get_value(i, "보유수량"))
            row.append(df.get_value(i, "현재가"))
            row.append(df.get_value(i, "매입금액"))

            evaluated = df.get_value(i, "평가금액")
            row.append(evaluated)

            evaluated = int(evaluated) if evaluated!='' else 0
            avgPrice = int(avgPrice) if avgPrice!='' else 0
            totalEvaluation = int(self.accountInfo['총평가'])
            
            row.append(evaluated * 0.0015)
            row.append(evaluated * 0.0015)
            row.append(evaluated * 100 / totalEvaluation
                       if totalEvaluation!=0 else 0)
            row.append(avgPrice / 0.997)

            if self.testFlag:
                print("\n")
                print("[getAccInfo()] row : ")
                print(row)

            self.insert(self.tblHoldings, row)
        

    # 당일매매 내역, 미체결 내역 얻고 표시
    def getTodayOrder(self):

        trcode = 'opt10075'
        inputdic = {'계좌번호' : self.kiwoom.account[0],
                    '체결구분' : '0',
                    '매매구분' : '0'}
        outputs = ["종목코드", "종목명", "주문번호", "주문수량", "미체결수량", "매매구분",
                   "주문가격", "현재가", "원주문번호", "체결량"]

        df = self.KUtil.kiwoomRequest(self.KUtil.getRqname(), trcode, inputdic, outputs)

        if self.testFlag:
            print("\n\n")
            print("[getTodayOrder()] df : ")
            print(df)

        trcode = 'opt10077'
        inputdic = {'계좌번호' : self.kiwoom.account[0],
                    '비밀번호' : '',
                    '종목코드' : ''}
        outputs = ["종목코드", "종목명", "당일매도손익", "손익율", "체결가", "체결량",
                   "당일매매수수료", "당일매매세금", "매입단가"]

        # tblToday, tblOrder 의 모든 행 지우기
        self.tblToday.setRowCount(0)
        self.tblOrder.setRowCount(0)

        for i in df.index:
            row = []

            # 매도이고 체결 수량이 0보다 큰 경우 당일매매내역 조회 -> tblToday
            # 미체결수량이 0보다 큰 경우 tblOrder

            contracted = df.get_value(i, "체결량")
            contracted = int(contracted) if contracted!='' else 0
            
            if (df.get_value(i, "매매구분")=='1' and contracted>0):

                inputdic['종목코드'] = df.get_value(i, "종목코드")
                df2 = self.KUtil.kiwoomRequest(self.KUtil.getRqname(), trcode, inputdic, outputs)

                if self.testFlag:
                    print("\n\n")
                    print("[getTodayOrder()] df2 : ")
                    print(df2)
                
                row.append(df.get_value(i, "종목코드"))
                row.append(df.get_value(i, "종목명"))
                row.append(df.get_value(i, "당일매도손익"))
                row.append(df.get_value(i, "손익율"))

                price = df.get_value(i, "체결가")
                row.append(price)
                row.append(str(contracted))

                price = int(price)
                row.append(str(price*contracted))

                premium = int(df.get_value(i, "당일매매수수료"))
                tax = int(df.get_value(i, "당일매매세금"))
                row.append(str(premium + tax))
                
                row.append(df.get_value(i, "매입단가"))

                if self.testFlag:
                    print("\n\n")
                    print("[getTodayOrder()] row : ")
                    print(row)

                self.insert(self.tblToday, row)


            notContracted = df.get_value(i, "미체결수량")
            notContracted = int(notContracted) if notContracted!='' else 0

            if notContracted>0:

                row.append(df.get_value(i, "종목코드"))
                row.append(df.get_value(i, "종목명"))
                row.append(df.get_value(i, "주문번호"))
                row.append(df.get_value(i, "주문수량"))
                row.append(str(notContracted))
                row.append(df.get_value(i, "매매구분"))
                row.append(df.get_value(i, "주문가격"))
                row.append(df.get_value(i, "현재가"))
                row.append(df.get_value(i, "원주문번호"))

                if self.testFlag:
                    print("\n\n")
                    print("[getTodayOrder()] row : ")
                    print(row)

                self.insert(self.tblOrder, row)
        

    # 테이블 위젯에 행 추가
    # rowlist에서 None인 셀은 갱신 안 함
    def insert(self, tblWidget, rowlist):
        
        rowCount = tblWidget.rowCount()
        tblWidget.insertRow(rowCount)

        for i in range(len(rowlist)):
            if rowlist[i]!=None:
                tblWidget.setItem(rowCount, i, self.tableWidgetItem(rowlist[i]))
        


    # 테이블 위젯에서 해당 종목명의 행 인덱스 반환
    def rowIndexByStockname(self, tblWidget, stockname):
        
        for i in range(tblWidget.rowCount()):
            if tblWidget.item(1, i).text() == stockname:
                return i


    # 테이블 위젯에서 해당 종목명의 행 제거
    def delete(self, tblWidget, stockname):

        row = self.rowIndexByStockname(tblWidget, stockname)
        
        if row == None: return
        
        tblWidget.removeRow(row)
    

    # 테이블 위젯에서 해당 종목명의 행 갱신
    # rowlist에서 None인 셀은 갱신 안 함
    def update(self, tblWidget, stockname, rowlist):

        row = self.rowIndexByStockname(tblWidget, stockname)
        
        if row == None: return

        for i in range(len(rowlist)):
            if i!=None:
                tblWidget.setItem(i, row, self.tableWidgetItem(rowlist[i]))


    # 테이블 위젯의 데이터를 DataFrame으로 얻기
    def getTableDf(self, tblWidget):

        # todo :::  테이블의 column names, row names 얻어 df의 rows, cols 세팅
        df = DataFrame()

        for i in range(tblWidget.rowCount()):
            for j in range(tblWidget.columnCount()):
                df.set_value(i, j, tblWidget.item(j, i).text())

        if self.testFlag:
            print("\n\n")
            print("[getTableDf()] df : ")
            print(df)

        return df


    # 테이블 위젯 아이템 얻기
    # 기본 : 우측 중앙 정렬
    def tableWidgetItem(self, text, align = Qt.AlignRight|Qt.AlignVCenter):
        tItem = QTableWidgetItem(text)
        tItem.setTextAlignment(align)
        return tItem


    # 1초마다 체크하는 thread 내용
    def infoUpdate(self):
        self.beforetime = self.KUtil.getNow()
        self.nowtime = self.beforetime
        
        while True:
            print("infoUpdate()")

            self.nowtime = self.KUtil.getNow()
            
            if self.nowtime>self.beforetime:
                
                realpool = self.kiwoom.getRealpool()
                
                if realpool!={}:
                    
                    df = DataFrame(columns = ['code', 'price', 'volume'])
                    i = 0
                    
                    for k, v in realpool.items():
                        df.loc[i] = [k, v[0], v[1]]
                        i += 1
                        
                    self.KUtil.saveRealtimeData(self.fp, df, self.nowtime)
                    self.beforetime = self.nowtime
            
                # 관심종목 현재가, 누적거래량 업데이트
                ###todo
                # 너무 느림. 미리 관심종목 코드 리스트 가지고 있다가 인덱스 알아내고
                # realpool before도 가지고 있다가 달라진 부분만 update하도록 할 것!
                #self.updateInterest()
            
            time.sleep(self.timeInterval)

        self.fp.close()




# 수동 매수/매도 다이얼로그
# 생성 매개변수가 1이면 매수, 2면 매도
class BuyOrSellDialog(QDialog, buyOrSellDialog):
    
    def __init__(self, buy1sell2, stockcode, KUtil, cashOrRest, totalEvaluation):
        
        super().__init__()
        self.setupUi(self)

        self.code = stockcode
        self.KUtil = KUtil
        self.cashOrRest = cashOrRest

        # UI 위젯 처리
        self.qleStockname.setText(self.KUtil.convertCodeOrName(code))
        self.qlePrice.setText(str(self.KUtil.getNowPrice(code)))
        
        self.btnSellPriceMinus.clicked.connect(self.sellPriceMinus)
        self.btnBuyPricePlus.clicked.connect(self.buyPricePlus)
        self.btnCancel.clicked.connect(self.close)

        # price, amount 변화 시 totalPrice 변경 # todo

        # 매수/매도의 경우 설정
        if int(buy1sell2)==1:
            self.setWindowTitle("매수")
            self.btnOK.setText("매수")
            
            self.btnPossible.clicked.connect(self.possibleBuy)
            self.btnOK.clicked.connect(self.buy)

        elif int(buy1sell2)==2:
            self.setWindowTitle("매도")
            self.btnOK.setText("매도")

            self.possibleSell()
            
            self.btnPossible.clicked.connect(self.possibleSell)
            self.btnOK.clicked.connect(self.sell)

        else:
            print("[BuyOrSellDialog] set 1 for 'buy', 2 for 'sell'")
            return


    # 가능한 매수 수량으로 세팅
    def possibleBuy(self):
        
        try:
            possible = int(self.cashOrRest / int(self.qlePrice.text()))
            qleAmount.setText(str(possible))
            
        except:
            pass


    # 가능한 매도 수량으로 세팅
    def possibleSell(self):
        self.qleAmount.setText(str(self.cashOrRest))


    # 매도호가-1 로 가격 세팅
    def sellPriceMinus(self):
        self.qlePrice.setText(str(self.KUtil.getSellPriceMinus(code)))


    # 매수호가+1 로 가격 세팅
    def buyPricePlus(self):
        self.qlePrice.setText(str(self.KUtil.getBuyPricePlus(code)))


    # 매수
    def buy(self):
        
        try:
            price = int(self.qlePrice.text())
            quantity = int(self.qleAmount.text())
            self.KUtil.buy(self.KUtil.getRqname(), self.code, price, quantity)

        except:
            print("[BuyOrSellDialog] failed to buy()!!")

        self.close()


    # 매도
    def sell(self):
        
        try:
            price = int(self.qlePrice.text())
            quantity = int(self.qleAmount.text())
            
            if quantity>self.cashOrRest: return
            
            self.KUtil.sell(self.KUtil.getRqname(), self.code, price, quantity)

        except:
            print("[BuyOrSellDialog] failed to sell()!!")

        self.close()


    # 총 금액 계산 및 표시
    def totalPrice(self):
        
        try:
            amount = int(self.qleAmount.text())
            price = int(self.qlePrice.text())
            self.qleTotalPrice.setText(str(amount*price))

        except:
            pass
        




class EditDialog(QDialog, editDialog):
    
    def __init__(self, buy1sell2, stockcode, originalOrder, KUtil, rest):
        
        super().__init__()
        self.setupUi(self)

        self.originalOrder = originalOrder
        self.code = stockcode
        self.KUtil = KUtil
        self.rest = rest

        # UI 위젯 처리
        self.qleStockname.setText(self.KUtil.convertCodeOrName(code))
        self.qleOriginalOrder.setText(originalOrder)
        self.rest()
        self.qlePrice.setText(str(self.KUtil.getNowPrice(code)))

        self.btnRest.clicked.connect(self.rest)
        self.btnSellPriceMinus.clicked.connect(self.sellPriceMinus)
        self.btnBuyPricePlus.clicked.connect(self.buyPricePlus)
        self.btnCancel.clicked.connect(self.close)

        # price, amount 변화 시 totalPrice 변경 # todo

        # 매수/매도 정정의 경우 설정
        if int(buy1sell2)==1:
            self.btnEdit.clicked.connect(self.editBuy)

        elif int(buy1sell2)==2:
            self.btnEdit.clicked.connect(self.editSell)

        else:
            print("[BuyOrSellDialog] set 1 for 'buy', 2 for 'sell'")
            return


    # 잔량으로 세팅
    def rest(self):
        self.qleAmount.setText(str(self.rest))


    # 매도호가-1 로 가격 세팅
    def sellPriceMinus(self):
        self.qlePrice.setText(str(self.KUtil.getSellPriceMinus(code)))


    # 매수호가+1 로 가격 세팅
    def buyPricePlus(self):
        self.qlePrice.setText(str(self.KUtil.getBuyPricePlus(code)))


    # 매수정정
    def editBuy(self):
        
        try:
            price = int(self.qlePrice.text())
            quantity = int(self.qleAmount.text())
            self.KUtil.changeBuy(self.KUtil.getRqname(), self.originalOrder, self.code, price, quantity)

        except:
            print("[BuyOrSellDialog] failed to editBuy()!!")

        self.close()


    # 매도정정
    def editSell(self):

        try:
            price = int(self.qlePrice.text())
            quantity = int(self.qleAmount.text())
            self.KUtil.changeSell(self.KUtil.getRqname(), self.originalOrder, self.code, price, quantity)

        except:
            print("[BuyOrSellDialog] failed to editSell()!!")

        self.close()



    # 총 금액 계산 및 표시
    def totalPrice(self):
        
        try:
            amount = int(self.qleAmount.text())
            price = int(self.qlePrice.text())
            self.qleTotalPrice.setText(str(amount*price))

        except:
            pass

