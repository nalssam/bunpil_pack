"""기존 덱의 '문구만' 바꿀 때(서식·이미지·배치 유지). from edit_helpers import *  →  prs = Presentation(src)
순서: find로 도형 찾기(정확히 1개) → set_text/sub로 교체 → 바닥글·쪽번호·대본 일괄 → qa.py --ban 으로 옛 단어 점검."""
import copy
from lxml import etree
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
IGN = {'lang', 'altLang', 'dirty', 'err', 'noProof', 'smtClean', 'smtId'}


def _sig(r):
    rp = r._r.find(A + 'rPr')
    if rp is None: return ''
    c = copy.deepcopy(rp)
    for k in list(c.attrib):
        if k in IGN: del c.attrib[k]
    return etree.tostring(c)


def merge_runs(p):
    """같은 서식으로 잘게 쪼개진 인접 run을 합친다(모양 변화 없음). 교체 전에 항상 호출."""
    runs = p.runs; i = 0
    while i < len(runs) - 1:
        a, b = runs[i], runs[i + 1]
        if a._r.getnext() is b._r and _sig(a) == _sig(b):
            a.text += b.text; b._r.getparent().remove(b._r); runs = p.runs
        else: i += 1


def find(prs, si, needle, exact=False):
    """si장에서 needle이 든 도형. 0개 또는 2개 이상이면 중단(엉뚱한 곳을 고치지 않게)."""
    hits = [sh for sh in prs.slides[si - 1].shapes if sh.has_text_frame and
            ((sh.text_frame.text.strip() == needle) if exact else (needle in sh.text_frame.text))]
    if len(hits) != 1: raise SystemExit(f'[find] {si}장 "{needle}" -> {len(hits)}개')
    return hits[0]


def set_text(sh, paras):
    """문단 리스트로 통째 교체. 문단마다 첫 run 서식을 유지, 문단 수가 늘면 마지막 문단을 복제."""
    tf = sh.text_frame; plist = list(tf.paragraphs)
    for i, p in enumerate(plist):
        if i >= len(paras): p._p.getparent().remove(p._p); continue
        merge_runs(p)
        for br in p._p.findall(A + 'br'): p._p.remove(br)
        runs = p.runs
        if runs:
            runs[0].text = paras[i]
            for r in runs[1:]: r._r.getparent().remove(r._r)
    if len(paras) > len(plist):
        last = tf.paragraphs[-1]._p
        for t in paras[len(plist):]:
            n = copy.deepcopy(last); last.addnext(n); last = n
            rs = n.findall(A + 'r')
            for r in rs[1:]: n.remove(r)
            rs[0].find(A + 't').text = t


def sub(sh, pairs):
    """run 안의 낱말만 바꾼다([(옛, 새), ...]). 못 찾으면 예외."""
    for p in sh.text_frame.paragraphs: merge_runs(p)
    for o, n in pairs:
        hit = False
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if o in r.text: r.text = r.text.replace(o, n); hit = True
        if not hit: raise SystemExit(f'[sub] "{o}" 없음: {sh.text_frame.text[:30]!r}')
