#!/usr/bin/env python3
"""live-pptx 스크립트 자동 시험.  실행:  python -m unittest test_live_pptx  (scripts 폴더에서)

브라우저가 없어도 돌도록 미리보기는 안내 그림으로 대신한다(브라우저를 쓰는 시험은 브라우저가 있을 때만 돈다).
"""
import base64
import contextlib
import html as htmllib
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
import zipfile
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_live_pptx as B   # noqa: E402
import qa_live_pptx as Q      # noqa: E402
import register_addin as R    # noqa: E402

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

DECK = """<!doctype html>
<html><head><meta charset="utf-8"><title>시험</title>
<!-- 주석 속 <section class="slide"> 는 세지 않는다 -->
<style>.slide{display:none}.slide.on{display:block}</style></head>
<body>
<section class="slide" data-notes="첫 장 &amp; 인사">
  <h1>하나 <em>둘</em></h1></section>
<section class='slide wide'><h2>둘째 장</h2>
  <aside class="notes"><p>발문 1</p><p>발문 2</p></aside></section>
<section class="other">슬라이드 아님</section>
<section class="slide"><p>제목 없는 장</p></section>
<script>
var s='<section class="slide">가짜</section>';
var n = window.__LIVE_SLIDE__ || 1;
</script>
</body></html>
"""

# 슬라이드 수를 잘못 세기 쉬운 입력: (HTML, 슬라이드 수). 변환기와 점검 도구가 똑같이 세어야 한다.
TRICKY = [
    (DECK, 3),
    ('<section id="cmp" data-notes="3 > 2 임을 확인" class="slide">a</section><section class="slide" data-notes="누른다 -> 답">b</section>', 2),
    ("<SECTION CLASS=slide><h1>A</h1></SECTION><SECTION CLASS=slide>b</SECTION>", 2),
    ('<section class="slides"></section><section class="slide-x"></section><section data-class="slide" class="x"></section>', 0),
    ('<section\n  id="a"\n  class="big\nslide">x</section>', 1),
    ("<section style=\"--a:'>'\" class='slide'>x</section>", 1),
    ('<section class="slide">a</section><script data-x="a>b">var s=\'<section class="slide">x</section>\';</script>', 1),
    ('<section class="slide">a<textarea><section class="slide"></textarea></section>', 1),
    ('<template><section class="slide">t</section></template><section class="slide">real</section>', 1),
    ('<section class="slide"><section class="slide">안쪽</section></section>', 2),
    ('<section class="slide">a</section><!-- <section class="slide">b</section> --><STYLE>.x{content:"<section class=slide>"}</STYLE>', 1),
    ('<div class="slide">a</div><article class="slide">b</article>', 0),
    ('<svg><title/></svg><section class="slide">a</section><section class="slide">b</section>', 2),
]


def run_main(module, argv):
    out = io.StringIO()
    with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out):
        try:
            code = module.main()
        except SystemExit as e:
            code = e.code
    return code, out.getvalue()


def quiet(module, argv):
    """argparse 가 stderr 에 쓰는 사용법 안내를 시험 출력에 섞지 않는다."""
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code, log = run_main(module, argv)
    return code, log + err.getvalue()


def read_props(pptx: Path, slide: int) -> dict:
    with zipfile.ZipFile(pptx) as z:
        from xml.etree import ElementTree as ET
        root = ET.fromstring(z.read(f"ppt/webextensions/webextension{slide}.xml"))
    return {p.get("name"): json.loads(p.get("value")) for p in root.iter("{%s}property" % B.NS_WE)}


def color_png(path: Path, rgb) -> Path:
    from PIL import Image
    Image.new("RGB", (8, 6), rgb).save(path)
    return path


class Html(unittest.TestCase):
    def test_count_ignores_comments_scripts_and_other_sections(self):
        self.assertEqual(B.count_slides(DECK), 3)

    def test_notes_from_attribute_and_aside(self):
        self.assertEqual(B.extract_notes(DECK, 3), ["첫 장 & 인사", "발문 1\n발문 2", ""])

    def test_titles(self):
        self.assertEqual(B.slide_titles(DECK, 3), ["하나 둘", "둘째 장", "슬라이드 3"])
        deck = '<section class="slide"><h3>이 슬라이드는<br><em>그림</em>이 아닙니다</h3><h1>둘째 제목</h1></section>'
        self.assertEqual(B.slide_titles(deck, 2), ["이 슬라이드는 그림이 아닙니다", "슬라이드 2"])

    def test_gt_inside_an_attribute_does_not_drop_slides(self):
        # F01: 속성값 속의 '>' 때문에 슬라이드가 빠지고 노트·제목이 밀리던 문제
        deck = ('<section class="slide" data-notes="인사한다"><h1>하나</h1></section>'
                '<section id="cmp" data-notes="3 > 2 임을 수직선으로 확인한다" class="slide"><h1>둘: 크기 비교</h1></section>'
                '<section class="slide" data-notes="카드를 누른다 -> 답을 확인한다"><h1>셋</h1></section>'
                '<section class="slide" data-notes="정리"><h1>넷</h1></section>')
        self.assertEqual(B.count_slides(deck), 4)
        self.assertEqual(B.extract_notes(deck, 4), ["인사한다", "3 > 2 임을 수직선으로 확인한다",
                                                    "카드를 누른다 -> 답을 확인한다", "정리"])
        self.assertEqual(B.slide_titles(deck, 4), ["하나", "둘: 크기 비교", "셋", "넷"])

    def test_notes_and_titles_come_only_from_inside_the_slide(self):
        # F17
        def notes(body, attr=""):
            return B.extract_notes(f'<section class="slide"{attr}>{body}</section>', 1)[0]
        self.assertEqual(notes('<!-- <aside class="notes">지운 노트</aside> --><p>x</p>'), "")
        self.assertEqual(notes('<aside class="notes-extra">화면에 보이는 글</aside>'), "")
        self.assertEqual(notes('<aside class="speaker notes x">n</aside>'), "n")
        self.assertEqual(notes('<aside class="notes">a<script>var x="<b>";</script><style>.a{}</style>b</aside>'), "ab")
        self.assertEqual(notes('<aside class="notes">a<aside>안쪽</aside>꼬리</aside>'), "a\n안쪽\n꼬리")
        self.assertEqual(notes('<aside class="notes"><ul><li>하나 <b>굵게</b></li><li>둘</li></ul>셋<br>넷</aside>'),
                         "하나 굵게\n둘\n셋\n넷")
        self.assertEqual(notes('<aside class="notes">aside 에서</aside>', ' data-notes=""'), "aside 에서")
        self.assertEqual(notes("x", " data-notes=hello"), "hello")
        self.assertEqual(notes("x", " data-notes='say \"hi\" &amp; bye'"), 'say "hi" & bye')
        deck = ('<section class="slide">s1</section><section class="slide">s2</section>'
                '<footer><h1>바닥글 제목</h1><aside class="notes">바닥 노트</aside></footer>')
        self.assertEqual(B.extract_notes(deck, 2), ["", ""])
        self.assertEqual(B.slide_titles(deck, 2), ["슬라이드 1", "슬라이드 2"])

    def test_crlf_in_notes_is_normalised(self):
        # F12: CRLF 가 노트에 _x000D_ 로 남던 문제
        deck = '<section class="slide" data-notes="줄1\r\n줄2\r\n  줄3\r\n">x</section>\r\n'
        self.assertEqual(B.extract_notes(deck, 1), ["줄1\n줄2\n줄3"])
        aside = '<section class="slide"><aside class="notes">가\r\n나\r다</aside></section>'
        self.assertEqual(B.extract_notes(aside, 1), ["가\n나\n다"])

    def test_builder_and_qa_count_slides_the_same_way(self):
        # 두 파일에 같은 코드가 한 벌씩 들어 있다. 한쪽만 고치면 여기서 걸린다.
        self.assertEqual(inspect.getsource(B.SlideScanner), inspect.getsource(Q.SlideScanner))
        for deck, expected in TRICKY:
            with self.subTest(deck=deck[:60]):
                self.assertEqual(B.count_slides(deck), expected)
                self.assertEqual(Q.count_sections(deck), expected)

    def test_marker_goes_right_after_head(self):
        out = B.with_slide_marker("<html><head><title>x</title></head></html>", 4)
        self.assertRegex(out, r'^<html><head><base href="about:srcdoc"><script>window\.__LIVE_SLIDE__=4;.*</script><title>')
        self.assertTrue(B.with_slide_marker("<p>머리 없음</p>", 2).startswith('<base href="about:srcdoc"><script>window.__LIVE_SLIDE__=2;'))
        self.assertTrue(B.with_slide_marker("\ufeff<p>BOM</p>", 2).startswith("<base "))

    def test_marker_is_not_fooled_by_comments_or_header(self):
        html = "<!doctype html>\n<!-- 규칙: 스타일은 <head> 안에 -->\n<html lang='ko'>\n<HEAD data-x=\"a>b\"><title>x</title></HEAD></html>"
        at = B.head_insertion_point(html)
        self.assertTrue(html[:at].endswith("<HEAD data-x=\"a>b\">"))
        self.assertEqual(B.head_insertion_point("<!doctype html><header>x</header><p>y</p>"), len("<!doctype html>"))
        self.assertEqual(B.head_insertion_point("<header>x</header>"), 0)
        self.assertEqual(B.head_insertion_point("<!doctype html><script>var t='<head>';</script><head>"), len("<!doctype html>"))

    def test_marker_gives_the_deck_what_the_addin_gives(self):
        # F05: 추가 기능처럼 liveSlide 가 있고, alert·confirm·prompt 가 창을 띄우지 않는다
        out = B.with_slide_marker("<p>x</p>", 3)
        for name in ("index:3", "keys:true", "next:", "prev:", "first:", "last:", "goTo:"):
            self.assertIn(name, out)
        for shim in ("window.alert=function(){}", "window.confirm=function(){return true}", "window.prompt=function(m,d)",
                     'fill("localStorage")', 'fill("sessionStorage")', '"cookie"', '"pushState","replaceState"'):
            self.assertIn(shim, out)

    def test_marker_fills_in_what_an_isolated_frame_blocks(self):
        # 격리된 틀에서는 localStorage·쿠키·history.pushState 가 오류를 낸다. 추가 기능처럼 덱이 멈추지 않게 메운다.
        node = shutil.which("node")
        if not node:
            self.skipTest("node 가 없는 컴퓨터")
        boot = re.search(r"<script>(.*)</script>", B.with_slide_marker("", 2), re.S).group(1)
        js = ("var blocked = {configurable: true, get: function () { throw new Error('SecurityError'); },"
              " set: function () { throw new Error('SecurityError'); }};"
              "var window = {history: {pushState: function () { throw new Error('SecurityError'); }, replaceState: function () { return 7; }}};"
              "var document = {};"
              "Object.defineProperty(window, 'localStorage', blocked); Object.defineProperty(window, 'sessionStorage', blocked);"
              "Object.defineProperty(document, 'cookie', blocked);"
              + boot +
              "window.localStorage.setItem('k', 5); window.sessionStorage.setItem('s', 'x'); document.cookie = 'a=1';"
              "window.history.pushState(null, '', '?a');"
              "process.stdout.write(JSON.stringify([window.__LIVE_SLIDE__, window.liveSlide.index, window.localStorage.getItem('k'),"
              " window.localStorage.length, window.localStorage.getItem('none'), window.sessionStorage.key(0), document.cookie,"
              " window.history.replaceState(), window.confirm('?'), window.prompt('?', 3), window.prompt('?'), window.open('x'),"
              " typeof window.alert('x')]));")
        r = subprocess.run([node, "-e", js], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, check=False)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        self.assertEqual(json.loads(r.stdout.decode("utf-8")), [2, 2, "5", 1, None, "s", "", 7, True, "3", None, None, "undefined"])

    def test_snapshot_page_runs_the_deck_in_an_isolated_frame(self):
        # 미리보기를 찍는 페이지는 추가 기능처럼 덱을 격리된 틀에서 연다. 파일로 바로 열면 넣지 않은 덱 폴더 밖의 파일까지 그림에 찍힌다.
        deck = '<html><head><title>x</title></head><body><iframe src="/etc/hostname"></iframe><img alt=\'a"b\' src="x.png">&amp;</body></html>'
        page = B.snapshot_page(deck, 3)
        m = re.search(r'<iframe sandbox="([^"]*)"[^>]* srcdoc="([^"]*)"></iframe>', page)
        self.assertTrue(m, page[:300])
        self.assertEqual(m.group(1), B.SNAPSHOT_SANDBOX)
        self.assertEqual(m.group(1).split(), ["allow-scripts", "allow-forms"])          # allow-same-origin 이 있으면 격리가 풀린다
        self.assertEqual(htmllib.unescape(m.group(2)), B.with_slide_marker(deck, 3))    # 덱은 글자 하나 바뀌지 않고 틀 안으로 들어간다
        self.assertEqual(page.count("<iframe"), 1)

    def test_lint_reports_things_that_differ_inside_powerpoint(self):
        found = B.lint("<script>alert('a'); if(confirm('b')){localStorage.setItem('k',1)}</script><!-- <iframe> -->")
        self.assertEqual(len(found), 3)
        self.assertEqual(B.lint("<p>alertness is fine; my localStorages too</p>"), [])

    def test_read_text_handles_bom_and_cp949(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d, "a.html"), Path(d, "b.html")
            a.write_bytes("\ufeff한글".encode("utf-8"))
            b.write_bytes("한글".encode("cp949"))
            self.assertEqual(B.read_text(a), "한글")
            self.assertEqual(B.read_text(b), "한글")

    def test_one_size_definition(self):
        # F11: 변환기와 점검 도구가 같은 값을 같은 한도로 잰다
        self.assertEqual((B.WARN_BYTES, B.MAX_BYTES), (Q.WARN_BYTES, Q.MAX_BYTES))
        self.assertEqual(B.stored_size('가"\n'), len(json.dumps('가"\n')))


