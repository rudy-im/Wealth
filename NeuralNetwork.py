#-*- coding : utf-8 -*-

from pandas import DataFrame
import numpy as np
import random as rd
import pandas as pd
import matplotlib.pyplot as plt

testFlag = False





# 다층 퍼셉트론 (Multi Layer Perceptron)
# dfInput : 입력 데이터 프레임. columns으로 노드 결정
# dfDesired : 목표 출력 데이터프레임. columns로 노드 결정
# dfInput과 dfDesired의 index는 같아야 함
# hiddenNodes : 은닉층 노드 개수. (임계치 제외)
# beta : 임계치 learning rate
# eta : 가중치 learning rate
#
# 학습으로 얻은 가중치 (dfWeight1, dfWeight2) 반환
# 단, dfWeight1의 columns는 (임계치 +)입력층, index는 은닉층 노드,
#     dfWeight2의 columns는 (임계치 +)은닉층, index는 출력층 노드 의미.
def mlp(dfInput, dfDesired, hiddenNodes=3, beta=0.9, eta=0.9, maxE=0.001, maxIteration=100):

    inputNodes = len(dfInput.columns)
    outputNodes = len(dfDesired.columns)

    # 출력층오차합
    E = 0

    # (1) 가중치와 임계치를 랜덤 넘버로 초기화
    dfWeight1 = randomDf(indexList=list(range(hiddenNodes)),
                         columnsList=['theta']+list(dfInput.columns))
    dfWeight2 = randomDf(indexList=list(dfDesired.columns),
                         columnsList=['theta']+list(range(hiddenNodes)))

    if testFlag:
        print('1')
        print(dfWeight1)
        print(dfWeight2)
        print('\n\n')

    for iteration in range(maxIteration):

        # 10회 반복마다 반복 횟수 표시
        if iteration%10==0: print('>>', iteration, '<<')
        
        for i in dfInput.index:

            # (2) 입력과 목표 출력 제시
            x_pi = list(dfInput.loc[i])
            d_pk = list(dfDesired.loc[i])

            if testFlag:
                print('2')
                print(x_pi)
                print(d_pk)
                print('\n\n')

            # (3) 제시된 입력 벡터를 이용하여 은닉층 j번째 뉴런으로의 입력값 계산
            net_pj = calcNet(x_pi, dfWeight1)

            if testFlag:
                print('3')
                print(net_pj)
                print('\n\n')

            # (4) 시그모이드 함수를 사용하여 은닉층의 출력 o_pj 계산
            o_pj = sigmoidList(net_pj)

            if testFlag:
                print('4')
                print(o_pj)
                print('\n\n')

            # (5) 은닉층의 출력을 이용하여 출력층 k번째 뉴런으로의 입력값 계산
            net_pk = calcNet(o_pj, dfWeight2)

            if testFlag:
                print('5')
                print(net_pk)
                print('\n\n')

            # (6) 시그모이드 함수를 사용하여 출력층의 출력 o_pk 계산
            o_pk = sigmoidList(net_pk)

            if testFlag:
                print('6')
                print(o_pk)
                print('\n\n')

            # (7) 목표 출력 d_pk와 계산된 출력 o_pk의 오차 delta_pk 계산
            #     학습 패턴 오차 E_p = SIGMA(delta_pk^2) 누적
            delta_pk = [(d_pk[j] - o_pk[j]) * o_pk[j] * (1 - o_pk[j])
                        for j in range(len(o_pk))]
            
            for j in range(len(delta_pk)): E += delta_pk[j] * delta_pk[j]

            if testFlag:
                print('7')
                print(delta_pk)
                print(E)
                print('\n\n')

            # (8) 출력층 오차 delta_pk와 은닉층-출력층 가중치 dfWeight2,
            #     은닉층 출력 o_pj를 사용하여 은닉층 오차 delta_pj 계산
            delta_pj = calcError(delta_pk, dfWeight2, o_pj)

            if testFlag:
                print('8')
                print(delta_pj)
                print('\n\n')

            # (9) 은닉층 출력 o_pj와 출력층 오차 delta_pk를 사용하여
            #     은닉층-출력층 가중치 dfWeight2 갱신.
            #     단, beta는 임계치, eta는 가중치의 학습률
            dfWeight2 = bp(dfWeight2, delta_pk, o_pj, beta, eta)

            if testFlag:
                print('9')
                print(dfWeight2)
                print('\n\n')

            # (10) 입력 x_pi와 은닉층 오차 delta_pj를 사용하여
            #      입력층-은닉층 가중치 dfWeight1 갱신.
            #     단, beta는 임계치, eta는 가중치의 학습률
            dfWeight1 = bp(dfWeight1, delta_pj, x_pi, beta, eta)

            if testFlag:
                print('10')
                print(dfWeight1)
                print('\n\n')

        # (11) 출력층의 오차합 E가 허용값 이하이거나, 최대 반복 횟수에 도달하면 종료
        if abs(E)<maxE: break

    return (dfWeight1, dfWeight2)




