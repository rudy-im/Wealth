import sqlite3
import sqlite3Util as sUtil
from pandas import Series, DataFrame


con = sqlite3.connect('test.db')


cols = sUtil.getColumns('test', con)
print(cols)

sUtil.addColumn('test', con, 'col')

cols = sUtil.getColumns('test', con)
print(cols)

con.close()
