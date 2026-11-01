"""nalssam 스타일 PPTX 헬퍼 (python-pptx 1.x). 16:9 = 13.333 x 7.5 in. 모든 좌표 단위는 inch."""
from pptx import Presentation
from pptx.util import Inches as I, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

NAVY = '132C3D'; TEAL = '18766B'; GRAY = '586875'; BG = 'FBFAF6'        # 제목·강조·보조글·배경
CORAL = 'D9734E'; LINE = 'E4DFD3'; CARD = 'FFFFFF'; TEAL_SOFT = 'E3F0EC'  # 포인트·테두리·카드·민트 띠
PAPER = 'F3F0E8'; ZEBRA = 'F5F2EA'                                        # 종이색 상자·표 줄무늬
CFG = {'foot': '행사명  |  nalssam 박준호  |  2026. 0. 0.'}                 # 바닥글: 덱마다 바꾼다


def rgb(h): return RGBColor.from_string(h)


def _flat(sh):
    """도형의 테마 스타일(p:style: 그림자·테두리 참조)을 지운다 → 어느 프로그램에서 열어도 그림자 없이 납작하게."""
    st = sh._element.find(qn('p:style'))
    if st is not None: sh._element.remove(st)


def new_deck(ref=None):
    """ref가 있으면 그 덱(이전 날쌤 덱)의 틀만 쓰고 장표를 비운다. 없으면 빈 16:9 덱."""
    if ref:
        prs = Presentation(ref); lst = prs.slides._sldIdLst
        for sid in list(lst):
            prs.part.drop_rel(sid.get(qn('r:id'))); lst.remove(sid)
        return prs
    prs = Presentation(); prs.slide_width = 12192000; prs.slide_height = 6858000
    return prs


def _blank(prs):
    for l in prs.slide_layouts:
        if l.name.strip().lower() in ('blank', '빈 화면'): return l
    return prs.slide_layouts[0] if len(prs.slide_layouts) == 1 else prs.slide_layouts[-1]


def add_slide(prs):
    s = prs.slides.add_slide(_blank(prs))
    for ph in list(s.placeholders): ph._element.getparent().remove(ph._element)
    f = s.background.fill; f.solid(); f.fore_color.rgb = rgb(BG)
    return s


def _font(run, size, bold, color, face):
    f = run.font; f.size = Pt(size); f.bold = bold; f.color.rgb = rgb(color); f.name = face
    rPr = run._r.get_or_add_rPr(); rPr.set('lang', 'ko-KR')
    for tag in ('a:ea', 'a:cs'):                       # 한글(ea)·복합(cs) 글꼴도 같은 이름으로
        el = rPr.find(qn(tag))
        if el is None: el = etree.SubElement(rPr, qn(tag))
        el.set('typeface', face)


def text(s, x, y, w, h, content, size=14, bold=False, color=NAVY, face='Pretendard',
         align='l', anchor='t', lnspc=1.14, spc_after=0):
    """content: str('\\n'=새 문단) 또는 문단 리스트. 문단 = str 또는 [(글, {size,bold,color,face}), ...]"""
    tb = s.shapes.add_textbox(I(x), I(y), I(w), I(h)); tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
    paras = content.split('\n') if isinstance(content, str) else content
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}[align]
        p.line_spacing = lnspc; p.space_after = Pt(spc_after)
        for t, o in ([(para, {})] if isinstance(para, str) else para):
            r = p.add_run(); r.text = t
            _font(r, o.get('size', size), o.get('bold', bold), o.get('color', color), o.get('face', face))
    return tb


def header(s, kicker, title, sub=None, tsize=29, compact=False):
    """키커(틸 10pt) + 결론 한 문장 제목(ExtraBold 29pt) + 부제(13pt). compact=True: 본문이 y=2.0부터 시작하는 빽빽한 장표용"""
    text(s, 0.58, 0.35, 12.15, 0.28, kicker, 10, True, TEAL)
    text(s, 0.58, 0.78 if compact else 0.85, 12.22, 0.6 if compact else 1.0, title, 28 if compact else tsize, False, NAVY, 'Pretendard ExtraBold')
    if sub: text(s, 0.58, 1.5 if compact else 1.83, 12.15, 0.32 if compact else 0.39, sub, 13, False, GRAY)


