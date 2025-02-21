from NeuralNetwork import *
from pandas import DataFrame
import random as rd
import pandas as pd



def randomDataFrame(columncount=3, indexcount=50):

    df = DataFrame(columns=list(range(columncount)))

    for i in range(indexcount):
        df.loc[i] = [rd.random() for j in range(columncount)]

    return df



def output1(dfInput):

    dfOutput = DataFrame(columns=[1, 2])
    
    for i in dfInput.index:
        dfOutput.loc[i] = [dfInput.get_value(i, 0) + dfInput.get_value(i, 1),
                           dfInput.get_value(i, 2) + dfInput.get_value(i, 1)]

    return dfOutput



def mlptest():

    dfInput = randomDataFrame(indexcount = 2)
    dfDesired = output1(dfInput)

    print(dfInput)

    dfWeight1, dfWeight2 = mlp(dfInput, dfDesired, maxIteration=100)

    print(dfWeight1)
    print(dfWeight2)

    dfOutput = getMlpOutput(dfInput, dfWeight1, dfWeight2)

    print(pd.concat([dfOutput, dfDesired], axis=1))

    errorGraph(dfOutput, dfDesired)



def olptest():

    dfInput = randomDataFrame()
    dfDesired = output1(dfInput)

    dfWeight = olp(dfInput, dfDesired, 0.02, maxIteration=1)

    print(dfWeight)

    dfOutput = calcNetDf(dfInput, dfWeight)

    print(pd.concat([dfOutput, dfDesired], axis=1))

    errorGraph(dfOutput, dfDesired)



def errortest1():

    dfInput = randomDataFrame()
    dfDesired = output1(dfInput)

    findOlpLearningRate(-0.2, 0.001, 0.2, dfInput, dfDesired) 


olptest()
