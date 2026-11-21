#!/usr/bin/env python3
"""HTML 한 파일을 '슬라이드 안에서 실행되는' PowerPoint 파일(.pptx)로 바꾼다.

    python build_live_pptx.py deck.html -o outputs/deck.pptx

슬라이드마다 Live HTML 콘텐츠 추가 기능을 하나씩 놓고, HTML 원문을 그 추가 기능의
설정값(pptx 안의 webextension 파트)에 저장한다. 추가 기능이 등록되지 않은 PC에서는
같은 자리에 미리 찍어 둔 그림이 보인다.

덱 HTML 규칙
  - 슬라이드 하나 = <section class="slide"> 하나 (다르면 --slides 로 장수를 준다)
  - 페이지가 열릴 때 window.__LIVE_SLIDE__ (1부터)를 읽어 그 슬라이드만 보여 준다
  - 발표자 노트는 <section class="slide" data-notes="..."> 또는 <aside class="notes">…</aside>

필요: python-pptx (lxml·Pillow 포함). 미리보기 그림은 Edge·Chrome·Chromium 중 하나로 찍고,
없으면 안내 그림으로 대신한다.
"""
import argparse
import base64
import html as htmllib
import io
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    from lxml import etree
    from pptx import Presentation
    from pptx.opc.package import Part
    from pptx.opc.packuri import PackURI
    from pptx.util import Emu
except ImportError:  # pragma: no cover
    sys.exit("python-pptx 가 필요합니다:  pip install python-pptx")

ADDIN_ID = "6f2b8c1e-4d7a-4e55-9a3b-2c8f5d1e7a90"   # assets/manifest.xml 의 <Id>
ADDIN_VERSION = "1.0.0.0"

NS_WE = "http://schemas.microsoft.com/office/webextensions/webextension/2010/11"
NS_PCA = "http://schemas.microsoft.com/office/powerpoint/2013/contentapp"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
RT_WEBEXT = "http://schemas.microsoft.com/office/2011/relationships/webextension"
RT_IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
CT_WEBEXT = "application/vnd.ms-office.webextension+xml"

SLIDE_W = 12192000                      # 13.333 in
WARN_BYTES = 1_500_000                  # 추가 기능 하나가 담는 설정값이 이보다 크면 경고
MAX_BYTES = 1_900_000                   # 이보다 크면 중단 (Office 설정 저장 한도 2MB)
SECTION_RE = re.compile(r"<section\b[^>]*\bclass\s*=\s*(\"[^\"]*\"|'[^']*')[^>]*>", re.I)


# ───────────────────────── HTML 준비 ─────────────────────────

def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"{path}: UTF-8(또는 CP949)로 읽을 수 없습니다. UTF-8로 저장해 주세요.")


def is_local(url: str) -> bool:
    u = url.strip()
    if not u or u.startswith(("#", "data:", "blob:", "javascript:", "mailto:", "about:", "//")):
        return False
    return urlparse(u).scheme in ("", "file")


def local_path(url: str, base: Path) -> Path:
    p = urlparse(url.strip())
    raw = unquote(p.path)
    if p.scheme == "file":
        if re.match(r"^/[A-Za-z]:", raw):
            raw = raw[1:]
        return Path(raw)
    return (base / raw).resolve()


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    if path.suffix.lower() in (".woff2", ".woff", ".ttf", ".otf"):
        mime = "font/" + path.suffix.lower().lstrip(".")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