class ConsoleLog(unittest.TestCase):
    def test_both_chrome_log_formats(self):
        new_style = '[1:1:1121/0328.89:INFO:CONSOLE:3] "Uncaught ReferenceError: f is not defined", source: file:///t/s.html (3)'
        old_style = '[1121/0328:INFO:CONSOLE(12)] "Uncaught TypeError: x", source: file:///t/s.html (12)'
        self.assertEqual(B.CONSOLE_RE.search(new_style).group(1), "Uncaught ReferenceError: f is not defined")
        self.assertEqual(B.CONSOLE_RE.search(old_style).group(3), "12")


class Inline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name) / "deck"
        (d / "img").mkdir(parents=True)
        (d / "css").mkdir()
        (d / "img" / "dot one.png").write_bytes(PNG_1PX)
        (d / "img" / "a.png").write_bytes(PNG_1PX)
        (d / "base.css").write_text("@import 'more.css';\nbody{background:url(img/dot%20one.png)}", encoding="utf-8")
        (d / "more.css").write_text(".x{color:red}", encoding="utf-8")
        (d / "app.js").write_text("var t='</script>'; var u='</SCRIPT>';", encoding="utf-8")
        (d / "late.js").write_text("document.body.className='한글';", encoding="utf-8")
        (d / "mod.js").write_text("import {x} from './dep.js'; console.log(x);", encoding="utf-8")
        (d / "dep.js").write_text("export const x=1;", encoding="utf-8")
        (d / "notes.txt").write_text("메모", encoding="utf-8")
        (d / "sub.html").write_text("<p>sub</p>", encoding="utf-8")
        (d.parent / "secret.png").write_bytes(PNG_1PX)
        (d.parent / "roster.css").write_text(".private{content:'PRIVATE-MARKER'}", encoding="utf-8")
        self.dir = d

    def tearDown(self):
        self.tmp.cleanup()

    def test_local_files_are_embedded(self):
        html = ('<link rel="stylesheet" href="base.css"><script src="app.js"></script>'
                '<img alt="점" src="img/dot one.png"><img src="https://example.com/a.png"><img src="none.png">'
                '<div style="background:url(\'img/dot one.png\')"></div>')
        inl = B.Inliner(self.dir)
        out = inl.html(html)
        self.assertNotIn("base.css", out)
        self.assertIn(".x{color:red}", out)
        self.assertEqual(out.count("data:image/png;base64,"), 3)        # css url, img, inline style
        self.assertIn("<script>\nvar t='<\\/script>'; var u='<\\/SCRIPT>';\n</script>", out)   # 닫는 태그는 대소문자 가리지 않고 무력화
        self.assertIn("https://example.com/a.png", out)                  # 바깥 주소는 그대로
        self.assertEqual(inl.missing, ["none.png"])
        self.assertEqual(inl.remote, {"example.com"})
        self.assertEqual(inl.inlined, ["base.css", "more.css", "img/dot one.png", "app.js"])   # 덱 폴더 기준 경로

    def test_data_and_anchor_urls_untouched(self):
        html = '<img src="data:image/png;base64,AAAA"><a href="#x">x</a><img src="//cdn.example.org/x.png">'
        inl = B.Inliner(self.dir)
        self.assertEqual(inl.html(html), html)
        self.assertEqual(inl.missing, [])

    def test_script_bodies_and_comments_are_never_rewritten(self):
        # F02: 자바스크립트 문자열 속의 src 를 큰따옴표로 바꿔 넣어 문법 오류를 만들던 문제
        html = ('<script>el.innerHTML = "<img src=\'img/a.png\' alt=\'빨강\'> JS OK"; var t = `<img src="${url}">`;'
                ' var c = "div{background:url(img/a.png)}";</script>'
                '<!-- <img src="img/a.png"> <link rel="stylesheet" href="base.css"> <script src="app.js"></script> -->'
                '<textarea><img src="img/a.png"></textarea>')
        inl = B.Inliner(self.dir)
        self.assertEqual(inl.html(html), html)
        self.assertEqual((inl.inlined, inl.missing), ([], []))
        self.assertIn("img/a.png (스크립트 안)", inl.left)                 # 고치지는 않지만 알려 준다

    def test_tags_are_found_the_way_a_browser_finds_them(self):
        inl = B.Inliner(self.dir)
        legacy = '<script><!--\ndocument.write(\'<script src="app.js"></script>\');\n//--></script>'   # 옛 방식의 스크립트 숨기기
        odd = '</p title="<img src=\'img/a.png\'>"><svg><title/><script/></svg>'
        out = inl.html(legacy + odd + '<img src="img/a.png">')
        self.assertTrue(out.startswith(legacy + odd + '<img src="data:image/png;base64,'), out[:200])
        self.assertEqual(inl.inlined, ["img/a.png"])

    def test_attributes_are_parsed_not_guessed(self):
        # F13: data-src 나 다른 속성값 속의 "src=" 를 src 로 잘못 읽던 문제. 따옴표는 쓴 사람의 것을 그대로 둔다.
        inl = B.Inliner(self.dir)
        out = inl.html('<img data-src="lazy.png" src="img/a.png"><img alt="src=x" src=\'img/a.png\'><IMG SRC=img/a.png>'
                       '<script data-src="x" src="app.js"></script>')
        uri = "data:image/png;base64," + base64.b64encode(PNG_1PX).decode()
        self.assertIn(f'<img data-src="lazy.png" src="{uri}">', out)
        self.assertIn(f"<img alt=\"src=x\" src='{uri}'>", out)
        self.assertIn(f'<IMG SRC="{uri}">', out)
        self.assertIn('<script data-src="x">\nvar t=', out)
        self.assertEqual(inl.missing, [])

    def test_defer_async_and_module_scripts_keep_their_timing(self):
        # F03: defer 스크립트를 본문으로 풀어 넣으면 곧바로 실행되어 덱이 멈춘다. 태그는 두고 주소만 data URI 로 바꾼다.
        inl = B.Inliner(self.dir)
        out = inl.html('<head><script defer src="late.js"></script><script async src=\'late.js\'></script>'
                       '<script type="module" src="mod.js"></script></head>')
        uri = "data:text/javascript;charset=utf-8;base64," + base64.b64encode("document.body.className='한글';".encode("utf-8")).decode()
        self.assertIn(f'<script defer src="{uri}"></script>', out)
        self.assertIn(f"<script async src='{uri}'></script>", out)
        self.assertRegex(out, r'<script type="module" src="data:text/javascript;charset=utf-8;base64,[A-Za-z0-9+/=]+"></script>')
        self.assertNotIn("document.body.className", out)                 # 본문으로 풀어 넣지 않았다
        self.assertEqual(len(inl.warnings), 1)                           # 모듈이 다른 파일을 import 한다
        self.assertIn("mod.js", inl.warnings[0])
        self.assertEqual(inl.hidden_js[0], "document.body.className='한글';")

    def test_data_uri_script_says_it_is_utf8(self):
        # CP949 로 저장한 스크립트는 UTF-8 로 다시 적어 넣는다. 태그에 charset="euc-kr" 가 남아 있어도 한글이 깨지지 않게 data URI 에 charset 을 적는다.
        (self.dir / "old.js").write_bytes("var 답 = '사과';".encode("cp949"))
        (self.dir / "bin.js").write_bytes(b"var x = '\xff\xfe\xfd';")                    # 글자로 읽을 수 없는 파일은 바이트 그대로
        inl = B.Inliner(self.dir)
        out = inl.html('<script defer src="old.js" charset="euc-kr"></script><script defer src="bin.js"></script>')
        m = re.search(r'<script defer src="data:text/javascript;charset=utf-8;base64,([A-Za-z0-9+/=]+)" charset="euc-kr"></script>', out)
        self.assertTrue(m, out)
        self.assertEqual(base64.b64decode(m.group(1)).decode("utf-8"), "var 답 = '사과';")
        self.assertIn('<script defer src="data:text/javascript;base64,' + base64.b64encode(b"var x = '\xff\xfe\xfd';").decode() + '">', out)
        self.assertIn("var 답 = '사과';", Q.readable(out))                  # 점검 도구도 charset 이 붙은 data URI 를 풀어 읽는다

    def test_only_files_inside_the_deck_folder_are_embedded(self):
        # F04: 덱 폴더 밖의 파일(상위 폴더, 절대 경로, file://)을 조용히 pptx 에 넣던 문제
        outside = self.dir.parent / "secret.png"
        html = (f'<link rel="stylesheet" href="../roster.css"><img src="../secret.png"><img src="{outside}">'
                f'<img src="{outside.as_uri()}"><img src="notes.txt"><img src="{self.dir / "img" / "a.png"}">')
        inl = B.Inliner(self.dir)
        out = inl.html(html)
        self.assertNotIn("PRIVATE-MARKER", out)
        self.assertEqual(out.count("data:image/png"), 1)                 # 덱 폴더 안을 가리키는 절대 경로는 넣는다
        self.assertEqual(sorted(inl.outside), sorted([str(outside.resolve()), str((self.dir.parent / "roster.css").resolve())]))
        self.assertEqual(inl.left, ["notes.txt (넣지 않는 형식)"])        # 그림·글꼴·CSS·JS·소리·영상·JSON 만 넣는다
        self.assertEqual(inl.inlined, ["img/a.png"])
        allowed = B.Inliner(self.dir, allow_outside=True)
        out = allowed.html(html)
        self.assertIn("PRIVATE-MARKER", out)
        self.assertEqual(allowed.outside, [])

    def test_windows_drive_paths_are_local_paths(self):
        # F07
        self.assertTrue(B.is_local("C:/Users/kim/a.png"))
        self.assertTrue(B.is_local(r"C:\Users\kim\Pictures\a.png"))
        self.assertFalse(B.is_local("https://example.com/a.png"))
        self.assertFalse(B.is_local("${url}"))
        inl = B.Inliner(self.dir)
        html = r'<img src="Z:\no\such\a.png"><img src="Z:/no/such/b.png"><img src="img\a.png">'
        out = inl.html(html)
        self.assertEqual(inl.missing, [r"Z:\no\such\a.png", "Z:/no/such/b.png"])
        self.assertEqual(out.count("data:image/png"), 1)                 # img\a.png 는 img/a.png 로 읽는다

    def test_addresses_that_cannot_be_parsed_do_not_stop_the_build(self):
        # "https://[학교서버]/logo.png" 처럼 대괄호가 든 주소에서 파이썬 오류(ValueError)로 끝나던 문제
        for url in ("https://[학교서버]/logo.png", "https://[server]/a.png", "http://[x"):
            self.assertFalse(B.is_local(url), url)
        html = ('<img src="https://[server]/a.png"><img src="http://[x"><img srcset="http://[x 1x, https://[학교서버]/b.png 2x">'
                '<link rel="stylesheet" href="https://[cdn]/a.css"><iframe src="http://[x"></iframe><video poster="http://[x"></video>'
                '<style>@import "http://[x/a.css"; .a{background:url(https://[host]/a.png)} .b{background:image-set("http://[x" 1x)}</style>'
                '<div style="background:url(https://[host]/b.png)"></div><a href="http://[x">x</a>'
                '<script src="https://[server]/a.js"></script><script>var u = "http://[x]/a.png", v = "https://[학교서버]/c.png";</script>')
        inl = B.Inliner(self.dir)
        self.assertEqual(inl.html(html), html)
        self.assertEqual((inl.inlined, inl.missing, inl.left, inl.outside), ([], [], [], []))

    def test_background_feimage_image_set_and_links(self):
        # 말없이 빠지던 것들: 배경 속성·SVG feImage·image-set("파일") 은 넣고, 다른 파일로 가는 링크는 알려 준다
        (self.dir / "활동지.pdf").write_bytes(b"%PDF-1.4")
        uri = "data:image/png;base64," + base64.b64encode(PNG_1PX).decode()
        html = ('<body background="img/a.png"><table background=\'img/a.png\'><tr><td background=img/a.png>x</td></tr></table>'
                '<style>.a{background-image:image-set("img/a.png" 1x, url(img/a.png) 2x)} '
                '.b{background-image:-webkit-image-set(\'img/a.png\' 1x); content:"img/a.png"} '
                '.c{background:image-set("none.png" type("image/png"))} .d{width:calc(1px + (2px))}</style>'
                '<div style="background-image:image-set(\'img/a.png\' 1x)"></div>'
                '<svg><filter><feImage href="img/a.png"/><feImage xlink:href="#shape"/></filter></svg>'
                '<a href="활동지.pdf">활동지</a><a href="next.html#top">다음</a><a href="#s2">2장</a><a href="?p=2">p2</a>'
                '<a href="https://example.com/x">바깥</a><a href="mailto:a@example.com">편지</a><a>빈 링크</a>'
                '<map><area href="img/a.png"></map></body>')
        inl = B.Inliner(self.dir)
        out = inl.html(html)
        self.assertIn(f'<body background="{uri}"><table background=\'{uri}\'><tr><td background="{uri}">', out)
        self.assertIn(".a{background-image:image-set(url(%s) 1x, url(%s) 2x)}" % (uri, uri), out)
        self.assertIn('.b{background-image:-webkit-image-set(url(%s) 1x); content:"img/a.png"}' % uri, out)   # 다른 문자열은 그대로
        self.assertIn('.c{background:image-set("none.png" type("image/png"))} .d{width:calc(1px + (2px))}', out)
        self.assertIn(f'<div style="background-image:image-set(url({uri}) 1x)">', out)
        self.assertIn(f'<feImage href="{uri}"/><feImage xlink:href="#shape"/>', out)
        self.assertEqual(inl.inlined, ["img/a.png"])
        self.assertEqual(inl.missing, ["none.png"])
        self.assertEqual(inl.left, ['<a href="활동지.pdf">', '<a href="next.html#top">', '<area href="img/a.png">'])
        self.assertEqual(inl.remote, set())                                    # 링크는 누르기 전에는 불러오지 않는다

    def test_srcset_and_svg_image(self):
        # F06
        inl = B.Inliner(self.dir)
        out = inl.html('<img src="img/a.png" srcset="img/a.png 1x, img/dot%20one.png 2x, https://x.example.com/c.png 3x">'
                       '<picture><source srcset="img/a.png" media="(min-width:800px)"></picture>'
                       '<svg><image href="img/a.png"/><image xlink:href=\'img/a.png\'/><use href="#icon"/></svg>')
        uri = "data:image/png;base64," + base64.b64encode(PNG_1PX).decode()
        self.assertIn(f'srcset="{uri} 1x, {uri} 2x, https://x.example.com/c.png 3x"', out)
        self.assertIn(f'<source srcset="{uri}" media=', out)
        self.assertIn(f'<image href="{uri}"/><image xlink:href=\'{uri}\'/>', out)
        self.assertEqual((inl.missing, inl.left), ([], []))
        self.assertEqual(inl.remote, {"x.example.com"})

    def test_references_that_cannot_be_embedded_are_reported(self):
        # F06: 합치지 못한 로컬 참조를 말없이 넘기던 문제
        inl = B.Inliner(self.dir)
        html = ('<iframe src="sub.html"></iframe><object data="img/a.png"></object><embed src="img/a.png">'
                '<video><track src="subs.vtt"></video><input type="image" src="img/a.png"><input type="text" src="x.png">'
                '<link rel="preload" href="app.js" as="script"><style>@import "more.css" layer(base);</style>'
                '<script>var q = {img: \'img/a.png\'}; new Audio("no-such.mp3"); el.style.backgroundImage = "url(img/dot one.png)";</script>')
        self.assertEqual(inl.html(html), html)
        self.assertEqual(inl.left, ['<iframe src="sub.html">', '<object data="img/a.png">', '<embed src="img/a.png">',
                                    '<track src="subs.vtt">', '<input src="img/a.png">', '<link rel="preload" href="app.js">',
                                    '@import "more.css" layer(base)', "img/a.png (스크립트 안)", "img/dot one.png (스크립트 안)"])

    def test_css_edge_cases(self):
        # F14
        d = self.dir
        (d / "cyc_a.css").write_text("@import 'cyc_b.css'; .a{}", encoding="utf-8")
        (d / "cyc_b.css").write_text("@import url(cyc_a.css); .b{}", encoding="utf-8")
        (d / "css" / "w.css").write_text("@charset \"utf-8\";\n.z{background:url(only-in-root.png)} .t::after{content:'</STYLE>'}"
                                         " /* @import 'old.css'; url(none.png) */ .s{content:\"url(str.png)\"}", encoding="utf-8")
        (d / "only-in-root.png").write_bytes(PNG_1PX)
        (d / "print.css").write_text(".p{color:blue}", encoding="utf-8")
        (d / "mix.css").write_text("@import 'more.css';\n@import url(https://fonts.example.com/f.css);\n.m{}", encoding="utf-8")
        inl = B.Inliner(d)
        out = inl.html('<link rel="stylesheet" href="cyc_a.css">')              # 서로를 불러와도 멈추지 않는다
        self.assertIn(".b{}", out)
        self.assertIn(".a{}", out)
        inl = B.Inliner(d)
        out = inl.html('<link rel="stylesheet" href="css/w.css" media="print" title="t">')
        self.assertTrue(out.startswith('<style media="print" title="t">\n'))    # media 를 잃지 않는다
        self.assertEqual(inl.missing, ["only-in-root.png"])                     # CSS 파일 기준으로 한 번만 찾는다
        self.assertNotIn("data:image", out)
        self.assertNotIn("@charset", out)
        self.assertEqual(out.lower().count("</style"), 1)                       # 본문 속 닫는 태그는 무력화
        self.assertIn("/* @import 'old.css'; url(none.png) */", out)            # 주석·문자열 속은 그대로
        inl = B.Inliner(d)
        out = inl.html('<style>@import "print.css" print;\n@import "css/w.css";</style>')
        self.assertIn("@media print{\n.p{color:blue}\n}", out)
        self.assertEqual(out.lower().count("</style"), 1)
        inl = B.Inliner(d)
        out = inl.html('<link rel="stylesheet" href="mix.css">')
        self.assertLess(out.index("@import url(https://fonts.example.com/f.css)"), out.index(".x{color:red}"))   # 남는 @import 는 맨 앞에
        self.assertEqual(inl.remote, {"fonts.example.com"})
        inl = B.Inliner(d)
        html = '<link rel="alternate stylesheet" title="dark" href="more.css">'
        self.assertEqual(inl.html(html), html)
        self.assertEqual(len(inl.left), 1)

    def test_remote_hosts_report_is_complete(self):
        # F15
        inl = B.Inliner(self.dir)
        inl.html('<script src="https://cdn.example.com/x.js"></script><link rel="stylesheet" href="//fonts.example.org/a.css">'
                 '<style>@import "https://imp.example.net/a.css"; .a{background:url(https://bg.example.io/a.png)}</style>'
                 '<img src="HTTP://UP.example.com/a.png"><iframe src="https://frame.example.com/"></iframe>'
                 '<object data="https://obj.example.com/a.swf"></object><embed src="https://embed.example.com/a">'
                 '<video><track src="https://track.example.com/a.vtt"></video>'
                 '<script>fetch("https://api.example.com/x"); var ns = "http://www.w3.org/2000/svg";</script>'
                 '<a href="https://link.example.com">x</a>')
        self.assertEqual(inl.remote, {"cdn.example.com", "fonts.example.org", "imp.example.net", "bg.example.io", "up.example.com",
                                      "frame.example.com", "obj.example.com", "embed.example.com", "track.example.com"})
        self.assertEqual(inl.script_hosts, {"api.example.com"})


