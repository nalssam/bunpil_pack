#!/usr/bin/env python3
"""페이퍼 크래프트 전개도 SVG 생성기 (표준 라이브러리만 사용, pip 불필요).

A4(210 x 297 mm) 세로 SVG를 만든다. 선 규약:
  실선(class="cut")    자르는 선
  점선(class="fold")   접는 선
  회색 면(class="glue") 풀칠하는 날개(풀칠 면)
  글자(class="label")  면 이름(선택)

사용 예:
  python3 net.py cube --size 50 --labels "수성,금성,지구,화성,목성,토성" -o cube.svg
  python3 net.py cuboid --width 60 --height 40 --depth 30 -o cuboid.svg
  python3 net.py prism --size 40 --height 70 -o prism.svg
  python3 net.py cylinder --radius 25 --height 60 -o cylinder.svg
  python3 net.py pyramid --size 60 --height 50 -o pyramid.svg

모든 길이의 단위는 mm이다. 전개도가 용지(여백 10 mm)보다 크면 자동으로 줄이고
줄인 비율을 표준 오류(stderr)에 알린다.
"""
import argparse
import math
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

PAGE_W, PAGE_H = 210.0, 297.0
MARGIN = 10.0
HEADER_H = 24.0      # 제목 영역 높이
FOOTER_H = 16.0      # 범례 영역 높이
FONT = "Malgun Gothic, Apple SD Gothic Neo, Noto Sans KR, sans-serif"

STYLE = {
    "cut": 'stroke="#000000" stroke-width="0.4" fill="none" stroke-linecap="round"',
    "fold": ('stroke="#000000" stroke-width="0.3" fill="none" '
             'stroke-dasharray="2 1.5" stroke-linecap="butt"'),
    "glue": 'fill="#d4d4d4" stroke="none"',
}

SHAPE_NAMES = {
    "cube": "정육면체",
    "cuboid": "직육면체",
    "prism": "삼각기둥",
    "cylinder": "원기둥",
    "pyramid": "사각뿔",
}
ALIASES = {
    "triangular-prism": "prism", "triprism": "prism", "triangular_prism": "prism",
    "square-pyramid": "pyramid", "square_pyramid": "pyramid",
}

LABEL_ORDER = {
    "cube": "앞, 오른쪽, 뒤, 왼쪽, 위, 아래",
    "cuboid": "앞, 오른쪽, 뒤, 왼쪽, 위, 아래",
    "prism": "직사각형1, 직사각형2, 직사각형3, 위 삼각형, 아래 삼각형",
    "cylinder": "옆면, 위 원, 아래 원",
    "pyramid": "밑면, 위쪽 삼각형, 오른쪽 삼각형, 아래쪽 삼각형, 왼쪽 삼각형",
}


# ---------------------------------------------------------------- 기하 도우미
def sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def mul(p, k):
    return (p[0] * k, p[1] * k)


def length(p):
    return math.hypot(p[0], p[1])


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def key(p):
    return (round(p[0], 2), round(p[1], 2))


def tab_poly(p, q, face_pts, t):
    """변 PQ에 붙는 풀칠 날개(사다리꼴). 날개는 면의 바깥쪽으로 나간다."""
    d = sub(q, p)
    ln = length(d)
    d = (d[0] / ln, d[1] / ln)
    n = (-d[1], d[0])
    mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    c = centroid(face_pts)
    if (mid[0] - c[0]) * n[0] + (mid[1] - c[1]) * n[1] < 0:
        n = (-n[0], -n[1])
    tt = min(t, ln * 0.45)
    inset = min(tt, ln * 0.2)
    return [p, q, add(add(q, mul(n, tt)), mul(d, -inset)),
            add(add(p, mul(n, tt)), mul(d, inset))]


