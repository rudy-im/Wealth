import time, threading
import timeUtil as tUtil
from KiwoomUtil import *



class InfoUpdater(threading.Thread):

    def __init__(self, KUtil):
        
        super().__init__()

        self.KUtil = KUtil

        # 세마포. True이면 자원 이용 중
        self.semaphore = False

        # 시간 관련
        self.nowtime = tUtil.getNowTime()
        self.beforetime = self.nowtime

        # 파일 이름
        self.realtimeDirectory = 'realtime data'
        self.realtimeFilename = tUtil.getToday() + '.txt'


    # 1초마다 실시간 데이터를 저장
    def run(self):
        
        while True:
            
            if not(self.semaphore):
                self.nowtime = tUtil.getNowTime()

                if self.nowtime>152000: break

                if self.nowtime<90000: pass
                
                elif self.nowtime>self.beforetime:

                    print(self.nowtime)
                    
                    self.semaphore = True
                    
                    #if self.nowtime%100==0: print(nowtime) # 1분마다 시간 프린트

                    filename = self.realtimeDirectory + '/' + self.realtimeFilename
                    fp = open(filename, 'a')
                    
                    realpool = self.KUtil.realpool.copy()

                    if realpool!={}:
                        
                        df = DataFrame(columns = ['code', 'price', 'volume'])
                        i = 0
                        
                        for k, v in realpool.items():
                            df.loc[i] = [k, v[0], v[1]]
                            i += 1
                            
                        self.saveRealtimeData(fp)

                    fp.close()
                    
                    self.beforetime = self.nowtime
                    self.semaphore = False
            
            time.sleep(0.2)


    # 1초 간격의 실시간 데이터 저장
    # 파일명 : realtime data/YYYY-MM-DD.txt
    #
    # 기재 방식 : realtime  hhmmss
    #             종목코드  가격  거래량
    #                       ...
    #             (가로 공백 부분은 \t)
    #
    def saveRealtimeData(self, fp):

        filename = self.realtimeDirectory + '/' + self.realtimeFilename

        try:
            
            fp = open(filename, 'a')

            realpool = self.KUtil.getRealpool()
            
            if realpool!={}:
                
                fp.write('\n')
                fp.write('realtime\t' + str(self.nowtime) + '\n')

                for k, v in realpool.items():
                    fp.write(k + '\t' + str(v[0]) + '\t' + str(v[1]) +
                             '\t' + str(v[2]) + '\t' + str(v[3]) + '\n')
                    
            fp.close()
            
        except:
        
            print("\n\n")
            print("[saveRealtimeData()] Failed to saveRealtimeData()!!!")


    