class Shoot(unittest.TestCase):
    LOG = (b'[1:1:1121/0328.89:INFO:CONSOLE:3] "Uncaught ReferenceError: f is not defined", source: file:///t/s.html (3)\n'
           b'[1:1:1121/0328.89:INFO:CONSOLE:9] "hello", source: file:///t/s.html (9)\n')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def browser(self, hang_at=0, empty_at=0):
        def run(cmd, **kw):
            self.calls.append((cmd, kw))
            png = [a for a in cmd if a.startswith("--screenshot=")][0][len("--screenshot="):]
            if hang_at == len(self.calls):
                raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))
            if empty_at != len(self.calls):
                Path(png).write_bytes(PNG_1PX)
            return types.SimpleNamespace(stderr=self.LOG, returncode=0)
        return run

    def shoot(self, run, slides=3):
        err = io.StringIO()
        with mock.patch.object(B.subprocess, "run", run), contextlib.redirect_stderr(err):
            result = B.shoot("some-browser", DECK, slides, 800, 600, self.dir, 500)
        return result, err.getvalue()

    def test_pages_flags_problems_and_progress(self):
        (pngs, problems, stopped), err = self.shoot(self.browser())
        self.assertEqual([p.name for p in pngs], ["slide1.png", "slide2.png", "slide3.png"])
        self.assertEqual(stopped, 0)
        self.assertEqual(problems, [(i, "Uncaught ReferenceError: f is not defined (줄 3)") for i in (1, 2, 3)])
        self.assertEqual(err.count("\n"), 3)                             # 장마다 진행 상황 한 줄
        self.assertIn("2/3", err)
        cmd, kw = self.calls[1]
        self.assertEqual(cmd[0], "some-browser")
        self.assertIn("--window-size=800,600", cmd)
        self.assertIn("--virtual-time-budget=500", cmd)
        self.assertEqual(kw["timeout"], B.SHOT_TIMEOUT)
        page = (self.dir / "slide2.html").read_bytes()
        self.assertTrue(page.startswith(b"\xef\xbb\xbf"))                # F08: BOM 이 있어야 덱의 charset 선언에 속지 않는다
        self.assertIn(b"window.__LIVE_SLIDE__=2;", page)
        self.assertIn(b'<iframe sandbox="allow-scripts allow-forms"', page)   # 덱은 격리된 틀 안에서 열린다
        self.assertEqual(page.count(b"<section"), 0)                          # 덱의 태그는 모두 srcdoc 속성값 안에 있다

    def test_empty_screenshot_counts_as_missing(self):
        (pngs, _, stopped), _ = self.shoot(self.browser(empty_at=2))
        self.assertEqual([p is None for p in pngs], [False, True, False])
        self.assertEqual(stopped, 0)

    def test_timeout_stops_the_remaining_slides(self):
        # F05: 한 장이 끝나지 않으면 남은 장마다 다시 기다리지 않는다
        (pngs, _, stopped), _ = self.shoot(self.browser(hang_at=2), slides=5)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(stopped, 2)
        self.assertEqual([p is None for p in pngs], [False, True, True, True, True])

    def test_no_sandbox_only_for_root_on_linux(self):
        # F04
        for platform, uid, expected in (("linux", 0, True), ("linux", 1000, False), ("win32", 0, False), ("darwin", 0, False)):
            self.calls.clear()
            with mock.patch.object(sys, "platform", platform), mock.patch.object(B.os, "geteuid", lambda: uid, create=True):
                self.shoot(self.browser(), slides=1)
            self.assertEqual("--no-sandbox" in self.calls[0][0], expected, (platform, uid))

    def test_save_shots_removes_stale_pictures(self):
        # F16: 지난번 변환의 slide02.png, slide03.png 가 남아 있으면 지운다
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (64, 36), (10, 20, 30)).save(buf, "PNG")
        folder = self.dir / "shots"
        B.save_shots([buf.getvalue()] * 3, folder)
        (folder / "notes.png").write_bytes(b"keep")
        B.save_shots([buf.getvalue()], folder)
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ["notes.png", "sheet.jpg", "slide01.png"])

    def test_placeholder_shows_the_title(self):
        # F22
        from PIL import Image
        blank = B.placeholder(1, 640, 360, self.dir / "a.png", "")
        titled = B.placeholder(1, 640, 360, self.dir / "b.png", "Adding fractions " * 12)   # 긴 제목도 그림 안에서 줄을 바꾼다
        korean = B.placeholder(1, 640, 360, self.dir / "k.png", "분수의 덧셈과 뺄셈")
        for path in (titled, korean):
            with Image.open(path) as im:
                self.assertEqual(im.size, (640, 360))
        self.assertTrue(blank.read_bytes() != titled.read_bytes(), "제목이 그림에 그려지지 않았다")
        with mock.patch.object(B, "korean_font_path", return_value=None):     # 한글 글꼴이 없는 컴퓨터
            plain = B.placeholder(2, 640, 360, self.dir / "c.png", "한글 제목")
        with Image.open(plain) as im:
            self.assertEqual(im.size, (640, 360))


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.deck = cls.dir / "deck.html"
        # JSON·XML 을 깨뜨리기 쉬운 글자를 일부러 넣는다
        cls.tricky = DECK.replace("둘째 장", "둘째 \"장\" <&> \\ \u0001   😀 </script>x")
        cls.deck.write_text(cls.tricky, encoding="utf-8")
        cls.out = cls.dir / "out" / "deck.pptx"
        cls.code, cls.log = run_main(B, ["build", str(cls.deck), "-o", str(cls.out), "--browser", str(cls.dir / "no-browser")])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def build_with_shots(self, name, shots, problems=(), stopped=0, extra=(), deck=None):
        """브라우저가 찍은 것처럼 꾸민다. shots: 장마다 색(튜플), "bad"(읽을 수 없는 파일), None(찍지 못함)."""
        def fake_shoot(browser, html, slides, w, h, outdir, wait_ms, timeout=B.SHOT_TIMEOUT):
            out = []
            for i, shot in enumerate(shots, 1):
                path = outdir / f"slide{i}.png"
                if shot is None:
                    out.append(None)
                elif shot == "bad":
                    path.write_bytes(b"not a png")
                    out.append(path)
                else:
                    out.append(color_png(path, shot))
            return out, list(problems), stopped
        out = self.dir / name
        with mock.patch.object(B, "find_browser", return_value="fake-browser"), mock.patch.object(B, "shoot", fake_shoot):
            code, log = run_main(B, ["build", str(deck or self.deck), "-o", str(out)] + list(extra))
        return code, log, out

    def test_build_succeeds_and_passes_qa(self):
        self.assertEqual(self.code, 0, self.log)
        code, log = run_main(Q, ["qa", str(self.out)])
        self.assertEqual(code, 0, log)
        self.assertIn("오류 0건", log)

    def test_html_round_trips_exactly(self):
        for i in (1, 2, 3):
            p = read_props(self.out, i)
            self.assertEqual(p["html"], self.tricky)
            self.assertEqual((p["slide"], p["width"], p["height"], p["v"]), (i, 1920, 1080, 1))
            self.assertTrue(p["poster"].startswith("data:image/jpeg;base64,"))

    def test_attribute_values_are_plain_ascii(self):
        with zipfile.ZipFile(self.out) as z:
            raw = z.read("ppt/webextensions/webextension2.xml")
        self.assertTrue(all(b < 128 for b in raw))

    def test_structure_matches_microsoft_template(self):
        with zipfile.ZipFile(self.out) as z:
            slide = z.read("ppt/slides/slide1.xml").decode("utf-8")
            we = z.read("ppt/webextensions/webextension1.xml").decode("utf-8")
            types_xml = z.read("[Content_Types].xml").decode("utf-8")
            ids = {z.read(f"ppt/webextensions/webextension{i}.xml").decode().split('id="{')[1][:36] for i in (1, 2, 3)}
        self.assertIn('Requires="we pca"', slide)
        self.assertIn("<mc:Fallback><p:pic>", slide)
        self.assertIn('store="developer" storeType="Registry"', we)
        self.assertIn(B.ADDIN_ID, we)
        self.assertEqual(types_xml.count(B.CT_WEBEXT), 3)
        self.assertEqual(len(ids), 3)                                    # 인스턴스 ID 는 장마다 달라야 한다

    def test_click_advance_is_powerpoint_default_and_can_be_switched_off(self):
        with zipfile.ZipFile(self.out) as z:
            self.assertNotIn("<p:transition", z.read("ppt/slides/slide2.xml").decode("utf-8"))
        out = self.dir / "noadv.pptx"
        code, log = run_main(B, ["build", str(self.deck), "-o", str(out), "--browser", "none", "--no-click-advance"])
        self.assertEqual(code, 0, log)
        with zipfile.ZipFile(out) as z:
            slide = z.read("ppt/slides/slide2.xml").decode("utf-8")
        self.assertIn('<p:transition advClick="0"/>', slide)
        self.assertLess(slide.index("</p:clrMapOvr>") if "</p:clrMapOvr>" in slide else slide.index("<p:clrMapOvr"),
                        slide.index("<p:transition"))
        old = self.dir / "old-flag.pptx"                                   # 예전 이름도 받아 준다(기본값과 같다)
        code, log = run_main(B, ["build", str(self.deck), "-o", str(old), "--browser", "none", "--click-advance"])
        self.assertEqual(code, 0, log)
        with zipfile.ZipFile(old) as z:
            self.assertNotIn("<p:transition", z.read("ppt/slides/slide2.xml").decode("utf-8"))

    def test_notes_and_python_pptx_reload(self):
        from pptx import Presentation
        prs = Presentation(str(self.out))
        slides = list(prs.slides)
        self.assertEqual(len(slides), 3)
        self.assertEqual(slides[0].notes_slide.notes_text_frame.text, "첫 장 & 인사")
        self.assertFalse(slides[2].has_notes_slide)

    def test_document_properties_do_not_carry_the_template_author(self):
        # F22: python-pptx 기본 틀의 'Steve Canny', 2013년 날짜, 빈 표지 그림이 남던 문제
        import datetime
        from pptx import Presentation
        core = Presentation(str(self.out)).core_properties
        self.assertEqual((core.author, core.last_modified_by, core.comments), ("", "", ""))
        self.assertEqual(core.title, "하나 둘")
        self.assertLess(abs((datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - core.created).total_seconds()), 3600)
        self.assertEqual(core.created, core.modified)
        with zipfile.ZipFile(self.out) as z:
            raw = z.read("docProps/core.xml").decode("utf-8") + z.read("docProps/app.xml").decode("utf-8", "replace")
            thumb = z.read("docProps/thumbnail.jpeg")
        self.assertNotIn("Steve Canny", raw)
        self.assertNotIn("2013-01-27", raw)
        from PIL import Image
        self.assertEqual(Image.open(io.BytesIO(thumb)).size, (256, 144))  # 첫 장 미리보기(16:9)로 바뀌었다

    def test_other_ratio(self):
        out = self.dir / "43.pptx"
        code, log = run_main(B, ["build", str(self.deck), "-o", str(out), "--size", "1024x768", "--browser", "none"])
        self.assertEqual(code, 0, log)
        from pptx import Presentation
        prs = Presentation(str(out))
        self.assertAlmostEqual(prs.slide_width / prs.slide_height, 1024 / 768, places=3)
        self.assertEqual(run_main(Q, ["qa", str(out)])[0], 0)

    def test_no_slides_is_an_error(self):
        empty = self.dir / "empty.html"
        empty.write_text("<p>슬라이드 없음</p>", encoding="utf-8")
        code, _ = quiet(B, ["build", str(empty), "-o", str(self.dir / "e.pptx"), "--browser", "none"])
        self.assertEqual(code, 2)

    def test_too_large_html_is_refused(self):
        # F11: 종료 코드 3(쓰는 법 오류 2와 구별), 인터넷에서 불러오라는 조언은 하지 않는다
        big = self.dir / "big.html"
        big.write_text(DECK + "<!--" + "가" * 600_000 + "-->", encoding="utf-8")
        code, log = run_main(B, ["build", str(big), "-o", str(self.dir / "big.pptx"), "--browser", "none"])
        self.assertEqual(code, 3, log)
        self.assertIn("오류: HTML 이 너무 큽니다(파일 1.80MB, pptx 에 저장되는 크기 3.60MB, 한도 3.0MB)", log)
        self.assertIn("그림을 줄이거나 덱을 나누세요", log)
        self.assertNotIn("인터넷", log)
        self.assertFalse((self.dir / "big.pptx").exists())

    def test_large_html_warns_and_qa_agrees(self):
        # F11: 변환은 통과했는데 점검에서 떨어지던 문제(1.9MB)
        large = self.dir / "large.html"
        large.write_text(DECK + "<!--" + "x" * 1_900_000 + "-->", encoding="utf-8")
        out = self.dir / "large.pptx"
        code, log = run_main(B, ["build", str(large), "-o", str(out), "--browser", "none"])
        self.assertEqual(code, 0, log)
        self.assertIn("주의: HTML 이 큽니다(파일 1.90MB, pptx 에 저장되는 크기 1.90MB)", log)
        code, log = run_main(Q, ["qa", str(out)])
        self.assertEqual(code, 0, log)
        self.assertIn("HTML 의 저장 크기가 1.90MB 로 크다", log)
        self.assertEqual(log.count("저장 크기가"), 1)                    # 장마다 되풀이하지 않는다

    def test_output_path_is_checked_before_work(self):
        # F10
        folder = self.dir / "outdir"
        folder.mkdir()
        code, log = run_main(B, ["build", str(self.deck), "-o", str(folder), "--browser", "none"])
        self.assertEqual(code, 0, log)
        self.assertTrue((folder / "deck.pptx").is_file())                # 폴더를 주면 그 안에 같은 이름으로
        code, log = quiet(B, ["build", str(self.deck), "-o", str(folder / "deck"), "--browser", "none"])
        self.assertEqual(code, 2)
        self.assertIn(".pptx 로 끝나야", log)
        self.assertFalse((folder / "deck").exists())
        twin = self.dir / "twin.pptx"                                    # 입력과 같은 파일에 쓰지 않는다
        twin.write_text(DECK, encoding="utf-8")
        code, log = quiet(B, ["build", str(twin), "-o", str(twin), "--browser", "none"])
        self.assertEqual(code, 2)
        self.assertEqual(twin.read_text(encoding="utf-8"), DECK)
        code, log = quiet(B, ["build", str(self.deck), "-o", str(self.dir / "s.pptx"), "--save-html", str(self.deck), "--browser", "none"])
        self.assertEqual(code, 2)
        self.assertEqual(self.deck.read_text(encoding="utf-8"), self.tricky)

    def test_file_open_in_powerpoint_gives_a_message_not_a_traceback(self):
        # F10: PowerPoint 에서 열어 둔 pptx 는 Windows 에서 쓸 수 없다(PermissionError)
        out = self.dir / "locked.pptx"
        with mock.patch("pptx.presentation.Presentation.save", side_effect=PermissionError(13, "Permission denied")):
            code, log = run_main(B, ["build", str(self.deck), "-o", str(out), "--browser", "none"])
        self.assertEqual(code, 1)
        self.assertIn("쓸 수 없습니다. PowerPoint 에서 이 파일을 닫고 다시 실행하세요.", log)
        out.write_bytes(b"old")
        real_open = open

        def locked(file, mode="r", *a, **kw):
            if str(file) == str(out) and ("a" in mode or "w" in mode):
                raise PermissionError(13, "Permission denied")
            return real_open(file, mode, *a, **kw)
        shoot = mock.Mock(side_effect=AssertionError("쓸 수 없는 파일은 미리보기를 찍기 전에 알아야 한다"))
        with mock.patch("builtins.open", locked), mock.patch.object(B, "find_browser", return_value="b"), \
                mock.patch.object(B, "shoot", shoot):
            code, log = run_main(B, ["build", str(self.deck), "-o", str(out)])
        self.assertEqual(code, 1)
        self.assertIn("PowerPoint 에서 이 파일을 닫고", log)
        self.assertEqual(out.read_bytes(), b"old")

    def test_size_and_wait_are_validated(self):
        # F16
        for extra in (["--size", "0x1080"], ["--size", "1920x0"], ["--size", "99999x99999"], ["--size", "1920"],
                      ["--size", "abc"], ["--wait", "0"], ["--wait", "-5"]):
            with self.subTest(extra=extra):
                code, log = quiet(B, ["build", str(self.deck), "-o", str(self.dir / "v.pptx"), "--browser", "none"] + extra)
                self.assertEqual(code, 2, log)
                self.assertIn("--" + extra[0].strip("-") + " 는", log)
        self.assertFalse((self.dir / "v.pptx").exists())

    def test_unreadable_or_missing_screenshot_becomes_a_placeholder(self):
        # F16
        code, log, out = self.build_with_shots("bad.pptx", [(200, 0, 0), "bad", None])
        self.assertEqual(code, 0, log)
        self.assertIn("미리보기 2장을 찍지 못해 안내 그림으로 대신했습니다", log)
        self.assertEqual(run_main(Q, ["qa", str(out)])[0], 0)

    def test_timeout_is_explained(self):
        # F05
        code, log, _ = self.build_with_shots("hang.pptx", [(200, 0, 0), None, None], stopped=2)
        self.assertEqual(code, 0, log)
        self.assertIn(f"슬라이드 2 이(가) {B.SHOT_TIMEOUT}초 안에 열리지 않아 미리보기 촬영을 멈췄습니다", log)
        self.assertIn("2장은 안내 그림으로 대신했습니다", log)

    def test_identical_first_screens_are_reported(self):
        # F09
        code, log, _ = self.build_with_shots("same.pptx", [(0, 0, 200)] * 3)
        self.assertIn("모든 슬라이드의 첫 화면이 같습니다", log)
        code, log, _ = self.build_with_shots("differ.pptx", [(0, 0, 200), (0, 200, 0), (200, 0, 0)])
        self.assertNotIn("첫 화면이 같습니다", log)

    def test_strict_turns_script_errors_into_a_failure(self):
        # F02: 스크립트 오류가 있어도 종료 코드 0 이라 놓치기 쉽던 문제
        shots = [(0, 0, 200), (0, 200, 0), (200, 0, 0)]
        problems = [(1, "Uncaught SyntaxError: Unexpected identifier 'data' (줄 8)")]
        code, log, out = self.build_with_shots("loose.pptx", shots, problems)
        self.assertEqual(code, 0, log)
        self.assertIn("주의: 슬라이드 1 를 열 때 스크립트 오류 - Uncaught SyntaxError", log)
        code, log, out = self.build_with_shots("strict.pptx", shots, problems, extra=["--strict"])
        self.assertEqual(code, 1, log)
        self.assertIn("--strict", log)
        self.assertTrue(out.is_file())
        code, log, _ = self.build_with_shots("strict-ok.pptx", shots, extra=["--strict"])
        self.assertEqual(code, 0, log)

    def test_strict_counts_every_caution(self):
        # '주의:' 로 알린 것은 '완료' 앞에 찍힌 것(장수·__LIVE_SLIDE__·크기)까지 모두 --strict 의 실패 사유다
        shots = [(0, 0, 200), (0, 200, 0), (200, 0, 0)]
        nolive = self.dir / "nolive.html"
        nolive.write_text('<section class="slide"><h1>하나</h1></section>' * 3, encoding="utf-8")
        large = self.dir / "strict-large.html"
        large.write_text(DECK + "<!--" + "x" * 1_600_000 + "-->", encoding="utf-8")
        cases = (          # (덱, 장마다 찍힌 그림, 더 주는 인자, 나와야 하는 주의)
            (nolive, shots, [], "주의: HTML 이 window.__LIVE_SLIDE__ 를 읽지 않습니다"),
            (self.deck, shots[:2], ["--slides", "2"], '주의: --slides 2 인데 HTML 의 <section class="slide"> 는 3개입니다.'),
            (large, shots, [], "주의: HTML 이 큽니다"),
            (self.deck, shots, ["--shots", str(self.deck)], "주의: 미리보기 그림을"),    # 파일을 폴더 자리에 주면 저장하지 못한다
        )
        for i, (deck, pictures, extra, text) in enumerate(cases):
            with self.subTest(text=text):
                code, log, out = self.build_with_shots(f"strict{i}.pptx", pictures, extra=extra, deck=deck)
                self.assertEqual(code, 0, log)                                   # --strict 가 없으면 알리기만 한다
                self.assertIn(text, log)
                code, log, out = self.build_with_shots(f"strict{i}.pptx", pictures, extra=extra + ["--strict"], deck=deck)
                self.assertEqual(code, 1, log)
                self.assertIn(text, log)
                self.assertIn("위의 주의 1가지 때문에", log)
                self.assertTrue(out.is_file())
        code, log = run_main(B, ["build", str(self.deck), "-o", str(self.dir / "strict-nb.pptx"), "--browser", "none", "--strict"])
        self.assertEqual(code, 1, log)                                           # 미리보기를 한 장도 찍지 못한 것도 주의다
        self.assertIn("주의: Edge·Chrome 을 찾지 못해", log)
        self.assertIn("위의 주의 1가지 때문에", log)

    def test_saved_html_is_read_as_utf8_whatever_the_deck_declares(self):
        # --save-html: <meta charset="euc-kr"> 가 남아 있는 덱을 BOM 없이 UTF-8 로 저장해 브라우저에서 글자가 깨지던 문제
        deck = self.dir / "cp949-save.html"
        deck.write_bytes(DECK.replace("utf-8", "euc-kr").encode("cp949"))
        out, saved = self.dir / "cp949-save.pptx", self.dir / "merged" / "deck.html"
        code, log = run_main(B, ["build", str(deck), "-o", str(out), "--browser", "none", "--save-html", str(saved)])
        self.assertEqual(code, 0, log)
        raw = saved.read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))                         # BOM 이 있으면 브라우저는 meta 보다 BOM 을 믿는다
        stored = read_props(out, 1)["html"]
        self.assertEqual(raw[3:].decode("utf-8"), stored)
        self.assertEqual(B.read_text(saved), stored)                             # 저장한 파일을 다시 변환해도 같은 글자다

    def test_odd_addresses_do_not_end_in_a_traceback(self):
        deck = self.dir / "bracket.html"
        deck.write_text(DECK.replace("<h2>", '<img src="https://[학교서버]/logo.png"><h2>')
                        .replace("var n =", 'var logo = "http://[x]/a.png"; var n ='), encoding="utf-8")
        code, log = run_main(B, ["build", str(deck), "-o", str(self.dir / "bracket.pptx"), "--browser", "none"])
        self.assertEqual(code, 0, log)
        self.assertIn("https://[학교서버]/logo.png", read_props(self.dir / "bracket.pptx", 2)["html"])

    def test_report_lists_what_was_embedded_and_what_was_not(self):
        # F04·F06·F15: 보고는 덱 폴더 기준 경로로, 넣지 않은 것은 이유와 함께
        d = self.dir / "report" / "deck"
        (d / "img").mkdir(parents=True)
        (d / "img" / "a.png").write_bytes(PNG_1PX)
        (d / "style.css").write_text(".slide{color:red}", encoding="utf-8")
        (d / "late.js").write_text("var n = window.__LIVE_SLIDE__ || 1; alert(n);", encoding="utf-8")
        (d.parent / "roster.css").write_text(".private{content:'PRIVATE-MARKER'}", encoding="utf-8")
        deck = d / "deck.html"
        deck.write_text('<html><head><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="../roster.css">'
                        '<script defer src="late.js"></script><script src="https://cdn.example.com/x.js"></script></head><body>'
                        '<section class="slide"><h1>하나</h1><img src="img/a.png"><img src="none.png"><iframe src="sub.html"></iframe>'
                        '</section><script>fetch("https://api.example.com/v1")</script></body></html>', encoding="utf-8")
        out = d / "deck.pptx"
        args = ["build", str(deck), "-o", str(out), "--browser", "none"]
        code, log = run_main(B, args)
        self.assertEqual(code, 0, log)
        self.assertIn("HTML 안으로 넣은 로컬 파일 3개: style.css, late.js, img/a.png", log)
        self.assertIn("주의: 찾지 못한 로컬 파일 1개: none.png", log)
        self.assertIn(f"주의: 덱 폴더 밖이라 넣지 않은 파일 1개: {(d.parent / 'roster.css').resolve()}", log)
        self.assertIn('주의: 합치지 못한 로컬 참조 1개: <iframe src="sub.html">', log)
        self.assertIn("주의: 인터넷에서 불러오는 주소 1곳: cdn.example.com", log)
        self.assertIn("스크립트에 적힌 인터넷 주소(실제로 불러오면 인터넷 필요): api.example.com", log)
        self.assertNotIn("window.__LIVE_SLIDE__ 를 읽지 않습니다", log)      # data URI 로 들어간 스크립트 안의 것도 본다
        self.assertIn("알림: alert()", log)
        self.assertNotIn("PRIVATE-MARKER", read_props(out, 1)["html"])
        code, log = run_main(Q, ["qa", str(out)])
        self.assertEqual(code, 0, log)
        self.assertIn("오류 0건, 주의 1건", log)                             # 점검 도구도 data URI 스크립트 안을 본다
        self.assertIn("주의: 발표자 노트가 없는 슬라이드: 전부", log)          # 남은 주의 하나는 노트가 없다는 것뿐
        self.assertEqual(run_main(B, args + ["--strict"])[0], 1)
        code, log = run_main(B, args + ["--allow-outside"])
        self.assertIn("PRIVATE-MARKER", read_props(out, 1)["html"])
        self.assertNotIn("덱 폴더 밖", log)

    def test_cp949_deck_is_read_and_reported(self):
        deck = self.dir / "cp949.html"
        deck.write_bytes(DECK.replace("utf-8", "euc-kr").encode("cp949"))
        out = self.dir / "cp949.pptx"
        code, log = run_main(B, ["build", str(deck), "-o", str(out), "--browser", "none"])
        self.assertEqual(code, 0, log)
        self.assertIn("CP949", log)
        self.assertIn("둘째 장", read_props(out, 1)["html"])