class Net:
    """도형 조각(면, 날개, 곡선)을 모아 선 종류를 정하는 그릇."""

    def __init__(self):
        self.faces = []    # (pts, label_box)  label_box=(cx, cy, w, h)
        self.tabs = []     # pts (앞의 두 점이 면에 붙는 변)
        self.prims = []    # 직접 그리는 요소: ('line'|'arc'|'glue', ...)

    def add_face(self, pts, label_w=None, label_h=None):
        cx, cy = centroid(pts)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w = label_w if label_w is not None else (max(xs) - min(xs))
        h = label_h if label_h is not None else (max(ys) - min(ys))
        self.faces.append((pts, (cx, cy, w, h)))
        return pts

    def add_tab(self, face_pts, i, t):
        """face_pts의 i번째 변(i -> i+1)에 날개를 붙인다."""
        p = face_pts[i]
        q = face_pts[(i + 1) % len(face_pts)]
        self.tabs.append(tab_poly(p, q, face_pts, t))

    def classify(self):
        """다각형 변을 세어 두 조각이 공유하는 변은 접는 선, 나머지는 자르는 선으로."""
        edges = {}
        order = []
        for pts in [f[0] for f in self.faces] + self.tabs:
            n = len(pts)
            for i in range(n):
                p, q = pts[i], pts[(i + 1) % n]
                k = frozenset((key(p), key(q)))
                if k not in edges:
                    edges[k] = [p, q, 0]
                    order.append(k)
                edges[k][2] += 1
        lines = []
        for k in order:
            p, q, cnt = edges[k]
            lines.append(("line", p, q, "fold" if cnt >= 2 else "cut"))
        glue = [("glue", pts) for pts in self.tabs]
        return glue, lines


# ---------------------------------------------------------------- 도형별 전개도
def build_cuboid(w, h, d, t):
    """십자형: 가운데 줄(위뚜껑·앞·아래·뒤) + 앞면 양옆(왼쪽·오른쪽)."""
    net = Net()
    # 가운데 줄 (x 0..w)
    lid = net.add_face([(0, 0), (w, 0), (w, d), (0, d)])
    front = net.add_face([(0, d), (w, d), (w, d + h), (0, d + h)])
    bottom = net.add_face([(0, d + h), (w, d + h), (w, 2 * d + h), (0, 2 * d + h)])
    back = net.add_face([(0, 2 * d + h), (w, 2 * d + h), (w, 2 * d + 2 * h), (0, 2 * d + 2 * h)])
    left = net.add_face([(-d, d), (0, d), (0, d + h), (-d, d + h)])
    right = net.add_face([(w, d), (w + d, d), (w + d, d + h), (w, d + h)])
    # 날개 7개: 뚜껑 3, 아래 2, 왼쪽·오른쪽 바깥 변
    net.add_tab(lid, 3, t)                 # 뚜껑 왼쪽 변 (x=0)
    net.add_tab(lid, 1, t)                 # 뚜껑 오른쪽 변
    net.add_tab(lid, 0, t)                 # 뚜껑 위쪽 변 (뒤 윗변과 붙음)
    net.add_tab(bottom, 3, t)              # 아래 왼쪽
    net.add_tab(bottom, 1, t)              # 아래 오른쪽
    net.add_tab(left, 3, t)                # 왼쪽면 바깥 변 (뒤 왼쪽 변과 붙음)
    net.add_tab(right, 1, t)               # 오른쪽면 바깥 변
    # 라벨 순서: 앞, 오른쪽, 뒤, 왼쪽, 위, 아래
    order = [front, right, back, left, lid, bottom]
    net.faces = [next(f for f in net.faces if f[0] is p) for p in order]
    return net