# 이전 층의 벡터와 가중치를 사용하여 다음 층의 벡터 반환
# 단, dfWeight의 맨 처음 column은 항상 임계치.
def calcNet(xList, dfWeight):

    yList = []

    for i in dfWeight.index:

        wList = list(dfWeight.loc[i])
        y = 0

        for j in range(len(wList)):

            if j==0: y += wList[j]
            else: y += wList[j] * xList[j-1]

        yList.append(y)

    return yList


# 시그모이드 함수
# 다층 퍼셉트론에서 사용
def sigmoid(net, lambda_=1):

    return 1 / (1 + np.exp(-net*lambda_))


# 리스트 전체에 시그모이드 함수 적용
def sigmoidList(net, lambda_=1):

    newnet = net.copy()

    for i in range(len(net)):
        
        newnet[i] = sigmoid(net[i], lambda_)

    return newnet


# 오류 역전파 중 사용
# 이전 층 오차, 이전층과 현재층의 가중치, 현재층의 직전 출력을 사용하여
# 현재층의 오차 계산
# 단, dfWeight의 맨 처음 column은 항상 임계치.
def calcError(beforedelta, dfWeight, output):

    delta = [0 for i in output]

    for i in range(len(dfWeight.index)):

        wList = list(dfWeight.loc[dfWeight.index[i]])

        for j in range(len(wList)):

            if j==0: pass
            else: delta[j-1] += beforedelta[i] * wList[j] * output[j-1] * (1-output[j-1])

    return delta
        

# 오류 역전파 (error Back Propagation)
# 직전 층의 오차와 현재 층의 값으로 둘 사이의 가중치 조정
# 단, df--Weight의 맨 처음 column은 항상 임계치.
def bp(dfBeforeWeight, delta, layer, beta, eta):

    dfNewWeight = dfBeforeWeight.copy()

    for i in range(len(dfBeforeWeight.index)):

        for j in range(len(dfBeforeWeight.columns)):

            ii = dfBeforeWeight.index[i]
            jj = dfBeforeWeight.columns[j]

            if j==0:
                w = dfBeforeWeight.get_value(ii, jj)   +   beta * delta[i]
                
            else:
                w = dfBeforeWeight.get_value(ii, jj)   +   eta * delta[i] * layer[j-1]

            dfNewWeight.set_value(ii, jj, w)

    if testFlag:
        print('\n\n')
        print('[bp()]')
        print(pd.concat([dfBeforeWeight, dfNewWeight], axis=1))

    return dfNewWeight


# 입력과 가중치에 대한 출력 데이터프레임 계산
# 단, dfWeight의 맨 처음 column은 항상 임계치.
def calcNetDf(dfInput, dfWeight):

    dfNet = DataFrame(index = list(dfInput.index), columns = list(dfWeight.index))
    
    for i in dfInput.index:
        for j in dfWeight.index:

            net = 0
            
            for k in range(len(dfWeight.columns)):
                kk = dfWeight.columns[k]
                if k==0: net += dfWeight.get_value(j, kk)
                else: net += dfWeight.get_value(j, kk) * dfInput.get_value(i, kk)
                
            dfNet.set_value(i, j, net)

    return dfNet


# 다층 퍼셉트론 출력 계산 확인
# 주어진 dfInput에 대하여, 가중치 dfWeight1, dfWeight2에 따른 출력 데이터 프레임 반환
def getMlpOutput(dfInput, dfWeight1, dfWeight2):

    dfHidden = calcNetDf(dfInput, dfWeight1)
    dfOutput = calcNetDf(dfHidden, dfWeight2)

    return dfOutput


