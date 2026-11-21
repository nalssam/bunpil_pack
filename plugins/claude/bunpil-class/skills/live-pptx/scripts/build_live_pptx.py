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
  - 그림·CSS·JS 는 덱 HTML 과 같은 폴더(또는 그 아래)에 둔다. 그 밖의 파일은 --allow-outside 를 줘야 넣는다

종료 코드: 0 완료 · 1 파일을 쓸 수 없음(또는 --strict 에서 주의가 있음) · 2 쓰는 법이 틀림 · 3 HTML 이 너무 큼

필요: python-pptx (lxml·Pillow 포함). 미리보기 그림은 Edge·Chrome·Chromium 중 하나로 찍고,
없으면 안내 그림으로 대신한다.
"""
import argparse
import base64
import collections
import datetime
import hashlib
import html as htmllib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from html.parser import HTMLParser
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
# 저장 크기 = len(json.dumps(html)): 설정값 'html' 하나가 pptx 안에서 차지하는 글자 수(qa_live_pptx.py 도 같은 값을 잰다).
# 실제 PowerPoint(Microsoft 365, Office LTSC 2024)에서 잰 결과: 4,000,000 은 열려서 실행되고 10,000,000 은 빈 값으로 돌아온다.
WARN_BYTES = 1_500_000                  # 이보다 크면 경고
MAX_BYTES = 3_000_000                   # 이보다 크면 중단
SHOT_TIMEOUT = 45                       # 미리보기 한 장을 기다리는 시간(초)

# HTML 안으로 넣는 파일 형식(그림·글꼴·CSS·JS·소리·영상·JSON). 여기에 없는 확장자는 넣지 않는다.
MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml",
    ".webp": "image/webp", ".avif": "image/avif", ".bmp": "image/bmp", ".ico": "image/x-icon",
    ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf",
    ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json",
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg", ".oga": "audio/ogg", ".m4a": "audio/mp4",
    ".aac": "audio/aac", ".flac": "audio/flac",
    ".mp4": "video/mp4", ".webm": "video/webm", ".ogv": "video/ogg", ".m4v": "video/mp4", ".mov": "video/quicktime",
}


# ───────────────────────── HTML 준비 ─────────────────────────

def decode(data: bytes):
    """(글자, 읽은 방식). UTF-8 이 아니면 CP949 로 읽어 보고, 둘 다 아니면 (None, None)."""
    for enc in ("utf-8-sig", "cp949"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return None, None


def read_text(path: Path) -> str:
    text, _ = decode(path.read_bytes())
    if text is None:
        raise SystemExit(f"{path}: UTF-8(또는 CP949)로 읽을 수 없습니다. UTF-8로 저장해 주세요.")
    return text


_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")          # C:\... 또는 C:/... (Windows 의 전체 경로)
_REMOTE = re.compile(r"^(?:https?:)?//", re.I)


def is_local(url: str) -> bool:
    u = url.strip()
    if not u or u.startswith(("#", "//")) or "${" in u or "{{" in u:
        return False
    if _DRIVE.match(u):
        return True
    try:
        return urlparse(u).scheme.lower() in ("", "file")
    except ValueError:                           # "https://[학교서버]/a.png" 처럼 주소로 읽을 수 없는 글자: 로컬 파일이 아니다
        return False


def local_path(url: str, base: Path, resolve: bool = True) -> Path:
    u = url.strip()
    if _DRIVE.match(u):
        return Path(unquote(re.split(r"[?#]", u, maxsplit=1)[0]))
    p = urlparse(u)
    raw = unquote(p.path).replace("\\", "/")     # 브라우저는 주소의 \ 를 / 로 읽는다
    if p.scheme.lower() == "file":
        if re.match(r"^/[A-Za-z]:", raw):
            raw = raw[1:]
        return Path(raw)
    return (base / raw).resolve() if resolve else base / raw


def data_uri(path: Path) -> str:
    mime = MIME.get(path.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


Attr = collections.namedtuple("Attr", "name value a0 a1 v0 v1 quote")   # a0:a1 = 속성 전체, v0:v1 = 값(따옴표 안쪽)

_RAW_ELEMENTS = ("script", "style", "textarea", "title", "xmp", "iframe", "noembed", "noframes", "noscript")
_RAW_END = {name: re.compile(r"</%s(?=[\s/>])" % name, re.I) for name in _RAW_ELEMENTS}
_COMMENT_END = re.compile(r"--!?>")
_TAG_NAME = re.compile(r"[^\s/>]+")
_TAG_GAP = re.compile(r"[\s/]*")
_TAG_ATTR = re.compile(r"""(=[^\s/>=]*|[^\s/>=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>"'][^\s>]*)?))?""")
_SCRIPT_STEP = re.compile(r"<!--|-->|<(/?)script(?=[\s/>])", re.I)


def _script_end(text: str, start: int) -> int:
    """<script> 본문이 끝나는 자리(닫는 태그가 시작하는 곳). 브라우저처럼, 본문 속 "<!-- <script> … </script> -->" 의
    </script> 는 본문으로 본다."""
    state = 0                                    # 0 보통 · 1 "<!--" 뒤 · 2 그 안의 "<script" 뒤
    for m in _SCRIPT_STEP.finditer(text, start):
        tok = m.group(0)
        if tok == "<!--":
            if state == 0 and not text.startswith((">", "->"), m.end()):
                state = 1
        elif tok == "-->":
            state = 0
        elif m.group(1):
            if state != 2:
                return m.start()
            state = 1
        elif state == 1:
            state = 2
    return len(text)


def _tag_rest(text: str, j: int):
    """태그 이름 뒤(j)부터 태그가 끝나는 > 까지 읽는다: (속성들, > 다음 자리, "/>" 로 끝났는가). 끝나지 않으면 None.
    따옴표로 싼 속성값 속의 > 는 태그의 끝이 아니다."""
    attrs, n = [], len(text)
    while True:
        gap = _TAG_GAP.match(text, j)
        j = gap.end()
        if j >= n:
            return None
        if text[j] == ">":
            return attrs, j + 1, gap.group(0).endswith("/")
        m = _TAG_ATTR.match(text, j)
        if m.end() == m.end(1):
            value, v0, v1, quote = None, m.end(), m.end(), ""
        elif m.group(2) is not None:
            value, v0, v1, quote = m.group(2), m.start(2), m.end(2), '"'
        elif m.group(3) is not None:
            value, v0, v1, quote = m.group(3), m.start(3), m.end(3), "'"
        elif m.group(4) is not None:
            value, v0, v1, quote = m.group(4), m.start(4), m.end(4), ""
        else:
            value, v0, v1, quote = "", m.end(), m.end(), ""
        attrs.append(Attr(m.group(1).lower(), value, m.start(), m.end(), v0, v1, quote))
        j = m.end()


def html_tokens(text: str):
    """HTML 을 앞에서부터 훑어 ("tag", 이름, 속성들, 시작, 끝) 과 ("raw", 이름, 시작, 끝) 을 차례로 낸다.
    "raw" 는 <script>·<style> 처럼 안쪽이 태그가 아닌 요소의 본문이다. 주석 안과 그런 본문 안은 태그로 읽지 않는다."""
    pos, n = 0, len(text)
    while pos < n:
        i = text.find("<", pos)
        if i < 0 or i + 1 >= n:
            return
        if text.startswith("<!--", i):
            if text.startswith(">", i + 4):
                pos = i + 5
            elif text.startswith("->", i + 4):
                pos = i + 6
            else:
                m = _COMMENT_END.search(text, i + 4)
                pos = m.end() if m else n                    # 닫지 않은 주석은 끝까지 주석이다
            continue
        closing = text[i + 1] == "/"
        first = text[i + 2:i + 3] if closing else text[i + 1]
        if not ("a" <= first.lower() <= "z"):
            if closing or first in "!?":                     # doctype, </> 같은 것: 다음 > 까지 건너뛴다
                j = text.find(">", i + 2)
                pos = j + 1 if j >= 0 else n
            else:
                pos = i + 1
            continue
        m = _TAG_NAME.match(text, i + (2 if closing else 1))
        name = m.group(0).lower()
        rest = _tag_rest(text, m.end())
        if rest is None:
            return                                           # 끝나지 않은 태그: 여기서 그만둔다
        attrs, j, self_closing = rest
        pos = j
        if closing:
            continue
        yield ("tag", name, attrs, i, j)
        if name in _RAW_ELEMENTS and not self_closing:       # <title/> 꼴(SVG 안)은 빈 요소로 본다
            if name == "script":
                pos = _script_end(text, j)
            else:
                m = _RAW_END[name].search(text, j)
                pos = m.start() if m else n
            yield ("raw", name, j, pos)


_CSS_TOKEN = re.compile(r"""
    /\*.*?(?:\*/|\Z)
  | @import\s*(?:url\(\s*(?:"(?P<iu1>[^"]*)"|'(?P<iu2>[^']*)'|(?P<iu3>[^)"'\s]*))\s*\)|"(?P<is1>[^"]*)"|'(?P<is2>[^']*)')
        (?P<rest>[^;{}]*);?
  | url\(\s*(?:"(?P<u1>[^"]*)"|'(?P<u2>[^']*)'|(?P<u3>[^)"'\s]+))\s*\)
  | (?P<set>(?:-webkit-)?image-set\()
  | (?P<str>"(?:[^"\\\n]|\\.)*"?|'(?:[^'\\\n]|\\.)*'?)
  | (?P<paren>[()])
""", re.I | re.S | re.X)
_CSS_CHARSET = re.compile(r"\A\s*@charset\s+[\"'][^\"']*[\"']\s*;", re.I)
_JS_TYPES = ("module", "text/javascript", "application/javascript", "text/ecmascript", "application/ecmascript",
             "application/x-javascript", "text/jscript")
_JS_IMPORT = re.compile(r"""\b(?:from|import)\s*\(?\s*["']\.{1,2}/[^"'\n]+["']""")
_JS_FILE = re.compile(r"\.(?:png|jpe?g|gif|svg|webp|avif|mp3|wav|ogg|m4a|mp4|webm|json|csv|css|js|woff2?)(?=[\"'`)?#])", re.I)
_HOST = re.compile(r"https?://([A-Za-z0-9.-]+)", re.I)
_LINK_LOADS = {"stylesheet", "preload", "prefetch", "modulepreload", "preconnect", "dns-prefetch"}
_URL_ATTRS = {"img": ("src",), "source": ("src",), "audio": ("src",), "video": ("src", "poster"),
              "image": ("href", "xlink:href"), "feimage": ("href", "xlink:href")}
_URL_ATTRS.update({name: ("background",) for name in ("body", "table", "thead", "tbody", "tfoot", "tr", "td", "th")})
# 넣을 수 없는 참조: PowerPoint 안에서는 열리지 않으니 알려 주기만 한다(<a href> 는 누르면 다른 파일을 여는 링크)
_LEFT_ATTRS = {"iframe": ("src",), "object": ("data",), "embed": ("src",), "track": ("src",), "input": ("src",),
               "use": ("href", "xlink:href"), "a": ("href", "xlink:href"), "area": ("href",)}


def _first(m, *names):
    for name in names:
        if m.group(name) is not None:
            return m.group(name)
    return ""


def _set(attr: Attr, value: str):
    """속성 값만 바꾼다. 쓴 사람이 쓴 따옴표를 그대로 둔다(따옴표 없이 쓴 값만 큰따옴표로 싼다)."""
    return attr.v0, attr.v1, value if attr.quote else '"' + value + '"'


def _apply(text: str, edits: list) -> str:
    if not edits:
        return text
    out, pos = [], 0
    for start, end, new in sorted(edits, key=lambda e: e[0]):
        if start < pos:
            continue
        out += [text[pos:start], new]
        pos = end
    out.append(text[pos:])
    return "".join(out)


class Inliner:
    """로컬 파일(그림·CSS·JS·글꼴)을 HTML 안으로 넣어 한 파일로 만든다.

    - 덱 폴더(HTML 이 있는 폴더) 안의 파일만 넣는다. 밖의 파일은 allow_outside 일 때만 넣는다.
    - <script> 본문과 주석 안은 고치지 않는다. <style> 본문과 style 속성은 CSS 의 url()·@import 만 고친다."""

    def __init__(self, base: Path, allow_outside: bool = False):
        self.base = base
        self.root = base.resolve()
        self.allow_outside = allow_outside
        self.inlined = []          # 넣은 파일(덱 폴더 기준 경로)
        self.missing = []          # 찾지 못한 로컬 파일(HTML 에 적힌 그대로)
        self.outside = []          # 덱 폴더 밖이라 넣지 않은 파일(전체 경로)
        self.left = []             # 합치지 못한 로컬 참조
        self.warnings = []         # 그 밖에 알려 줄 것
        self.remote = set()        # 인터넷에서 불러오는 주소
        self.script_hosts = set()  # 스크립트 본문에 적힌 인터넷 주소
        self.hidden_js = []        # data URI 로 넣은 스크립트의 원문(HTML 글자만 보아서는 보이지 않는다)
        self._cache = {}
        self._js_seen = set()

    @staticmethod
    def _add(items: list, item: str) -> None:
        if item not in items:
            items.append(item)

    def _name(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def _remote(self, url: str) -> None:
        u = url.strip()
        if _REMOTE.match(u):
            try:
                host = urlparse("https:" + u if u.startswith("//") else u).hostname
            except ValueError:
                host = None
            if host:
                self.remote.add(host.lower())

    def _file(self, url: str, base: Path, exts=None):
        """로컬 주소가 가리키는, 넣어도 되는 파일. 넣지 않을 때는 이유를 적어 두고 None."""
        try:
            if os.name != "nt" and _DRIVE.match(url.strip()):
                raise OSError("Windows 경로")
            path = local_path(url, base, resolve=False).resolve()
            if not path.is_file():
                raise OSError("파일 없음")
        except (OSError, ValueError):
            self._add(self.missing, url)
            return None
        try:
            path.relative_to(self.root)
        except ValueError:
            if not self.allow_outside:
                self._add(self.outside, str(path))
                return None
        if path.suffix.lower() not in (exts or MIME):
            self._add(self.left, f"{url} (넣지 않는 형식)")
            return None
        return path

    def _read(self, path: Path):
        try:
            text, _ = decode(path.read_bytes())
        except OSError:
            text = None
        if text is None:
            self._add(self.left, f"{self._name(path)} (글자를 읽을 수 없음)")
        return text

    def _uri(self, url: str, base: Path):
        if not is_local(url):
            self._remote(url)
            return None
        path = self._file(url, base)
        if path is None:
            return None
        if path not in self._cache:
            try:
                self._cache[path] = data_uri(path)
            except OSError:
                self._add(self.missing, url)
                return None
        self._add(self.inlined, self._name(path))
        return self._cache[path]

    # ── CSS ──

    def css(self, text: str, base: Path, attr: bool = False) -> str:
        """CSS 안의 url(...) 과 @import 가 가리키는 로컬 파일을 넣는다. 주석과 문자열 안은 건드리지 않는다."""
        hoisted, body = self._css(text, base, (), attr)
        return "".join(hoisted) + body

    def _css(self, text: str, base: Path, chain: tuple, attr: bool = False):
        out, hoisted, pos, merged = [], [], 0, False
        opened = []                                 # 열려 있는 괄호마다: image-set( 이면 True
        for m in _CSS_TOKEN.finditer(text):
            tok = m.group(0)
            if tok[0] == "/":
                continue
            if m.group("set") or m.group("paren"):
                if tok == ")":
                    del opened[-1:]
                else:
                    opened.append(tok != "(")
                continue
            if m.group("str"):                      # 문자열은 image-set("a.png" 1x) 의 주소일 때만 넣는다
                if not (opened and opened[-1]) or len(tok) < 2 or tok[-1] != tok[0] or "\\" in tok:
                    continue
                uri = self._uri(htmllib.unescape(tok[1:-1]) if attr else tok[1:-1], base)
                if uri is None:
                    continue
                new = f"url({uri})"
            elif tok[0] == "@":
                got = self._css_import(_first(m, "iu1", "iu2", "iu3", "is1", "is2"), " ".join(m.group("rest").split()),
                                       base, chain)
                if got is None:                     # 그대로 두는 @import (인터넷 주소 등)
                    if not merged:
                        continue
                    # 앞에 다른 파일을 합쳐 넣었으면 뒤따르는 @import 는 효력이 없다. 맨 앞으로 올린다.
                    hoisted.append(tok if tok.rstrip().endswith(";") else tok + ";")
                    new = ""
                else:
                    sub_hoisted, new = got
                    if merged:
                        hoisted += sub_hoisted
                    else:
                        new = "".join(sub_hoisted) + new
                    merged = True
            else:
                url = _first(m, "u1", "u2", "u3")
                if attr:
                    url = htmllib.unescape(url).strip().strip("\"'")
                uri = self._uri(url, base)
                if uri is None:
                    continue
                new = f"url({uri})"
            out += [text[pos:m.start()], new]
            pos = m.end()
        out.append(text[pos:])
        return hoisted, "".join(out)

    def _css_import(self, url: str, rest: str, base: Path, chain: tuple):
        if not url.strip():
            return None
        if not is_local(url):
            self._remote(url)
            return None
        if re.search(r"\b(?:layer|supports)\b", rest, re.I):
            self._add(self.left, f'@import "{url}" {rest}')
            return None
        path = self._file(url, base, (".css",))
        if path is None:
            return None
        got = self._css_file(path, chain)
        if got is None:
            return None
        hoisted, body = got
        if rest:                                    # @import "print.css" print;  ->  @media print{...}
            body = "@media %s{\n%s\n}" % (rest, body)
            hoisted = [h if _CSS_TOKEN.match(h).group("rest").strip() else h.rstrip().rstrip(";") + " " + rest + ";"
                       for h in hoisted]
        return hoisted, body

    def _css_file(self, path: Path, chain: tuple = ()):
        """CSS 파일 하나를 (맨 앞에 둘 @import 들, 본문) 으로 읽는다. 읽지 못하면 None."""
        if path in chain:
            return [], ""                           # 서로를 불러오는 CSS: 한 번만 넣는다
        text = self._read(path)
        if text is None:
            return None
        self._add(self.inlined, self._name(path))
        return self._css(_CSS_CHARSET.sub("", text, 1), path.parent, chain + (path,))

    # ── HTML ──

    def html(self, text: str) -> str:
        edits = []
        toks = list(html_tokens(text))
        for k, tok in enumerate(toks):
            if tok[0] == "raw":
                _, name, start, end = tok
                if name == "style":
                    new = re.sub(r"</(style)", r"<\\/\1", self.css(text[start:end], self.base), flags=re.I)
                    if new != text[start:end]:
                        edits.append((start, end, new))
                elif name == "script":
                    self._scan_script(text[start:end])
                continue
            _, name, attrs, start, end = tok
            first = {}
            for a in attrs:
                first.setdefault(a.name, a)
            if name == "link":
                self._link(text, first, attrs, start, end, edits)
                continue
            if name == "script":
                nxt = toks[k + 1] if k + 1 < len(toks) else None
                self._script(text, first, start, end, nxt if nxt and nxt[0] == "raw" else None, edits)
                continue
            self._media(name, first, edits)
            style = first.get("style")
            if style is not None and style.value and re.search(r"url\(|image-set\(", style.value, re.I):
                new = self.css(style.value, self.base, attr=True)
                if new != style.value:
                    edits.append((style.v0, style.v1, new))
        return _apply(text, edits)

    def _link(self, text, a, attrs, start, end, edits) -> None:
        href = a.get("href")
        if href is None or not href.value:
            return
        rel = (a["rel"].value or "").lower().split() if "rel" in a else []
        url = htmllib.unescape(href.value)
        if not is_local(url):
            if _LINK_LOADS.intersection(rel):
                self._remote(url)
            return
        if "stylesheet" not in rel:
            if {"preload", "prefetch", "modulepreload"}.intersection(rel):
                self._add(self.left, f'<link rel="{" ".join(rel)}" href="{url}">')
            return
        if "alternate" in rel or "disabled" in a:
            self._add(self.left, f'<link rel="{" ".join(rel)}" href="{url}"> (꺼 둔 스타일)')
            return
        path = self._file(url, self.base, (".css",))
        got = self._css_file(path) if path is not None else None
        if got is None:
            return
        css = re.sub(r"</(style)", r"<\\/\1", "".join(got[0]) + got[1], flags=re.I)
        keep = "".join(" " + text[x.a0:x.a1] for x in attrs if x.name in ("media", "title"))
        edits.append((start, end, f"<style{keep}>\n{css}\n</style>"))

    def _script(self, text, a, start, end, body, edits) -> None:
        src = a.get("src")
        if src is None or not src.value:
            return
        kind = (a["type"].value or "").split(";")[0].strip().lower() if "type" in a else ""
        if "nomodule" in a or (kind and kind not in _JS_TYPES):
            return                                  # 브라우저가 실행하지 않는 스크립트
        url = htmllib.unescape(src.value)
        if not is_local(url):
            self._remote(url)
            return
        path = self._file(url, self.base, (".js", ".mjs"))
        if path is None:
            return
        try:
            raw = path.read_bytes()
        except OSError:
            self._add(self.missing, url)
            return
        name = self._name(path)
        js, _ = decode(raw)
        if js is not None:
            raw = js.encode("utf-8")
            self._scan_script(js)
            if kind == "module" and _JS_IMPORT.search(js):
                self._add(self.warnings, f"모듈 {name} 이 다른 파일을 import 합니다. 그 파일은 함께 들어가지 않으니 "
                                         "한 파일로 합쳐 주세요.")
        self._add(self.inlined, name)
        if kind == "module" or "defer" in a or "async" in a or js is None or "<!--" in js or body is None:
            # 실행 시점(defer·async·module)을 지키려면 태그를 그대로 두고 주소만 data URI 로 바꾼다.
            # 글자로 읽은 스크립트는 UTF-8 로 다시 적어 넣었으니 charset 도 같이 적는다(태그에 charset="euc-kr" 가 남아 있어도 깨지지 않게).
            self.hidden_js.append(js or "")
            mime = "text/javascript" if js is None else "text/javascript;charset=utf-8"
            edits.append(_set(src, f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")))
            return
        tag = text[start:src.a0].rstrip() + text[src.a1:end]
        js = re.sub(r"</(script)", r"<\\/\1", js, flags=re.I)
        tail = "" if body[3] < len(text) else "</script>"
        edits.append((start, body[3], tag + "\n" + js + "\n" + tail))

    def _media(self, name, a, edits) -> None:
        for attr_name in _URL_ATTRS.get(name, ()):
            at = a.get(attr_name)
            if at is not None and at.value:
                uri = self._uri(htmllib.unescape(at.value), self.base)
                if uri:
                    edits.append(_set(at, uri))
        at = a.get("srcset") if name in ("img", "source") else None
        if at is not None and at.value:
            new = self._srcset(at.value)
            if new != at.value:
                edits.append(_set(at, new))
        if name == "input" and ("type" not in a or (a["type"].value or "").strip().lower() != "image"):
            return
        for attr_name in _LEFT_ATTRS.get(name, ()):
            at = a.get(attr_name)
            if at is not None and at.value:
                url = htmllib.unescape(at.value)
                if is_local(url):
                    if re.split(r"[?#]", url.strip(), maxsplit=1)[0]:        # "?page=2" 처럼 파일 이름이 없는 것은 참조가 아니다
                        self._add(self.left, f'<{name} {attr_name}="{url}">')
                elif name not in ("a", "area"):                     # 링크는 누르기 전에는 불러오지 않는다
                    self._remote(url)

    def _srcset(self, value: str) -> str:
        """srcset 의 후보("주소 1x, 주소 2x")마다 로컬 그림을 넣는다."""
        edits, i, n = [], 0, len(value)
        while True:
            while i < n and (value[i].isspace() or value[i] == ","):
                i += 1
            if i >= n:
                break
            j = i
            while j < n and not value[j].isspace():
                j += 1
            url = value[i:j].rstrip(",")
            uri = self._uri(htmllib.unescape(url), self.base)
            if uri:
                edits.append((i, i + len(url), uri))
            if len(url) < j - i:                    # 주소 바로 뒤가 쉼표: 후보 하나가 끝났다
                i = j
                continue
            depth = 0
            while j < n and not (value[j] == "," and depth == 0):
                depth += {"(": 1, ")": -1}.get(value[j], 0)
                j += 1
            i = j
        return _apply(value, edits)

    def _scan_script(self, js: str) -> None:
        """스크립트 본문은 고치지 않는다. 인터넷 주소와, 덱 폴더의 파일을 가리키는 문자열만 찾아 적어 둔다."""
        for m in _HOST.finditer(js):
            host = m.group(1).strip(".-").lower()
            if host and host != "www.w3.org":
                self.script_hosts.add(host)
        for m in _JS_FILE.finditer(js):
            end = m.end()
            begin = max(js.rfind(q, max(0, end - 300), end) for q in "\"'`(")
            if begin < 0:
                continue
            url = js[begin + 1:end].strip()
            if not url or url in self._js_seen or any(c in url for c in "\n\\<>{}$;=+,") or not is_local(url):
                continue
            self._js_seen.add(url)
            try:
                path = local_path(url, self.base, resolve=False)
                if path.is_file():
                    path.resolve().relative_to(self.root)
                    self._add(self.left, f"{url} (스크립트 안)")
            except (OSError, ValueError):
                continue


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


def scan_slides(html: str) -> list:
    parser = SlideScanner()
    try:
        parser.feed(html)
        parser.close()
    except Exception:           # 읽다 멈춰도 거기까지 찾은 것으로 계속한다
        pass
    return parser.result()


def count_slides(html: str) -> int:
    return len(scan_slides(html))


_XML_BAD = re.compile("[^\t\n\r\u0020-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]")


def xml_safe(text: str) -> str:
    """XML 에 쓸 수 없는 제어 문자를 뺀다(제목·노트처럼 pptx 본문에 직접 들어가는 글자용)."""
    return _XML_BAD.sub("", text)


def _notes(slides: list, n: int) -> list:
    return [slides[i]["notes"] if i < len(slides) else "" for i in range(n)]


def _titles(slides: list, n: int) -> list:
    return [xml_safe(slides[i]["title"] if i < len(slides) else "")[:200] or f"슬라이드 {i + 1}" for i in range(n)]


def extract_notes(html: str, n: int) -> list:
    """슬라이드별 발표자 노트. data-notes 속성이 먼저, 없으면 <aside class="notes">."""
    return _notes(scan_slides(html), n)


def slide_titles(html: str, n: int) -> list:
    """슬라이드별 제목(그 슬라이드의 첫 h1·h2·h3). 없으면 '슬라이드 N'."""
    return _titles(scan_slides(html), n)


_HTML_SPACE = " \t\n\f\r"


def _tag_end(s: str, i: int) -> int:
    """i 는 태그 이름 바로 뒤. 따옴표로 싼 속성값 속의 > 는 건너뛰고, 태그를 닫는 > 다음 자리를 돌려준다(없으면 -1)."""
    n = len(s)
    while i < n:
        c = s[i]
        if c == ">":
            return i + 1
        i += 1
        if c != "=":
            continue
        while i < n and s[i] in _HTML_SPACE:
            i += 1
        q = s[i:i + 1]
        if q == '"' or q == "'":
            i = s.find(q, i + 1)
            if i < 0:
                return -1
            i += 1
        else:
            while i < n and s[i] not in _HTML_SPACE and s[i] != ">":
                i += 1
    return -1


def head_insertion_point(html: str) -> int:
    """추가 기능 페이지(bridgeSpot)가 덱에 스크립트를 끼워 넣는 자리와 같은 곳을 고른다. 두 곳의 규칙은 같아야 한다.

    덱의 머리말(공백·주석·doctype·<html …>·<head …>)만 앞에서부터 차례로 읽고, 진짜 <head> 바로 뒤
    (없으면 <html> 뒤, 그것도 없으면 doctype 뒤나 맨 앞)를 돌려준다. 문서 전체에서 "<head" 를 찾지 않으므로
    주석·스크립트 문자열·속성값 속의 "<head>" 나 <header> 에 속지 않는다."""
    s, n, i, saw_html = html, len(html), 0, False
    while i < n:
        if s[i] in _HTML_SPACE:
            i += 1
            continue
        if s[i] != "<":
            break
        t = s[i:i + 10].lower()
        if t.startswith("<!--"):
            j = s.find("-->", i + 2)
            if j < 0:
                break
            i = j + 3
            continue
        if not saw_html and (t.startswith("<!doctype") or t.startswith("<?")):
            j = s.find(">", i)
            if j < 0:
                break
            i = j + 1
            continue
        if not saw_html and re.match(r"<html[ \t\n\f\r/>]", t):
            j = _tag_end(s, i + 5)
            if j < 0:
                break
            i, saw_html = j, True
            continue
        if re.match(r"<head[ \t\n\f\r/>]", t):
            j = _tag_end(s, i + 5)
            if j > 0:
                i = j
        break
    return i


# 미리보기를 찍을 때 덱에 넣는 스크립트. 추가 기능 페이지(bridgeSource)가 넣어 주는 것과 같은 것을 준다:
# 격리된 틀에서는 막혀 있는 localStorage·sessionStorage(그 장이 떠 있는 동안만 기억)·쿠키(빈 값)·history.pushState 를
# 덱이 멈추지 않게 메우고, alert·confirm(항상 예)·prompt(기본값)·window.open 은 창을 띄우지 않는다.
_SNAPSHOT_SHIMS = (
    "(function(){"
    "function mem(){var d={};return{getItem:function(k){k=String(k);return Object.prototype.hasOwnProperty.call(d,k)?d[k]:null},"
    "setItem:function(k,v){d[String(k)]=String(v)},removeItem:function(k){delete d[String(k)]},clear:function(){d={}},"
    "key:function(i){var a=Object.keys(d);return i<a.length?a[i]:null},get length(){return Object.keys(d).length}}}"
    "function fill(n){var ok=false;try{ok=!!window[n]}catch(e){}"
    "if(!ok){try{Object.defineProperty(window,n,{configurable:true,value:mem()})}catch(e){}}}"
    'fill("localStorage");fill("sessionStorage");'
    'try{document.cookie}catch(e){try{Object.defineProperty(document,"cookie",{configurable:true,get:function(){return ""},'
    "set:function(){}})}catch(e2){}}"
    'var H=window.history;if(H){["pushState","replaceState"].forEach(function(f){var o=H[f];if(typeof o!=="function")return;'
    "H[f]=function(){try{return o.apply(H,arguments)}catch(e){}}})}"
    "})();"
    "window.alert=function(){};window.confirm=function(){return true};"
    "window.prompt=function(m,d){return d===undefined?null:String(d)};"
    "window.open=function(){return null};"
)
SNAPSHOT_SANDBOX = "allow-scripts allow-forms"      # 추가 기능 페이지의 <iframe id="view" sandbox="…"> 와 같아야 한다


def with_slide_marker(html: str, slide: int) -> str:
    """미리보기 촬영용: 추가 기능이 덱에 넣어 주는 것을 흉내 낸다. 슬라이드 번호(window.__LIVE_SLIDE__),
    아무 일도 하지 않는 window.liveSlide, 그리고 _SNAPSHOT_SHIMS(저장소·알림 창 대신 쓰는 것)."""
    n = str(int(slide))
    boot = ('<base href="about:srcdoc"><script>window.__LIVE_SLIDE__=' + n + ";window.liveSlide={index:" + n
            + ",keys:true,next:function(){},prev:function(){},first:function(){},last:function(){},goTo:function(){}};"
            + _SNAPSHOT_SHIMS + "</script>")
    if html[:1] == "\ufeff":                    # 맨 앞의 BOM 은 내용이 아니다(추가 기능도 떼고 넣는다)
        html = html[1:]
    at = head_insertion_point(html)
    return html[:at] + boot + html[at:]


def snapshot_page(html: str, slide: int, w: int = 1920, h: int = 1080) -> str:
    """미리보기를 찍을 페이지. 추가 기능 페이지처럼 덱을 격리된 틀(<iframe sandbox srcdoc>) 안에서 연다.

    덱을 파일로 바로 열면 그 페이지는 컴퓨터의 어떤 파일이든 불러올 수 있어서, HTML 안으로 넣지 않은 덱 폴더 밖의
    파일(절대 경로·file:// 주소의 그림이나 문서)이 미리보기 그림에 찍힌다. 격리된 틀 안에서는 그런 파일이 열리지 않고,
    그림도 PowerPoint 안에서 보이는 모습과 같아진다.

    틀의 크기는 처음부터 w×h 픽셀로 못 박는다. 100% 로 두면 틀이 제 크기가 되기 전에 덱이 열려, 화면 크기에 맞춰 그리는
    덱이 가끔 작게 찍힌다(같은 덱이 실행할 때마다 다르게 찍히던 문제)."""
    return ('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;overflow:hidden;'
            f'background:#fff}}iframe{{display:block;border:0;width:{int(w)}px;height:{int(h)}px;background:#fff}}</style></head><body>'
            f'<iframe sandbox="{SNAPSHOT_SANDBOX}" allow="autoplay; fullscreen" srcdoc="'
            + htmllib.escape(with_slide_marker(html, slide), quote=True) + '"></iframe></body></html>')


LINT = (
    (r"\b(?:window\.)?alert\s*\(", "alert() 는 PowerPoint 안에서 화면 위쪽의 알림 글자로 바뀐다(창이 뜨지 않는다)"),
    (r"\b(?:window\.)?(?:confirm|prompt)\s*\(", "confirm()·prompt() 는 PowerPoint 안에서 묻지 않는다(confirm 은 항상 '예', prompt 는 기본값). 화면 안 단추·입력칸으로 바꾼다"),
    (r"\b(?:localStorage|sessionStorage)\b|document\.cookie", "localStorage·sessionStorage·쿠키에 넣은 값은 그 슬라이드가 떠 있는 동안만 남고 슬라이드끼리 나누지 못한다"),
    (r"<iframe\b", "다른 사이트를 넣은 틀(iframe)은 PowerPoint 안에서 로그인·저장이 안 될 수 있다"),
)


def lint(html: str) -> list:
    """PowerPoint 안에서 브라우저와 다르게 동작하는 것을 찾아 알려 준다."""
    text = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    return [msg for pattern, msg in LINT if re.search(pattern, text)]


def stored_size(html: str) -> int:
    """pptx 안에 저장되는 크기: 설정값 'html' 의 JSON 글자 수. 한글 한 글자는 6으로 센다(\\uXXXX)."""
    return len(json.dumps(html))


def _size(n: int) -> str:
    return f"{max(1, round(n / 1024))}KB" if n < 1_000_000 else f"{n / 1e6:.2f}MB"


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


def shoot(browser: str, html: str, slides: int, w: int, h: int, outdir: Path, wait_ms: int, timeout: int = SHOT_TIMEOUT):
    """돌려주는 것: 슬라이드별 PNG(찍지 못한 장은 None), 열릴 때 난 스크립트 오류 [(슬라이드, 메시지)],
    시간 안에 열리지 않아 촬영을 멈춘 슬라이드 번호(없으면 0).

    한 장이 timeout 초 안에 열리지 않으면(끝나지 않는 반복 등) 남은 장은 찍지 않는다. 진행 상황은 stderr 에 한 줄씩 쓴다."""
    out, problems, stopped = [], [], 0
    profile = outdir / "profile"
    flags = ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
             "--no-first-run", "--no-default-browser-check", "--force-device-scale-factor=1",
             "--enable-logging=stderr", "--log-level=0"]
    if sys.platform.startswith("linux") and getattr(os, "geteuid", lambda: 1)() == 0:
        flags.append("--no-sandbox")                 # 리눅스에서 root 로 돌 때만: 그 밖에는 브라우저의 보호 기능을 켠 채로 연다
    for i in range(1, slides + 1):
        print(f"  미리보기 찍는 중 {i}/{slides}", file=sys.stderr, flush=True)
        page = outdir / f"slide{i}.html"
        png = outdir / f"slide{i}.png"
        page.write_text(snapshot_page(html, i, w, h), encoding="utf-8-sig")    # BOM: 틀림없이 UTF-8 로 읽힌다
        cmd = [browser] + flags + [f"--user-data-dir={profile}", f"--window-size={w},{h}",
                                   f"--virtual-time-budget={wait_ms}", f"--screenshot={png}", page.resolve().as_uri()]
        try:
            r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout, check=False)
            log = r.stderr.decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            stopped = i
            out += [None] * (slides - i + 1)
            break
        except OSError:
            log = ""
        for m in CONSOLE_RE.finditer(log):
            msg = m.group(1)
            if "Uncaught" in msg or "is not defined" in msg or "SyntaxError" in msg:
                problems.append((i, f"{msg[:160]} (줄 {m.group(3)})"))
        out.append(png if png.is_file() and png.stat().st_size > 0 else None)
    return out, problems, stopped


def save_shots(pngs: list, folder: Path, cols: int = 3) -> Path:
    """장마다 미리보기 PNG 와 모아보기(sheet.jpg)를 저장한다. 눈으로 겹침·잘림을 확인하는 용도.
    같은 폴더에 남아 있던, 이번 장수보다 큰 번호의 slideNN.png 는 지운다(지난번 변환의 그림이 섞이지 않게)."""
    from PIL import Image, ImageDraw
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("slide*.png"):
        m = re.match(r"slide(\d+)\.png$", old.name)
        if m and int(m.group(1)) > len(pngs):
            try:
                old.unlink()
            except OSError:
                pass
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


_KOREAN_FONT = []          # 한 번 찾은 결과를 적어 둔다: [경로 또는 None]


def korean_font_path():
    """한글을 그릴 수 있는 글꼴 파일(맑은 고딕, Apple SD 산돌고딕 Neo, 나눔고딕, Noto Sans CJK 순). 없으면 None."""
    if _KOREAN_FONT:
        return _KOREAN_FONT[0]
    from PIL import ImageFont
    win = Path(os.environ.get("WINDIR") or os.environ.get("SystemRoot") or r"C:\Windows") / "Fonts"
    candidates = [win / "malgunbd.ttf", win / "malgun.ttf",
                  Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
                  Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
                  Path("/Library/Fonts/AppleGothic.ttf")]
    for root in ("/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts"),
                 os.path.expanduser("~/.local/share/fonts")):
        if os.path.isdir(root):
            for pattern in ("NanumGothicBold.*", "NanumGothic.*", "NanumBarunGothic*.*", "NotoSansCJK*Bold.*",
                            "NotoSansCJK*.*", "NotoSansKR*.*"):
                candidates += sorted(Path(root).rglob(pattern))
    if sys.platform.startswith("linux") and shutil.which("fc-list"):      # 그 밖의 한글 글꼴(시스템에 있는 것)
        try:
            r = subprocess.run(["fc-list", ":lang=ko", "--format=%{file}\n"], stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, timeout=10, check=False)
            files = sorted(set(r.stdout.decode("utf-8", "replace").split("\n")))
            candidates += [Path(f) for f in sorted(files, key=lambda f: "unifont" in f.lower()) if f.strip()]
        except (OSError, subprocess.SubprocessError):
            pass
    found = None
    for c in candidates:
        try:
            if c.is_file():
                ImageFont.truetype(str(c), 20)
                found = str(c)
                break
        except Exception:
            continue
    _KOREAN_FONT.append(found)
    return found


def _font(size: int):
    """(글꼴, 한글을 그릴 수 있는가)"""
    from PIL import ImageFont
    path = korean_font_path()
    if path:
        try:
            return ImageFont.truetype(path, size), True
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size), False
    except TypeError:                                  # 오래된 Pillow: 크기를 고를 수 없는 작은 글꼴
        return ImageFont.load_default(), False


