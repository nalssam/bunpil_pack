#!/usr/bin/env python3
"""build_live_pptx.py 가 만든 pptx 를 점검한다 (표준 라이브러리만 사용).

    python qa_live_pptx.py outputs/deck.pptx

오류가 있으면 종료 코드 1. 확인하는 것: 파일 구조, 슬라이드마다 추가 기능 1개와 대체 그림,
저장된 HTML·슬라이드 번호·크기, 설정값 용량, 인터넷에서 불러오는 주소, 개인정보 형식.
"""
import argparse
import base64
import hashlib
import json
import posixpath
import re
import sys
import zipfile
import zlib
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ADDIN_ID = "6f2b8c1e-4d7a-4e55-9a3b-2c8f5d1e7a90"
NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "we": "http://schemas.microsoft.com/office/webextensions/webextension/2010/11",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
}
RT_WEBEXT = "http://schemas.microsoft.com/office/2011/relationships/webextension"
RT_SLIDE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
RT_NOTES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
CT_WEBEXT = "application/vnd.ms-office.webextension+xml"
# 저장 크기 = len(json.dumps(html)): 설정값 'html' 하나가 pptx 안에서 차지하는 글자 수(build_live_pptx.py 와 같은 값을 잰다).
# 실제 PowerPoint(Microsoft 365, Office LTSC 2024)에서 잰 결과: 4,000,000 은 열려서 실행되고 10,000,000 은 빈 값으로 돌아온다.
WARN_BYTES = 1_500_000
MAX_BYTES = 3_000_000
RRN = re.compile(r"(?<!\d)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])-?[1-8]\d{6}(?!\d)")
PHONE = re.compile(r"(?<!\d)01[016789]-?(?!0000)\d{3,4}-?\d{4}(?!\d)")


