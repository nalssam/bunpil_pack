#!/usr/bin/env python3
"""live-pptx 스크립트 자동 시험.  실행:  python -m unittest test_live_pptx  (scripts 폴더에서)

브라우저가 없어도 돌도록 미리보기는 안내 그림으로 대신한다.
"""
import base64
import contextlib
import io
import json
import os
import sys
import tempfile
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


def run_main(module, argv):
    out = io.StringIO()
    with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out):
        try:
            code = module.main()
        except SystemExit as e:
            code = e.code
    return code, out.getvalue()


def read_props(pptx: Path, slide: int) -> dict:
    with zipfile.ZipFile(pptx) as z:
        from xml.etree import ElementTree as ET
        root = ET.fromstring(z.read(f"ppt/webextensions/webextension{slide}.xml"))
    return {p.get("name"): json.loads(p.get("value")) for p in root.iter("{%s}property" % B.NS_WE)}


class Html(unittest.TestCase):
    def test_count_ignores_comments_scripts_and_other_sections(self):
        self.assertEqual(B.count_slides(DECK), 3)

    def test_notes_from_attribute_and_aside(self):
        self.assertEqual(B.extract_notes(DECK, 3), ["첫 장 & 인사", "발문 1\n발문 2", ""])

    def test_titles(self):
        self.assertEqual(B.slide_titles(DECK, 3), ["하나 둘", "둘째 장", "슬라이드 3"])

    def test_marker_goes_right_after_head(self):
        out = B.with_slide_marker("<html><head><title>x</title></head></html>", 4)
        self.assertIn("<head><script>window.__LIVE_SLIDE__=4;</script><title>", out)
        self.assertTrue(B.with_slide_marker("<p>머리 없음</p>", 2).startswith("<script>window.__LIVE_SLIDE__=2;"))

    def test_read_text_handles_bom_and_cp949(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d, "a.html"), Path(d, "b.html")
            a.write_bytes("﻿한글".encode("utf-8"))
            b.write_bytes("한글".encode("cp949"))
            self.assertEqual(B.read_text(a), "한글")
            self.assertEqual(B.read_text(b), "한글")


class ConsoleLog(unittest.TestCase):
    def test_both_chrome_log_formats(self):
        new_style = '[1:1:1121/0328.89:INFO:CONSOLE:3] "Uncaught ReferenceError: f is not defined", source: file:///t/s.html (3)'
        old_style = '[1121/0328:INFO:CONSOLE(12)] "Uncaught TypeError: x", source: file:///t/s.html (12)'
        self.assertEqual(B.CONSOLE_RE.search(new_style).group(1), "Uncaught ReferenceError: f is not defined")
        self.assertEqual(B.CONSOLE_RE.search(old_style).group(3), "12")


