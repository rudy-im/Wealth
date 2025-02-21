#-*- coding : utf-8 -*-
import sqlite3
import datetime
from pandas import Series, DataFrame


#====================================================
# sqlite3 사용 방법
#
# con = sqlite3.connect('파일명')
# cursor = con.cursor()
# cursor.execute('sql문')
# con.commit()
# con.close
#====================================================


# 테스트 로그 출력
testFlag = False


# 테이블 생성
# if_not_exists==False 이면 기존 테이블 삭제
def create(tablename, con, columnstr, if_not_exists=True):
    
    cursor = con.cursor()
    
    if not(if_not_exists):
        drop(tablename, con)
    
    sql = 'CREATE TABLE '
    if if_not_exists: sql = sql + 'IF NOT EXISTS '
    sql = sql + tablename
    sql = sql + ' (' + columnstr + ')'
    sql = sql + ';'

    if testFlag:
        print("\n\n")
        print("[create()] sql : ")
        print(sql)

    try:
        cursor.execute(sql)
        con.commit()
        
    except:
        print("\n\n")
        print("Failed to create()!!")
        print("--tablename :: " + tablename)
        print("--columnstr :: " + columnstr)


# TODO
# 테이블 삭제
def drop(tablename, con):
    
    pass


# 테이블 행 추가
# columns, values 는 list형
# values에서 DB 함수로 된 문자열은 [... , [함수문자열], ...] 처럼 리스트로 묶어 전달할 것!
def insert(tablename, con, columns, values, replace=True):
    
    cursor = con.cursor()

    sql = 'INSERT '
    if replace: sql = sql + 'OR REPLACE '
    sql = sql + 'INTO '
    sql = sql + tablename
    sql = sql + ' (' + ', '.join(columns) + ') '

    # value 는 숫자, 문자열 1개만 있는 리스트, 문자열만 가능
    valuesstr = ', '.join([str(i) if type(i)==type(int()) or type(i)==type(float())
                           else i[0] if type(i)==type(list())
                           else '"'+i+'"'
                           
                           for i in values
                           
                           if type(i)==type(int()) or type(i)==type(float())
                           or (type(i)==type(list()) and type(i[0])==type(str()))
                           or type(i)==type(str())])
    
    sql = sql + 'VALUES'
    sql = sql + ' (' + valuesstr + ')'
    sql = sql + ';'

    if testFlag:
        print("\n\n")
        print("[insert()] sql : ")
        print(sql)

    try:
        cursor.execute(sql)
        con.commit()
    
    except:
        print("\n\n")
        print("Failed to insert()!!")
        print("--tablename :: " + tablename)


# 테이블 업데이트
# values에서 DB 함수로 된 문자열은 [... , [함수문자열], ...] 처럼 리스트로 묶어 전달할 것!
def update(tablename, con, columns, values, wherestr):
    cursor = con.cursor()

    sql = 'UPDATE '
    sql = sql + tablename
    sql = sql + ' SET '

    # value 는 숫자, 문자열 1개만 있는 리스트, 문자열만 가능
    value = [str(i) if type(i)==type(int()) or type(i)==type(float())
                       else i[0] if type(i)==type(list())
                       else '"'+i+'"'
                       
                       for i in values
                       
                       if type(i)==type(int()) or type(i)==type(float())
                       or (type(i)==type(list()) and type(i[0])==type(str()))
                       or type(i)==type(str())]

    for i in range(len(columns)):
        if i!=0:
            sql = sql + ', '
        sql = sql + columns[i]
        sql = sql + ' = '
        sql = sql + value[i]

    sql = sql + ' WHERE '
    sql = sql + wherestr
    sql = sql + ';'

    if testFlag:
        print("\n\n")
        print("[update()] sql : ")
        print(sql)

    try:
        cursor.execute(sql)
        con.commit()
    
    except:
        print("\n\n")
        print("Failed to update()!!")
        print("--tablename :: " + tablename)


# 테이블 행 삭제
# condition은 조건식 문자열
def delete(tablename, con, wherestr):
    
    cursor = con.cursor()
    
    sql = 'DELETE FROM '
    sql = sql + tablename
    sql = sql + ' WHERE '
    sql = sql + wherestr
    sql = sql + ';'

    if testFlag:
        print("\n\n")
        print("[delete()] sql : ")
        print(sql)
        
    try:
        cursor.execute(sql)
        con.commit()
        
    except:
        print("\n\n")
        print("Failed to delete()!!")
        print("--tablename :: " + tablename)
        print("--wherestr :: " + wherestr)