def build_prism(a, length_, t):
    """정삼각기둥: 직사각형 3개 가로줄 + 위·아래 정삼각형."""
    net = Net()
    L = length_
    H = a * math.sqrt(3) / 2
    r0 = net.add_face([(0, 0), (a, 0), (a, L), (0, L)])
    r1 = net.add_face([(a, 0), (2 * a, 0), (2 * a, L), (a, L)])
    r2 = net.add_face([(2 * a, 0), (3 * a, 0), (3 * a, L), (2 * a, L)])
    # 위 삼각형: r0의 윗변에 붙는다 (꼭짓점이 위)
    t_top = net.add_face([(0, 0), (a, 0), (a / 2, -H)])
    # 아래 삼각형: r1의 아랫변에 붙는다 (꼭짓점이 아래)
    t_bot = net.add_face([(a, L), (2 * a, L), (1.5 * a, L + H)])
    # 날개 5개
    net.add_tab(r2, 1, t)                  # 가로줄 오른쪽 끝 변
    net.add_tab(t_top, 1, t)               # 위 삼각형 오른쪽 빗변
    net.add_tab(t_top, 2, t)               # 위 삼각형 왼쪽 빗변
    net.add_tab(t_bot, 1, t)               # 아래 삼각형 오른쪽 빗변
    net.add_tab(t_bot, 2, t)               # 아래 삼각형 왼쪽 빗변
    # 삼각형 라벨 상자는 작게
    for tri in (t_top, t_bot):
        for i, (pts, box) in enumerate(net.faces):
            if pts is tri:
                cx, cy, _, _ = box
                gy = cy + (H * 0.1 if tri is t_top else -H * 0.1)
                net.faces[i] = (pts, (cx, gy, a * 0.5, H * 0.4))
    order = [r0, r1, r2, t_top, t_bot]
    net.faces = [next(f for f in net.faces if f[0] is p) for p in order]
    return net


def build_pyramid(s, height, t):
    """사각뿔: 밑면 사각형 + 네 방향 이등변삼각형(별 모양)."""
    net = Net()
    slant = math.sqrt(height ** 2 + (s / 2) ** 2)
    base = net.add_face([(0, 0), (s, 0), (s, s), (0, s)])
    top = net.add_face([(0, 0), (s, 0), (s / 2, -slant)])
    right = net.add_face([(s, 0), (s, s), (s + slant, s / 2)])
    bottom = net.add_face([(s, s), (0, s), (s / 2, s + slant)])
    left = net.add_face([(0, s), (0, 0), (-slant, s / 2)])
    # 날개 4개: 각 삼각형의 시계 방향 쪽 빗변
    net.add_tab(top, 1, t)      # (s,0) -> 꼭짓점
    net.add_tab(right, 1, t)    # (s,s) -> 꼭짓점
    net.add_tab(bottom, 1, t)   # (0,s) -> 꼭짓점
    net.add_tab(left, 1, t)     # (0,0) -> 꼭짓점
    for tri in (top, right, bottom, left):
        for i, (pts, box) in enumerate(net.faces):
            if pts is tri:
                cx, cy, _, _ = box
                net.faces[i] = (pts, (cx, cy, s * 0.5, slant * 0.35))
    order = [base, top, right, bottom, left]
    net.faces = [next(f for f in net.faces if f[0] is p) for p in order]
    return net


