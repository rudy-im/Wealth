#-*- coding : utf-8 -*-

import sqlite3
import sqlite3Util as sUtil
import shutil, os
from pandas import DataFrame

##############################################################
# ** 패턴 저장 전용 모듈 **
#
# 
##############################################################



# 테스트 시 주요 변수 내용 표시 플래그
testFlag = True
testcon = None

# modifiedLen 주요 상수
min5Len = 78
dayLen = 23
weekLen = 5
monthLen = 12

# 종목의 차트 등 종목코드.db 파일 저장 경로
stockDirectory = 'stock data'






    


    


######################################################################################
# 내부에서 사용하는 함수
######################################################################################



# 패턴 테이블 이름 얻기
def getPatternTableName(charttablename):

    ret = charttablename + '_pattern'

    if testFlag:
        print('\n\n')
        print("[getPatternTableName()] ret = ", ret)

    return ret


# 대표 패턴 테이블 이름 얻기
def getRPTableName(charttablename, startNo, modifiedLen, matchLimit):

    ret = charttablename + '_rp_' + str(startNo) + '_' + str(modifiedLen) + '_' + str(matchLimit)

    if testFlag:
        print('\n\n')
        print("[getRPTableName()] ret = ", ret)

    return ret


# 패턴 테이블이 없는 경우, 생성
# 테이블 이름 : 차트테이블명_pattern
# 칼럼 : candleTime, close, colse_modifiedLen, volume, volume_modifiedLen
def makePatternTable(charttablename, con, modifiedLen=0):

    chartcolumns = ['close', 'volume']

    candleTime = '20'
    if charttablename.startswith('min'): candleTime = '14'
    elif charttablename.startswith('day'): candleTime = '8'
    elif charttablename.startswith('week'): candleTime = '8'
    elif charttablename.startswith('month'): candleTime = '8'

    modifiedLen_ = modifiedLen
    if modifiedLen==0:
        if charttablename.startswith('min5'): modifiedLen_ = min5Len
        elif charttablename.startswith('day'): modifiedLen_ = dayLen
        elif charttablename.startswith('week'): modifiedLen_ = weekLen
        elif charttablename.startswith('month'): modifiedLen_ = monthLen

    tablename = getPatternTableName(charttablename)

    patternLen = str(len(str(pow(2, modifiedLen_+1))))

    try:

        columnstr = '''candleTime CHAR(''' + candleTime + ''') NOT NULL UNIQUE,'''
        patterncols = {}
        
        for col in chartcolumns:
            patterncols[col] = 'NUMBER(' + patternLen+ ')'
            patterncols[col + '_' + str(modifiedLen_)] = 'NUMBER(' + patternLen + ')'

        for k, v in patterncols.items():
            columnstr += k + ' ' + v + ', '

        columnstr = columnstr[:-2]

        if testFlag:
            print('\n\n')
            print('[makePatternTable()] columnstr :')
            print(columnstr)

        sUtil.create(tablename, con, columnstr)

        # 이미 패턴 테이블이 존재하여 새로 만들어지지 않은 경우,
        # 없는 칼럼만 추가
        columns = sUtil.getColumns(tablename, con)
        
        for k, v in patterncols.items():
            
            if columns.count(k)==0:
                
                sUtil.addColumn(tablename, con, k + ' ' + v)

                if testFlag:
                    print('')
                    print('[makePatternTable()] k : ', k)
                    print('[makePatternTable()] v : ', v)

        # 만들어진 패턴 테이블 이름 반환
        return tablename
            
    except:
        
        print("\n\n")
        print("[makePatternTable()] Failed to makePatternTable()!!!")