class SlideScanner(HTMLParser):
    """HTML 을 한 번 읽어 슬라이드(<section> 의 class 에 slide 가 있는 것)마다 노트와 제목을 모은다.

    주석·<script>·<style>·<textarea>·<template> 안은 세지 않는다. 노트와 제목은 그 슬라이드의 <section> 안에서만 찾는다.
    build_live_pptx.py 와 qa_live_pptx.py 에 같은 코드가 들어 있다(점검 도구는 혼자서도 돈다). 고칠 때는 둘 다 고친다."""

    RAW = ("script", "style", "textarea", "title")
    INLINE = frozenset("a abbr b bdi bdo cite code data del dfn em font i ins kbd mark q rp rt ruby s samp small span "
                       "strong sub sup time u var wbr".split())

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.slides = []        # 슬라이드마다 {"attr": data-notes, "aside": [글자…], "title": [글자…] 또는 None}
        self._open = []         # 열려 있는 <section> 마다 그 슬라이드(슬라이드가 아니면 None)
        self._raw = None        # 안쪽을 읽지 않는 요소 이름
        self._template = 0
        self._aside = 0         # 노트 <aside> 안쪽 깊이
        self._head = None       # 읽고 있는 제목 태그

    def _slide(self):
        for s in reversed(self._open):
            if s is not None:
                return s
        return None

    def handle_startendtag(self, tag, attrs):
        if tag not in self.RAW and tag != "template":      # <title/> 꼴(SVG 안)은 빈 요소다
            self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        if self._raw:
            return
        if tag in self.RAW:
            self._raw = tag
            return
        if tag == "template":
            self._template += 1
            return
        if self._template:
            return
        a = {}
        for k, v in attrs:
            a.setdefault(k, v or "")
        if tag == "section":
            slide = None
            if "slide" in a.get("class", "").split():
                slide = {"attr": a.get("data-notes", ""), "aside": [], "title": None}
                self.slides.append(slide)
            self._open.append(slide)
            self._aside, self._head = 0, None
            return
        cur = self._slide()
        if cur is None:
            return
        if self._aside:
            if tag == "aside":
                self._aside += 1
            if tag not in self.INLINE:
                cur["aside"].append("\n")
        elif tag == "aside" and "notes" in a.get("class", "").split():
            self._aside = 1
            cur["aside"].append("\n")
        elif self._head:
            if tag not in self.INLINE:
                cur["title"].append(" ")
        elif tag in ("h1", "h2", "h3") and cur["title"] is None:
            cur["title"] = []
            self._head = tag

    def handle_endtag(self, tag):
        if self._raw:
            if tag == self._raw:
                self._raw = None
            return
        if tag == "template":
            self._template = max(0, self._template - 1)
            return
        if self._template:
            return
        if tag == "section":
            if self._open:
                self._open.pop()
            self._aside, self._head = 0, None
            return
        cur = self._slide()
        if cur is None:
            return
        if self._aside:
            if tag == "aside":
                self._aside -= 1
            if tag not in self.INLINE:
                cur["aside"].append("\n")
        elif self._head:
            if tag == self._head:
                self._head = None
            elif tag not in self.INLINE:
                cur["title"].append(" ")

    def handle_data(self, data):
        if self._raw or self._template:
            return
        cur = self._slide()
        if cur is None:
            return
        if self._aside:
            cur["aside"].append(data)
        elif self._head:
            cur["title"].append(data)

    @staticmethod
    def _lines(text: str, keep_blank: bool) -> str:
        lines = [ln.strip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        return "\n".join(ln for ln in lines if ln or keep_blank).strip()

    def result(self) -> list:
        """슬라이드마다 {"notes": 발표자 노트, "title": 첫 제목}. 노트는 data-notes 가 먼저, 비어 있으면 <aside class="notes">."""
        return [{"notes": self._lines(s["attr"], True) or self._lines("".join(s["aside"]), False),
                 "title": " ".join("".join(s["title"] or []).split())} for s in self.slides]


def count_sections(html: str) -> int:
    """HTML 안의 슬라이드(<section class="slide">) 수. 변환기와 같은 방법으로 센다."""
    parser = SlideScanner()
    try:
        parser.feed(html)
        parser.close()
    except Exception:           # 읽다 멈춰도 거기까지 찾은 것으로 계속한다
        pass
    return len(parser.slides)


def readable(html: str) -> str:
    """HTML 에, data URI 로 들어 있는 스크립트를 풀어서 붙인 글자(글자를 찾는 점검에 쓴다)."""
    parts = [html]
    for m in re.finditer(r"data:text/javascript(?:;charset=[A-Za-z0-9_-]+)?;base64,([A-Za-z0-9+/=]+)", html):
        try:
            parts.append(base64.b64decode(m.group(1)).decode("utf-8", "replace"))
        except ValueError:
            pass
    return "\n".join(parts)


def rels_of(z: zipfile.ZipFile, part: str) -> dict:
    d, b = posixpath.split(part)
    path = f"{d}/_rels/{b}.rels"
    if path not in z.namelist():
        return {}
    out = {}
    for r in ET.fromstring(z.read(path)).findall("rel:Relationship", NS):
        target = r.get("Target") or ""
        if r.get("TargetMode") != "External":
            target = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(d, target))
        out[r.get("Id")] = (r.get("Type"), target)
    return out


def _positive_int(v) -> bool:
    return type(v) is int and v > 0


def damaged(z: zipfile.ZipFile) -> list:
    """끝까지 읽히지 않는 파트 이름들(압축이 깨졌거나 내용이 바뀐 것). 그림 파트까지 모두 읽어 본다."""
    bad = []
    for item in z.infolist():
        try:
            with z.open(item) as f:
                while f.read(1 << 20):
                    pass
        except (zipfile.BadZipFile, zlib.error, EOFError, OSError, RuntimeError, NotImplementedError):
            bad.append(item.filename)
    return bad


def shape_ids(el, skip: str, out: list) -> list:
    """슬라이드 안 도형들의 ID(p:cNvPr id). 이름이 skip 인 요소(mc:Choice 또는 mc:Fallback) 안쪽은 세지 않는다."""
    for child in el:
        if child.tag == skip:
            continue
        if child.tag == f"{{{NS['p']}}}cNvPr":
            out.append(child.get("id"))
        shape_ids(child, skip, out)
    return out


