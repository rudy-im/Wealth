import sqlite3
import sqlite3Util as sUtil

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report,confusion_matrix

from pandas import DataFrame


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

y = list(dfDesired['종가'])

# 데이터를 평균 0, 분산 1이 되도록 조정
X_train, X_test, y_train, y_test = train_test_split(dfInput, y)

print(X_train)
print("")
print(X_test)
print("")
print(y_train)
print("")
print(y_test)
print("")

scaler = StandardScaler()

# Fit only to the training data
scaler.fit(X_train)

# Now apply the transformations to the data:
X_train = scaler.transform(X_train)
X_test = scaler.transform(X_test)

mlp = MLPClassifier(hidden_layer_sizes=(100, 100),max_iter=6000)
mlp.fit(X_train,y_train)



predictions = mlp.predict(X_test)

print('')
print(y_test)
print('')
print(predictions)
print('')
print(confusion_matrix(y_test,predictions))
print('')
print(classification_report(y_test,predictions))

    
