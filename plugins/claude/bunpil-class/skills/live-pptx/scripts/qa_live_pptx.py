#!/usr/bin/env python3
"""build_live_pptx.py 가 만든 pptx 를 점검한다 (표준 라이브러리만 사용).

    python qa_live_pptx.py outputs/deck.pptx

오류가 있으면 종료 코드 1. 확인하는 것: 파일 구조, 슬라이드마다 추가 기능 1개와 대체 그림,
저장된 HTML·슬라이드 번호·크기, 설정값 용량, 인터넷에서 불러오는 주소, 개인정보 형식.
"""
import hashlib
import json
import posixpath
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
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
LIMIT = 1_900_000
RRN = re.compile(r"(?<!\d)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])-?[1-8]\d{6}(?!\d)")
PHONE = re.compile(r"(?<!\d)01[016789]-?(?!0000)\d{3,4}-?\d{4}(?!\d)")

errors, warns, info = [], [], []


def count_sections(html: str) -> int:
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    t = re.sub(r"<!--.*?-->", blank, html, flags=re.S)
    t = re.sub(r"(?<=<script)\b[^>]*>.*?(?=</script\s*>)", blank, t, flags=re.S | re.I)
    t = re.sub(r"(?<=<style)\b[^>]*>.*?(?=</style\s*>)", blank, t, flags=re.S | re.I)
    n = 0
    for m in re.finditer(r"<section\b[^>]*\bclass\s*=\s*(\"[^\"]*\"|'[^']*')[^>]*>", t, re.I):
        if "slide" in m.group(1).strip("\"'").split():
            n += 1
    return n