class Browser(unittest.TestCase):
    """진짜 브라우저로 찍어 본다(브라우저가 있을 때만)."""

    @unittest.skipUnless(B.find_browser(), "Edge·Chrome 이 없는 컴퓨터")
    def test_alert_and_defer_do_not_break_the_snapshot(self):
        # F03·F05·F08: defer 스크립트가 제때 돌고, alert() 가 촬영을 붙잡지 않고, charset 선언이 달라도 한글이 깨지지 않는다
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            # 스크립트 파일도 CP949: 덱에 넣을 때 UTF-8 로 바뀌고, 태그의 charset="euc-kr" 에 속지 않아야 '가' 가 '가' 로 읽힌다.
            # localStorage·쿠키·history 는 격리된 틀에서 막혀 있지만 추가 기능처럼 메워져 있어야 한다.
            (d / "deck.js").write_bytes(
                ("var n = window.__LIVE_SLIDE__ || 1; alert('안녕'); localStorage.setItem('장', String(n));"
                 " sessionStorage.setItem('k', '1'); document.cookie = 'a=1'; history.replaceState(null, '', '?s=' + n);"
                 " if (confirm('?') && '가'.charCodeAt(0) === 0xAC00 && localStorage.getItem('장') === String(n)) {"
                 " document.querySelectorAll('.slide')[n - 1].className += ' on'; }").encode("cp949"))
            (d / "deck.html").write_bytes(
                ('<!doctype html><html><head><meta charset="euc-kr"><style>.slide{display:none;font-size:120px}'
                 '.slide.on{display:block}</style><script defer src="deck.js" charset="euc-kr"></script></head><body>'
                 '<section class="slide"><h1>하나</h1></section><section class="slide"><h1>둘</h1><p>더 긴 글</p></section>'
                 '</body></html>').encode("cp949"))
            started = time.time()
            with contextlib.redirect_stderr(io.StringIO()):
                code, log = run_main(B, ["build", str(d / "deck.html"), "-o", str(d / "deck.pptx"), "--wait", "500",
                                         "--size", "640x360", "--shots", str(d / "shots"), "--strict"])
            if "찍지 못해" in log:
                self.skipTest("브라우저가 이 환경에서는 화면을 찍지 못한다")
            self.assertEqual(code, 0, log)
            self.assertLess(time.time() - started, 40)
            self.assertNotIn("스크립트 오류", log)
            self.assertNotIn("첫 화면이 같습니다", log)
            self.assertNotEqual((d / "shots" / "slide01.png").read_bytes(), (d / "shots" / "slide02.png").read_bytes())

    @unittest.skipUnless(B.find_browser(), "Edge·Chrome 이 없는 컴퓨터")
    def test_files_outside_the_deck_folder_never_reach_the_preview(self):
        # HTML 안으로 넣지 않은 덱 폴더 밖의 파일이 미리보기 그림(대체 그림·poster·탐색기의 작은 그림)에는 찍히던 문제
        from PIL import Image

        def count(data, rgb):
            im = Image.open(io.BytesIO(data)).convert("RGB")
            return sum(n for n, c in im.getcolors(1 << 24) if all(abs(a - b) < 48 for a, b in zip(c, rgb)))
        yellow, cyan, magenta = (255, 230, 0), (0, 200, 255), (255, 0, 255)
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp).resolve() / "deck"
            d.mkdir()
            photo, roster = d.parent / "private.png", d.parent / "roster.html"
            Image.new("RGB", (300, 150), yellow).save(photo)
            Image.new("RGB", (300, 150), magenta).save(d / "mine.png")
            roster.write_text('<body style="margin:0;background:rgb(0,200,255)">PRIVATE</body>', encoding="utf-8")
            (d / "deck.html").write_text(
                '<!doctype html><html><head><meta charset="utf-8"></head><body style="background:#fff">'
                f'<section class="slide"><h1>하나</h1><img src="mine.png"><img src="{photo}"><img src="{photo.as_uri()}">'
                f'<img src="../private.png"><iframe src="{roster.as_uri()}" style="width:300px;height:150px;border:0"></iframe>'
                '</section><script>var n = window.__LIVE_SLIDE__; var im = new Image();'
                f' im.src = "{photo.as_uri()}"; document.body.appendChild(im);</script></body></html>', encoding="utf-8")
            out = d / "deck.pptx"
            with contextlib.redirect_stderr(io.StringIO()):
                code, log = run_main(B, ["build", str(d / "deck.html"), "-o", str(out), "--wait", "500",
                                         "--size", "800x600", "--shots", str(d / "shots")])
            if "찍지 못해" in log:
                self.skipTest("브라우저가 이 환경에서는 화면을 찍지 못한다")
            self.assertEqual(code, 0, log)
            self.assertIn("주의: 덱 폴더 밖이라 넣지 않은 파일 1개", log)
            shot = (d / "shots" / "slide01.png").read_bytes()
            self.assertGreater(count(shot, magenta), 20000, "덱 폴더 안의 그림은 미리보기에 보여야 한다")
            with zipfile.ZipFile(out) as z:
                pictures = [shot] + [z.read(n) for n in z.namelist() if n.startswith("ppt/media/") or n == "docProps/thumbnail.jpeg"]
            pictures.append(base64.b64decode(read_props(out, 1)["poster"].split(",", 1)[1]))
            self.assertEqual(len(pictures), 4)
            for data in pictures:
                self.assertEqual((count(data, yellow), count(data, cyan)), (0, 0), "덱 폴더 밖의 파일이 미리보기에 찍혔다")


