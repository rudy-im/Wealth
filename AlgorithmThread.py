import time, threading
import timeUtil as tUtil
from KiwoomUtil import *
from PyQt5.QtCore import *
from WealthAlgorithm import *




# 시그널 전용 클래스
# thread 내에서 바로 kiwoom 호출 시 컨텍스트 문제 발생
# 따라서, 시그널을 보내 kiwoom 함수를 다른 클래스에서 호출하게 함
class SignalClass(QObject):
    signal = pyqtSignal(str)




class AlgorithmThread(threading.Thread):

    def __init__(self, KUtil):

        super().__init__()

        self.KUtil = KUtil

        self.wa = WealthAlgorithm(KUtil)

        # 시그널 객체 처리
        # self.signal.emit('알고리즘클래스 내에서 함수 사용 형식')
        self.sc = SignalClass()
        
        self.signal = self.sc.signal
        self.signal.connect(self.wa.executeSignal)
        
        # 세마포
        # 자원 이용중이면 True
        self.semaphore = False

        # 시간 관련
        self.nowtime = tUtil.getNowTime()
        self.beforetime = self.nowtime

       
    def run(self):

        while True:

            # 휴식기.
            # continue의 경우에도 스킵되지 않게 하기 위해 맨 앞에 위치.
            time.sleep(0.2)

            # 자원 사용 중이면 동작 X
            if self.semaphore: continue
            if self.wa.getSemaphore(): continue

            # 현재시간 설정
            self.nowtime = tUtil.getNowTime()
            self.wa.setNowtime(self.nowtime)

            # 1초가 안 된 경우 동작 X
            if self.nowtime<=self.beforetime: continue

            # 1분마다 시간 print
            #if self.nowtime%100==0:
            print(self.nowtime)

            # 9시 이전이면 동작 X
            if self.nowtime<90000: continue

            # 3시 반 이후이면 자동 종료
            if self.nowtime>153000: break

            # 손실이 너무 크면 자동 종료
            if self.wa.isLossTooBig(): break

            # 자원 플래그 세우기
            self.semaphore = True

            # 알고리즘에 따른 매매 발동
            # (Kiwoom API의 컨텍스트 문제로 thread 내 동작이 안 됨.
            #  따라서 시그널을 보내 thread 외부 클래스에서 호출하게 함.
            #  해당 함수 동작 중에는 wa의 세마포가 설정됨)
            self.signal.emit('self.run()')

            # 자원 플래그 해제
            self.semaphore = False

            # 이전시간 설정
            self.beforetime = self.nowtime
            self.wa.setBeforetime(self.beforetime)

            
                