def footer(s, n, total):
    """n: 정수 또는 '13-1' 같은 문자열"""
    text(s, 0.58, 7.14, 11.0, 0.19, CFG['foot'], 9, False, GRAY)
    lab = f'{n:02d}' if isinstance(n, int) else n
    text(s, 11.61, 7.07, 1.3, 0.32, f'{lab} / {total}', 10, False, GRAY, 'Pretendard Medium', align='r')


def _round(pic, adj=6000, line=None):
    geom = pic._element.spPr.find(qn('a:prstGeom')); geom.set('prst', 'roundRect')
    av = geom.find(qn('a:avLst'))
    for c in list(av): av.remove(c)
    gd = etree.SubElement(av, qn('a:gd')); gd.set('name', 'adj'); gd.set('fmla', f'val {adj}')
    if line: pic.line.color.rgb = rgb(line); pic.line.width = Pt(0.75)


def pic(s, path, x, y, w, h, mode='contain', anchor='c', adj=6000, line=None, valign='c', alt=None):
    """contain: 비율 유지하며 상자 안에 / cover: 상자를 채우고 넘치는 부분은 크롭(anchor l/c/r, t/c/b).
    adj: 모서리 둥글기(None=직각). 일러스트(배경 투명 느낌)는 adj=None, 스크린샷은 adj=5000, line=LINE"""
    iw, ih = Image.open(path).size; ar = iw / ih; br = w / h
    if mode == 'contain':
        pw, ph = (w, w / ar) if ar > br else (h * ar, h)
        p = s.shapes.add_picture(path, I(x + (w - pw) / 2), I({'t': y, 'c': y + (h - ph) / 2, 'b': y + h - ph}[valign]), I(pw), I(ph))
    else:
        p = s.shapes.add_picture(path, I(x), I(y), I(w), I(h))
        if ar > br:
            cut = 1 - br / ar; l = {'l': 0, 'c': cut / 2, 'r': cut}[anchor if anchor in 'lcr' else 'c']
            p.crop_left = l; p.crop_right = cut - l
        else:
            cut = 1 - ar / br; t = {'t': 0, 'c': cut / 2, 'b': cut}[anchor if anchor in 'tcb' else 'c']
            p.crop_top = t; p.crop_bottom = cut - t
    if adj is not None: _round(p, adj, line)
    if alt: p._element.nvPicPr.cNvPr.set('descr', alt)          # 대체 텍스트(접근성)
    return p


def box(s, x, y, w, h, fill=CARD, line=LINE, radius=0.08, lw=0.75, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sh = s.shapes.add_shape(shape, I(x), I(y), I(w), I(h))
    if fill: sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    else: sh.fill.background()
    if line: sh.line.color.rgb = rgb(line); sh.line.width = Pt(lw)
    else: sh.line.fill.background()
    sh.shadow.inherit = False; _flat(sh)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: sh.adjustments[0] = radius
    sh.text_frame.text = ''
    return sh


def chip(s, x, y, w, h, label, fill=TEAL_SOFT, color=TEAL, size=10, bold=True, line=None):
    b = box(s, x, y, w, h, fill=fill, line=line, radius=0.5); tf = b.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = label; _font(r, size, bold, color, 'Pretendard')
    return b


def hline(s, x1, y1, x2, y2, color=LINE, w=1.0, dash=False):
    ln = s.shapes.add_connector(1, I(x1), I(y1), I(x2), I(y2))
    ln.line.color.rgb = rgb(color); ln.line.width = Pt(w)
    if dash: ln.line.dash_style = 4
    _flat(ln)
    return ln


def dot(s, cx, cy, d=0.16, fill=TEAL):
    sh = s.shapes.add_shape(MSO_SHAPE.OVAL, I(cx - d / 2), I(cy - d / 2), I(d), I(d))
    sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill); sh.line.fill.background(); sh.shadow.inherit = False; _flat(sh)
    return sh


