#-*- coding : utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import  *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic
from pandas import DataFrame



mainWindow = uic.loadUiType("MainWindow.ui")[0]



class WealthUI(QMainWindow, mainWindow):
    
    def __init__(self):
        
        super().__init__()
        self.setupUi(self)

        # UI 위젯 처리
        #self.btnBuy.clicked.connect(self.buy)
        


######################################################################################
# UI 동작 함수
######################################################################################



######################################################################################
# UI 내용 표시
######################################################################################



    # 잔고 내역 표시
    def showBalance(self, balance):

        # tblBalance1
        
        self.tblBalance1.setItem(0, 0, self.tableWidgetItem(str(balance['총매입'])))
        self.tblBalance1.setItem(0, 1, self.tableWidgetItem(str(balance['총평가'])))
        self.tblBalance1.setItem(0, 2, self.tableWidgetItem(str(balance['총손익'])))
        self.tblBalance1.setItem(0, 3, self.tableWidgetItem(str(balance['총수익률']) + '%'))

        # tblBalance2

        self.tblBalance2.setItem(0, 0, self.tableWidgetItem(str(balance['D+1예수금'])))
        self.tblBalance2.setItem(0, 1, self.tableWidgetItem(str(balance['D+1정산금액'])))
        self.tblBalance2.setItem(0, 2, self.tableWidgetItem(str(balance['D+1추정인출가능금'])))

        self.tblBalance2.setItem(1, 0, self.tableWidgetItem(str(balance['D+2예수금'])))
        self.tblBalance2.setItem(1, 1, self.tableWidgetItem(str(balance['D+2정산금액'])))
        self.tblBalance2.setItem(1, 2, self.tableWidgetItem(str(balance['D+2추정인출가능금'])))


    # 계좌 보유 종목 내역 표시
    # 종목코드 : [종목명, 손익율, 주문가능수량, 보유수량, 매입단가, 현재가]
    def showBalancepool(self, balancepool):

        # tblBalancepool

        self.clearTable(self.tblBalancepool)

        for k, v in balancepool.items():

            self.insertTableRow(self.tblBalancepool, [k] + v)


    # 주문 내역 표시
    # 주문번호 : [코드, 종목명, 구분(매수/매도), 주문가격, 현재가,
    #             주문수량, 체결수량, 미체결수량, 주문/체결시간, 원주문번호]
    def showOrderpool(self, orderpool):

        # tblOrderpool

        self.clearTable(self.tblOrderpool)

        for k, v in orderpool.items():

            self.insertTableRow(self.tblOrderpool, [k] + v)



######################################################################################
# GUI 공통 함수
######################################################################################



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


    # 테이블 위젯에 행 추가
    # rowlist에서 None인 셀은 갱신 안 함
    def insertTableRow(self, tblWidget, rowlist):
        
        rowCount = tblWidget.rowCount()
        tblWidget.insertRow(rowCount)

        for i in range(len(rowlist)):
            if rowlist[i]!=None:
                tblWidget.setItem(rowCount, i, self.tableWidgetItem(rowlist[i]))


    # 테이블 위젯에서 해당 종목명의 행 제거
    def deleteTableRow(self, tblWidget, row):
        
        tblWidget.removeRow(row)
    

    # 테이블 위젯에서 해당 행 갱신
    # rowlist에서 None인 셀은 갱신 안 함
    def updateTableRow(self, tblWidget, row, rowlist):

        for i in range(len(rowlist)):
            if i!=None:
                tblWidget.setItem(i, row, self.tableWidgetItem(rowlist[i]))


    # 테이블 위젯의 모든 행 삭제
    def clearTable(self, tblWidget):

        tblWidget.setRowCount(0)

    
