import sqlite3
import sqlite3Util as sUtil
from KiwoomUtil import *
from NeuralNetwork import *




        
def olpTest():

    dfWeight = olp(dfInput, dfDesired, 0, 1)

    print(dfWeight)

    dfOutput = calcNetDf(dfInput, dfWeight)

    print(pd.concat([dfOutput, dfDesired], axis=1))

    errorGraph(dfOutput, dfDesired)



def mlpTest():
    
    dfWeight1, dfWeight2 = mlp(dfInput, dfDesired, maxIteration=100)

    print(dfWeight1)
    print(dfWeight2)

    dfOutput = getMlpOutput(dfInput, dfWeight1, dfWeight2)

    print(pd.concat([dfOutput, dfDesired], axis=1))

    errorGraph(dfOutput, dfDesired)
        






    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    KUtil = KiwoomUtil()
    KUtil.commConnect()
    
    #codes = ['122990']
    #KUtil.setRealtime(codes)

    #KUtil.saveMinChart(code, 3, 10)

    #################################################################################
    # 데이터 프레임 생성 (dfInput, dfDesired)
    #################################################################################

    code = '122990'
    filename = 'stock data/' + code + '.db'
    tablename = 'min3'

    selectstr = 'candleTime, close, volume'

    # 차트 데이터 얻기
    con = sqlite3.connect(filename)
    dfData1 = sUtil.select(tablename, con, selectstr, limit=130)
    con.close()

    dfInput = DataFrame(columns = ['종가', '거래량', '직전종가', '직전거래량'])
    dfDesired = DataFrame(columns = ['종가', '거래량'])

    reversedindex = list(dfData1.index)
    reversedindex.reverse()
    index = 0

    for i in reversedindex:
        
        time = int(dfData1.get_value(i, 'candleTime'))%1000000

        if (time<90600 or time>150000): continue

        dfInput.loc[index] = [dfData1.get_value(i, 'close'),
                              dfData1.get_value(i, 'volume'),
                              dfData1.get_value(i+1, 'close'),
                              dfData1.get_value(i+1, 'volume')]

        dfDesired.loc[index] = [dfData1.get_value(i-1, 'close'),
                                dfData1.get_value(i-1, 'volume')]

        index += 1
        
        
    #################################################################################
    # 실행할 코드
    #################################################################################

    #findOlpLearningRate(-0.01, 0.0001, 0.01, dfInput, dfDesired)

    findOlpWeight(-20.0, 1.0, -10.0, dfInput, dfDesired, otherWeight=-10.0) 