def notes(s, body): s.notes_slide.notes_text_frame.text = body


# ───────── 장표 유형 헬퍼 ─────────
def cover(prs, kicker, title, lines, byline, hero=None, tsize=54):
    """표지: 키커 / 54pt ExtraBold 제목 / 왼쪽 26pt 굵은 문구(list) / 오른쪽 히어로 / 틸 21pt 소속·이름(list)"""
    s = add_slide(prs)
    text(s, 0.58, 0.35, 12.15, 0.28, kicker, 10, True, TEAL)
    text(s, 0.58, 0.85, 12.22, 0.9, title, tsize, False, NAVY, 'Pretendard ExtraBold')
    if hero: pic(s, hero, 5.42, 2.31, 7.33, 4.13, 'contain', adj=None)
    text(s, 0.64, 2.46, 4.78, 2.35, lines, 26, True, NAVY)
    text(s, 0.58, 5.59, 6.51, 0.9, byline, 21, True, TEAL)
    text(s, 0.58, 7.14, 11.81, 0.19, CFG['foot'], 9, False, GRAY)
    return s


def cards3(s, items, img_y=2.47, img_h=3.12, title_y=5.76, xs=(0.58, 4.75, 8.92), w=3.83):
    """3열 카드. items: (이미지경로|None, 'contain'|'cover', 제목, 설명[, {h,dy,anchor,adj,line,valign}])"""
    for (path, mode, title, desc, *o), x in zip(items, xs):
        o = o[0] if o else {}
        if path:
            if mode == 'cover':
                ch = o.get('h', 2.6)
                pic(s, path, x, img_y + (img_h - ch) / 2 + o.get('dy', 0), w, ch, 'cover', o.get('anchor', 'c'),
                    adj=o.get('adj', 6000), line=o.get('line', LINE))
            else:
                pic(s, path, x, img_y, w, img_h, 'contain', adj=None, valign=o.get('valign', 'c'))
        text(s, x, title_y, w, 0.42, title, 20, True, NAVY)
        text(s, x, title_y + 0.5, w, 0.6, desc, 14, False, GRAY)


def banner(s, msg, y=6.1, label=None, x=0.58, w=12.17, h=0.58, size=15):
    """민트 결론 띠(장표의 한 줄 결론). label을 주면 '라벨   본문'(틸+네이비) 두 색."""
    box(s, x, y, w, h, TEAL_SOFT, None, 0.45)
    runs = [(label + '   ', {'color': TEAL}), (msg, {'color': NAVY})] if label else [(msg, {})]
    text(s, x, y, w, h, [runs], size, True, TEAL, align='c', anchor='m')


def timeline(s, cols, xs=(0.58, 3.66, 6.74, 9.82), cw=2.93, img_y=2.3, img_h=2.35, yl=4.86, last_coral=True, yw=0.62):
    """가로 타임라인(4칸). cols: (이미지|None, '2023', 제목, 설명). 마지막 칸 점은 코랄."""
    hline(s, 0.9, yl, 12.4, yl, TEAL, 1.5, dash=True)
    for i, ((img, yr, t, d), x) in enumerate(zip(cols, xs)):
        c = CORAL if (last_coral and i == len(cols) - 1) else TEAL
        if img: pic(s, img, x, img_y, cw, img_h, 'contain', adj=None)
        dot(s, x + 0.12, yl, 0.2, c)
        yb = text(s, x + 0.27, yl - 0.14, yw, 0.3, yr, 14, True, c, align='c')
        yb.fill.solid(); yb.fill.fore_color.rgb = rgb(BG)          # 점선이 글자를 가리지 않게
        text(s, x, yl + 0.32, cw, 0.4, t, 18, True, NAVY)
        text(s, x, yl + 0.76, cw, 0.7, d, 13, False, GRAY)