class Inline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        (d / "img").mkdir()
        (d / "img" / "dot one.png").write_bytes(PNG_1PX)
        (d / "base.css").write_text("@import 'more.css';\nbody{background:url(img/dot%20one.png)}", encoding="utf-8")
        (d / "more.css").write_text(".x{color:red}", encoding="utf-8")
        (d / "app.js").write_text("var t='</script>';", encoding="utf-8")
        self.dir = d

    def tearDown(self):
        self.tmp.cleanup()

    def test_local_files_are_embedded(self):
        html = ('<link rel="stylesheet" href="base.css"><script src="app.js" defer></script>'
                '<img alt="점" src="img/dot one.png"><img src="https://example.com/a.png"><img src="none.png">'
                '<div style="background:url(\'img/dot one.png\')"></div>')
        inl = B.Inliner(self.dir)
        out = inl.html(html)
        self.assertNotIn("base.css", out)
        self.assertIn(".x{color:red}", out)
        self.assertEqual(out.count("data:image/png;base64,"), 3)        # css url, img, inline style
        self.assertIn("<\\/script>", out)                                # 스크립트 안의 닫는 태그는 무력화
        self.assertNotIn('src="app.js"', out)
        self.assertIn("https://example.com/a.png", out)                  # 바깥 주소는 그대로
        self.assertEqual(inl.missing, ["none.png"])
        self.assertEqual(inl.remote, {"example.com"})

    def test_data_and_anchor_urls_untouched(self):
        html = '<img src="data:image/png;base64,AAAA"><a href="#x">x</a><img src="//cdn.example.org/x.png">'
        inl = B.Inliner(self.dir)
        self.assertEqual(inl.html(html), html)
        self.assertEqual(inl.missing, [])


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.deck = cls.dir / "deck.html"
        # JSON·XML 을 깨뜨리기 쉬운 글자를 일부러 넣는다
        cls.tricky = DECK.replace("둘째 장", "둘째 \"장\" <&> \\ \u0001   😀 </script>x")
        cls.deck.write_text(cls.tricky, encoding="utf-8")
        cls.out = cls.dir / "out" / "deck.pptx"
        cls.code, cls.log = run_main(B, ["build", str(cls.deck), "-o", str(cls.out), "--browser", str(cls.dir / "no-browser")])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_build_succeeds_and_passes_qa(self):
        self.assertEqual(self.code, 0, self.log)
        code, log = run_main(Q, ["qa", str(self.out)])
        self.assertEqual(code, 0, log)
        self.assertIn("오류 0건", log)

    def test_html_round_trips_exactly(self):
        for i in (1, 2, 3):
            p = read_props(self.out, i)
            self.assertEqual(p["html"], self.tricky)
            self.assertEqual((p["slide"], p["width"], p["height"]), (i, 1920, 1080))
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

    def test_notes_and_python_pptx_reload(self):
        from pptx import Presentation
        prs = Presentation(str(self.out))
        slides = list(prs.slides)
        self.assertEqual(len(slides), 3)
        self.assertEqual(slides[0].notes_slide.notes_text_frame.text, "첫 장 & 인사")
        self.assertFalse(slides[2].has_notes_slide)

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
        with contextlib.redirect_stderr(io.StringIO()):
            code, _ = run_main(B, ["build", str(empty), "-o", str(self.dir / "e.pptx"), "--browser", "none"])
        self.assertNotEqual(code, 0)

    def test_too_large_html_is_refused(self):
        big = self.dir / "big.html"
        big.write_text(DECK + "<!--" + "가" * 400_000 + "-->", encoding="utf-8")
        code, log = run_main(B, ["build", str(big), "-o", str(self.dir / "big.pptx"), "--browser", "none"])
        self.assertEqual(code, 2, log)
        self.assertFalse((self.dir / "big.pptx").exists())


class Template(unittest.TestCase):
    """스킬에 들어 있는 시작 틀이 그대로 변환되고 규칙을 지키는지 본다(스킬 폴더 안에서만)."""
    TEMPLATE = HERE.parent / "assets" / "deck-template.html"

    @unittest.skipUnless(TEMPLATE.is_file(), "assets/deck-template.html 이 없는 위치")
    def test_template_builds_clean(self):
        import re
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
            for lst in (Q.errors, Q.warns, Q.info):
                lst.clear()
            code, log = run_main(Q, ["qa", str(out)])
            self.assertEqual(code, 0, log)
            self.assertIn("주의 0건", log)

    @unittest.skipUnless((HERE.parent / "assets" / "manifest.xml").is_file(), "assets/manifest.xml 이 없는 위치")
    def test_manifest_matches_scripts(self):
        self.assertEqual(R.manifest_id(HERE.parent / "assets" / "manifest.xml"), B.ADDIN_ID)
        self.assertTrue(R.manifest_url(HERE.parent / "assets" / "manifest.xml").startswith("https://"))


