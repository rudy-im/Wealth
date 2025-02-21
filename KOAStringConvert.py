#-*- coding:utf-8 -*-




# KOA Studio에서 실시간 목록을 dic화
def realConvert(koaRealString):

    s = koaRealString.strip()
    
    # koareal은 '공백 [번호] = 내용\n' 형식의 나열

    # 1. 줄바꿈에 따라 split
    l1 = s.split('\n')

    # 2. 각 줄을 ['[번호]', '내용'] 으로 나눔. (단, 공백도 있음)
    l2 = [i.split('=') for i in l1]

    # 3. 각 줄을 (번호, 내용)의 튜플화
    l3 = [(num.strip()[1:-1], field.strip()) for num, field in l2]

    # 4. dic 형식의 문자열화
    ret = 'dic = {'

    for num, field in l3:

        ret += "'"
        ret += field
        ret += "':"
        ret += num
        ret += ", "

    ret = ret[:-2] + '}'

    return ret

# realConvert 사용

s = '''[9201] = 계좌번호
	[9001] = 종목코드,업종코드
	[917] = 신용구분
	[916] = 대출일
	[302] = 종목명
	[10] = 현재가
	[930] = 보유수량
	[931] = 매입단가
	[932] = 총매입가
	[933] = 주문가능수량
	[945] = 당일순매수량
	[946] = 매도/매수구분
	[950] = 당일총매도손일
	[951] = 예수금
	[27] = (최우선)매도호가
	[28] = (최우선)매수호가
	[307] = 기준가
	[8019] = 손익율
	[957] = 신용금액
	[958] = 신용이자
	[918] = 만기일
	[990] = 당일실현손익(유가)
	[991] = 당일실현손익률(유가)
	[992] = 당일실현손익(신용)
	[993] = 당일실현손익률(신용)
	[959] = 담보대출수량
	[924] = Extra Item
'''

print(realConvert(s))