def build_cylinder(r, h, t):
    """원기둥: 옆면 직사각형 + 위·아래 원(접선에서 연결, 둘레에 풀칠 날개)."""
    net = Net()
    W = 2 * math.pi * r
    side = net.add_face([(0, 0), (W, 0), (W, h), (0, h)])
    tp = tab_poly(side[1], side[2], side, min(t, 10))   # 옆면 오른쪽 변 풀칠 날개
    net.prims.append(("glue_poly", tp))
    net.prims.append(("line", tp[1], tp[2], "cut"))
    net.prims.append(("line", tp[2], tp[3], "cut"))
    net.prims.append(("line", tp[3], tp[0], "cut"))
    n_tabs = 10                            # 짝수 (위·아래 접선이 칸 경계가 되도록)
    step = 360.0 / n_tabs
    neck = min(8.0, r * 0.7)               # 원과 옆면이 이어지는 접는 선 길이
    theta_n = math.degrees(math.asin(min(0.99, neck / 2 / r)))
    tab_t = min(t, r * 0.35)
    cx = W / 2
    circles = [((cx, -r), 90.0, "top"), ((cx, h + r), 270.0, "bottom")]
    for (c, tang, name) in circles:
        # 접선 방향(tang)을 칸 경계로 삼아 원을 n_tabs칸으로 나눈다.
        # 옆면 직사각형과 겹치는 칸(접선 가까운 칸)은 날개를 만들지 않는다.
        cursor = tang + theta_n                 # 접선 부근(접는 선 구간)은 원호를 그리지 않는다
        end = tang + 360.0 - theta_n
        for j in range(n_tabs):
            a0 = tang + j * step
            a1 = a0 + step
            b0, b1 = a0 + 2.5, a1 - 2.5          # 날개가 붙는 호
            o0, o1 = b0 + 0.18 * step * 0.6, b1 - 0.18 * step * 0.6

            def at(rad, ang):
                return (c[0] + rad * math.cos(math.radians(ang)),
                        c[1] + rad * math.sin(math.radians(ang)))
            P0, P1 = at(r, b0), at(r, b1)
            O0, O1 = at(r + tab_t, o0), at(r + tab_t, o1)
            ys = [P0[1], P1[1], O0[1], O1[1]]
            overlaps = (max(ys) > -0.5) if name == "top" else (min(ys) < h + 0.5)
            if overlaps:
                continue
            if b0 > cursor:
                net.prims.append(("arc", c, r, cursor, b0, "cut"))
            net.prims.append(("glue_tab", c, r, b0, b1, [P0, O0, O1, P1]))
            net.prims.append(("line", P0, O0, "cut"))
            net.prims.append(("line", O0, O1, "cut"))
            net.prims.append(("line", O1, P1, "cut"))
            net.prims.append(("arc", c, r, b0, b1, "fold"))
            cursor = b1
        if end > cursor:
            net.prims.append(("arc", c, r, cursor, end, "cut"))
    # 옆면 윗변·아랫변: 접선 구간만 점선, 나머지 실선
    x0, x1 = cx - neck / 2, cx + neck / 2
    for y in (0.0, h):
        net.prims.append(("line", (0, y), (x0, y), "cut"))
        net.prims.append(("line", (x0, y), (x1, y), "fold"))
        net.prims.append(("line", (x1, y), (W, y), "cut"))
    # 옆면 나머지 변: 왼쪽 실선, 오른쪽은 날개가 붙은 접는 선
    net.prims.append(("line", (0, 0), (0, h), "cut"))
    net.prims.append(("line", (W, 0), (W, h), "fold"))
    # 라벨 상자
    net.faces = [
        (side, (cx, h / 2, W * 0.9, h * 0.8)),
        ([(cx - r, -r), (cx + r, -r), (cx + r, -r + 0.001)], (cx, -r, r * 1.5, r * 1.2)),
        ([(cx - r, h + r), (cx + r, h + r), (cx + r, h + r + 0.001)], (cx, h + r, r * 1.5, r * 1.2)),
    ]
    net.cylinder = True
    return net


# ---------------------------------------------------------------- SVG 출력
def sample_arc(c, r, a0, a1, n=24):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def all_points(net, glue, lines):
    pts = []
    for pr in net.faces:
        if not getattr(net, "cylinder", False):
            pts.extend(pr[0])
    for pr in glue:
        pts.extend(pr[1])
    for ln in lines:
        pts.extend([ln[1], ln[2]])
    for pr in net.prims:
        if pr[0] == "line":
            pts.extend([pr[1], pr[2]])
        elif pr[0] == "arc":
            pts.extend(sample_arc(pr[1], pr[2], pr[3], pr[4]))
        elif pr[0] == "glue_poly":
            pts.extend(pr[1])
        elif pr[0] == "glue_tab":
            pts.extend(pr[5])
            pts.extend(sample_arc(pr[1], pr[2], pr[3], pr[4], 6))
    if getattr(net, "cylinder", False):
        pts.extend(p for f in net.faces[:1] for p in f[0])
    return pts


def fmt(v):
    s = "%.2f" % v
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def text_units(text):
    return sum(1.0 if ord(ch) > 127 else 0.58 for ch in text)