# 테이블 행을 쿼리하여 DataFrame으로 반환
# limit은 최대 쿼리 행 수. 0이면 제한 없음.
def select(tablename, con, selectstr='*', wherestr='', limit=0):
    
    cursor = con.cursor()

    sql = 'SELECT '
    sql = sql + selectstr
    sql = sql + ' FROM '
    sql = sql + tablename

    if wherestr!='':
        sql = sql + ' WHERE '
        sql = sql + wherestr

    if limit!=0:
        sql = sql + ' LIMIT '
        sql = sql + str(limit)

    sql = sql + ';'

    if testFlag:
        print("\n\n")
        print("[select()] sql = ")
        print(sql)

    try:
        cursor.execute(sql)
        ret = cursor.fetchall()
            
        if testFlag:
            print("\n")
            print("[select()] type(ret) = " + str(type(ret)))
            print("[select()] ret = ")
            print(ret)

        if selectstr == '*':
            col = getColumns(tablename, con)
            
        else:
            col = [i.strip() for i in selectstr.split(',') if i.strip()!='']

        df = DataFrame(columns = col)
        
        for i in range(len(ret)):
            df.loc[i] = ret[i]

        if testFlag:
            print("[select()] df = ")
            print(df)
        
        return df
    
    except:
        print("\n\n")
        print("[select()] Failed to select()!!")
        print("--tablename :: " + tablename)
        print("--selectstr :: " + selectstr)
        print("--wherestr :: " + wherestr)
    

# column 이름 리스트 얻기
# nameOnly가 True이면 [칼럼 이름, ...] 리스트 반환,
# False이면 [[칼럼이름, 자료형, 길이, 제약조건], ...] 리스트 반환
def getColumns(tablename, con, nameOnly=True):

    try:
        cursor = con.cursor()

        sql = 'SELECT sql FROM sqlite_master WHERE tbl_name = "'
        sql = sql + tablename
        sql = sql + '" AND type = "table";'
        
        cursor.execute(sql)
        result = cursor.fetchall()

        if testFlag:
            print("\n\n")
            print("[getColumns()] sql : ")
            print(sql)
            print("[getColumns()] result : ")
            print(result)

        s = result[0][0]

        s = s.partition('(')[2]
        s = s.rpartition(')')[0]

        l = [i.strip() for i in s.split(',')]

        if testFlag:
            print("\n")
            print("[getColumns()] s : " + s)
            print("[getColumns()] l : ")
            print(l)

        ret = []
        
        for i in l:
            part = i.partition(' ')
            name = part[0]

            if nameOnly:
                ret.append(name)

            else:
                part = part[2].partition(' ')
                typeAndLen = part[0]
                constraints = part[2]

                if testFlag:
                    print("\n")
                    print("[getColumns()] typeAndLen : " + typeAndLen)
                    print("[getColumns()] constraints : " + constraints)

                
                tal = typeAndLen.split('(')
                datatype = tal[0]
                
                if len(tal)==1:
                    length = ''
                else:
                    length = tal[1].split(')')[0]

                if testFlag:
                    print("[getColumns()] datatype : " + datatype)
                    print("[getColumns()] length : " + length)

                ret.append([name, datatype, length, constraints])
                
        if testFlag:
            print("\n\n")
            print("[getColumns()] ret : ")
            print(ret)

        return ret

    except:
        print("\n\n")
        print("[getColumns()] Failed to getColumns()!!!")
    

# DB의 DATE 형에 저장 가능한 현재시간 문자열 반환
# date("strf")
def now(withDateFunc = True, strf='%Y-%m-%d'):
    
    ret = datetime.datetime.now().strftime(strf)
    if withDateFunc: ret = 'date("' + ret + '")'
    
    if testFlag:
        print("\n\n")
        print("[now()] ret : " + ret)
        
    return ret


# DataFrame 객체를 받아 테이블에 insert (인덱스 값은 저장 안 됨)
# create : 테이블이 없는 경우 새로 생성
# drop : 테이블이 존재하는 경우 drop하고 새로 생성
# replace : 테이블에서 같은 고유값 행이 존재하는 경우 대체
def insertDataFrame(tablename, con, dataFrame, createFlag=True, dropFlag=False, replaceFlag=True):

    if dropFlag:
        drop(tablename, con)        

    # 새로 생성하는 경우, 데이터타입은 VARCHAR2로 고정
    if (createFlag or dropFlag):
        columnstr = ', '.join([str(i) + ' VARCHAR2' for i in dataFrame.columns])

        if testFlag:
            print("\n\n")
            print("[insertDataFrame()] dropFlag == " + str(dropFlag))
            print("[insertDataFrame()] createFlag == " + str(createFlag))
            print("[insertDataFrame()] columnstr : ")
            print(columnstr)                  
        
        create(tablename, con, columnstr)

    columns = getColumns(tablename, con)

    for i in dataFrame.index:

        if testFlag:
            print("\n")
            print("[insertDataFrame()] type(dataFrame.columns) : " + str(type(dataFrame.columns)))
            print("[insertDataFrame()] dataFrame.columns : ")
            print(dataFrame.columns)
            print("[insertDataFrame()] type(dataFrame.loc[i]) : " + str(type(dataFrame.loc[i])))
            print("[insertDataFrame()] dataFrame.loc[i] : ")
            print(dataFrame.loc[i])

        row = []
        for j in columns:
            row.append(dataFrame.get_value(i, j))

        if testFlag:
            print("\n")
            print("[insertDataFrame()] row : ")
            print(row)
            
        try:
            insert(tablename, con, columns, row, replaceFlag)

        except:
            pass




    
    