def table(s, heads, rows, cx=(0.58, 3.25, 6.0, 10.1), cw=(2.6, 2.7, 4.0, 2.65), y=2.38, rh=0.66, strong=2, number=True):
    """줄무늬 비교표(4열 기본). strong 열은 진한 글씨(핵심), 나머지는 회색. 첫 열은 '01 ' 번호."""
    for x, w, h in zip(cx, cw, heads): text(s, x + 0.1, y, w, 0.3, h, 12, True, TEAL)
    hline(s, 0.58, y + 0.38, 12.75, y + 0.38, TEAL, 1.25)
    for i, r in enumerate(rows):
        yy = y + 0.5 + i * rh
        if i % 2 == 0: box(s, 0.58, yy - 0.06, 12.17, rh - 0.04, ZEBRA, None, 0.15)
        for j, (x, w, t) in enumerate(zip(cx, cw, r)):
            if j == 0:
                text(s, x + 0.1, yy + 0.1, w, 0.4, [[(f'{i + 1:02d} ' if number else '', {'color': TEAL}), (t, {})]], 14, True, NAVY)
            else:
                text(s, x + 0.1, yy + 0.12, w - 0.1, 0.45, t, 12.5, j == strong, NAVY if j == strong else GRAY)


def steps(s, items, x=5.45, y=2.45, pitch=1.18, w=6.2):
    """세로 단계(칩 + 굵은 제목 + 설명). items: (칩 라벨 '1주', 제목, 설명). 마지막 칩은 진한 틸."""
    for i, (c, t, d) in enumerate(items):
        yy = y + i * pitch; last = i == len(items) - 1
        chip(s, x, yy + 0.05, 0.9, 0.36, c, TEAL if last else TEAL_SOFT, 'FFFFFF' if last else TEAL, 12)
        text(s, x + 1.1, yy, w, 0.42, t, 19, True, NAVY)
        text(s, x + 1.1, yy + 0.48, w, 0.45, d, 13, False, GRAY)


def step_cards(s, steps4, guard=None, y=2.0, h=3.78):
    """4단계 카드(수업 적용 예시용). steps4: (칩, 장면, AI가 하는 일, 예시 요청, 도구). guard: 아래 '교사가 지키는 것' 띠."""
    for i, (c, scene, ai, ask, tool) in enumerate(steps4):
        x = 0.58 + i * 3.08; w = 2.88
        box(s, x, y, w, h, CARD, LINE, 0.06)
        chip(s, x + 0.2, y + 0.2, 1.45, 0.3, c, TEAL_SOFT, TEAL, 10.5)
        text(s, x + 0.2, y + 0.62, w - 0.35, 0.36, scene, 15, True, NAVY)
        text(s, x + 0.2, y + 1.02, w - 0.35, 0.95, [[('AI  ', {'bold': True, 'color': TEAL}), (ai, {})]], 11.5, False, GRAY, lnspc=1.2)
        box(s, x + 0.15, y + 2.02, w - 0.3, 1.2, PAPER, None, 0.1)
        text(s, x + 0.3, y + 2.1, w - 0.55, 0.25, '예시 요청', 9, True, CORAL)
        text(s, x + 0.3, y + 2.36, w - 0.55, 0.84, f'“{ask}”', 10.5, False, NAVY, lnspc=1.2)
        chip(s, x + 0.2, y + 3.34, min(w - 0.4, 0.3 + 0.105 * len(tool)), 0.28, tool, 'FFFFFF', GRAY, 9.5, True, line=LINE)
        if i < len(steps4) - 1: text(s, x + w - 0.02, y + h / 2 - 0.2, 0.24, 0.4, '›', 18, True, GRAY, align='c')
    if guard: banner(s, guard, y=6.02, label='교사가 지키는 것', size=13, h=0.6)


def rows_arrow(s, pairs, y=2.38, pitch=0.7, w=8.25, last_hi=True):
    """'이전 → 이후' 요약 줄. pairs: (이전, 이후). 마지막 줄은 민트 강조(결론)."""
    for i, (a, b) in enumerate(pairs):
        yy = y + i * pitch; hi = last_hi and i == len(pairs) - 1
        box(s, 0.58, yy, w, 0.58, TEAL_SOFT if hi else CARD, None if hi else LINE, 0.3)
        text(s, 0.82, yy, 2.5, 0.58, a, 14, False, GRAY, anchor='m')
        text(s, 3.2, yy, 0.4, 0.58, '→', 15, True, TEAL, anchor='m')
        text(s, 3.65, yy, w - 3.15, 0.58, b, 15, True, TEAL if hi else NAVY, anchor='m')