def _wrap(draw, text: str, font, width: float, max_lines: int = 3) -> list:
    def fits(s):
        return draw.textlength(s, font=font) <= width
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if fits(trial):
            cur = trial
            continue
        if cur:
            lines.append(cur)
        cur = word
        while len(cur) > 1 and not fits(cur):           # 낱말 하나가 한 줄보다 길면 글자 단위로 끊는다
            k = len(cur) - 1
            while k > 1 and not fits(cur[:k]):
                k -= 1
            lines.append(cur[:k])
            cur = cur[k:]
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + "…"
    return lines


def placeholder(i: int, w: int, h: int, path: Path, title: str = "") -> Path:
    """미리보기를 찍지 못했을 때 대신 넣는 그림: 슬라이드 제목을 크게 쓰고, 아래에 안내 한 줄."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (244, 241, 234))
    d = ImageDraw.Draw(im)
    pad = round(w * 0.08)
    d.rectangle([pad // 2, pad // 2, w - pad // 2, h - pad // 2], outline=(31, 111, 92), width=max(2, w // 320))
    big, korean = _font(max(16, h // 11))
    small, _ = _font(max(11, h // 30))
    if korean:
        head, foot = title or f"슬라이드 {i}", f"슬라이드 {i} · 미리보기를 찍지 못했습니다"
    else:                                               # 한글 글꼴이 없으면 영문만 쓴다
        head, foot = (title if title and title.isascii() else f"Live HTML - slide {i}"), f"slide {i} - no preview"
    try:
        lines = _wrap(d, head, big, w - 2 * pad)
        step = max(16, h // 11) * 1.3
        y = h * 0.46 - step * len(lines) / 2
        for line in lines:
            d.text((pad, y), line, fill=(29, 27, 22), font=big)
            y += step
        d.text((pad, h - pad - max(11, h // 30) * 1.4), foot, fill=(122, 117, 106), font=small)
    except Exception:                                   # 글꼴이 그리지 못하는 글자: 글자 없는 그림으로 둔다
        pass
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


def _replace_thumbnail(prs, png: bytes) -> bool:
    """탐색기·Finder 가 보여 주는 작은 그림(docProps/thumbnail.jpeg)을 첫 장 미리보기로 바꾼다.
    파트 이름·형식·관계는 그대로 두고 그림 내용만 바꾼다. 조금이라도 다르면 손대지 않는다."""
    try:
        from PIL import Image
        for rel in prs.part.package.iter_rels():
            if rel.is_external or not rel.reltype.endswith("/metadata/thumbnail"):
                continue
            part = rel.target_part
            if not str(part.partname).lower().endswith((".jpeg", ".jpg")) or not hasattr(part, "_blob"):
                return False
            im = Image.open(io.BytesIO(png)).convert("RGB")
            im.thumbnail((256, 256))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=80)
            part._blob = buf.getvalue()
            return True
    except Exception:
        pass
    return False


def build(html: str, slides: int, w: int, h: int, pngs: list, notes: list, titles: list, out: Path,
          click_advance: bool = True) -> dict:
    prs = Presentation()
    prs.slide_width = Emu(SLIDE_W)
    prs.slide_height = Emu(round(SLIDE_W * h / w))
    blank = prs.slide_layouts[6]
    for i in range(1, slides + 1):
        slide = prs.slides.add_slide(blank)
        png = pngs[i - 1]
        # 1) 미리보기 그림 - 추가 기능을 쓸 수 없는 환경에서 보이는 대체 화면
        pic = slide.shapes.add_picture(io.BytesIO(png), 0, 0, prs.slide_width, prs.slide_height)
        pic.name = f"Live HTML 미리보기 {i}"
        pic._element.nvPicPr.cNvPr.set("descr", titles[i - 1])
        image_part = slide.part.related_part(pic._element.blipFill.blip.rEmbed)

        # 2) webextension 파트 - HTML 원문과 작은 미리보기가 여기에 들어간다
        props = {"html": html, "slide": i, "width": w, "height": h, "poster": poster_data_uri(png), "v": 1}
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

        # 4) --no-click-advance: 슬라이드 쇼에서 마우스 클릭으로는 넘어가지 않게 한다.
        #    기본은 PowerPoint 그대로(클릭하면 넘어감)다. HTML 이 실행되는 Microsoft 365 에서는 어느 쪽이든 클릭을 HTML 이 받고,
        #    HTML 이 실행되지 않는 곳(등록 안 된 PC, LTSC 의 슬라이드 쇼, 옛 Office)에서는 보통 PPT 처럼 클릭으로 넘어가야 덜 헷갈린다.
        #    (실제 PowerPoint 에서 잰 결과: 이 스킬의 references/troubleshooting.md)
        if not click_advance:
            sld = slide._element
            for old in sld.findall(f"{{{NS_P}}}transition"):
                sld.remove(old)
            tr = etree.SubElement(sld, f"{{{NS_P}}}transition")
            tr.set("advClick", "0")
            sld.remove(tr)
            sld.find(f"{{{NS_P}}}clrMapOvr").addnext(tr)

    # 문서 정보: python-pptx 기본 틀에 들어 있는 만든 사람 이름·날짜·작은 그림을 남기지 않는다
    core = prs.core_properties
    core.title = titles[0] if titles else out.stem
    core.author = ""
    core.last_modified_by = ""
    core.comments = ""
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None, microsecond=0)
    core.created = now
    core.modified = now
    if pngs:
        _replace_thumbnail(prs, pngs[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return {"stored_bytes": stored_size(html)}


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


def _same_file(a: Path, b: Path) -> bool:
    try:
        return os.path.normcase(str(a.resolve())) == os.path.normcase(str(b.resolve()))
    except OSError:
        return False


def _writable(out: Path) -> bool:
    """출력 파일을 쓸 수 있는지 미리 본다(PowerPoint 에서 열어 둔 파일은 Windows 에서 쓸 수 없다). 파일 내용은 건드리지 않는다."""
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            with open(out, "ab"):
                pass
        return True
    except OSError:
        return False


def _cannot_write(out: Path) -> int:
    print(f"오류: {out} 을 쓸 수 없습니다. PowerPoint 에서 이 파일을 닫고 다시 실행하세요.")
    return 1


def _some(items: list, limit: int = 8) -> str:
    return ", ".join(items[:limit]) + (" …" if len(items) > limit else "")


def main() -> int:
    _console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", type=Path, help="슬라이드 덱 HTML")
    ap.add_argument("-o", "--out", type=Path, help="출력 pptx 경로 (기본: HTML 과 같은 이름). 폴더를 주면 그 안에 같은 이름으로 만든다")
    ap.add_argument("--slides", type=int, help="슬라이드 수 (기본: <section class=\"slide\"> 개수)")
    ap.add_argument("--size", default="1920x1080", help="HTML 기준 해상도 (기본 1920x1080)")
    ap.add_argument("--browser", help="미리보기 그림을 찍을 Edge·Chrome 실행 파일 경로")
    ap.add_argument("--wait", type=int, default=4000, help="미리보기를 찍기 전 기다리는 시간(ms, 기본 4000)")
    ap.add_argument("--no-inline", action="store_true", help="로컬 그림·CSS·JS 를 HTML 안으로 넣지 않는다")
    ap.add_argument("--allow-outside", action="store_true",
                    help="덱 폴더(HTML 이 있는 폴더) 밖의 파일도 HTML 안으로 넣는다(기본: 넣지 않고 알려 준다)")
    ap.add_argument("--save-html", type=Path, help="한 파일로 합친 HTML 을 따로 저장한다")
    ap.add_argument("--no-click-advance", action="store_true",
                    help="슬라이드 쇼에서 마우스 클릭으로는 넘어가지 않게 한다(키보드·리모컨·덱 안의 단추로 넘긴다). "
                         "기본: PowerPoint 그대로, HTML 이 실행되지 않는 화면에서는 클릭하면 넘어간다")
    ap.add_argument("--click-advance", action="store_true", help=argparse.SUPPRESS)    # 예전 이름(지금은 기본값)
    ap.add_argument("--shots", type=Path, help="장마다 미리보기 PNG 와 모아보기(sheet.jpg)를 이 폴더에 저장한다")
    ap.add_argument("--strict", action="store_true",
                    help="'주의:' 로 알린 것(스크립트 오류·빠진 파일·합치지 못한 참조·찍지 못한 미리보기 등)이 하나라도 있으면 "
                         "종료 코드 1 로 끝낸다(pptx 는 만든다)")
    args = ap.parse_args()

    if not args.html.is_file():
        ap.error(f"파일이 없습니다: {args.html}")
    try:
        w, h = (int(x) for x in args.size.lower().split("x"))
    except ValueError:
        ap.error("--size 는 1920x1080 꼴로 씁니다")
    if not (200 <= w <= 7680 and 200 <= h <= 7680):
        ap.error("--size 는 가로·세로 모두 200 에서 7680 사이로 씁니다")
    if args.wait < 100:
        ap.error("--wait 는 100(ms) 이상으로 씁니다")
    out = args.out or args.html.with_suffix(".pptx")
    if out.is_dir():
        out = out / (args.html.stem + ".pptx")
    if out.suffix.lower() != ".pptx":
        ap.error(f"출력 파일 이름은 .pptx 로 끝나야 합니다: {out}")
    if _same_file(out, args.html):
        ap.error("출력 파일이 입력 HTML 과 같은 파일입니다. 다른 이름을 주세요.")
    if args.save_html and (args.save_html.is_dir() or _same_file(args.save_html, args.html)):
        ap.error("--save-html 에는 입력 HTML 과 다른 파일 이름을 주세요.")

    html, encoding = decode(args.html.read_bytes())
    if html is None:
        raise SystemExit(f"{args.html}: UTF-8(또는 CP949)로 읽을 수 없습니다. UTF-8로 저장해 주세요.")

    inl = Inliner(args.html.resolve().parent, allow_outside=args.allow_outside)
    if not args.no_inline:
        html = inl.html(html)
    if args.save_html:
        try:
            args.save_html.parent.mkdir(parents=True, exist_ok=True)
            # BOM 을 붙여 쓴다: 덱에 <meta charset="euc-kr"> 가 남아 있어도 브라우저가 UTF-8 로 읽는다
            args.save_html.write_text(html, encoding="utf-8-sig")
        except OSError as e:
            print(f"오류: {args.save_html} 에 합친 HTML 을 저장하지 못했습니다 - {e}")
            return 1

    cautions = []                                           # --strict 는 여기에 하나라도 있으면 실패로 끝낸다

    def caution(msg: str, indent: str = "  ") -> None:
        cautions.append(msg)
        print(f"{indent}주의: {msg}")

    scanned = scan_slides(html)
    found = len(scanned)
    n = args.slides or found
    if args.slides and found and args.slides != found:
        caution(f"--slides {args.slides} 인데 HTML 의 <section class=\"slide\"> 는 {found}개입니다.", "")
    if n < 1:
        ap.error('슬라이드를 찾지 못했습니다. <section class="slide"> 로 나누거나 --slides 로 장수를 주세요.')
    readable = html + "\n" + "\n".join(inl.hidden_js)      # data URI 로 들어간 스크립트까지 글자로 본다
    if "__LIVE_SLIDE__" not in readable:
        caution("HTML 이 window.__LIVE_SLIDE__ 를 읽지 않습니다. 모든 슬라이드가 같은 화면으로 보일 수 있습니다.", "")

    file_bytes, size = len(html.encode("utf-8", "surrogatepass")), stored_size(html)
    if size > MAX_BYTES:
        print(f"오류: HTML 이 너무 큽니다(파일 {_size(file_bytes)}, pptx 에 저장되는 크기 {_size(size)}, "
              f"한도 {MAX_BYTES / 1e6:.1f}MB). 그림을 줄이거나 덱을 나누세요.")
        return 3
    if size > WARN_BYTES:
        caution(f"HTML 이 큽니다(파일 {_size(file_bytes)}, pptx 에 저장되는 크기 {_size(size)}). "
                "슬라이드마다 한 벌씩 들어가 파일이 커지고 열 때 느릴 수 있습니다.", "")

    notes = [xml_safe(x) for x in _notes(scanned, n)]
    titles = _titles(scanned, n)
    if not _writable(out):
        return _cannot_write(out)

    tmpdir = Path(tempfile.mkdtemp(prefix="live-pptx-"))
    try:
        browser = find_browser(args.browser)
        shots, problems, stopped = shoot(browser, html, n, w, h, tmpdir, args.wait) if browser else ([None] * n, [], 0)
        pngs, drawn = [], 0
        for i, s in enumerate(shots, 1):
            png = None
            if s is not None:
                try:
                    png = normalize_png(s, w, h)
                    drawn += 1
                except (OSError, ValueError):           # 읽을 수 없는 그림(찍다 만 파일 등)
                    png = None
            if png is None:
                png = normalize_png(placeholder(i, w, h, tmpdir / f"ph{i}.png", titles[i - 1]), w, h)
            pngs.append(png)
        same_screens = n > 1 and drawn == n and len({hashlib.sha256(p).digest() for p in pngs}) == 1
        try:
            build(html, n, w, h, pngs, notes, titles, out, click_advance=not args.no_click_advance)
        except OSError:
            return _cannot_write(out)
        sheet, shots_failed = None, False
        if args.shots:
            try:
                sheet = save_shots(pngs, args.shots)
            except OSError:
                shots_failed = True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"완료: {out}")
    print(f"  슬라이드 {n}장 · HTML {_size(file_bytes)}(pptx 에 저장되는 크기 {_size(size)}) · "
          f"파일 {out.stat().st_size / 1024:.0f}KB · 발표자 노트 {sum(1 for x in notes if x)}장")
    if encoding == "cp949":
        print("  알림: HTML 을 CP949(한글 Windows 글자표)로 읽었습니다. UTF-8 로 저장해 두면 더 안전합니다.")
    if inl.inlined:
        print(f"  HTML 안으로 넣은 로컬 파일 {len(inl.inlined)}개: {_some(inl.inlined)}")
    if inl.missing:
        caution(f"찾지 못한 로컬 파일 {len(inl.missing)}개: {_some(inl.missing)}")
    if inl.outside:
        caution(f"덱 폴더 밖이라 넣지 않은 파일 {len(inl.outside)}개: {_some(inl.outside)} "
                "(덱 폴더로 옮기거나 --allow-outside)")
    if inl.left:
        caution(f"합치지 못한 로컬 참조 {len(inl.left)}개: {_some(inl.left)} (PowerPoint 안에서는 열리지 않습니다)")
    for msg in inl.warnings:
        caution(msg)
    if inl.remote:
        caution(f"인터넷에서 불러오는 주소 {len(inl.remote)}곳: {', '.join(sorted(inl.remote))} - 그 파일을 내려받아 덱 옆에 두고 "
                "주소를 파일 이름으로 바꾸면 pptx 안에 함께 들어갑니다(그대로 두면 발표 PC 가 그 주소에 접속하지 못할 때 화면이 깨집니다).")
    if inl.script_hosts - inl.remote:
        print(f"  스크립트에 적힌 인터넷 주소(실제로 불러오면 인터넷 필요): {', '.join(sorted(inl.script_hosts - inl.remote))}")
    if sheet:
        print(f"  미리보기 모아보기: {sheet}")
    elif shots_failed:
        caution(f"미리보기 그림을 {args.shots} 에 저장하지 못했습니다.")
    for slide_no, msg in problems[:10]:
        caution(f"슬라이드 {slide_no} 를 열 때 스크립트 오류 - {msg}")
    if same_screens:
        caution("모든 슬라이드의 첫 화면이 같습니다 - window.__LIVE_SLIDE__ 로 장을 고르는 코드가 동작하는지 확인하세요.")
    for msg in lint(readable):
        print(f"  알림: {msg}")
    if not browser:
        caution("Edge·Chrome 을 찾지 못해 미리보기를 안내 그림으로 대신했습니다(--browser 로 경로 지정).")
    elif stopped:
        caution(f"슬라이드 {stopped} 이(가) {SHOT_TIMEOUT}초 안에 열리지 않아 미리보기 촬영을 멈췄습니다 - "
                f"끝나지 않는 반복이 있는지 확인하세요. {n - drawn}장은 안내 그림으로 대신했습니다.")
    elif drawn < n:
        caution(f"미리보기 {n - drawn}장을 찍지 못해 안내 그림으로 대신했습니다.")
    if args.strict and cautions:
        print(f"엄격 점검(--strict): 위의 주의 {len(cautions)}가지 때문에 실패로 끝냅니다(pptx 는 만들어졌습니다).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
