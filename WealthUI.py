#-*- coding : utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import  *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic
import pickle
import datetime
import sqlite3
from pandas import Series, DataFrame


mainWindow = uic.loadUiType("MainWindow.ui")[0]

class WealthUI(QMainWindow, mainWindow):
    def __init__(self, kiwoom):
        super().__init__()
        self.setupUi(self)
        self.kiwoom = kiwoom
        
        self.btnDeleteInterest.clicked.connect(self.deleteInterest)
        self.btnDownInterest.clicked.connect(self.downInterest)
        self.btnUpInterest.clicked.connect(self.upInterest)
        self.btnAddInterest.clicked.connect(self.addInterest)

        # rqname 용
        self.rqNo = 0

        # 파일명
        self.interestListFile = 'interest.pkl'
        self.stocksCodeNameFile = 'stocks.db'
        self.minDataFile = 'minData.db'  # 맨 앞엔 몇 분인지 숫자로.

        # 초기화
        self.readInterest()
        self.updateStock()
        
    # 관심종목 불러오기
    def readInterest(self):
        try :
            fp = open(self.interestListFile, 'rb')
            interest = pickle.load(fp)
            self.listInterest.addItems(interest)
            fp.close()
        except Exception:
            print('관심종목 불러오기 실패')
        
    # 종목코드-종목명 DB 업데이트
    def updateStock(self):
        con = sqlite3.connect(self.stocksCodeNameFile)
        cursor = con.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS stocks
                      (code CHAR(6) NOT NULL UNIQUE,
                      name VARCHAR2(30) NOT NULL,
                      modified_date DATE NOT NULL);''')
        now = datetime.datetime.now().strftime("%Y-%m-%d")

        # 장내&코스닥 종목코드-이름을 stocks 테이블에 저장
        marketStocks = self.kiwoom.getCodeListByMarket(self.kiwoom.noMarket)
        for code in marketStocks:
            name = self.kiwoom.getMasterCodeName(code)
            cursor.execute('''INSERT OR REPLACE INTO stocks (code, name, modified_date)
                          VALUES ("''' + code + '''", "''' + name + '''", date("''' + now + '''"));''')

        kosdaqStocks = self.kiwoom.getCodeListByMarket(self.kiwoom.noKosdaq)
        for code in kosdaqStocks:
            name = self.kiwoom.getMasterCodeName(code)
            cursor.execute('''INSERT OR REPLACE INTO stocks (code, name, modified_date)
                          VALUES ("''' + code + '''", "''' + name + '''", date("''' + now + '''"));''')

        cursor.execute('''DELETE FROM stocks WHERE modified_date!=date("''' + now + '''");''')
        
        con.commit()
        con.close()
                        
    
    # 관심종목 삭제
    def deleteInterest(self):
        for item in self.listInterest.selectedItems():
            info = item.text().split('\t')
            self.listInterest.takeItem(self.listInterest.row(item))
            self.log("[" + info[0] + "]" + info[1] + " 이(가) 관심종목에서 제거되었습니다.")
        self.saveInterest()

    # 해당 관심종목을 한 칸 아래로
    def downInterest(self):
        currentRow = self.listInterest.currentRow()
        if currentRow==-1 : return
        currentItem = self.listInterest.takeItem(currentRow)
        self.listInterest.insertItem(currentRow + 1, currentItem)
        self.listInterest.setCurrentRow(currentRow + 1)
        self.saveInterest()

    # 해당 관심종목을 한 칸 위로
    def upInterest(self):
        currentRow = self.listInterest.currentRow()
        if currentRow==-1 : return
        currentItem = self.listInterest.takeItem(currentRow)
        self.listInterest.insertItem(currentRow - 1, currentItem)
        self.listInterest.setCurrentRow(currentRow - 1)
        self.saveInterest()

    # 관심종목 추가
    def addInterest(self):
        # 관심종목 추가 버튼 비활성화
        self.btnAddInterest.setEnabled(False)
        
        name, ok = QInputDialog.getText(self, "관심종목 추가", "추가할 종목명을 입력하시오.")

        # 해당 종목명이 제대로 존재하는지 확인
        if ok:
            con = sqlite3.connect(self.stocksCodeNameFile)
            cursor = con.cursor()
            
            cursor.execute('''SELECT * FROM stocks WHERE name = "''' + name + '''";''')
            result = cursor.fetchone()
            
            checkRedundancy = cursor.fetchall()
            if len(checkRedundancy) != 0 :
                ans = QMessageBox.warning(self, "DB Error", "해당 종목명이 중복 등록되어 있습니다.",
                                          QMessageBox.Ok, QMessageBox.Ok)
                ok = False
                
            if result == None :
                ans = QMessageBox.warning(self, "No result", "해당 종목이 없습니다.",
                                          QMessageBox.Ok, QMessageBox.Ok)
                ok = False
                
            con.commit()
            con.close()

        # 정상적으로 관심종목을 추가하는 경우
        # result[0] : 종목코드, result[1] : 종목명
        if ok:
            # 최근 3600번의 1분 분봉 저장
            self.rqNo += 1
            df = self.kiwoom.getTrMin("rq" + str(self.rqNo), result[0], "1", 4)
            self.saveChart(result[0], df, 1)

            # 관심종목 리스트 추가
            self.listInterest.addItems([result[0] + "\t" + result[1]])
            self.saveInterest()

            # 로그
            self.log("[" + result[0] + "]" + result[1] + " 이(가) 관심종목에 추가되었습니다.")

        # 관심종목 추가 버튼 활성화
        self.btnAddInterest.setEnabled(True)

    # 관심종목 저장
    def saveInterest(self):
        try:
            fp = open(self.interestListFile, 'wb')
            interest = []
            for index in range(self.listInterest.count()):
                 interest.append(self.listInterest.item(index).text())
            pickle.dump(interest, fp)
            fp.close()
        except Exception:
            print('관심종목 저장 실패')

    # 시스템 로그
    def log(self, msg):
        self.txtLog.append(msg)
        ### 나중에 로그 파일 만드는 코드 추가할 것!

    # 차트 데이터 저장
    # candleTime : 분봉은 해당 분, 일봉은 -1, 주봉은 -2, 월봉은 -3
    def saveChart(self, code, dataChart, candleTime):
        # 데이터를 저장할 파일 이름 결정
        filename = ''
        candleTimeLength = 0
        if candleTime == -1 :  # 일봉
            pass
        elif candleTime == -2 : # 주봉
            pass
        elif candleTime == -3 : # 월봉
            pass
        elif candleTime > 0 and candleTime <= 60: # 분봉
            filename = str(candleTime) + self.minDataFile
            candleTimeLength = 13
        else :
            return
        if len(filename) == 0 :
            return
        
        # 데이터 저장 준비
        con = sqlite3.connect(filename)
        cursor = con.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS s''' + code + '''
                      (candleTime CHAR(''' + str(candleTimeLength) + ''') NOT NULL UNIQUE,
                      open NUMBER(10) NOT NULL,
                      high NUMBER(10) NOT NULL,
                      low NUMBER(10) NOT NULL,
                      close NUMBER(10) NOT NULL,
                      volume NUMBER(20) NOT NULL);''')


        # 차트 데이터를 s종목코드 이름의 테이블에 저장
        for i in dataChart.index:
            date = i
            open = str(dataChart['open'][i])
            high = str(dataChart['high'][i])
            low = str(dataChart['low'][i])
            close = str(dataChart['close'][i])
            volume = str(dataChart['volume'][i])

            cursor.execute('''INSERT OR REPLACE INTO s''' + code + '''
                          (candleTime, open, high, low, close, volume)
                          VALUES ("''' + date + '''", ''' + open + ''',
                          ''' + high + ''', ''' + low + ''', ''' + close + ''', ''' + volume + ''');''')
        
        con.commit()
        con.close()

    