class Qa(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        deck = d / "deck.html"
        deck.write_text(DECK, encoding="utf-8")
        self.good = d / "good.pptx"
        run_main(B, ["build", str(deck), "-o", str(self.good), "--browser", "none"])
        self.dir = d

    def tearDown(self):
        self.tmp.cleanup()

    def broken(self, name, edit):
        dst = self.dir / name
        with zipfile.ZipFile(self.good) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = edit(item.filename, zin.read(item.filename))
                if data is not None:
                    zout.writestr(item, data)
        for lst in (Q.errors, Q.warns, Q.info):
            lst.clear()
        return run_main(Q, ["qa", str(dst)])

    def test_wrong_addin_id(self):
        code, log = self.broken("id.pptx", lambda n, b: b.replace(B.ADDIN_ID.encode(), b"11111111-2222-3333-4444-555555555555"))
        self.assertEqual(code, 1)
        self.assertIn("ID", log)

    def test_broken_json(self):
        code, log = self.broken("json.pptx", lambda n, b: b.replace(b'name="slide" value="2"', b'name="slide" value="{oops"'))
        self.assertEqual(code, 1)
        self.assertIn("JSON", log)

    def test_missing_part(self):
        code, log = self.broken("part.pptx", lambda n, b: None if n == "ppt/webextensions/webextension3.xml" else b)
        self.assertEqual(code, 1)

    def test_not_a_zip(self):
        bad = self.dir / "bad.pptx"
        bad.write_bytes(b"not a zip")
        for lst in (Q.errors, Q.warns, Q.info):
            lst.clear()
        self.assertEqual(run_main(Q, ["qa", str(bad)])[0], 1)


class Register(unittest.TestCase):
    MANIFEST = ('<?xml version="1.0"?><OfficeApp><Id>6f2b8c1e-4d7a-4e55-9a3b-2c8f5d1e7a90</Id>'
                '<DefaultSettings><SourceLocation DefaultValue="https://example.com/app.html"/></DefaultSettings></OfficeApp>')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.manifest = self.dir / "manifest.xml"
        self.manifest.write_text(self.MANIFEST, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_manifest_parsing(self):
        self.assertEqual(R.manifest_id(self.manifest), B.ADDIN_ID)
        self.assertEqual(R.manifest_url(self.manifest), "https://example.com/app.html")

    def test_windows_register_status_remove(self):
        store = {}
        fake = types.ModuleType("winreg")
        fake.HKEY_CURRENT_USER, fake.REG_SZ, fake.KEY_SET_VALUE = "HKCU", 1, 2

        class Key:
            def __init__(self, path): self.path = path
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def create(root, path): store.setdefault(path, {}); return Key(path)
        def open_(root, path, *a):
            if path not in store: raise OSError("no key")
            return Key(path)
        def set_(key, name, _r, _t, value): store[key.path][name] = value
        def query(key, name):
            if name not in store[key.path]: raise OSError("no value")
            return store[key.path][name], 1
        def delete(key, name):
            if name not in store[key.path]: raise OSError("no value")
            del store[key.path][name]
        fake.CreateKey, fake.OpenKey, fake.SetValueEx, fake.QueryValueEx, fake.DeleteValue = create, open_, set_, query, delete

        local = self.dir / "한글 사용자" / "AppData" / "Local"
        with mock.patch.dict(sys.modules, {"winreg": fake}), mock.patch.object(sys, "platform", "win32"), \
                mock.patch.dict(os.environ, {"LOCALAPPDATA": str(local)}):
            code, log = run_main(R, ["reg", "--manifest", str(self.manifest), "--status"])
            self.assertEqual(code, 1)
            code, log = run_main(R, ["reg", "--manifest", str(self.manifest)])
            self.assertEqual(code, 0, log)
            target = local / "LiveHTML" / "manifest.xml"
            self.assertTrue(target.is_file())
            self.assertEqual(store[R.REG_KEY][B.ADDIN_ID], str(target))
            self.assertEqual(run_main(R, ["reg", "--manifest", str(self.manifest), "--status"])[0], 0)
            self.assertEqual(run_main(R, ["reg", "--manifest", str(self.manifest), "--remove"])[0], 0)
            self.assertNotIn(B.ADDIN_ID, store[R.REG_KEY])
            self.assertFalse(target.exists())

    def test_mac_register_and_remove(self):
        home = self.dir / "home"
        (home / "Library/Containers/com.microsoft.Powerpoint/Data/Documents").mkdir(parents=True)
        with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(Path, "home", return_value=home):
            self.assertEqual(run_main(R, ["reg", "--manifest", str(self.manifest)])[0], 0)
            f = home / "Library/Containers/com.microsoft.Powerpoint/Data/Documents/wef" / f"{B.ADDIN_ID}.manifest.xml"
            self.assertTrue(f.is_file())
            self.assertEqual(run_main(R, ["reg", "--manifest", str(self.manifest), "--status"])[0], 0)
            self.assertEqual(run_main(R, ["reg", "--manifest", str(self.manifest), "--remove"])[0], 0)
            self.assertFalse(f.exists())

    def test_mac_without_powerpoint(self):
        home = self.dir / "empty-home"
        home.mkdir()
        with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(Path, "home", return_value=home):
            self.assertEqual(run_main(R, ["reg", "--manifest", str(self.manifest)])[0], 1)

    def test_ids_agree_across_scripts(self):
        self.assertEqual(B.ADDIN_ID, Q.ADDIN_ID)


if __name__ == "__main__":
    unittest.main()