class Template(unittest.TestCase):
    """스킬에 들어 있는 시작 틀이 그대로 변환되고 규칙을 지키는지 본다(스킬 폴더 안에서만)."""
    TEMPLATE = HERE.parent / "assets" / "deck-template.html"

    @unittest.skipUnless(TEMPLATE.is_file(), "assets/deck-template.html 이 없는 위치")
    def test_template_builds_clean(self):
        html = self.TEMPLATE.read_text(encoding="utf-8")
        self.assertEqual(B.count_slides(html), 6)
        self.assertTrue(all(B.extract_notes(html, 6)), "모든 장에 발표자 노트가 있어야 한다")
        self.assertIn("window.__LIVE_SLIDE__", html)
        hosts = set(re.findall(r"https?://([A-Za-z0-9.-]+)", html)) - {"www.w3.org"}
        self.assertEqual(hosts, set(), "시작 틀은 인터넷 주소를 불러오지 않는다")
        for banned in ("localStorage", "alert(", "confirm(", "prompt("):
            self.assertNotIn(banned, html)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "t.pptx"
            code, log = run_main(B, ["build", str(self.TEMPLATE), "-o", str(out), "--browser", "none"])
            self.assertEqual(code, 0, log)
            code, log = run_main(Q, ["qa", str(out)])
            self.assertEqual(code, 0, log)
            self.assertIn("주의 0건", log)

    @unittest.skipUnless((HERE.parent / "assets" / "manifest.xml").is_file(), "assets/manifest.xml 이 없는 위치")
    def test_manifest_matches_scripts(self):
        self.assertEqual(R.manifest_id(HERE.parent / "assets" / "manifest.xml"), B.ADDIN_ID)
        self.assertTrue(R.manifest_url(HERE.parent / "assets" / "manifest.xml").startswith("https://"))