class Inliner:
    """로컬 파일(그림·CSS·JS·글꼴)을 HTML 안으로 넣어 한 파일로 만든다."""

    def __init__(self, base: Path):
        self.base = base
        self.inlined = []
        self.missing = []
        self.remote = set()

    def _uri(self, url: str, base: Path):
        if not is_local(url):
            if re.match(r"^(https?:)?//", url.strip()):
                self.remote.add(urlparse(url.strip() if not url.strip().startswith("//") else "https:" + url.strip()).netloc)
            return None
        path = local_path(url, base)
        if not path.is_file():
            self.missing.append(url)
            return None
        self.inlined.append(path.name)
        return data_uri(path)

    def css(self, text: str, base: Path) -> str:
        def repl_import(m):
            url = m.group(2)
            if not is_local(url):
                return m.group(0)
            path = local_path(url, base)
            if not path.is_file():
                self.missing.append(url)
                return m.group(0)
            self.inlined.append(path.name)
            return self.css(read_text(path), path.parent)

        text = re.sub(r"@import\s+(?:url\()?\s*([\"']?)([^\"')\s]+)\1\s*\)?\s*;", repl_import, text)

        def repl_url(m):
            uri = self._uri(m.group(2), base)
            return f"url({uri})" if uri else m.group(0)

        return re.sub(r"url\(\s*([\"']?)([^\"')]+)\1\s*\)", repl_url, text)

    def html(self, text: str) -> str:
        base = self.base

        def attr(tag: str, name: str):
            m = re.search(rf"\b{name}\s*=\s*(\"([^\"]*)\"|'([^']*)'|([^\s>]+))", tag, re.I)
            if not m:
                return None, None
            return m, next(g for g in m.groups()[1:] if g is not None)

        def repl_link(m):
            tag = m.group(0)
            if not re.search(r"\brel\s*=\s*[\"']?[^\"'>]*stylesheet", tag, re.I):
                return tag
            _, href = attr(tag, "href")
            if href is None:
                return tag
            href = htmllib.unescape(href)
            if not is_local(href):
                self._uri(href, base)
                return tag
            path = local_path(href, base)
            if not path.is_file():
                self.missing.append(href)
                return tag
            self.inlined.append(path.name)
            css = self.css(read_text(path), path.parent).replace("</style", "<\\/style")
            return f"<style>\n{css}\n</style>"

        text = re.sub(r"<link\b[^>]*>", repl_link, text, flags=re.I)

        def repl_script(m):
            tag, body = m.group(1), m.group(2)
            am, src = attr(tag, "src")
            if src is None:
                return m.group(0)
            src = htmllib.unescape(src)
            if not is_local(src):
                self._uri(src, base)
                return m.group(0)
            path = local_path(src, base)
            if not path.is_file():
                self.missing.append(src)
                return m.group(0)
            self.inlined.append(path.name)
            js = read_text(path).replace("</script", "<\\/script")
            return tag[:am.start()].rstrip() + tag[am.end():] + "\n" + js + "\n</script>"

        text = re.sub(r"(<script\b[^>]*>)(.*?)</script\s*>", repl_script, text, flags=re.I | re.S)

        def repl_style(m):
            return m.group(1) + self.css(m.group(2), base) + m.group(3)

        text = re.sub(r"(<style\b[^>]*>)(.*?)(</style\s*>)", repl_style, text, flags=re.I | re.S)

        def repl_src(m):
            tag = m.group(0)
            for name in ("src", "poster"):
                am, val = attr(tag, name)
                if val is None:
                    continue
                uri = self._uri(htmllib.unescape(val), base)
                if uri:
                    tag = tag[:am.start()] + f'{name}="{uri}"' + tag[am.end():]
            return tag

        text = re.sub(r"<(?:img|source|audio|video|image)\b[^>]*>", repl_src, text, flags=re.I)

        def repl_inline_style(m):
            return m.group(1) + self.css(m.group(2), base) + m.group(1)

        text = re.sub(r"(?<=\sstyle=)([\"'])(.*?)\1", lambda m: m.group(1) + self.css(m.group(2), base) + m.group(1),
                      text, flags=re.I | re.S)
        return text