# 대표 패턴 테이블이 없는 경우, 생성
# 테이블이름 : 차트테이블명_rp_modifiedLen_matchLimit
# startNo : 일봉의 경우 1~31일(startNo=1), 15~14일(startNo=15) 의 2종류
# 칼럼 : representitivePattern(종가패턴+거래량패턴),
#        inflectionPoints(종가변곡점개수;거래량변곡점개수;종가변곡점위치, ...;거래량변곡점위치, ...),
#        weights(종가에만 적용. 소수점2째자리까지. 가중치11;가중치21,가중치22;가중치31, ...)
def makeRPTable(charttablename, con, startNo, modifiedLen=0, matchLimit=90):
    
    candleTime = '20'
    if charttablename.startswith('min'): candleTime = '14'
    elif charttablename.startswith('day'): candleTime = '8'
    elif charttablename.startswith('week'): candleTime = '8'
    elif charttablename.startswith('month'): candleTime = '8'
    
    modifiedLen_ = modifiedLen
    if modifiedLen==0:
        if charttablename.startswith('min5'): modifiedLen_ = min5Len
        elif charttablename.startswith('day'): modifiedLen_ = dayLen
        elif charttablename.startswith('week'): modifiedLen_ = weekLen
        elif charttablename.startswith('month'): modifiedLen_ = monthLen

    tablename = getRPTableName(charttablename, startNo, modifiedLen_, matchLimit)
    
    patternLen = str(len(str(pow(2, modifiedLen_*2 + 1))))

    if testFlag:
        print('\n\n')
        print('[makeRPTable()] patternLen : ', patternLen)

    try:

        columnstr = '''representitivePattern NUMBER(''' + patternLen + ''') NOT NULL UNIQUE,
                       inflectionPoints VARCHAR2(100) NOT NULL,
                       weights VARCHAR2(200)'''

        sUtil.create(tablename, con, columnstr)

        # 만들어진 대표 패턴 테이블 이름 반환
        return tablename
            
    except:
        
        print("\n\n")
        print("[makeRPTable()] Failed to makeRPTable()!!!")


# 패턴 길이 수정
def getModifiedPattern(patternstr, modifiedLen):

    pLen = len(patternstr)
    modified = ''

    # 패턴 길이가 수정 길이보다 2배 이상 작거나 크면 실패
    if (pLen>=modifiedLen*2 or pLen*2<=modifiedLen):
        return modified

    # 패턴 길이를 더 길게 해야 하는 경우,
    # 패턴을 늘려야 하는 길이만큼 등분하여 사이에 직전 패턴 끼워넣기
    if pLen<modifiedLen:

        diff = modifiedLen-pLen
        part = int(pLen/(diff+1))
        pt = 0

        for i in range(diff):
            modified += patternstr[pt:pt+part]
            pt += part
            modified += patternstr[pt-1]

        modified += patternstr[pt:]

    # 길이를 수정할 필요가 없는 경우
    elif pLen==modifiedLen:
        
        modified = patternstr

    # 패턴 길이를 더 줄여야 하는 경우,
    # 패턴을 줄여야 하는 길이만큼 등분하여 사이의 패턴 하나씩 지우기
    else:

        diff = pLen-modifiedLen
        part = int(pLen/(diff+1))
        pt = 0

        for i in range(diff):
            modified += patternstr[pt:pt+part]
            pt += part
            modified = modified[:-1]

        modified += patternstr[pt:]

    if testFlag:
        print('\n\n')
        print('[getModifiedPattern()] patternstr : ', patternstr)
        print('[getModifiedPattern()] modified : ', modified)

    # 수정된 패턴 반환
    return modified


###
# 대표 패턴 테이블에서 대표 패턴 리스트를 얻어 반환
def getRPList(rptablename, con):

    df = sUtil.select(rptablename, con, 'representitivePattern')
    ret = list(df['representitivePattern'])

    if testFlag:
        print('\n\n')
        print('[getRPList()] ret : ')
        print(ret)
        
    return ret


# 대표 패턴 리스트에서 지정 패턴과의 매치율이 matchLimit 이상인 것들을
# {해당대표패턴:매치율} 형식의 dic으로 반환
def findRepresentitivePatterns(rpList, modifiedStr, matchLimit=90):

    ret = {}
    modifiedLen = len(modifiedStr)
    matchCountLimit = int(int(modifiedStr, 2)*matchLimit/100)

    for rp in rpList:

        matched = int(rp)^int(modifiedStr, 2)
        matchCount = modifiedLen - str(bin(matched)).count('1')
        if matchCount>matchCountLimit:
            ret[rp] = float(matchCount)/float(modifiedLen)

    if testFlag:
        print('\n\n')
        print('[findRepresentitivePatterns()] ret : ')
        print(ret)

    return ret


# 변곡점 찾기
# 직전 패턴과 다르고, 2단계 전 패턴과도 달라야 변곡점. (진동 시 변곡점이 많아지는 것 방지)
# 변곡점 위치의 인덱스 리스트 반환
def findInflectionPoints(patternstr):

    before1 = ''
    before2 = ''
    ipList = []

    for loc in range(len(patternstr)):

        p = patternstr[loc]
        if (p!=before1 and p!=before2): ipList.append(loc)

        before2 = before1
        before1 = p

    if testFlag:
        print('\n\n')
        print('[findInflectionPoints()] patternstr : ', patternstr)
        print('[findInflectionPoints()] ipList : ')
        print(ipList)

    return ipList