def addin_page():
    """추가 기능 페이지: 시험장에서는 ../addin/index.html, 분필팩에서는 site/live-html/app.html. 없으면 None."""
    candidates = [HERE.parent / "addin" / "index.html"]
    parents = Path(__file__).resolve().parents
    if len(parents) > 6:
        candidates.append(parents[6] / "site" / "live-html" / "app.html")
    for c in candidates:
        if c.is_file():
            return c
    return None


class Contract(unittest.TestCase):
    """변환기와 추가 기능 페이지가 서로 약속한 것. 한쪽만 바꾸면 여기서 걸린다(페이지가 곁에 있을 때만)."""

    def setUp(self):
        page = addin_page()
        if page is None:
            self.skipTest("추가 기능 페이지가 없는 위치")
        self.page = page.read_text(encoding="utf-8")

    def test_every_stored_setting_is_read_by_the_page(self):
        with tempfile.TemporaryDirectory() as d:
            deck, out = Path(d) / "deck.html", Path(d) / "deck.pptx"
            deck.write_text(DECK, encoding="utf-8")
            self.assertEqual(run_main(B, ["build", str(deck), "-o", str(out), "--browser", "none"])[0], 0)
            keys = sorted(read_props(out, 1))
        self.assertEqual(keys, ["height", "html", "poster", "slide", "v", "width"])
        for key in keys:
            self.assertTrue(f"settings.get('{key}')" in self.page, f"추가 기능 페이지가 설정값 {key} 를 읽지 않는다")

    def test_snapshot_marker_has_the_same_liveslide_shape(self):
        marker = B.with_slide_marker("<p>x</p>", 1)
        for name in ("index", "keys", "next", "prev", "first", "last", "goTo"):
            pattern = r"\b%s:\s*(?:N\b|\d|true|function)" % name
            self.assertTrue(re.search(pattern, marker), name)
            self.assertTrue(re.search(pattern, self.page), f"추가 기능 페이지의 liveSlide 에 {name} 이 없다")
        self.assertTrue("window.__LIVE_SLIDE__=" in self.page and "window.__LIVE_SLIDE__=" in marker)

    def test_snapshot_frame_is_isolated_like_the_page_frame(self):
        # 미리보기는 추가 기능과 같은 조건(sandbox)의 틀에서 찍는다. 한쪽만 바꾸면 그림이 PowerPoint 안의 모습과 달라진다.
        m = re.search(r'<iframe\b[^>]*\bid="view"[^>]*>', self.page)
        self.assertTrue(m, "추가 기능 페이지에 <iframe id=\"view\"> 가 없다")
        sandbox = re.search(r'\bsandbox="([^"]*)"', m.group(0))
        self.assertTrue(sandbox, m.group(0))
        self.assertEqual(sorted(sandbox.group(1).split()), sorted(B.SNAPSHOT_SANDBOX.split()))
        self.assertNotIn("allow-same-origin", B.SNAPSHOT_SANDBOX)
        marker = B.with_slide_marker("<p>x</p>", 1)
        for word in ("about:srcdoc", "localStorage", "sessionStorage", "cookie", "pushState", "replaceState"):
            self.assertTrue(word in marker and word in self.page, word)        # 페이지가 메워 주는 것은 미리보기에서도 메운다

    def test_snapshot_marker_goes_where_the_page_puts_its_script(self):
        node = shutil.which("node")
        m = re.search(r"\n  function tagEnd\(.*?\n  function inject\(", self.page, re.S)
        if not node or not m:
            self.skipTest("node 가 없거나 페이지에 bridgeSpot 이 없다")
        decks = [DECK, "", "<p>머리 없음</p>", "<html><head><title>x</title></head></html>", "<head", "<html><head/><p>",
                 "<!doctype html>\n<!-- 규칙: 스타일은 <head> 안에 -->\n<html lang='ko'>\n<HEAD data-x=\"a>b\"><title>x</title></HEAD>",
                 "<!doctype html><header>x</header><p>y</p>", "<header>x</header>", "<!-- 닫지 않은 주석 <head>",
                 "<!doctype html><script>var t='<head>';</script><head>", "\n\t <html data-a='<head>' lang=ko ><head\n>x",
                 "<?xml version='1.0'?><!DOCTYPE html><html><body><head>", "<html><html><head>", "<html a=\"1><head>x"]
        src = m.group(0)[:-len("\n  function inject(")]
        js = src + "\nprocess.stdout.write(JSON.stringify(JSON.parse(require('fs').readFileSync(0, 'utf8')).map(bridgeSpot)));"
        r = subprocess.run([node, "-e", js], input=json.dumps(decks).encode("utf-8"), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=60, check=False)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        self.assertEqual([B.head_insertion_point(d) for d in decks], json.loads(r.stdout.decode("utf-8")))