def check(z: zipfile.ZipFile, path: Path, errors: list, warns: list, info: list) -> None:
    names = set(z.namelist())
    for n in sorted(names):
        if n.endswith((".xml", ".rels")):
            try:
                ET.fromstring(z.read(n))
            except ET.ParseError as e:
                errors.append(f"{n}: XML 형식 오류 - {e}")
    if errors:
        return
    for need in ("[Content_Types].xml", "ppt/presentation.xml"):
        if need not in names:
            errors.append(f"PowerPoint 파일 구조가 아닙니다({need} 이 없다)")
    if errors:
        return

    overrides = {(o.get("PartName") or "").lstrip("/"): o.get("ContentType")
                 for o in ET.fromstring(z.read("[Content_Types].xml")).findall("ct:Override", NS)}
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    prels = rels_of(z, "ppt/presentation.xml")
    slides = []
    for s in pres.findall("p:sldIdLst/p:sldId", NS):
        rid = s.get(f"{{{NS['r']}}}id")
        if rid not in prels:
            errors.append(f"PowerPoint 파일 구조가 아닙니다(슬라이드 관계 {rid} 가 없다)")
            return
        slides.append(prels[rid][1])
    sz = pres.find("p:sldSz", NS)
    try:
        ratio = int(sz.get("cx")) / int(sz.get("cy"))
    except (AttributeError, TypeError, ValueError, ZeroDivisionError):
        ratio = None
        errors.append("슬라이드 크기(sldSz)를 읽을 수 없다")
    if not slides:
        errors.append("슬라이드가 없습니다")

    no_notes = []                              # 발표자 노트가 없는 슬라이드 번호
    htmls, numbers, notes = {}, [], 0          # htmls: 해시 -> (그 HTML 이 처음 나온 슬라이드, HTML)
    part_owner, instance_owner = {}, {}
    for idx, sp in enumerate(slides, 1):
        tag = f"슬라이드 {idx}"
        if sp not in names:
            errors.append(f"{tag}: {sp} 파트가 없다")
            continue
        srels = rels_of(z, sp)
        root = ET.fromstring(z.read(sp))
        # 추가 기능 프레임(mc:Choice)과 대체 그림(mc:Fallback)은 둘 중 하나만 쓰이는 같은 자리의 도형이다. PowerPoint 는
        # 저장할 때 둘에 같은 ID 를 준다. 그래서 "Choice 쪽으로 읽을 때"와 "Fallback 쪽으로 읽을 때"를 따로 본다.
        dup = set()
        for skip in ("Fallback", "Choice"):
            ids = shape_ids(root, f"{{{NS['mc']}}}{skip}", [])
            dup |= {i for i in ids if ids.count(i) > 1}
        dup = sorted(dup, key=str)
        if dup:
            errors.append(f"{tag}: 도형 ID 가 겹친다 ({', '.join(str(i) for i in dup)})")
        frames = [f for f in root.findall(".//mc:AlternateContent/mc:Choice/p:graphicFrame", NS)
                  if f.findall(".//we:webextensionref", NS)]
        refs = [r for f in frames for r in f.findall(".//we:webextensionref", NS)]
        if len(refs) != 1:
            errors.append(f"{tag}: 추가 기능 프레임이 {len(refs)}개 (1개여야 한다)")
            continue
        for choice in root.findall(".//mc:AlternateContent/mc:Choice", NS):
            if choice.findall(".//we:webextensionref", NS) and not {"we", "pca"} <= set((choice.get("Requires") or "").split()):
                errors.append(f"{tag}: 추가 기능 묶음의 Requires 가 'we pca' 가 아니다 ({choice.get('Requires')})")
        if not root.findall(".//mc:AlternateContent/mc:Fallback/p:pic", NS):
            errors.append(f"{tag}: 대체 그림(Fallback)이 없다")
        gd = frames[0].find("a:graphic/a:graphicData", NS)
        if gd is None or gd.get("uri") != NS["we"]:
            errors.append(f"{tag}: 추가 기능 프레임의 graphicData uri 가 다르다 ({None if gd is None else gd.get('uri')})")
        ext = frames[0].find("p:xfrm/a:ext", NS)
        try:
            sized = ext is not None and int(ext.get("cx")) > 0 and int(ext.get("cy")) > 0
        except (TypeError, ValueError):
            sized = False
        if not sized:
            errors.append(f"{tag}: 추가 기능 프레임의 크기가 0 이거나 없다")
        rid = refs[0].get(f"{{{NS['r']}}}id")
        if rid not in srels or srels[rid][0] != RT_WEBEXT:
            errors.append(f"{tag}: 추가 기능 관계({rid})가 없거나 형식이 다르다")
            continue
        wp = srels[rid][1]
        if wp not in names:
            errors.append(f"{tag}: {wp} 파트가 없다")
            continue
        if wp in part_owner:
            errors.append(f"{tag}: 슬라이드 {part_owner[wp]} 와 같은 추가 기능 파트({wp})를 쓴다")
        part_owner.setdefault(wp, idx)
        if overrides.get(wp) != CT_WEBEXT:
            errors.append(f"{tag}: {wp} 의 콘텐츠 형식이 등록되지 않았다")
        we = ET.fromstring(z.read(wp))
        instance = we.get("id")
        if instance and instance_owner.get(instance, wp) != wp:
            errors.append(f"{tag}: 추가 기능 인스턴스 ID 가 다른 슬라이드와 같다 ({instance})")
        instance_owner.setdefault(instance, wp)
        ref = we.find("we:reference", NS)
        if ref is None or ref.get("id") != ADDIN_ID:
            errors.append(f"{tag}: 추가 기능 ID 가 다르다 ({None if ref is None else ref.get('id')})")
        elif (ref.get("store"), ref.get("storeType")) != ("developer", "Registry"):
            warns.append(f"{tag}: 참조 방식이 developer/Registry 가 아니다 ({ref.get('store')}/{ref.get('storeType')})")
        props = {}
        for p in we.findall("we:properties/we:property", NS):
            try:
                props[p.get("name")] = json.loads(p.get("value") or "")
            except ValueError:
                errors.append(f"{tag}: 설정값 '{p.get('name')}' 이 JSON 이 아니다")
        for need in ("html", "slide", "width", "height"):
            if need not in props:
                errors.append(f"{tag}: 설정값 '{need}' 이 없다")
        html = props.get("html")
        if "html" in props and not (isinstance(html, str) and html):
            errors.append(f"{tag}: 설정값 'html' 이 비어 있거나 글자가 아니다")
        if isinstance(html, str) and html:
            htmls.setdefault(hashlib.sha256(html.encode("utf-8", "surrogatepass")).hexdigest(), (idx, html))
        number = props.get("slide")
        if "slide" in props:
            if type(number) is not int or not 1 <= number <= len(slides):
                errors.append(f"{tag}: 설정값 'slide' 가 1..{len(slides)} 사이의 정수가 아니다 ({number!r})")
            elif number in numbers:
                errors.append(f"{tag}: 설정값 'slide' {number} 이 다른 슬라이드와 겹친다")
        numbers.append(number)
        w, h = props.get("width"), props.get("height")
        for key in ("width", "height"):
            if key in props and not _positive_int(props[key]):
                errors.append(f"{tag}: 설정값 '{key}' 가 양의 정수가 아니다 ({props[key]!r})")
        if _positive_int(w) and _positive_int(h) and ratio and abs(w / h - ratio) > 0.01:
            warns.append(f"{tag}: HTML 비율 {w}x{h} 이 슬라이드 비율과 다르다(여백이 생긴다)")
        poster = props.get("poster")
        if "poster" in props and not (isinstance(poster, str) and (not poster or poster.startswith("data:image/"))):
            warns.append(f"{tag}: 설정값 'poster' 가 그림(data:image/…)이 아니다")
        snap = we.find("we:snapshot", NS)
        wrels = rels_of(z, wp)
        srid = None if snap is None else snap.get(f"{{{NS['r']}}}embed")
        if srid not in wrels or wrels[srid][1] not in names:
            errors.append(f"{tag}: 미리보기 그림(snapshot) 연결이 끊겼다")
        if any(t == RT_NOTES for t, _ in srels.values()):
            notes += 1
        else:
            no_notes.append(idx)

    hosts = set()
    for idx, html in sorted(htmls.values()):
        label = "HTML" if len(htmls) == 1 else f"슬라이드 {idx} 의 HTML"
        size = len(json.dumps(html))
        if size > MAX_BYTES:
            errors.append(f"{label} 의 저장 크기가 {size / 1e6:.2f}MB - 한도({MAX_BYTES / 1e6:.1f}MB)를 넘는다")
        elif size > WARN_BYTES:
            warns.append(f"{label} 의 저장 크기가 {size / 1e6:.2f}MB 로 크다(슬라이드마다 한 벌씩 들어가 열 때 느릴 수 있다)")
        sections = count_sections(html)
        if sections and sections != len(slides):
            warns.append(f"{label} 의 <section class=\"slide\"> 는 {sections}개인데 슬라이드는 {len(slides)}장이다")
        text = readable(html)
        if "__LIVE_SLIDE__" not in text and "liveSlide" not in text:
            warns.append(f"{label} 이 window.__LIVE_SLIDE__ 를 읽지 않는다 - 모든 슬라이드가 같은 화면일 수 있다")
        hosts |= {m.group(1) for m in re.finditer(r"https?://([A-Za-z0-9.-]+)", text)} - {"www.w3.org"}
        for m in RRN.finditer(text):
            errors.append(f"{label} 에 주민등록번호 형식이 있다: {m.group(0)[:8]}…")
        for m in PHONE.finditer(text):
            warns.append(f"{label} 에 휴대전화 번호 형식이 있다: {m.group(0)} - 실제 번호인지 확인")
    if hosts:
        info.append("인터넷에서 불러올 수 있는 주소: " + ", ".join(sorted(hosts)[:10]))

    if numbers and sorted(n for n in numbers if type(n) is int) == list(range(1, len(slides) + 1)) \
            and numbers != list(range(1, len(slides) + 1)):
        warns.append(f"슬라이드 번호 순서가 1..{len(slides)} 가 아니다: {numbers}")
    if len(htmls) > 1:
        warns.append("슬라이드마다 저장된 HTML 이 서로 다르다(의도한 것이 아니면 다시 변환)")
    if no_notes and slides:
        which = "전부" if len(no_notes) == len(slides) else ", ".join(str(i) for i in no_notes[:20])
        warns.append(f"발표자 노트가 없는 슬라이드: {which} (교사 발문을 그 장의 data-notes 에 적고 다시 변환한다)")
    info.append(f"슬라이드 {len(slides)}장 · 발표자 노트 {notes}장 · 파일 {path.stat().st_size / 1024:.0f}KB")