###
# 대표 패턴 테이블에서 해당 rp의 변곡점 정보를 얻어 반환
# [종가변곡점개수, 거래량변곡점개수, '종가변곡점위치, ...', '거래량변곡점위치, ...'] 형식으로 반환
def getRPInflectionPoints(rptablename, con, rp):

    df = sUtil.select(rptablename, con, 'inflectionPoints', 'representitivePattern = ' + str(rp))

    # 해당 rp가 없으면 실패
    if len(df.index)==0: return

    ret = df.get_value(0, 'inflectionPoints').split(';')
    ret[0] = int(ret[0])
    ret[1] = int(ret[1])

    if testFlag:
        print('\n\n')
        print('[getRPInflectionPoints()] ret : ')
        print(ret)

    return ret


###
# 해당 패턴을 대표 패턴 리스트와 비교하여,
# matchLimit보다 매치율이 높은 대표 패턴이 있으면 변곡점 개수가 작은 것을 등록.
# 없으면, 그냥 새로 등록.
# 변경된 rp 리스트를 반환
def insertSimplerRP(rptablename, con, rpList, modifiedCloseStr, modifiedVolumeStr):

    if testFlag:
        print('\n\n')
        print('[insertSimplerRP()]')

    ret = rpList.copy()

    nowP = modifiedCloseStr + modifiedVolumeStr
    print('nowP str')
    print(nowP)

    ipClose = findInflectionPoints(modifiedCloseStr)
    ipVolume = findInflectionPoints(modifiedVolumeStr)
    ipCloseLen = len(ipClose)
    ipVolumeLen = len(ipVolume)

    matchdic = findRepresentitivePatterns(rpList, nowP)
    nowP = int(nowP, 2)

    print('')
    print('nowP bin')
    print(nowP)

    insertFlag = False

    # 매치되는 패턴이 아예 없으면 새로 등록 확정
    if len(matchdic)==0: insertFlag = True

    else:

        # 매치율이 가장 큰 rp
        compareRP = [k for k in matchdic.keys() if matchdic[k] == max(matchdic.values())][0]

        compareIP = getRPInflectionPoints(rptablename, con, compareRP)

        # 변곡점 개수 합계가 해당 패턴 쪽이 적은 경우,
        # 기존 대표 패턴을 버리고 새로운 대표 패턴으로 등록
        if ipCloseLen+ipVolumeLen < compareIP[0]+compareIP[1]:
            
            insertFlag = True
            sUtil.delete(rptablename, con, 'representitivePattern = ' + str(compareRP))
            ret.remove(compareRP)

            if testFlag:
                print('')
                print('[insertSimplerRP()] compareRP : ', compareRP, '   is removed!!')

                sUtil.delete(rptablename, testcon, 'representitivePattern = ' + str(bin(compareRP))[2:])
                
    # 새로운 패턴 등록
    if insertFlag:
        
        columns = ['representitivePattern', 'inflectionPoints']
        values = [nowP,
                  str(ipCloseLen) + ';' + str(ipVolumeLen) + ';' +
                  ','.join([str(i) for i in ipClose]) + ';' + ','.join([str(i) for i in ipVolume])]

        sUtil.insert(rptablename, con, columns, values)
        ret.append(nowP)

        if testFlag:
            print('')
            print('[insertSimplerRP()] nowP : ', nowP, '   is inserted!!')

            testvalues = values.copy()
            testvalues[0] = str(bin(nowP))[2:]
            sUtil.insert(rptablename, testcon, columns, testvalues)

    # 변경된 rpList 반환
    return ret
            

# 패턴테이블에서 새로 저장을 시작해야 하는 최신 날짜 반환
def getSaveStartDate(patterntablename, con):

    df = sUtil.select(patterntablename, con, 'candleTime', ordercolumn='candleTime', limit=2)

    if len(df.index)<2: return 0
    else: return int(df.get_value(1, 'candleTime'))



######################################################################################
# 테스트 플래그 전용
######################################################################################