def set_prop(slide_no: int, name: str, new_json: str):
    """슬라이드 slide_no 의 설정값 name 을 new_json(JSON 글자)으로 바꾸는 편집 함수."""
    def edit(n, b):
        if n != f"ppt/webextensions/webextension{slide_no}.xml":
            return b
        return re.sub(r'(<we:property name="%s" value=")[^"]*(")' % name,
                      lambda m: m.group(1) + htmllib.escape(new_json, quote=True) + m.group(2), b.decode("utf-8")).encode("utf-8")
    return edit


def in_part(prefix: str, edit):
    return lambda n, b: edit(b) if n.startswith(prefix) else b


THREE = '<section class="slide"></section>' * 3 + "<script>var n = window.__LIVE_SLIDE__;</script>"


class Qa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        deck = cls.dir / "deck.html"
        deck.write_text(DECK, encoding="utf-8")
        cls.good = cls.dir / "good.pptx"
        run_main(B, ["build", str(deck), "-o", str(cls.good), "--browser", "none"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def broken(self, name, edit):
        dst = self.dir / name
        with zipfile.ZipFile(self.good) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = edit(item.filename, zin.read(item.filename))
                if data is not None:
                    zout.writestr(item, data)
        return run_main(Q, ["qa", str(dst)])

    def check(self, name, edit, code, text):
        got, log = self.broken(name, edit)
        self.assertEqual(got, code, log)
        self.assertIn(text, log)
        return log

    def test_good_file_is_clean_every_time(self):
        # F20: 점검 결과가 다음 점검으로 넘어가지 않는다
        self.check("id0.pptx", lambda n, b: b.replace(B.ADDIN_ID.encode(), b"11111111-2222-3333-4444-555555555555"), 1, "ID")
        for _ in range(2):
            code, log = run_main(Q, ["qa", str(self.good)])
            self.assertEqual(code, 0, log)
            self.assertIn("오류 0건, 주의 1건", log)                          # 3번 장에는 일부러 노트를 넣지 않았다
            self.assertIn("주의: 발표자 노트가 없는 슬라이드: 3 ", log)

    def test_help_and_usage(self):
        # F18: -h 가 '파일을 열 수 없습니다' 로 끝나던 문제
        code, log = run_main(Q, ["qa", "-h"])
        self.assertEqual(code, 0)
        self.assertIn("점검할 pptx 파일", log)
        self.assertEqual(quiet(Q, ["qa"])[0], 2)

    def test_wrong_addin_id(self):
        self.check("id.pptx", lambda n, b: b.replace(B.ADDIN_ID.encode(), b"11111111-2222-3333-4444-555555555555"), 1, "추가 기능 ID 가 다르다")

    def test_broken_json(self):
        self.check("json.pptx", lambda n, b: b.replace(b'name="slide" value="2"', b'name="slide" value="{oops"'), 1, "JSON 이 아니다")

    def test_missing_setting(self):
        self.check("noprop.pptx", in_part("ppt/webextensions/webextension2.xml",
                                          lambda b: re.sub(rb'<we:property name="width"[^>]*/>', b"", b)), 1, "설정값 'width' 이 없다")

    def test_missing_part(self):
        self.check("part.pptx", lambda n, b: None if n == "ppt/webextensions/webextension3.xml" else b, 1, "webextension3.xml 파트가 없다")

    def test_missing_slide_part(self):
        self.check("slidepart.pptx", lambda n, b: None if n == "ppt/slides/slide2.xml" else b, 1, "ppt/slides/slide2.xml 파트가 없다")

    def test_not_a_zip(self):
        bad = self.dir / "bad.pptx"
        bad.write_bytes(b"not a zip")
        code, log = run_main(Q, ["qa", str(bad)])
        self.assertEqual(code, 1)
        self.assertIn("파일을 열 수 없습니다", log)

    def test_zip_that_is_not_a_presentation(self):
        other = self.dir / "other.pptx"
        with zipfile.ZipFile(other, "w") as z:
            z.writestr("word/document.xml", "<a/>")
        code, log = run_main(Q, ["qa", str(other)])
        self.assertEqual(code, 1)
        self.assertIn("PowerPoint 파일 구조가 아닙니다", log)

    def test_slide_list_pointing_nowhere(self):
        self.check("norel.pptx", in_part("ppt/_rels/presentation.xml.rels",
                                         lambda b: re.sub(rb'<Relationship [^>]*slides/slide1\.xml[^>]*/>', b"", b)),
                   1, "PowerPoint 파일 구조가 아닙니다(슬라이드 관계")

    def test_xml_error(self):
        self.check("xml.pptx", in_part("ppt/slides/slide1.xml", lambda b: b[:-10]), 1, "XML 형식 오류")

    def test_missing_slide_size(self):
        self.check("nosize.pptx", in_part("ppt/presentation.xml", lambda b: re.sub(rb"<p:sldSz [^>]*/>", b"", b)), 1,
                   "슬라이드 크기(sldSz)를 읽을 수 없다")

    def test_no_slides(self):
        self.check("noslides.pptx", in_part("ppt/presentation.xml", lambda b: re.sub(rb"<p:sldId [^>]*/>", b"", b)), 1, "슬라이드가 없습니다")

    def test_no_addin_frame(self):
        self.check("frame.pptx", in_part("ppt/slides/slide2.xml", lambda b: re.sub(rb"<mc:Choice.*?</mc:Choice>", b"", b, flags=re.S)),
                   1, "슬라이드 2: 추가 기능 프레임이 0개")

    def test_no_fallback_picture(self):
        self.check("fallback.pptx", in_part("ppt/slides/slide2.xml",
                                            lambda b: re.sub(rb"<mc:Fallback>.*?</mc:Fallback>", b"<mc:Fallback/>", b, flags=re.S)),
                   1, "슬라이드 2: 대체 그림(Fallback)이 없다")

    def test_requires_attribute(self):
        self.check("requires.pptx", in_part("ppt/slides/slide1.xml", lambda b: b.replace(b'Requires="we pca"', b'Requires="we"')),
                   1, "Requires 가 'we pca' 가 아니다")

    def test_graphic_data_uri(self):
        self.check("uri.pptx", in_part("ppt/slides/slide1.xml",
                                       lambda b: b.replace(b'<a:graphicData uri="' + B.NS_WE.encode(), b'<a:graphicData uri="http://example.com/x')),
                   1, "graphicData uri 가 다르다")

    FRAME_ID = b'<p:cNvPr id="3" name="Live HTML 3"'          # 변환기가 만든 추가 기능 프레임. 대체 그림은 id="2", 도형 묶음은 id="1"

    def test_duplicate_shape_ids(self):
        # 서로 다른 두 도형이 같은 ID 를 쓰면 오류: 프레임과 도형 묶음, 대체 그림과 도형 묶음
        self.check("shapeid.pptx", in_part("ppt/slides/slide3.xml", lambda b: b.replace(self.FRAME_ID, b'<p:cNvPr id="1" name="Live HTML 3"')),
                   1, "슬라이드 3: 도형 ID 가 겹친다 (1)")
        self.check("shapeid2.pptx", in_part("ppt/slides/slide2.xml", lambda b: b.replace(b'<p:cNvPr id="2" ', b'<p:cNvPr id="1" ')),
                   1, "슬라이드 2: 도형 ID 가 겹친다 (1)")

    def test_frame_and_fallback_picture_may_share_an_id(self):
        # PowerPoint 는 저장할 때 추가 기능 프레임(mc:Choice)과 대체 그림(mc:Fallback)에 같은 ID 를 준다.
        # PowerPoint 에서 한 번 저장한 파일을 오류로 보던 문제.
        def like_powerpoint(b):
            self.assertIn(self.FRAME_ID, b)
            return b.replace(self.FRAME_ID, b'<p:cNvPr id="2" name="Live HTML 3"')
        self.check("resaved.pptx", in_part("ppt/slides/slide", like_powerpoint), 0, "오류 0건, 주의 1건")   # 주의 = 3번 장의 노트 없음

    def damage(self, name, member):
        """good.pptx 를 복사해, member 의 압축된 내용 가운데 여섯 바이트를 뒤집는다(전송·저장 중에 깨진 파일)."""
        import struct
        data = bytearray(self.good.read_bytes())
        with zipfile.ZipFile(self.good) as z:
            info = z.getinfo(member)
        name_len, extra_len = struct.unpack("<HH", data[info.header_offset + 26:info.header_offset + 30])
        middle = info.header_offset + 30 + name_len + extra_len + info.compress_size // 2
        for k in range(middle, middle + 6):
            data[k] ^= 0xFF
        dst = self.dir / name
        dst.write_bytes(data)
        return run_main(Q, ["qa", str(dst)])

    def test_damaged_parts_are_reported_not_a_traceback(self):
        # 압축이 깨진 파트(zlib.error)에서 파이썬 오류 화면으로 끝나던 문제. 그림 파트가 깨진 것도 알아챈다.
        with zipfile.ZipFile(self.good) as z:
            picture = sorted(n for n in z.namelist() if n.startswith("ppt/media/"))[0]
        for i, member in enumerate(("ppt/slides/slide2.xml", "ppt/webextensions/webextension1.xml", "[Content_Types].xml", picture)):
            with self.subTest(member=member):
                code, log = self.damage(f"damaged{i}.pptx", member)
                self.assertEqual(code, 1, log)
                self.assertIn(f"오류: 파일이 깨져 있습니다 - 읽을 수 없는 부분 1개: {member}", log)
                self.assertIn("오류 1건", log)

    def test_unexpected_failure_is_a_message_not_a_traceback(self):
        with mock.patch.object(Q, "check", side_effect=RuntimeError("boom")):
            code, log = run_main(Q, ["qa", str(self.good)])
        self.assertEqual(code, 1)
        self.assertIn("오류: 점검하다 멈췄습니다 - RuntimeError: boom", log)
        with mock.patch.object(Q, "check", side_effect=Q.zlib.error("Error -3 while decompressing data")):
            code, log = run_main(Q, ["qa", str(self.good)])
        self.assertEqual(code, 1)
        self.assertIn("오류: 파일이 깨져 있습니다 - Error -3", log)

    def test_zero_size_frame(self):
        self.check("zero.pptx", in_part("ppt/slides/slide1.xml",
                                        lambda b: re.sub(rb'(<p:xfrm><a:off x="0" y="0"/><a:ext cx=")\d+(" cy=")\d+', rb"\g<1>0\g<2>0", b)),
                   1, "프레임의 크기가 0")

    def test_relationship_type(self):
        self.check("rel.pptx", in_part("ppt/slides/_rels/slide1.xml.rels", lambda b: b.replace(B.RT_WEBEXT.encode(), b"http://example.com/rel")),
                   1, "추가 기능 관계")

    def test_content_type(self):
        self.check("ct.pptx", in_part("[Content_Types].xml", lambda b: b.replace(B.CT_WEBEXT.encode(), b"application/xml")),
                   1, "콘텐츠 형식이 등록되지 않았다")

    def test_two_slides_sharing_one_part(self):
        self.check("shared.pptx", in_part("ppt/slides/_rels/slide2.xml.rels", lambda b: b.replace(b"webextension2.xml", b"webextension1.xml")),
                   1, "슬라이드 2: 슬라이드 1 와 같은 추가 기능 파트")

    def test_duplicate_instance_ids(self):
        first = []

        def edit(n, b):
            if not re.match(r"ppt/webextensions/webextension\d+\.xml$", n):
                return b
            found = re.search(rb'id="(\{[^"]+\})"', b).group(1)
            first.append(found)
            return b.replace(found, first[0])
        self.check("instance.pptx", edit, 1, "인스턴스 ID 가 다른 슬라이드와 같다")

    def test_store_type_is_a_warning(self):
        self.check("store.pptx", in_part("ppt/webextensions/webextension", lambda b: b.replace(b'storeType="Registry"', b'storeType="OMEX"')),
                   0, "참조 방식이 developer/Registry 가 아니다")

    def test_html_must_be_a_non_empty_string(self):
        self.check("empty.pptx", set_prop(2, "html", '""'), 1, "슬라이드 2: 설정값 'html' 이 비어 있거나 글자가 아니다")
        self.check("number.pptx", set_prop(2, "html", "123"), 1, "설정값 'html' 이 비어 있거나 글자가 아니다")

    def test_slide_number_must_be_a_unique_integer_in_range(self):
        self.check("s-str.pptx", set_prop(2, "slide", '"2"'), 1, "설정값 'slide' 가 1..3 사이의 정수가 아니다 ('2')")
        self.check("s-99.pptx", set_prop(3, "slide", "99"), 1, "설정값 'slide' 가 1..3 사이의 정수가 아니다 (99)")
        self.check("s-dup.pptx", set_prop(3, "slide", "1"), 1, "설정값 'slide' 1 이 다른 슬라이드와 겹친다")

    def test_slide_numbers_out_of_order_is_a_warning(self):
        def swap(n, b):
            return set_prop(1, "slide", "2")(n, set_prop(2, "slide", "1")(n, b))
        self.check("order.pptx", swap, 0, "슬라이드 번호 순서가 1..3 가 아니다: [2, 1, 3]")

    def test_width_and_height_must_be_positive_integers(self):
        self.check("w0.pptx", set_prop(1, "width", "0"), 1, "설정값 'width' 가 양의 정수가 아니다 (0)")
        self.check("h-str.pptx", set_prop(1, "height", '"tall"'), 1, "설정값 'height' 가 양의 정수가 아니다 ('tall')")

    def test_ratio_mismatch_is_a_warning(self):
        self.check("ratio.pptx", set_prop(1, "width", "1000"), 0, "슬라이드 1: HTML 비율 1000x1080 이 슬라이드 비율과 다르다")

    def test_poster_must_be_a_picture(self):
        self.check("poster.pptx", set_prop(1, "poster", '"javascript:alert(1)"'), 0, "설정값 'poster' 가 그림")

    def test_snapshot_link(self):
        self.check("snap.pptx", lambda n, b: None if n == "ppt/webextensions/_rels/webextension1.xml.rels" else b,
                   1, "슬라이드 1: 미리보기 그림(snapshot) 연결이 끊겼다")

    def test_size_limit_is_the_builders(self):
        # F11: 변환기와 같은 값(len(json.dumps(html)))을 같은 한도로 본다
        self.check("big.pptx", set_prop(1, "html", json.dumps(THREE + "<!--" + "x" * 3_000_000 + "-->")), 1, "한도(3.0MB)를 넘는다")
        self.check("large.pptx", set_prop(1, "html", json.dumps(THREE + "<!--" + "x" * 1_600_000 + "-->")), 0, "로 크다")

    def test_section_count_differs_from_slides(self):
        self.check("sections.pptx", set_prop(1, "html", json.dumps(THREE.replace("</section>", "</section><section class='slide'>x</section>", 1))),
                   0, '<section class="slide"> 는 4개인데 슬라이드는 3장이다')

    def test_html_that_never_reads_the_slide_number(self):
        self.check("nomarker.pptx", set_prop(1, "html", json.dumps('<section class="slide"></section>' * 3)), 0,
                   "window.__LIVE_SLIDE__ 를 읽지 않는다")
        for i, mime in enumerate(("text/javascript", "text/javascript;charset=utf-8")):
            hidden = f"data:{mime};base64," + base64.b64encode(b"var n = window.__LIVE_SLIDE__;").decode()
            log = self.check(f"hidden{i}.pptx", set_prop(1, "html", json.dumps('<section class="slide"></section>' * 3 + f'<script defer src="{hidden}"></script>')),
                             0, "서로 다르다")
            self.assertNotIn("읽지 않는다", log)                           # data URI 로 들어 있는 스크립트 안도 본다

    def test_differing_html_is_a_warning(self):
        self.check("differ.pptx", set_prop(2, "html", json.dumps(THREE)), 0, "슬라이드마다 저장된 HTML 이 서로 다르다")

    def test_personal_data_is_searched_in_every_html(self):
        # F18: 첫 장의 HTML 만 보던 문제
        fake = "900101" + "-" + "1234567"                                  # 한 줄로 적으면 팩의 개인정보 검사에 걸린다
        self.check("rrn.pptx", set_prop(2, "html", json.dumps(THREE + "<p>" + fake + "</p>")), 1,
                   "슬라이드 2 의 HTML 에 주민등록번호 형식이 있다: 900101-1…")
        self.check("phone.pptx", set_prop(3, "html", json.dumps(THREE + "<p>010-1234-5678</p>")), 0,
                   "슬라이드 3 의 HTML 에 휴대전화 번호 형식이 있다: 010-1234-5678")

    def test_remote_hosts_are_listed(self):
        self.check("hosts.pptx", set_prop(1, "html", json.dumps(THREE + '<img src="https://cdn.example.com/a.png">')), 0,
                   "인터넷에서 불러올 수 있는 주소: cdn.example.com")


class Register(unittest.TestCase):
    MANIFEST = ('<?xml version="1.0"?><OfficeApp><Id>6f2b8c1e-4d7a-4e55-9a3b-2c8f5d1e7a90</Id>'
                '<DefaultSettings><SourceLocation DefaultValue="https://example.com/app.html"/></DefaultSettings></OfficeApp>')
    OTHER_ID = "11111111-2222-3333-4444-555555555555"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.manifest = self.dir / "manifest.xml"
        self.manifest.write_text(self.MANIFEST, encoding="utf-8")
        self.other = self.dir / "dev.xml"
        self.other.write_text(self.MANIFEST.replace(B.ADDIN_ID, self.OTHER_ID).replace("example.com", "localhost"), encoding="utf-8")
        self.local = self.dir / "한글 사용자" / "AppData" / "Local"
        self.target = self.local / "LiveHTML" / "manifest.xml"
        self.store = {}

    def tearDown(self):
        self.tmp.cleanup()

    def windows(self, deny=False):
        store = self.store
        fake = types.ModuleType("winreg")
        fake.HKEY_CURRENT_USER, fake.REG_SZ, fake.KEY_SET_VALUE = "HKCU", 1, 2

        class Key:
            def __init__(self, path): self.path = path
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def create(root, path):
            if deny:
                raise PermissionError(5, "Access is denied")
            store.setdefault(path, {})
            return Key(path)

        def open_(root, path, *a):
            if path not in store:
                raise OSError("no key")
            return Key(path)

        def set_(key, name, _r, _t, value): store[key.path][name] = value

        def query(key, name):
            if name not in store[key.path]:
                raise OSError("no value")
            return store[key.path][name], 1

        def delete(key, name):
            if name not in store[key.path]:
                raise OSError("no value")
            del store[key.path][name]
        fake.CreateKey, fake.OpenKey, fake.SetValueEx, fake.QueryValueEx, fake.DeleteValue = create, open_, set_, query, delete
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.dict(sys.modules, {"winreg": fake}))
        stack.enter_context(mock.patch.object(sys, "platform", "win32"))
        stack.enter_context(mock.patch.dict(os.environ, {"LOCALAPPDATA": str(self.local)}))
        return stack

    def reg(self, *args, manifest=None):
        return run_main(R, ["reg", "--manifest", str(manifest or self.manifest)] + list(args))

    def test_manifest_parsing(self):
        self.assertEqual(R.manifest_id(self.manifest), B.ADDIN_ID)
        self.assertEqual(R.manifest_url(self.manifest), "https://example.com/app.html")
        utf16 = self.dir / "u16.xml"                                     # F19: UTF-16 manifest 에서 traceback 이 나던 문제
        utf16.write_bytes(self.MANIFEST.encode("utf-16"))
        self.assertEqual(R.manifest_id(utf16), B.ADDIN_ID)
        bad = self.dir / "bad.xml"
        bad.write_bytes(b"\x80\x81<Id>")
        with self.assertRaises(SystemExit):
            R.manifest_id(bad)

    def test_windows_register_status_remove(self):
        with self.windows():
            code, log = self.reg("--status")
            self.assertEqual(code, 1)
            code, log = self.reg()
            self.assertEqual(code, 0, log)
            self.assertTrue(self.target.is_file())
            self.assertEqual(self.store[R.REG_KEY][B.ADDIN_ID], str(self.target))
            code, log = self.reg("--status")
            self.assertEqual(code, 0, log)
            self.assertIn("추가 기능 페이지: https://example.com/app.html", log)
            self.assertEqual(self.reg("--remove")[0], 0)
            self.assertNotIn(B.ADDIN_ID, self.store[R.REG_KEY])
            self.assertFalse(self.target.exists())

    def test_windows_registering_the_installed_copy_again(self):
        # F19: 이미 설치된 파일을 --manifest 로 주면 SameFileError 가 나던 문제
        with self.windows():
            self.assertEqual(self.reg()[0], 0)
            code, log = self.reg(manifest=self.target)
            self.assertEqual(code, 0, log)
            self.assertEqual(R.manifest_id(self.target), B.ADDIN_ID)

    def test_windows_registry_failure_is_a_message_and_leaves_nothing_behind(self):
        with self.windows(deny=True):
            code, log = self.reg()
        self.assertEqual(code, 1)
        self.assertIn("오류: 등록하지 못했습니다", log)
        self.assertFalse(self.target.exists())

    def test_windows_status_and_remove_look_inside_the_file(self):
        # F19: 다른 추가 기능의 manifest 가 같은 자리에 덮여도 '등록됨' 이라 하고, 남의 파일을 지우던 문제
        with self.windows():
            self.assertEqual(self.reg()[0], 0)
            self.assertEqual(self.reg(manifest=self.other)[0], 0)        # 같은 자리에 다른 추가 기능이 덮어쓴다
            code, log = self.reg("--status")
            self.assertEqual(code, 1)
            self.assertIn("다른 추가 기능의 것", log)
            self.assertEqual(self.reg("--remove")[0], 0)                 # 내 등록 기록만 지우고
            self.assertTrue(self.target.is_file())                       # 남의 manifest 는 그대로 둔다
            self.assertEqual(R.manifest_id(self.target), self.OTHER_ID)
            self.assertEqual(self.reg("--status", manifest=self.other)[0], 0)
            self.store[R.REG_KEY][B.ADDIN_ID] = str(self.dir / "gone.xml")
            code, log = self.reg("--status")
            self.assertEqual(code, 1)
            self.assertIn("파일이 없습니다", log)

    def test_mac_register_and_remove(self):
        home = self.dir / "home"
        (home / "Library/Containers/com.microsoft.Powerpoint/Data/Documents").mkdir(parents=True)
        with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(Path, "home", return_value=home):
            self.assertEqual(self.reg()[0], 0)
            f = home / "Library/Containers/com.microsoft.Powerpoint/Data/Documents/wef" / f"{B.ADDIN_ID}.manifest.xml"
            self.assertTrue(f.is_file())
            self.assertEqual(self.reg("--status")[0], 0)
            self.assertEqual(self.reg(manifest=f)[0], 0)                 # 설치된 파일을 다시 등록해도 된다
            self.assertEqual(self.reg("--remove")[0], 0)
            self.assertFalse(f.exists())

    def test_mac_without_powerpoint(self):
        home = self.dir / "empty-home"
        home.mkdir()
        with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(Path, "home", return_value=home):
            self.assertEqual(self.reg()[0], 1)

    def test_other_systems_get_the_one_line_commands(self):
        # F19·ADDIN-16: 리눅스(클라우드 작업 공간 등)에서는 등록 대신 PowerPoint 가 있는 컴퓨터에서 할 일을 알려 준다
        with mock.patch.object(sys, "platform", "linux"):
            code, log = run_main(R, ["reg", "--manifest", str(self.dir / "no-such-manifest.xml")])
        self.assertEqual(code, 1)
        self.assertIn('Windows: powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/live-html/register.ps1 | iex"', log)
        self.assertIn("Mac:     curl -fsSL https://nalssam-bunpil.vercel.app/live-html/register.sh | sh", log)
        self.assertIn("홈 → 추가 기능 → 기타 설정 → 내 추가 기능 업로드(Upload My Add-in)", log)

    def test_ids_agree_across_scripts(self):
        self.assertEqual(B.ADDIN_ID, Q.ADDIN_ID)


if __name__ == "__main__":
    unittest.main()
