import time, datetime
from datetime import timedelta

testFlag = False

# 현재 시간을 hhmmss 형식으로 반환.
# rettype이 str이면 문자열, 그 외엔 int로 반환.
# TODO :: str 변환 시 6자리로 고정(예 : 093241)
def getNowTime(rettype='int'):
    localtime = time.localtime()
    now = localtime.tm_hour * 10000 + localtime.tm_min * 100 + localtime.tm_sec

    if testFlag:
        print("[getNowTime()] now : " + str(now))

    if rettype == 'str':
        return str(now)
    else:
        return now



# withDataFunc==True 이면 DB의 DATE 형에 저장 가능한 현재시간 문자열 반환
#   예 : date("strf")
def getToday(strf='%Y-%m-%d', withDateFunc = False):
    
    ret = datetime.datetime.now().strftime(strf)
    if withDateFunc: ret = 'date("' + ret + '")'
    
    if testFlag:
        print("\n\n")
        print("[now()] ret : " + ret)
        
    return ret


# timeA에서 timeB를 더하거나 뺀 값 얻기
# 매개변수와 반환값 시간은 (h)hmmss 형식의 숫자
# timeB의 부호로 덧셈/뺄셈 결정
def timeCalc(timeA, timeB):
    
    a = timedelta(hours = int(timeA/10000),
                  minutes = int((timeA%10000)/100),
                  seconds = timeA%100)

    tmpB = abs(timeB)
    b = timedelta(hours = int(tmpB/10000),
                  minutes = int((tmpB%10000)/100),
                  seconds = tmpB%100)

    if timeB>0: calcdelta = a + b
    else: calcdelta = a - b

    l = str(calcdelta).split(':')
    ret = int(l[0]) * 10000 + int(l[1]) * 100 + int(l[2])
    
    return ret


# 시간을 hh:mm:ss 형식으로 반환
# time은 hhmmss 형식의 숫자
def timeFormat(time):
    
    hour = int(time/10000)
    minute = int(time%10000/100)
    sec = time%100

    ret = '{:02d}:{:02d}:{:02d}'.format(hour, minute, sec)
    return ret
