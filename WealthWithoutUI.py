from Kiwoom import *
from KiwoomUtil import *
from RoughAlgorithm import *
import time, sqlite3, threading
import sqlite3Util as sUtil

KUtil = None

# 1초마다 체크하는 thread 내용
def infoUpdate():
    beforetime = KUtil.getNow()
    nowtime = beforetime
    
    # True이면 자원 이용 중
    semaphore = False
    
    while True:
        if not(semaphore):
            nowtime = KUtil.getNow()

            if nowtime>152000: break

            if nowtime<90000: pass
            
            elif nowtime>beforetime:
                
                semaphore = True
                
                if nowtime%100==0: print(nowtime) # 1분마다 시간 프린트

                filename = 'realtime data/' + sUtil.now(False) + '.txt'
                fp = open(filename, 'a')
                
                realpool = kiwoom.getRealpool().copy()

                if realpool!={}:
                    
                    df = DataFrame(columns = ['code', 'price', 'volume'])
                    i = 0
                    
                    for k, v in realpool.items():
                        df.loc[i] = [k, v[0], v[1]]
                        i += 1
                        
                    KUtil.saveRealtimeData(fp, df, nowtime)

                fp.close()
                
                beforetime = nowtime
                semaphore = False
        
        time.sleep(0.2)
        

# 테스트 사용 시 내용만 변경하여 동작
def tmptest():
    
    r = RoughAlgorithm(kiwoom)
    r.test('20170626', '20170629')

    filename = 'algorithm log/roughAlgorithm.db'
    tablename = 'earning_rate_log'
    con = sqlite3.connect(filename)
    
    print(sUtil.select(tablename, con, 'sum(earning)'))

    con.close()

            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.commConnect()
    KUtil = KiwoomUtil(kiwoom)
    
    KUtil.saveStocksInfo()
    KUtil.setRealtime(KUtil.queryByMargin(20))

    #th1 = threading.Thread(target = infoUpdate)
    #th1.start()

    r = RoughAlgorithm(kiwoom)
    r.setTradingMode()
    r.start()
    
    #r.buy('000020', 1)
    #r.checkOrder()
    #r.sell('000020')