def render(net, title, labels, name_box, guide, scale_override=None):
    glue, lines = net.classify() if net.faces and not getattr(net, "cylinder", False) else ([], [])
    pts = all_points(net, glue, lines)
    minx = min(p[0] for p in pts)
    maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts)
    maxy = max(p[1] for p in pts)
    bw, bh = maxx - minx, maxy - miny
    area_x0, area_x1 = MARGIN, PAGE_W - MARGIN
    area_y0 = HEADER_H
    area_y1 = PAGE_H - (FOOTER_H if guide else MARGIN)
    aw, ah = area_x1 - area_x0, area_y1 - area_y0
    scale = min(1.0, aw / bw, ah / bh)
    if scale_override:
        scale = scale_override
    ox = area_x0 + (aw - bw * scale) / 2 - minx * scale
    oy = area_y0 + (ah - bh * scale) / 2 - miny * scale

    def T(p):
        return (p[0] * scale + ox, p[1] * scale + oy)

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" '
               'viewBox="0 0 210 297" font-family="%s">' % escape(FONT, {'"': "&quot;"}))
    out.append('<title>%s</title>' % escape(title))
    out.append('<desc>실선=자르기, 점선=접기, 회색=풀칠. 단위 mm, A4 세로. 초안이며 인쇄 전 교사가 확인한다.</desc>')
    out.append('<rect x="0" y="0" width="210" height="297" fill="#ffffff"/>')

    # 머리말
    out.append('<g id="header">')
    out.append('<text class="title" x="%s" y="15" font-size="7" font-weight="bold" fill="#000">%s</text>'
               % (fmt(MARGIN), escape(title)))
    if name_box:
        out.append('<text class="namebox" x="130" y="15" font-size="4.5" fill="#000">이름:</text>')
        out.append('<line class="namebox" x1="141" y1="15.5" x2="200" y2="15.5" stroke="#000" stroke-width="0.3"/>')
    out.append('</g>')

    # 풀칠 날개 (먼저 깔아서 선이 위로 오게)
    out.append('<g id="glue">')
    for g in glue:
        d = "M " + " L ".join("%s %s" % tuple(map(fmt, T(p))) for p in g[1]) + " Z"
        out.append('<path class="glue" d="%s" %s/>' % (d, STYLE["glue"]))
    for pr in net.prims:
        if pr[0] == "glue_poly":
            d = "M " + " L ".join("%s %s" % tuple(map(fmt, T(p))) for p in pr[1]) + " Z"
            out.append('<path class="glue" d="%s" %s/>' % (d, STYLE["glue"]))
        if pr[0] == "glue_tab":
            _, c, r, b0, b1, quad = pr
            P0, O0, O1, P1 = [T(p) for p in quad]
            rr = r * scale
            large = 1 if (b1 - b0) > 180 else 0
            d = ("M %s %s L %s %s L %s %s L %s %s A %s %s 0 %d 0 %s %s Z" %
                 (fmt(P0[0]), fmt(P0[1]), fmt(O0[0]), fmt(O0[1]), fmt(O1[0]), fmt(O1[1]),
                  fmt(P1[0]), fmt(P1[1]), fmt(rr), fmt(rr), large, fmt(P0[0]), fmt(P0[1])))
            out.append('<path class="glue" d="%s" %s/>' % (d, STYLE["glue"]))
    out.append('</g>')

    # 선
    out.append('<g id="lines">')
    for ln in lines:
        a, b, cls = T(ln[1]), T(ln[2]), ln[3]
        out.append('<line class="%s" x1="%s" y1="%s" x2="%s" y2="%s" %s/>' %
                   (cls, fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), STYLE[cls]))
    for pr in net.prims:
        if pr[0] == "line":
            a, b, cls = T(pr[1]), T(pr[2]), pr[3]
            out.append('<line class="%s" x1="%s" y1="%s" x2="%s" y2="%s" %s/>' %
                       (cls, fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), STYLE[cls]))
        elif pr[0] == "arc":
            _, c, r, a0, a1, cls = pr
            if a1 - a0 <= 0.01:
                continue
            p0 = T((c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0))))
            p1 = T((c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1))))
            rr = r * scale
            large = 1 if (a1 - a0) > 180 else 0
            out.append('<path class="%s" d="M %s %s A %s %s 0 %d 1 %s %s" %s/>' %
                       (cls, fmt(p0[0]), fmt(p0[1]), fmt(rr), fmt(rr), large,
                        fmt(p1[0]), fmt(p1[1]), STYLE[cls]))
    out.append('</g>')

    # 면 라벨
    if labels:
        out.append('<g id="labels">')
        for (pts_, box), text in zip(net.faces, labels):
            text = text.strip()
            if not text:
                continue
            cx, cy, bw_, bh_ = box
            c = T((cx, cy))
            aw_, ah_ = bw_ * scale * 0.8, bh_ * scale * 0.5
            size = max(2.5, min(9.0, ah_, aw_ / max(1.0, text_units(text))))
            out.append('<text class="label" x="%s" y="%s" font-size="%s" text-anchor="middle" '
                       'dominant-baseline="central" fill="#333">%s</text>' %
                       (fmt(c[0]), fmt(c[1]), fmt(size), escape(text)))
        out.append('</g>')

    # 범례
    if guide:
        y = PAGE_H - 8
        out.append('<g id="guide">')
        out.append('<line class="cut" x1="10" y1="%s" x2="24" y2="%s" %s/>' % (fmt(y), fmt(y), STYLE["cut"]))
        out.append('<text x="26" y="%s" font-size="3.5" fill="#000">실선: 자르기</text>' % fmt(y + 1.2))
        out.append('<line class="fold" x1="62" y1="%s" x2="76" y2="%s" %s/>' % (fmt(y), fmt(y), STYLE["fold"]))
        out.append('<text x="78" y="%s" font-size="3.5" fill="#000">점선: 접기</text>' % fmt(y + 1.2))
        out.append('<rect class="glue" x="112" y="%s" width="14" height="4" %s/>' % (fmt(y - 2), STYLE["glue"]))
        out.append('<text x="128" y="%s" font-size="3.5" fill="#000">회색: 풀칠(풀 바르는 곳)</text>' % fmt(y + 1.2))
        out.append('<text x="10" y="%s" font-size="3" fill="#555">초안입니다. 인쇄 배율 100%%(실제 크기)로 출력하세요.%s</text>'
                   % (fmt(y + 6), (" 전개도를 %d%%로 줄였습니다." % round(scale * 100)) if scale < 0.999 else ""))
        out.append('</g>')
    out.append('</svg>')
    return "\n".join(out) + "\n", scale, (bw * scale, bh * scale)


