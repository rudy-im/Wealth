###############################################################
####    테스트 완료
###############################################################



import sqlite3
import sqlite3Util as sUtil
from pandas import Series, DataFrame


con = sqlite3.connect('test.db')

columnstr = '''code CHAR(6) NOT NULL UNIQUE,
                name VARCHAR2(30) NOT NULL,
                modified_date DATE NOT NULL'''
#sUtil.create('stocks1', con, columnstr)

#sUtil.insert('stocks1', con, ['code', 'name', 'modified_date'],
#                            ['a', 'b', [sUtil.now()]])

#sUtil.insert('stocks1', con, ['code', 'name', 'modified_date'],
#                            ['a', 'c', [sUtil.now()]])

#sUtil.delete('stocks1', con, 'code=="a"')
  
#sUtil.create('stocks1', con, columnstr, if_not_exists=False)
#sUtil.create('stocks2', con, columnstr, if_not_exists=False)
             

             
df = DataFrame(columns=['code', 'name', 'modified_date'])
df.loc[0]=['a', 'a', [sUtil.now()]]
df.loc[2]=['b', 'b', [sUtil.now()]]

#sUtil.insertDataFrame('stocks2', con, df, dropFlag = True)

#sUtil.insertDataFrame('stocks4', con, df, createFlag = False)
#sUtil.insertDataFrame('stocks3', con, df, createFlag = True)

#sUtil.insertDataFrame('stocks1', con, df, replaceFlag = False)





#sUtil.getColumns('stocks1', con)
#sUtil.getColumns('stocks4', con, False)

sUtil.select('stocks1', con)

con.close()
