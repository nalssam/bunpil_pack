"""build.py 뼈대(예시 3장). 이 파일을 작업 폴더에 build.py 로 복사해 장을 늘린다. 이미지가 없으면 글자만으로 만든다."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '.')
from nalssam_lib import *
def img(p): return p if os.path.exists(p) else None   # 생성 이미지가 아직 없으면 빈 자리로
CFG['foot'] = '○○교육지원청 교원연수  |  ○○○  |  2026. 0. 0.(토)'   # 행사명 | 강사 | 날짜
prs = new_deck()                  # 이전 날쌤 덱이 있으면 new_deck('이전.pptx'): 틀만 쓰고 장표는 비운다
TOTAL = 3; n = 0
def slide():
    global n; n += 1; s = add_slide(prs)
    if n > 1: footer(s, n, TOTAL)
    return s

s = cover(prs, '○○교육지원청  /  2026. 0. 0.(토) 10:00~12:00', 'AI Agent 시대, 교실은?',
          ['선생님의 아이디어를', 'AI 비서와 함께'], ['○○초등학교 ○○○', '소속·직함'], img('gen/hero_fx.jpg')); n += 1
notes(s, '1장 · 1분 · 10:00~10:01\n\n안녕하세요. ○○초 교사 ○○○입니다. 오늘은 AI Agent 시대에 교실이 어떻게 달라지는지 함께 보겠습니다.')
s = slide(); header(s, '01 오늘의 질문', 'AI는 교사의 무엇을 바꾸고, 무엇을 남겨 둘까요?', '세 가지 질문을 따라갑니다.')
cards3(s, [(img('gen/a_fx.jpg'), 'contain', '01 일하는 방식', '프롬프트에서 환경 설정으로'), (img('gen/b_fx.jpg'), 'contain', '02 교수전략', '설계 · 자료 · 평가'), (img('gen/c_fx.jpg'), 'contain', '03 우리 교실', '월요일에 시작할 한 가지')])
notes(s, '2장 · 1분 · 10:01~10:02\n\n먼저 질문 하나를 드립니다. AI는 교사의 무엇을 바꾸고, 무엇을 남겨 둘까요? 세 가지를 따라가겠습니다.')
s = slide(); header(s, 'THANK YOU', '감사합니다')          # 바닥글·쪽번호는 slide() 가 단다. QR 은 qr_card(s, make_qr(url))
notes(s, '3장 · 1분 · 10:02~10:03\n\n끝까지 함께해 주셔서 감사합니다. 화면의 QR 코드로 오늘 자료와 연수 소식을 보실 수 있습니다.')
assert n == TOTAL, n
prs.save('raw.pptx')              # → python embed_fonts.py raw.pptx 최종.pptx
# 장 끼워 넣기: 맨 뒤에 만든 장을 13번째 뒤로 →  lst = prs.slides._sldIdLst; el = list(lst)[-1]; lst.remove(el); lst.insert(13, el)