def mask(html: str) -> str:
    """주석·스크립트·스타일 안쪽을 같은 길이의 공백으로 가린다(그 안의 '<section' 글자를 세지 않도록)."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    out = re.sub(r"<!--.*?-->", blank, html, flags=re.S)
    out = re.sub(r"(?<=<script)\b[^>]*>.*?(?=</script\s*>)", blank, out, flags=re.S | re.I)
    out = re.sub(r"(?<=<style)\b[^>]*>.*?(?=</style\s*>)", blank, out, flags=re.S | re.I)
    return out


def slide_starts(html: str) -> list:
    return [m for m in SECTION_RE.finditer(mask(html)) if "slide" in m.group(1).strip("\"'").split()]


def count_slides(html: str) -> int:
    return len(slide_starts(html))


def extract_notes(html: str, n: int) -> list:
    """슬라이드별 발표자 노트. data-notes 속성이 먼저, 없으면 <aside class="notes">."""
    notes = [""] * n
    starts = slide_starts(html)
    for i, m in enumerate(starts[:n]):
        tag = html[m.start():m.end()]
        end = starts[i + 1].start() if i + 1 < len(starts) else len(html)
        body = html[m.end():end]
        dm = re.search(r"\bdata-notes\s*=\s*(\"([^\"]*)\"|'([^']*)')", tag, re.I | re.S)
        if dm:
            notes[i] = htmllib.unescape(dm.group(2) if dm.group(2) is not None else dm.group(3)).strip()
            continue
        am = re.search(r"<aside\b[^>]*\bclass\s*=\s*[\"'][^\"']*\bnotes\b[^\"']*[\"'][^>]*>(.*?)</aside\s*>", body, re.I | re.S)
        if am:
            txt = re.sub(r"<br\s*/?>|</p\s*>|</li\s*>|</div\s*>", "\n", am.group(1), flags=re.I)
            txt = htmllib.unescape(re.sub(r"<[^>]+>", "", txt))
            notes[i] = "\n".join(line.strip() for line in txt.splitlines() if line.strip())
    return notes


_XML_BAD = re.compile("[^\t\n\r\u0020-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]")


def xml_safe(text: str) -> str:
    """XML 에 쓸 수 없는 제어 문자를 뺀다(제목·노트처럼 pptx 본문에 직접 들어가는 글자용)."""
    return _XML_BAD.sub("", text)


def with_slide_marker(html: str, slide: int) -> str:
    """추가 기능이 실행할 때와 똑같은 방식으로 슬라이드 번호를 끼워 넣는다(미리보기 촬영용)."""
    boot = f"<script>window.__LIVE_SLIDE__={int(slide)};</script>"
    m = re.search(r"<head[^>]*>", html, re.I)
    if m:
        return html[:m.end()] + boot + html[m.end():]
    return boot + html


# ───────────────────────── 미리보기 그림 ─────────────────────────

def find_browser(explicit: str = None):
    if explicit:
        return explicit if Path(explicit).exists() or shutil.which(explicit) else None
    env = os.environ.get("LIVE_PPTX_BROWSER")
    if env and (Path(env).exists() or shutil.which(env)):
        return env
    names = ["msedge", "microsoft-edge", "microsoft-edge-stable", "google-chrome", "google-chrome-stable",
             "chromium", "chromium-browser", "chrome"]
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    candidates = []
    for root in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
        if root:
            candidates += [Path(root) / "Microsoft/Edge/Application/msedge.exe",
                           Path(root) / "Google/Chrome/Application/chrome.exe"]
    candidates += [Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                   Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                   Path("/Applications/Chromium.app/Contents/MacOS/Chromium")]
    pw = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
    if pw.is_dir():
        candidates += sorted(pw.glob("chromium-*/chrome-linux*/chrome"), reverse=True)
        candidates += [pw / "chromium"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


CONSOLE_RE = re.compile(r'CONSOLE[:(]\d+\)?\] "(.*?)", source: (\S*) \((\d+)\)')   # 크롬 판에 따라 CONSOLE(3) 또는 CONSOLE:3


def shoot(browser: str, html: str, slides: int, w: int, h: int, outdir: Path, wait_ms: int):
    """슬라이드별 PNG(실패한 장은 None)와, 열릴 때 난 스크립트 오류 목록 [(슬라이드, 메시지)]."""
    out, problems = [], []
    profile = outdir / "profile"
    for i in range(1, slides + 1):
        page = outdir / f"slide{i}.html"
        png = outdir / f"slide{i}.png"
        page.write_text(with_slide_marker(html, i), encoding="utf-8")
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--mute-audio",
               "--no-first-run", "--no-default-browser-check", "--force-device-scale-factor=1",
               "--enable-logging=stderr", "--log-level=0",
               f"--user-data-dir={profile}", f"--window-size={w},{h}", f"--virtual-time-budget={wait_ms}",
               f"--screenshot={png}", page.resolve().as_uri()]
        try:
            r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=90, check=False)
            log = r.stderr.decode("utf-8", "replace")
        except (OSError, subprocess.TimeoutExpired):
            log = ""
        for m in CONSOLE_RE.finditer(log):
            msg = m.group(1)
            if "Uncaught" in msg or "is not defined" in msg or "SyntaxError" in msg:
                problems.append((i, f"{msg[:160]} (줄 {m.group(3)})"))
        out.append(png if png.is_file() and png.stat().st_size > 0 else None)
    return out, problems


def save_shots(pngs: list, folder: Path, cols: int = 3) -> Path:
    """장마다 미리보기 PNG 와 모아보기(sheet.jpg)를 저장한다. 눈으로 겹침·잘림을 확인하는 용도."""
    from PIL import Image, ImageDraw
    folder.mkdir(parents=True, exist_ok=True)
    thumbs = []
    for i, png in enumerate(pngs, 1):
        (folder / f"slide{i:02d}.png").write_bytes(png)
        im = Image.open(io.BytesIO(png)).convert("RGB")
        im.thumbnail((640, 640))
        thumbs.append(im)
    tw, th = thumbs[0].size
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * (th + 34) + 12), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(thumbs):
        x, y = 12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 34)
        d.text((x, y), f"slide {i + 1}", fill=(90, 90, 90))
        sheet.paste(im, (x, y + 18))
        d.rectangle([x - 1, y + 17, x + tw, y + 18 + th], outline=(200, 200, 200))
    out = folder / "sheet.jpg"
    sheet.save(out, "JPEG", quality=85)
    return out


def placeholder(i: int, w: int, h: int, path: Path) -> Path:
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (244, 241, 234))
    d = ImageDraw.Draw(im)
    d.rectangle([w * 0.08, h * 0.42, w * 0.92, h * 0.58], outline=(31, 111, 92), width=6)
    d.text((w * 0.1, h * 0.47), f"Live HTML  -  slide {i}", fill=(29, 27, 22))
    im.save(path)
    return path


def normalize_png(src: Path, w: int, h: int) -> bytes:
    """크기를 맞추고(브라우저에 따라 몇 픽셀 다를 수 있다) 용량을 줄인다."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    if im.size != (w, h):
        im = im.resize((w, h))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def poster_data_uri(png: bytes, max_w: int = 960) -> str:
    """추가 기능이 HTML을 그리기 전·그리지 못할 때 보여 줄 작은 그림."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=70, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


# ───────────────────────── pptx 조립 ─────────────────────────

def webextension_xml(props: dict, snapshot_rid: str) -> bytes:
    root = etree.Element(f"{{{NS_WE}}}webextension", nsmap={"we": NS_WE, "r": NS_R})
    root.set("id", "{%s}" % str(uuid.uuid4()).upper())
    ref = etree.SubElement(root, f"{{{NS_WE}}}reference")
    ref.set("id", ADDIN_ID)
    ref.set("version", ADDIN_VERSION)
    ref.set("store", "developer")
    ref.set("storeType", "Registry")
    etree.SubElement(root, f"{{{NS_WE}}}alternateReferences")
    pr = etree.SubElement(root, f"{{{NS_WE}}}properties")
    for k, v in props.items():
        p = etree.SubElement(pr, f"{{{NS_WE}}}property")
        p.set("name", k)
        p.set("value", json.dumps(v))        # Office 설정값은 JSON 으로 저장된다 (ASCII 만 남는다)
    etree.SubElement(root, f"{{{NS_WE}}}bindings")
    snap = etree.SubElement(root, f"{{{NS_WE}}}snapshot")
    snap.set(f"{{{NS_R}}}embed", snapshot_rid)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def frame_xml(shape_id: int, rid: str, cx: int, cy: int, title: str) -> etree._Element:
    """Microsoft 견본(office-addin-dev-settings 의 PowerPointPresentationWithContent.pptx)과 같은 구조."""
    name = htmllib.escape(title, quote=True)
    xml = (
        f'<mc:AlternateContent xmlns:mc="{NS_MC}" xmlns:p="{NS_P}" xmlns:a="{NS_A}" xmlns:r="{NS_R}">'
        f'<mc:Choice xmlns:we="{NS_WE}" xmlns:pca="{NS_PCA}" Requires="we pca">'
        f'<p:graphicFrame><p:nvGraphicFramePr>'
        f'<p:cNvPr id="{shape_id}" name="Live HTML {shape_id}" title="Live HTML" descr="{name}"/>'
        f'<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/>'
        f'</p:nvGraphicFramePr>'
        f'<p:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>'
        f'<a:graphic><a:graphicData uri="{NS_WE}"><we:webextensionref r:id="{rid}"/></a:graphicData></a:graphic>'
        f'</p:graphicFrame></mc:Choice><mc:Fallback/></mc:AlternateContent>'
    )
    return etree.fromstring(xml)


def slide_titles(html: str, n: int) -> list:
    titles = []
    starts = slide_starts(html)
    for i in range(n):
        title = ""
        if i < len(starts):
            end = starts[i + 1].start() if i + 1 < len(starts) else len(html)
            hm = re.search(r"<h[12]\b[^>]*>(.*?)</h[12]\s*>", html[starts[i].end():end], re.I | re.S)
            if hm:
                title = " ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", hm.group(1))).split())
        titles.append(xml_safe(title)[:200] or f"슬라이드 {i + 1}")
    return titles


def build(html: str, slides: int, w: int, h: int, pngs: list, notes: list, titles: list, out: Path) -> dict:
    prs = Presentation()
    prs.slide_width = Emu(SLIDE_W)
    prs.slide_height = Emu(round(SLIDE_W * h / w))
    blank = prs.slide_layouts[6]
    per_slide = 0
    for i in range(1, slides + 1):
        slide = prs.slides.add_slide(blank)
        png = pngs[i - 1]
        # 1) 미리보기 그림 - 추가 기능을 쓸 수 없는 환경에서 보이는 대체 화면
        pic = slide.shapes.add_picture(io.BytesIO(png), 0, 0, prs.slide_width, prs.slide_height)
        pic.name = f"Live HTML 미리보기 {i}"
        pic._element.nvPicPr.cNvPr.set("descr", titles[i - 1])
        image_part = slide.part.related_part(pic._element.blipFill.blip.rEmbed)

        # 2) webextension 파트 - HTML 원문과 작은 미리보기가 여기에 들어간다
        props = {"html": html, "slide": i, "width": w, "height": h, "poster": poster_data_uri(png)}
        per_slide = max(per_slide, sum(len(json.dumps(v)) for v in props.values()))
        we_part = Part(PackURI(f"/ppt/webextensions/webextension{i}.xml"), CT_WEBEXT, prs.part.package, b"")
        snap_rid = we_part.relate_to(image_part, RT_IMAGE)
        we_part._blob = webextension_xml(props, snap_rid)
        we_rid = slide.part.relate_to(we_part, RT_WEBEXT)

        # 3) 그림을 "추가 기능 프레임 / 대체 그림" 묶음으로 감싼다
        pic_el = pic._element
        used = [int(x) for x in slide.shapes._spTree.xpath(".//p:cNvPr/@id")]
        alt = frame_xml(max(used) + 1, we_rid, prs.slide_width, prs.slide_height, titles[i - 1])
        pic_el.addprevious(alt)
        alt.find(f"{{{NS_MC}}}Fallback").append(pic_el)

        if notes[i - 1]:
            slide.notes_slide.notes_text_frame.text = notes[i - 1]

    prs.core_properties.title = titles[0] if titles else out.stem
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return {"per_slide_bytes": per_slide}



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
    ap.add_argument("html", type=Path, help="슬라이드 덱 HTML")
    ap.add_argument("-o", "--out", type=Path, help="출력 pptx 경로 (기본: HTML 과 같은 이름)")
    ap.add_argument("--slides", type=int, help="슬라이드 수 (기본: <section class=\"slide\"> 개수)")
    ap.add_argument("--size", default="1920x1080", help="HTML 기준 해상도 (기본 1920x1080)")
    ap.add_argument("--browser", help="미리보기 그림을 찍을 Edge·Chrome 실행 파일 경로")
    ap.add_argument("--wait", type=int, default=4000, help="미리보기를 찍기 전 기다리는 시간(ms, 기본 4000)")
    ap.add_argument("--no-inline", action="store_true", help="로컬 그림·CSS·JS 를 HTML 안으로 넣지 않는다")
    ap.add_argument("--save-html", type=Path, help="한 파일로 합친 HTML 을 따로 저장한다")
    ap.add_argument("--shots", type=Path, help="장마다 미리보기 PNG 와 모아보기(sheet.jpg)를 이 폴더에 저장한다")
    args = ap.parse_args()

    if not args.html.is_file():
        ap.error(f"파일이 없습니다: {args.html}")
    try:
        w, h = (int(x) for x in args.size.lower().split("x"))
    except ValueError:
        ap.error("--size 는 1920x1080 꼴로 씁니다")
    html = read_text(args.html)

    inl = Inliner(args.html.resolve().parent)
    if not args.no_inline:
        html = inl.html(html)
    if args.save_html:
        args.save_html.parent.mkdir(parents=True, exist_ok=True)
        args.save_html.write_text(html, encoding="utf-8")

    found = count_slides(html)
    n = args.slides or found
    if args.slides and found and args.slides != found:
        print(f"주의: --slides {args.slides} 인데 HTML 의 <section class=\"slide\"> 는 {found}개입니다.")
    if n < 1:
        ap.error('슬라이드를 찾지 못했습니다. <section class="slide"> 로 나누거나 --slides 로 장수를 주세요.')
    if "__LIVE_SLIDE__" not in html:
        print("주의: HTML 이 window.__LIVE_SLIDE__ 를 읽지 않습니다. 모든 슬라이드가 같은 화면으로 보일 수 있습니다.")

    size = len(json.dumps(html))
    if size > MAX_BYTES:
        print(f"오류: HTML 이 {size / 1e6:.2f}MB 입니다(한도 약 {MAX_BYTES / 1e6:.1f}MB). "
              "큰 그림·글꼴·영상을 줄이거나 인터넷 주소로 불러오게 바꾸세요.")
        return 2
    if size > WARN_BYTES:
        print(f"주의: HTML 이 {size / 1e6:.2f}MB 로 큽니다. 슬라이드마다 한 벌씩 들어가 파일이 커지고 열 때 느릴 수 있습니다.")

    notes = [xml_safe(x) for x in extract_notes(html, n)]
    titles = slide_titles(html, n)
    out = args.out or args.html.with_suffix(".pptx")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        browser = find_browser(args.browser)
        shots, problems = shoot(browser, html, n, w, h, tmpdir, args.wait) if browser else ([None] * n, [])
        pngs, drawn = [], 0
        for i, s in enumerate(shots, 1):
            if s is None:
                s = placeholder(i, w, h, tmpdir / f"ph{i}.png")
            else:
                drawn += 1
            pngs.append(normalize_png(s, w, h))
        info = build(html, n, w, h, pngs, notes, titles, out)
        sheet = save_shots(pngs, args.shots) if args.shots else None

    print(f"완료: {out}")
    print(f"  슬라이드 {n}장 · HTML {len(html.encode('utf-8')) / 1024:.0f}KB · 파일 {out.stat().st_size / 1024:.0f}KB · "
          f"발표자 노트 {sum(1 for x in notes if x)}장")
    if inl.inlined:
        print(f"  HTML 안으로 넣은 로컬 파일 {len(inl.inlined)}개: {', '.join(sorted(set(inl.inlined))[:8])}")
    if inl.missing:
        print(f"  주의: 찾지 못한 로컬 파일 {len(inl.missing)}개: {', '.join(sorted(set(inl.missing))[:8])}")
    if inl.remote:
        print(f"  인터넷에서 불러오는 주소(발표할 때 인터넷 필요): {', '.join(sorted(inl.remote))}")
    if sheet:
        print(f"  미리보기 모아보기: {sheet}")
    for slide_no, msg in problems[:10]:
        print(f"  주의: 슬라이드 {slide_no} 를 열 때 스크립트 오류 - {msg}")
    if not browser:
        print("  주의: Edge·Chrome 을 찾지 못해 미리보기를 안내 그림으로 대신했습니다(--browser 로 경로 지정).")
    elif drawn < n:
        print(f"  주의: 미리보기 {n - drawn}장을 찍지 못해 안내 그림으로 대신했습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