def makeTestRowTable(charttablename, con):

    candleTime = '20'
    if charttablename.startswith('min'): candleTime = '14'
    elif charttablename.startswith('day'): candleTime = '8'
    elif charttablename.startswith('week'): candleTime = '8'
    elif charttablename.startswith('month'): candleTime = '8'

    tablename = charttablename + '_row'

    if testFlag:
        print('\n\n')
        print('[makeTestRowTable()]')

    try:

        columnstr = '''candleTime CHAR(''' + candleTime + ''') NOT NULL UNIQUE,
                       close CHAR(1),
                       volume CHAR(1)'''

        sUtil.create(tablename, con, columnstr)

        # 만들어진 로우 패턴 테이블 이름 반환
        return tablename
            
    except:
        
        print("\n\n")
        print("[makeTestRowTable()] Failed to makeTestRowTable()!!!")



# 테스트 패턴 테이블이 있으면 삭제하고 새로 생성
# 테이블 이름 : 차트테이블명_pattern
# 칼럼 : candleTime, close, colse_modifiedLen, volume, volume_modifiedLen
def makeTestPatternTable(charttablename, con, modifiedLen=0):

    chartcolumns = ['close', 'volume']

    candleTime = '20'
    if charttablename.startswith('min'): candleTime = '14'
    elif charttablename.startswith('day'): candleTime = '8'
    elif charttablename.startswith('week'): candleTime = '8'
    elif charttablename.startswith('month'): candleTime = '8'

    modifiedLen_ = modifiedLen
    if modifiedLen==0:
        if charttablename.startswith('min5'): modifiedLen_ = min5Len
        elif charttablename.startswith('day'): modifiedLen_ = dayLen
        elif charttablename.startswith('week'): modifiedLen_ = weekLen
        elif charttablename.startswith('month'): modifiedLen_ = monthLen

    tablename = getPatternTableName(charttablename)

    try:

        columnstr = '''candleTime CHAR(''' + candleTime + ''') NOT NULL UNIQUE,'''
        patterncols = {}
        
        for col in chartcolumns:
            patterncols[col] = 'CHAR(' + modifiedLen_ + ')'
            patterncols[col + '_' + str(modifiedLen_)] = 'CHAR(' + modifiedLen_ + ')'

        for k, v in patterncols.items():
            columnstr += k + ' ' + v + ', '

        columnstr = columnstr[:-2]

        if testFlag:
            print('\n\n')
            print('[makeTestPatternTable()] columnstr :')
            print(columnstr)

        sUtil.create(tablename, con, columnstr, False)

        # 이미 패턴 테이블이 존재하여 새로 만들어지지 않은 경우,
        # 없는 칼럼만 추가
        columns = sUtil.getColumns(tablename, con)
        
        for k, v in patterncols.items():
            
            if columns.count(k)==0:
                
                sUtil.addColumn(tablename, con, k + ' ' + v)

                if testFlag:
                    print('')
                    print('[makePatternTable()] k : ', k)
                    print('[makePatternTable()] v : ', v)

        # 만들어진 패턴 테이블 이름 반환
        return tablename
            
    except:
        
        print("\n\n")
        print("[makeTestPatternTable()] Failed to makeTestPatternTable()!!!")



# 대표 패턴 테이블이 있으면 삭제하고 새로 생성
# 테이블이름 : 차트테이블명_rp_modifiedLen_matchLimit
# startNo : 일봉의 경우 1~31일(startNo=1), 15~14일(startNo=15) 의 2종류
# 칼럼 : representitivePattern(종가패턴+거래량패턴),
#        inflectionPoints(종가변곡점개수;거래량변곡점개수;종가변곡점위치, ...;거래량변곡점위치, ...),
#        weights(종가에만 적용. 소수점2째자리까지. 가중치11;가중치21,가중치22;가중치31, ...)
def makeTestRPTable(charttablename, con, startNo, modifiedLen=0, matchLimit=90):
    
    candleTime = '20'
    if charttablename.startswith('min'): candleTime = '14'
    elif charttablename.startswith('day'): candleTime = '8'
    elif charttablename.startswith('week'): candleTime = '8'
    elif charttablename.startswith('month'): candleTime = '8'
    
    modifiedLen_ = modifiedLen
    if modifiedLen==0:
        if charttablename.startswith('min5'): modifiedLen_ = min5Len
        elif charttablename.startswith('day'): modifiedLen_ = dayLen
        elif charttablename.startswith('week'): modifiedLen_ = weekLen
        elif charttablename.startswith('month'): modifiedLen_ = monthLen

    tablename = getRPTableName(charttablename, startNo, modifiedLen_, matchLimit)
    
    patternLen = modifiedLen_ * 2

    if testFlag:
        print('\n\n')
        print('[makeTestRPTable()]')

    try:

        columnstr = '''representitivePattern CHAR(''' + patternLen + ''') NOT NULL UNIQUE,
                       inflectionPoints VARCHAR2(100) NOT NULL,
                       weights VARCHAR2(200)'''

        sUtil.create(tablename, con, columnstr)

        # 만들어진 대표 패턴 테이블 이름 반환
        return tablename
            
    except:
        
        print("\n\n")
        print("[makeTestRPTable()] Failed to makeTestRPTable()!!!")



