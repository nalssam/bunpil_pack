"""납품 전 자동 점검 (렌더링 눈 확인을 대신하지 않는다).
사용: python qa.py deck.pptx [--ban 단어1,단어2] [--no-notes]   · 오류가 있으면 종료코드 1
점검: 글꼴 이름 / 글자 넘침 추정 / 슬라이드 밖 도형 / 대본 유무 / 쪽번호 분모 / 제목 길이 / 금칙어(이전 행사 단어)"""
import sys, re, os
from pptx import Presentation
from PIL import ImageFont

FONTDIR = os.path.expanduser('~/.local/share/fonts')
OK_FACES = {'Pretendard', 'Pretendard ExtraBold', 'Pretendard Medium'}
LH = 1.193                                  # Pretendard 한 줄 높이 = 글자 크기의 1.193배
_fc = {}


def font(face, bold):
    n = 'ExtraBold' if 'ExtraBold' in face else 'Medium' if 'Medium' in face else 'Bold' if bold else 'Regular'
    if n not in _fc: _fc[n] = ImageFont.truetype(os.path.join(FONTDIR, f'Pretendard-{n}.ttf'), 100)
    return _fc[n]


def tokens(p):
    """문단을 (글자, 폭 함수 인자) 단어 토큰으로: 공백 기준, 서식은 run별로 유지"""
    out = []
    for r in p.runs:
        face = r.font.name or 'Pretendard'; sz = r.font.size.pt if r.font.size else 18
        for part in re.findall(r'\S+|\s+', r.text):
            out.append((part, font(face, bool(r.font.bold)), sz))
    return out


def para_lines(p, w_in):
    lines, cur = 1, 0.0
    for part, f, sz in tokens(p):
        wd = f.getlength(part) / 100 * sz / 72
        if part.isspace():
            cur += wd; continue
        if cur + wd <= w_in + 0.01: cur += wd; continue
        if wd > w_in:                                      # 한 단어가 한 줄보다 길면 글자 단위로 쪼개짐
            lines += int(wd // w_in) + (1 if cur > 0 else 0); cur = wd % w_in; continue
        lines += 1; cur = wd
    return lines


def text_height(sh):
    tf = sh.text_frame
    w = (sh.width - tf.margin_left - tf.margin_right) / 914400
    h = 0.0
    for p in tf.paragraphs:
        sz = max([r.font.size.pt for r in p.runs if r.font.size] or [18])
        ls = p.line_spacing if isinstance(p.line_spacing, float) else 1.0
        h += para_lines(p, w) * sz * LH * ls / 72 + (p.space_after.pt / 72 if p.space_after else 0)
    return h + (tf.margin_top + tf.margin_bottom) / 914400


args = sys.argv[1:]; ban = []; need_notes = '--no-notes' not in args
if '--ban' in args: ban = [b for b in args[args.index('--ban') + 1].split(',') if b]
prs = Presentation(args[0]); W, H = prs.slide_width, prs.slide_height
errs, warns, totals = [], [], set()
for i, s in enumerate(prs.slides, 1):
    full = ''
    for sh in s.shapes:
        if sh.left is not None and not (sh.left == 0 and sh.top == 0 and sh.width >= W - 10):      # 전면 이미지는 제외
            if sh.left < -9144 or sh.top < -9144 or sh.left + sh.width > W + 9144 or sh.top + sh.height > H + 9144:
                warns.append(f'{i}장 슬라이드 밖으로 나감: {sh.name}')
        if not sh.has_text_frame or not sh.text_frame.text.strip(): continue
        t = sh.text_frame.text; full += t + '\n'
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if (r.font.name or 'Pretendard') not in OK_FACES:
                    warns.append(f'{i}장 허용 밖 글꼴 "{r.font.name}": {r.text[:20]}'); break
        m = re.fullmatch(r'(\S+) / (\d+)', t.strip())
        if m: totals.add(m.group(2))
        try:
            need = text_height(sh)
            if need > sh.height / 914400 * 1.12 + 0.06:
                warns.append(f'{i}장 글자 넘침 추정(필요 {need:.2f}in > 상자 {sh.height / 914400:.2f}in): {t[:28]!r}')
        except Exception as e:
            warns.append(f'{i}장 높이 추정 실패: {t[:20]!r} ({e})')
        if any(r.font.name == 'Pretendard ExtraBold' and r.font.size and 24 <= r.font.size.pt <= 32 for p in sh.text_frame.paragraphs for r in p.runs) \
                and len(t.replace('\n', '')) > 36:
            warns.append(f'{i}장 제목이 36자 초과(결론 한 문장 30자 안팎): {t[:20]}…')
    note = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ''
    if need_notes and not note: errs.append(f'{i}장 대본(메모)이 비어 있음')
    elif need_notes and len(note) < 40: warns.append(f'{i}장 대본이 40자 미만(의도한 짧은 장이면 무시)')
    for b in ban:
        if b in full or b in note: errs.append(f'{i}장 금칙어 "{b}" 남아 있음')
if len(totals) > 1: warns.append(f'쪽번호 분모가 제각각: {sorted(totals)}')
for e in errs: print('오류', e)
for w in warns: print('주의', w)
print(f'장표 {len(prs.slides)}장 · 오류 {len(errs)} · 주의 {len(warns)}')
sys.exit(1 if errs else 0)