# ---------------------------------------------------------------- CLI
def parse_args(argv):
    ap = argparse.ArgumentParser(
        prog="net.py",
        description="A4 SVG 전개도 생성 (cube, cuboid, prism, cylinder, pyramid). 단위 mm.")
    ap.add_argument("shape", help="cube | cuboid | prism | cylinder | pyramid")
    ap.add_argument("--size", type=float, default=50.0,
                    help="기본 길이: 정육면체 모서리, 삼각기둥의 삼각형 한 변, 사각뿔 밑면 한 변 (기본 50)")
    ap.add_argument("--width", type=float, help="직육면체 가로")
    ap.add_argument("--height", type=float, help="높이(직육면체·기둥 길이·뿔의 수직 높이)")
    ap.add_argument("--depth", type=float, help="직육면체 세로(깊이)")
    ap.add_argument("--radius", type=float, help="원기둥 반지름 (없으면 size/2)")
    ap.add_argument("--tab", type=float, default=8.0, help="풀칠 날개 너비 mm (기본 8)")
    ap.add_argument("--labels", default="",
                    help="면 이름을 쉼표로. 순서: cube/cuboid=앞,오른쪽,뒤,왼쪽,위,아래 / "
                         "prism=직사각형3개,위삼각형,아래삼각형 / cylinder=옆면,위원,아래원 / "
                         "pyramid=밑면,위,오른쪽,아래,왼쪽 삼각형")
    ap.add_argument("--title", help="머리말 제목 (기본: 도형 이름 전개도)")
    ap.add_argument("--name-box", action="store_true", help="오른쪽 위에 이름 쓰는 줄을 둔다")
    ap.add_argument("--no-guide", action="store_true", help="아래쪽 선 범례를 넣지 않는다")
    ap.add_argument("-o", "--output", help="출력 SVG 경로 (기본 <shape>.svg, '-'면 표준 출력)")
    ap.add_argument("--check", action="store_true", help="만든 SVG를 다시 읽어 구조를 검사한다")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    shape = ALIASES.get(args.shape.lower(), args.shape.lower())
    if shape not in SHAPE_NAMES:
        sys.stderr.write("알 수 없는 도형: %s (cube, cuboid, prism, cylinder, pyramid 중 선택)\n" % args.shape)
        return 2
    size = args.size
    for name, v in (("size", size), ("width", args.width), ("height", args.height),
                    ("depth", args.depth), ("radius", args.radius), ("tab", args.tab)):
        if v is not None and v <= 0:
            sys.stderr.write("--%s 값은 0보다 커야 한다.\n" % name)
            return 2
    t = args.tab

    if shape == "cube":
        net = build_cuboid(size, size, size, t)
        dims = "모서리 %s mm" % fmt(size)
    elif shape == "cuboid":
        w = args.width or size
        h = args.height or size
        d = args.depth or size
        net = build_cuboid(w, h, d, t)
        dims = "가로 %s x 높이 %s x 깊이 %s mm" % (fmt(w), fmt(h), fmt(d))
    elif shape == "prism":
        L = args.height or size * 1.5
        net = build_prism(size, L, t)
        dims = "정삼각형 한 변 %s, 기둥 길이 %s mm" % (fmt(size), fmt(L))
    elif shape == "pyramid":
        hh = args.height or size
        net = build_pyramid(size, hh, t)
        dims = "밑면 한 변 %s, 높이 %s mm" % (fmt(size), fmt(hh))
    else:
        r = args.radius or size / 2
        h = args.height or size
        net = build_cylinder(r, h, t)
        dims = "반지름 %s, 높이 %s mm" % (fmt(r), fmt(h))

    labels = [s for s in args.labels.split(",")] if args.labels else []
    nfaces = len(net.faces)
    if len(labels) > nfaces:
        sys.stderr.write("경고: 면은 %d개인데 라벨이 %d개 — 남는 라벨은 무시한다. 순서: %s\n"
                         % (nfaces, len(labels), LABEL_ORDER[shape]))
        labels = labels[:nfaces]
    title = args.title or ("%s 전개도" % SHAPE_NAMES[shape])
    svg, scale, (pw, ph) = render(net, title, labels, args.name_box, not args.no_guide)

    out = args.output or ("%s.svg" % shape)
    if out == "-":
        sys.stdout.write(svg)
    else:
        with open(out, "w", encoding="utf-8") as f:
            f.write(svg)
    msg = "%s (%s) -> %s | 전개도 크기 %.0f x %.0f mm" % (SHAPE_NAMES[shape], dims, out, pw, ph)
    if scale < 0.999:
        msg += " | A4에 맞추려고 %d%%로 줄임 (실제 치수는 이 비율만큼 작아짐)" % round(scale * 100)
    sys.stderr.write(msg + "\n")

    if args.check:
        text = svg
        root = ET.fromstring(text.encode("utf-8"))
        ns = "{http://www.w3.org/2000/svg}"
        cnt = {}
        for el in root.iter():
            c = el.get("class")
            if c:
                cnt[c] = cnt.get(c, 0) + 1
        sys.stderr.write("검사 통과: SVG 구조 정상. 요소 수 %s\n" % dict(sorted(cnt.items())))
        assert root.tag == ns + "svg"
    return 0


if __name__ == "__main__":
    sys.exit(main())