######################################################################################
# 기본 동작
######################################################################################



###
# 일봉 패턴 저장
def saveDayPattern(code, matchLimit=90):

    if testFlag:
        print('\n\n')
        print('[saveDayPattern()]')

    charttablename = 'day'
    
    modifiedLen = dayLen
    filename = stockDirectory + '/' + code + '.db'
    tmpfilename = stockDirectory + '/tmp_saveDayPattern.db'

    # chart 데이터를 하나씩 fetch하는 동안 db insert/delete 작업을 해야 하므로,
    # db 파일을 카피하여 tmp_saveDayPattern 파일을 만듬
    shutil.copy2(filename, tmpfilename)

    # 데이터를 읽고 쓰기 위해 원본 db 파일에 접속
    con1 = sqlite3.connect(filename)

    patterntablename = makePatternTable(charttablename, con1, modifiedLen)
    rptablename1 = makeRPTable(charttablename, con1, 1, modifiedLen, matchLimit)
    rptablename15 = makeRPTable(charttablename, con1, 15, modifiedLen, matchLimit)

    patterncolumns = ['candleTime', 'close', 'close_' + str(modifiedLen),
                      'volume', 'volume_' + str(modifiedLen)]

    if testFlag:
        testcon = splite3.connect('test.db')

        testrowtablename = makeTestRowTable(charttablename, testcon)
        testpatterntablename = makeTestPatternTable(charttablename, testcon, modifiedLen)
        testrptablename1 = makeTestRPTable(charttablename, testcon, 1, modifiedLen, matchLimit)
        testrptablename15 = makeTestRPTable(charttablename, testcon, 15, modifiedLen, matchLimit)

        rowcolumns = ['candleTime', 'close', 'volume']

    beforefetched = []
    nowmonth = ''
    beforeday = 0
    
    # [rp1_close, rp1_volume, rp15_close, rp15_volume]
    nowpattern = ['', '', '', '']

    rpList1 = getRPList(rptablename1, con1)
    rpList15 = getRPList(rptablename15, con1)

    first1Flag = True
    first15Flag = True

    candleTime1Flag = False
    candleTime15Flag = False
    candleTime1 = ''
    candleTime15 = ''

    # 패턴 테이블에 이미 저장되어 있어 그냥 건너뛸 수 있는 날짜 얻기
    loopstartdate = getSaveStartDate(patterntablename, con1)

    # 루프를 위해 카피한 tmp_saveDayPattern.db 파일에 접속
    con2 = sqlite3.connect(tmpfilename)
    cursor = con2.cursor()

    sql = 'SELECT candleTime, close, volume FROM ' + charttablename + ';'
    cursor.execute(sql)
    
    # cursor.fetchone() 이 끝날 때까지 루프
    while True:

        nowfetched = cursor.fetchone()
        if nowfetched==None: break

        nowdate = int(nowfetched[0])
        # 2014.8.1. 이전의 차트데이터는 불안정하므로 전부 버림
        if nowdate < 20140801: continue

        # 패턴 테이블에 이미 저장되어 있는 부분 건너뛰기
        if nowdate < loopstartdate: continue

        nowday = int(nowfetched[0][6:8])

        if candleTime1Flag:
            candleTime1 = nowfetched[0]
            candleTime1Flag = False

        elif candleTime15Flag:
            candleTime15 = nowfetched[0]
            candleTime15Flag = False

        if testFlag:
            print('[saveDayPattern()] nowfetched : ', nowfetched)

        # 아직 아무 패턴도 저장하지 않은 경우
        # nowmonth와 beforefetched만 설정하고 패스
        if nowmonth=='':
            nowmonth = nowfetched[0][0:6]
            beforeday = int(nowfetched[0][6:8])
            beforefetched = nowfetched

            if beforeday==1:
                first1Flag = False
                candleTime1Flag = True
                
            elif beforeday==15:
                first15Flag = False
                candleTime15Flag = True
            
            continue

        # month가 바뀐 경우 rp1 저장
        if nowmonth!=nowfetched[0][0:6]:
            
            # 패턴이 잘리는 최초의 경우, 저장은 안 함.
            if first1Flag: first1Flag = False

            else:

                modifiedCloseStr = getModifiedPattern(nowpattern[0], modifiedLen)
                modifiedVolumeStr = getModifiedPattern(nowpattern[1], modifiedLen)
                
                values = [candleTime1, # candleTime
                          int('1' + nowpattern[0], 2), int(modifiedCloseStr, 2), # close
                          int('1' + nowpattern[1], 2), int(modifiedVolumeStr, 2)] # volume

                if testFlag:
                    print('')
                    print('[saveDayPattern()] rp1 - values : ')
                    print(values)
                
                sUtil.insert(patterntablename, con1, patterncolumns, values)

                if testFlag:
                    testvalues = [candleTime1, # candleTime
                                  '1' + nowpattern[0], modifiedCloseStr, # close
                                  '1' + nowpattern[1], modifiedVolumeStr] # volume
                    sUtil.insert(testpatterntablename, testcon, patterncolumns, testvalues)

                rpList1 = insertSimplerRP(rptablename1, con1, rpList1, modifiedCloseStr, modifiedVolumeStr)

            nowmonth = nowfetched[0][0:6]
            nowpattern[0] = ''
            nowpattern[1] = ''
            candleTime1 = nowfetched[0]

        # 15일이 된 경우 rp15 저장
        elif (beforeday<15 and nowday>=15):

            # 패턴이 잘리는 최초의 경우, 저장은 안 함.
            if first15Flag: first15Flag = False

            else:

                modifiedCloseStr = getModifiedPattern(nowpattern[2], modifiedLen)
                modifiedVolumeStr = getModifiedPattern(nowpattern[3], modifiedLen)

                values = [candleTime15, # candleTime
                         int('1' + nowpattern[2], 2), int(modifiedCloseStr, 2), # close
                         int('1' + nowpattern[3], 2), int(modifiedVolumeStr, 2)] # volume

                if testFlag:
                    print('')
                    print('[saveDayPattern()] rp15 - values : ')
                    print(values)
                
                sUtil.insert(patterntablename, con1, patterncolumns, values)

                if testFlag:
                    testvalues = [candleTime15, # candleTime
                                  '1' + nowpattern[2], modifiedCloseStr, # close
                                  '1' + nowpattern[3], modifiedVolumeStr] # volume
                    sUtil.insert(testpatterntablename, testcon, patterncolumns, testvalues)

                rpList15 = insertSimplerRP(rptablename15, con1, rpList15, modifiedCloseStr, modifiedVolumeStr)

            nowpattern[2] = ''
            nowpattern[3] = ''
            candleTime15 = nowfetched[0]

        # close 패턴 추가
        p1 = '0'
        
        if beforefetched[1]>nowfetched[1]: p1 = '0'
            
        elif beforefetched[1]<nowfetched[1]: p1 = '1'
            
        else:
            if len(nowpattern[0])>0: p1 = nowpattern[0][len(nowpattern[0])-1]
            elif len(nowpattern[2])>0: p1 = nowpattern[2][len(nowpattern[2])-1]
            
        nowpattern[0] += p1
        nowpattern[2] += p1

        # volume 패턴 추가
        p2 = '0'
        
        if beforefetched[2]>nowfetched[2]: p2 = '0'
            
        elif beforefetched[2]<nowfetched[2]: p2 = '1'
            
        else:
            if len(nowpattern[1])>0: p2 = nowpattern[1][len(nowpattern[1])-1]
            elif len(nowpattern[3])>0: p2 = nowpattern[3][len(nowpattern[3])-1]
            
        nowpattern[1] += p2
        nowpattern[3] += p2

        if testFlag:
            print('[saveDayPattern()] nowpattern : ', nowpattern)
            
            sUtil.insert(testrowtablename, testcon, rowcolumns, [nowfetched[0], p1, p2])
                
        # before 데이터 업데이트
        beforeday = nowday
        beforefetched = nowfetched

    # con1, con2를 해제하고 임시로 카피했던 파일 삭제
    con1.close()
    con2.close()
    os.remove(tmpfilename)

    if testFlag:
        testcon.close()



    