def _console() -> None:
    """출력을 다른 프로그램이 받아 갈 때(파이프)는 UTF-8 로 내보내고, 어떤 경우에도 글자 때문에 멈추지 않게 한다."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream.isatty():
                stream.reconfigure(errors="replace")
            else:
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def main() -> int:
    _console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx", type=Path, help="점검할 pptx 파일")
    path = ap.parse_args().pptx
    errors, warns, info = [], [], []          # 실행할 때마다 새로 만든다(이전 점검 결과가 섞이지 않게)
    try:
        z = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as e:
        print(f"오류: 파일을 열 수 없습니다 - {e}")
        return 1
    with z:
        try:
            bad = damaged(z)
            if bad:
                more = " …" if len(bad) > 5 else ""
                errors.append(f"파일이 깨져 있습니다 - 읽을 수 없는 부분 {len(bad)}개: {', '.join(bad[:5])}{more}")
            else:
                check(z, path, errors, warns, info)
        except KeyError:                       # 있어야 할 파트·관계가 없다
            errors.append("PowerPoint 파일 구조가 아닙니다(있어야 할 부분이 빠져 있다)")
        except (zipfile.BadZipFile, zlib.error, EOFError, OSError) as e:
            errors.append(f"파일이 깨져 있습니다 - {e}")
        except Exception as e:                 # 어떤 파일을 주어도 파이썬 오류 화면으로 끝나지 않게 한다
            errors.append(f"점검하다 멈췄습니다 - {type(e).__name__}: {e}")
    for x in info:
        print("정보:", x)
    for x in warns:
        print("주의:", x)
    for x in errors:
        print("오류:", x)
    print(f"{path.name} 점검 - 오류 {len(errors)}건, 주의 {len(warns)}건")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