# 0에서 1 사이의 난수로 초기화된 데이터프레임 반환
def randomDf(columnsList, indexList):

    df = DataFrame(columns=columnsList, index = indexList)

    for i in df.index:
        for j in df.columns:
            df.set_value(i, j, rd.random())

    return df
    




# 단층 퍼셉트론 (One Layer Perceptron)
#
# 출력 노드 개수는 데이터프레임의 column length와 같음
# 입력 노드에는 상수 역할을 하는 임계치(theta)가 있으므로 column length + 1
# 입력/출력 데이터프레임 index는 서로 순서까지 같아야 함
#
# 반환값은 columns가 input node(맨 앞에 임계치 포함), index가 output node 인 가중치 데이터프레임
def olp(dfInput, dfDesired, learningRate=0.6, maxIteration=1, initDfWeight=None):

    inputNodes = len(dfInput.columns) + 1
    outputNodes = len(dfDesired.columns)

    # (1) 가중치와 임계치를 랜덤 넘버로 초기화
    #     단, 초기 가중치 지정 시 해당 가중치로 초기화
    if type(initDfWeight)==type(None):
        dfWeight = randomDf(indexList=list(dfDesired.columns),
                            columnsList=['theta']+list(dfInput.columns))
    else:
        dfWeight = initDfWeight

    if testFlag:
        print('1')
        print(dfWeight)
        print('\n\n')

    for iteration in range(maxIteration):

        # 10회 반복마다 반복 횟수 표시
        if iteration%10==0: print('>>', iteration, '<<')
        
        for i in dfInput.index:
            
            # (2) 입력 패턴과 목표 출력 패턴 제시
            x = list(dfInput.loc[i])
            d = list(dfDesired.loc[i])

            if testFlag:
                print('2')
                print(x)
                print(d)
                print('\n\n')

            # (3) 하드 리미터 함수를 사용하여 실제 출력값 계산
            #     단, 여기서는 하드 리미터 함수를 사용하지 않고 그냥 net을 출력 y로 사용
            net = calcNet(x, dfWeight)  # 원래는 net 계산용
            y = hardLimiterList(net, 0.5)

            if testFlag:
                print('3')
                print(y)
                print('\n\n')

            # (4) 가중치 갱신
            dfWeight = updateOlpWeight(dfWeight, learningRate, d, y, x)

            if testFlag:
                print('4')
                print(dfWeight)
                print('\n\n')

            # (5) (2)로 돌아가서 반복 수행

    return dfWeight



# 하드리미터 함수. (step function)
# threshold 이하이면 0, 초과이면 1 반환
# 단층 퍼셉트론에서 사용
def hardLimiter(net, threshold):
    
    if net<=threshold: return 0
    else: return 1


# 리스트 전체에 하드리미터 함수 적용
def hardLimiterList(net, threshold):

    newnet = net.copy()
    
    for i in range(len(net)):
        newnet[i] = hardLimiter(net[i], threshold)

    return newnet


# 단층 퍼셉트론에서 가중치를 갱신하는 함수.
# dfBeforeWeight는 원래 가중치, learningRate는 학습률,
# d는 목표출력벡터, y는 계산된출력벡터, x는 입력벡터
# 단, dfWeight의 맨 처음 column은 항상 임계치.
def updateOlpWeight(dfBeforeWeight, learningRate, d, y, x):

    dfWeight = dfBeforeWeight.copy()

    for i in range(len(dfBeforeWeight.index)):

        for j in range(len(dfBeforeWeight.columns)):
            
            ii = dfBeforeWeight.index[i]
            jj = dfBeforeWeight.columns[j]

            # 임계치의 경우 입력값을 1로 취급
            if j==0:
                w = dfBeforeWeight.get_value(ii, jj) + learningRate * (d[i]-y[i])

            else :
                w = dfBeforeWeight.get_value(ii, jj) + learningRate * (d[i]-y[i]) * x[j-1]

            dfWeight.set_value(ii, jj, w)

    return dfWeight