def case_grid(s, cases, ncol=3, y0=2.4, dx=4.17, dy=2.15):
    """번호 카드 격자(사례 지도). cases: (제목, 한 줄 설명, 도구 칩). 앞 절반 번호는 틸, 뒤 절반은 코랄."""
    for i, (a, b, c) in enumerate(cases):
        x = 0.58 + (i % ncol) * dx; y = y0 + (i // ncol) * dy
        box(s, x, y, 3.83, 1.92, CARD, LINE, 0.08)
        text(s, x + 0.25, y + 0.2, 1.0, 0.4, f'{i + 1:02d}', 20, True, TEAL if i < len(cases) / 2 else CORAL, 'Pretendard ExtraBold')
        text(s, x + 0.25, y + 0.62, 3.4, 0.4, a, 18, True, NAVY)
        text(s, x + 0.25, y + 1.03, 3.4, 0.4, b, 12.5, False, GRAY)
        chip(s, x + 0.25, y + 1.43, min(0.2 + len(c) * 0.11, 3.3), 0.3, c, TEAL_SOFT, TEAL, 10)


def idea_grid(s, items, x0=5.05, y0=2.35, ncol=2, w=3.7, h=1.78, dx=3.9, dy=1.95):
    """2x2 아이디어 카드(적용 방안). items: (틸 굵은 제목, 네이비 설명)"""
    for i, (t, d) in enumerate(items):
        x = x0 + (i % ncol) * dx; y = y0 + (i // ncol) * dy
        box(s, x, y, w, h, CARD, LINE, 0.08)
        text(s, x + 0.22, y + 0.18, w - 0.4, 0.4, t, 15, True, TEAL)
        text(s, x + 0.22, y + 0.62, w - 0.4, h - 0.7, d, 12, False, NAVY, lnspc=1.22)


def refs(s, rows, y=2.0, pitch=0.78):
    """참고문헌 장. rows: (분류, 출처 문장). 일러스트 생성 도구와 상표 고지 한 줄도 넣는다."""
    for i, (a, b) in enumerate(rows):
        text(s, 0.58, y + i * pitch, 2.2, 0.35, a, 13, True, TEAL)
        text(s, 2.8, y + i * pitch, 9.95, 0.7, b, 12, False, NAVY, lnspc=1.2)


def alpha(shape, pct):
    """채움색 투명도(pct % 불투명). 벤다이어그램 원 등에 사용"""
    clr = shape.fill._xPr.find(qn('a:solidFill'))[0]
    etree.SubElement(clr, qn('a:alpha')).set('val', str(int(pct * 1000)))


def fullbleed(prs, s, path, anchor='c'):
    """슬라이드 전체를 덮는 이미지(스토리 장면). 머리말·바닥글을 넣지 않는다."""
    return pic(s, path, 0, 0, prs.slide_width / 914400, prs.slide_height / 914400, 'cover', anchor, adj=None)


def qr_card(s, qr_path, x=0.58, y=4.85, size=1.75):
    box(s, x, y, size, size, CARD, LINE, 0.08)
    pic(s, qr_path, x + 0.1, y + 0.1, size - 0.2, size - 0.2, 'contain', adj=None)


def make_qr(url, out='qr.png', scale=12):
    """QR 생성 + 디코드 검증(zxingcpp > cv2). 검증 실패 시 예외."""
    import qrcode
    qrcode.make(url, box_size=scale, border=2).convert('RGB').save(out)
    got = None
    try:
        import zxingcpp; r = zxingcpp.read_barcodes(Image.open(out)); got = r[0].text if r else None
    except ImportError:
        import cv2; got = cv2.QRCodeDetector().detectAndDecode(cv2.imread(out))[0] or None
    assert got == url, f'QR 디코드 불일치: {got!r}'
    return out