def rels_of(z: zipfile.ZipFile, part: str) -> dict:
    d, b = posixpath.split(part)
    path = f"{d}/_rels/{b}.rels"
    if path not in z.namelist():
        return {}
    out = {}
    for r in ET.fromstring(z.read(path)).findall("rel:Relationship", NS):
        target = r.get("Target")
        if r.get("TargetMode") != "External":
            target = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(d, target))
        out[r.get("Id")] = (r.get("Type"), target)
    return out



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
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    try:
        z = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as e:
        print(f"오류: 파일을 열 수 없습니다 - {e}")
        return 1
    names = set(z.namelist())
    for n in sorted(names):
        if n.endswith((".xml", ".rels")):
            try:
                ET.fromstring(z.read(n))
            except ET.ParseError as e:
                errors.append(f"{n}: XML 형식 오류 - {e}")
    if errors:
        return report(path)

    overrides = {o.get("PartName").lstrip("/"): o.get("ContentType")
                 for o in ET.fromstring(z.read("[Content_Types].xml")).findall("ct:Override", NS)}
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    prels = rels_of(z, "ppt/presentation.xml")
    slides = [prels[s.get(f"{{{NS['r']}}}id")][1] for s in pres.findall("p:sldIdLst/p:sldId", NS)]
    sz = pres.find("p:sldSz", NS)
    ratio = int(sz.get("cx")) / int(sz.get("cy"))
    if not slides:
        errors.append("슬라이드가 없습니다")

    htmls, numbers, notes = set(), [], 0
    for idx, sp in enumerate(slides, 1):
        tag = f"슬라이드 {idx}"
        srels = rels_of(z, sp)
        root = ET.fromstring(z.read(sp))
        refs = root.findall(".//mc:AlternateContent/mc:Choice/p:graphicFrame//we:webextensionref", NS)
        if len(refs) != 1:
            errors.append(f"{tag}: 추가 기능 프레임이 {len(refs)}개 (1개여야 한다)")
            continue
        if not root.findall(".//mc:AlternateContent/mc:Fallback/p:pic", NS):
            errors.append(f"{tag}: 대체 그림(Fallback)이 없다")
        rid = refs[0].get(f"{{{NS['r']}}}id")
        if rid not in srels or srels[rid][0] != RT_WEBEXT:
            errors.append(f"{tag}: 추가 기능 관계({rid})가 없거나 형식이 다르다")
            continue
        wp = srels[rid][1]
        if wp not in names:
            errors.append(f"{tag}: {wp} 파트가 없다")
            continue
        if overrides.get(wp) != CT_WEBEXT:
            errors.append(f"{tag}: {wp} 의 콘텐츠 형식이 등록되지 않았다")
        we = ET.fromstring(z.read(wp))
        ref = we.find("we:reference", NS)
        if ref is None or ref.get("id") != ADDIN_ID:
            errors.append(f"{tag}: 추가 기능 ID 가 다르다 ({None if ref is None else ref.get('id')})")
        elif (ref.get("store"), ref.get("storeType")) != ("developer", "Registry"):
            warns.append(f"{tag}: 참조 방식이 developer/Registry 가 아니다 ({ref.get('store')}/{ref.get('storeType')})")
        props, size = {}, 0
        for p in we.findall("we:properties/we:property", NS):
            raw = p.get("value") or ""
            size += len(raw)
            try:
                props[p.get("name")] = json.loads(raw)
            except ValueError:
                errors.append(f"{tag}: 설정값 '{p.get('name')}' 이 JSON 이 아니다")
        for need in ("html", "slide", "width", "height"):
            if need not in props:
                errors.append(f"{tag}: 설정값 '{need}' 이 없다")
        if size > LIMIT:
            errors.append(f"{tag}: 설정값이 {size / 1e6:.2f}MB - 한도(약 1.9MB)를 넘는다")
        html = props.get("html") or ""
        if isinstance(html, str) and html:
            htmls.add(hashlib.sha256(html.encode("utf-8", "surrogatepass")).hexdigest())
        numbers.append(props.get("slide"))
        w, h = props.get("width"), props.get("height")
        if isinstance(w, int) and isinstance(h, int) and h and abs(w / h - ratio) > 0.01:
            warns.append(f"{tag}: HTML 비율 {w}x{h} 이 슬라이드 비율과 다르다(여백이 생긴다)")
        snap = we.find("we:snapshot", NS)
        wrels = rels_of(z, wp)
        srid = None if snap is None else snap.get(f"{{{NS['r']}}}embed")
        if srid not in wrels or wrels[srid][1] not in names:
            errors.append(f"{tag}: 미리보기 그림(snapshot) 연결이 끊겼다")
        if any(t == RT_NOTES for t, _ in srels.values()):
            notes += 1
        if idx == 1 and isinstance(html, str):
            sections = count_sections(html)
            if sections and sections != len(slides):
                warns.append(f"HTML 의 <section class=\"slide\"> 는 {sections}개인데 슬라이드는 {len(slides)}장이다")
            if "__LIVE_SLIDE__" not in html and "liveSlide" not in html:
                warns.append("HTML 이 window.__LIVE_SLIDE__ 를 읽지 않는다 - 모든 슬라이드가 같은 화면일 수 있다")
            hosts = sorted({m.group(1) for m in re.finditer(r"https?://([A-Za-z0-9.-]+)", html)}
                           - {"www.w3.org"})
            if hosts:
                info.append("인터넷에서 불러올 수 있는 주소: " + ", ".join(hosts[:10]))
            for m in RRN.finditer(html):
                errors.append(f"HTML 에 주민등록번호 형식이 있다: {m.group(0)[:8]}…")
            for m in PHONE.finditer(html):
                warns.append(f"HTML 에 휴대전화 번호 형식이 있다: {m.group(0)} - 실제 번호인지 확인")

    if numbers and numbers != list(range(1, len(slides) + 1)):
        warns.append(f"슬라이드 번호 순서가 1..{len(slides)} 가 아니다: {numbers}")
    if len(htmls) > 1:
        warns.append("슬라이드마다 저장된 HTML 이 서로 다르다(의도한 것이 아니면 다시 변환)")
    info.append(f"슬라이드 {len(slides)}장 · 발표자 노트 {notes}장 · 파일 {path.stat().st_size / 1024:.0f}KB")
    return report(path)


def report(path: Path) -> int:
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