# 오차 그래프 확인
# dfCalcOutput과 dfDesired의 index, columns는 서로 같아야 함
def errorGraph(dfCalcOutput, dfDesired):

    for j in dfDesired.columns:

        plt.figure(j)

        cList = []
        dList = []
        eList = []
        epList = []
        
        for i in dfDesired.index:

            c = dfCalcOutput.get_value(i, j)
            d = dfDesired.get_value(i, j)

            e = c - d
            ep = e/d

            cList.append(c)
            dList.append(d)
            eList.append(e)
            epList.append(ep)

        plt.subplot(211)
        plt.plot(cList, 'g', dList, 'b', eList, 'r')
        plt.text(0, 0, 'r:error, g:calcOutput, b:desired')

        plt.subplot(212)
        plt.plot(epList)
        plt.ylabel('percent')

    plt.show()


# 계산된 출력과 목표 출력 간의 퍼센트 오차 데이터프레임 반환
def getPercentError(dfCalcOutput, dfDesired):
    
    dfError = dfDesired.copy()

    for i in dfDesired.index:

        for j in dfDesired.columns:

            c = dfCalcOutput.get_value(i, j)
            d = dfDesired.get_value(i, j)

            e = (c-d)/d

            dfError.set_value(i, j, e*100)

    return dfError


# 데이터프레임의 각 column의 절대값의 평균값 리스트 반환
def getAbsAvg(df):

    indexLen = float(len(df.index))
    if indexLen==0: return

    avgList = []
    
    for j in df.columns:

        avg = 0

        for i in df.index: avg += abs(df.get_value(i, j))

        avgList.append(avg/indexLen)

    return avgList


# 단층 퍼셉트론에서 학습률에 따른 오차 그래프 확인
def findOlpLearningRate(minVal, interval, maxVal, dfInput, dfDesired, maxIteration=5, initWeight=None):

    dfError = DataFrame(columns = list(dfDesired.columns))

    for learningRate in np.arange(minVal, maxVal+interval, interval):

        if learningRate==0: continue

        # 단층 퍼셉트론으로 계산된 가중치 얻기
        dfNewWeight = olp(dfInput, dfDesired, learningRate, maxIteration, initWeight)

        # 해당 가중치로 계산된 출력을 얻어, 목표 출력과의 오차를 그래프로 그릴 데이터프레임에 적재
        dfCalcOutput = calcNetDf(dfInput, dfNewWeight)
        
        dfPercentError = getPercentError(dfCalcOutput, dfDesired)
        
        errorList = getAbsAvg(dfPercentError)
                
        dfError.loc[learningRate] = errorList

    drawErrorGraph(dfError)


# 그래프 그리기
def drawErrorGraph(dfError):

    xAxis = list(dfError.index)
    
    for k in range(len(dfError.columns)):

        if k%2!=0: plt.figure(k/2 + 1)

        line = list(dfError[dfError.columns[k]])
        
        plt.subplot(210 + k%2 + 1)
        plt.plot(xAxis, line)
        plt.ylabel('percent')

    plt.show()


# 단층 퍼셉트론에서 초기 가중치에 따른 오차 그래프 확인 (임계치 포함)
# otherWeight : 가중치 중 하나를 지정 범위 내에서 변경할 동안 고정시킬 다른 가중치들의 값
def findOlpWeight(minVal, interval, maxVal, dfInput, dfDesired, learningRate=0.1, maxIteration=5, otherWeight=1.0):

    dfError = DataFrame(columns = list(dfDesired.columns))

    wColumns = ['theta']+list(dfInput.columns)
    wIndex = list(dfDesired.columns)

    for i in wIndex:

        for j in wColumns:

            dfWeight = DataFrame(data=otherWeight, index=wIndex,
                                 columns=wColumns)

            for w in np.arange(minVal, maxVal+interval, interval):

                if w==0: continue

                dfWeight.set_value(i, j, w)
                
                # 단층 퍼셉트론으로 계산된 가중치 얻기
                dfNewWeight = olp(dfInput, dfDesired, learningRate, maxIteration, dfWeight)

                # 해당 가중치로 계산된 출력을 얻어, 목표 출력과의 오차를 그래프로 그릴 데이터프레임에 적재
                dfCalcOutput = calcNetDf(dfInput, dfNewWeight)
                
                dfPercentError = getPercentError(dfCalcOutput, dfDesired)

                #print(dfPercentError)
                
                errorList = getAbsAvg(dfPercentError)
                        
                dfError.loc[w] = errorList

            drawErrorGraph(dfError)








