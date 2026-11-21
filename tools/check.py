#!/usr/bin/env python3
"""분필팩 자동 점검 (표준 라이브러리만).

검사: SKILL.md frontmatter(name·description만, name=폴더명, 설명 길이),
개인정보 원칙 블록, 점검 절, 본문 길이, 'Claude' 표기(허용 목록 외),
금지 디렉터리(bin/), 개인정보 패턴(src·evals), 플러그인 이름 규칙, dist zip 구조,
설치 문장(채팅창에 붙여넣는 첫 문단)이 사이트·README·설치 안내에서 같은지, 문서 링크·사이트 앵커,
살아있는 PPT(live-pptx) 추가 기능의 ID·주소가 스킬·사이트·배포 묶음에서 같은지.
사용: python3 tools/check.py   (실패 시 종료 코드 1)
"""
import html
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "plugins"
PRIVACY = ("학생 실명·학번·생년월일·주소·연락처·가족관계·사진 등 개인을 알아볼 수 있는 정보가 보이면 "
           "작업을 멈추고 '학생A'처럼 가명으로 바꾸자고 제안한다. 결과물에는 개인정보를 넣지 않는다.")
# 제품·명령 이름으로서의 Claude 표기를 허용하는 스킬(설치·연결 안내)
CLAUDE_OK = {"setup", "checkup", "harness-gallery", "skill-maker", "share-skill", "connect", "hwpx-doc", "privacy-guard"}
RRN = re.compile(r"(?<!\d)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])-?[1-8]\d{6}(?!\d)")
REAL_PHONE = re.compile(r"(?<!\d)01[016789]-?(?!0000)\d{3,4}-?\d{4}(?!\d)")
FAKE_OK = re.compile(r"010-?(0000|1234)-?(0000|5678)")

errors, warns = [], []


def fm(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    keys = {}
    for line in m.group(1).splitlines():
        if re.match(r"^[A-Za-z_-]+:", line):
            k, v = line.split(":", 1)
            keys[k.strip()] = v.strip().strip('"')
    return keys, text[m.end():]


def check_skills():
    count = 0
    for skill_md in sorted(SRC.glob("*/skills/*/SKILL.md")):
        count += 1
        name = skill_md.parent.name
        rel = skill_md.relative_to(ROOT)
        text = skill_md.read_text(encoding="utf-8")
        keys, body = fm(text)
        if keys is None:
            errors.append(f"{rel}: frontmatter 없음"); continue
        if set(keys) != {"name", "description"}:
            errors.append(f"{rel}: frontmatter 키 {sorted(keys)} (name, description만 허용)")
        if keys.get("name") != name:
            errors.append(f"{rel}: name '{keys.get('name')}' ≠ 폴더명 '{name}'")
        d = keys.get("description", "")
        if not (80 <= len(d) <= 600):
            errors.append(f"{rel}: description 길이 {len(d)} (80~600)")
        if PRIVACY not in body:
            errors.append(f"{rel}: 개인정보 원칙 블록 없음")
        if "## 점검" not in body:
            errors.append(f"{rel}: '## 점검' 절 없음")
        if len(body) > 12000:
            warns.append(f"{rel}: 본문 {len(body)}자 — 길다(references로 분리 검토)")
        if "Claude" in body and name not in CLAUDE_OK:
            errors.append(f"{rel}: 본문에 'Claude' 표기 (모델명 대신 'AI')")
        if name.startswith(("claude", "anthropic")):
            errors.append(f"{rel}: 금지된 이름 접두어")
    return count


def check_personal_info():
    for f in list(SRC.rglob("*")) + list((ROOT / "evals").rglob("*")):
        if not f.is_file() or f.suffix not in (".md", ".yaml", ".csv", ".html", ".svg", ".json", ".py", ".txt"):
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        for m in RRN.finditer(t):
            # evals는 가드 시험용 가짜 값을 일부러 담을 수 있다 → 주의로만 표시
            (warns if "evals" in f.parts else errors).append(f"{f.relative_to(ROOT)}: 주민번호 형식 '{m.group(0)}'")
        for m in REAL_PHONE.finditer(t):
            if not FAKE_OK.search(m.group(0)):
                warns.append(f"{f.relative_to(ROOT)}: 실제 같은 휴대전화 번호 '{m.group(0)}' — 가짜 번호인지 확인")


def check_structure():
    for p in SRC.iterdir():
        if (p / "bin").exists():
            errors.append(f"{p.name}: bin/ 디렉터리 금지(Chat·Cowork 설치 거부)")
    for host in ("claude", "codex"):
        for f in (ROOT / "plugins" / host).rglob("*.ps1"):
            if not f.read_bytes().startswith(b"\xef\xbb\xbf"):
                errors.append(f"{f.relative_to(ROOT)}: BOM 없음(PowerShell 5.1 한글 깨짐)")
        for f in (ROOT / "plugins" / host).rglob("*.sh"):
            if b"\r\n" in f.read_bytes():
                errors.append(f"{f.relative_to(ROOT)}: CRLF 줄바꿈(sh 실패)")
    dist = ROOT / "dist" / "claude-app"
    for z in sorted(dist.glob("*.zip")) if dist.exists() else []:
        names = zipfile.ZipFile(z).namelist()
        n = sum(1 for x in names if x.endswith(".claude-plugin/plugin.json"))
        if n != 1:
            errors.append(f"{z.name}: plugin.json {n}개 (정확히 1개)")
        if any("/bin/" in x for x in names):
            errors.append(f"{z.name}: bin/ 포함")
    for z in sorted((ROOT / "dist" / "skills").glob("*.zip")) if (ROOT / "dist" / "skills").exists() else []:
        names = zipfile.ZipFile(z).namelist()
        if f"{z.stem}/SKILL.md" not in names:
            errors.append(f"{z.name}: '{z.stem}/SKILL.md' 없음")


def check_site():
    """public/ 배포 묶음 점검 (tools/make_site.py 결과)"""
    pub = ROOT / "public"
    if not pub.exists():
        warns.append("public/ 없음 — python3 tools/make_site.py 를 실행하세요")
        return
    for n in ("install", "claude", "codex", "uninstall"):
        sh, ps = pub / f"{n}.sh", pub / f"{n}.ps1"
        for f in (sh, ps):
            if not f.exists():
                errors.append(f"public/{f.name} 없음")
                continue
            if n != "install" and b"@BUNPIL_PRESET@" in f.read_bytes():
                errors.append(f"public/{f.name}: 미리 정한 값이 채워지지 않음")
        if sh.exists() and b"\r\n" in sh.read_bytes():
            errors.append(f"public/{sh.name}: CRLF 줄바꿈(sh 실패)")
        if ps.exists() and ps.read_bytes().startswith(b"\xef\xbb\xbf"):
            errors.append(f"public/{ps.name}: BOM 있음(irm | iex 용은 BOM 없이 charset 헤더로 읽는다)")
    z = pub / "bunpil-pack.zip"
    if not z.exists():
        errors.append("public/bunpil-pack.zip 없음")
    else:
        with zipfile.ZipFile(z) as zz:
            names = set(zz.namelist())
            for need in ("bunpil-pack/.claude-plugin/marketplace.json", "bunpil-pack/.agents/plugins/marketplace.json",
                         "bunpil-pack/install.sh", "bunpil-pack/install.ps1", "bunpil-pack/Install-Windows.bat",
                         "bunpil-pack/Install-Mac.command", "bunpil-pack/VERSION",
                         "bunpil-pack/studio/pack.py", "bunpil-pack/studio/pack.lock.json", "bunpil-pack/studio/install.sh",
                         "bunpil-pack/plugins/claude/bunpil-start/hooks/hooks.windows.json"):
                if need not in names:
                    errors.append(f"bunpil-pack.zip: {need} 없음")
            if "bunpil-pack/install.ps1" in names and not zz.read("bunpil-pack/install.ps1").startswith(b"\xef\xbb\xbf"):
                errors.append("bunpil-pack.zip: install.ps1 BOM 없음(PowerShell 5.1 -File 한글 깨짐)")
            if "bunpil-pack/Install-Windows.bat" in names:
                bat = zz.read("bunpil-pack/Install-Windows.bat")
                if not bat.isascii() or b"\r\n" not in bat:
                    errors.append("bunpil-pack.zip: Install-Windows.bat 은 ASCII + CRLF 여야 한다")
            for exe in ("bunpil-pack/install.sh", "bunpil-pack/Install-Mac.command"):
                if exe in names and not (zz.getinfo(exe).external_attr >> 16) & 0o111:
                    errors.append(f"bunpil-pack.zip: {exe} 실행 권한 없음")
            ver = zz.read("bunpil-pack/VERSION").decode().strip() if "bunpil-pack/VERSION" in names else "?"
            meta = (SRC / "bunpil-start" / "meta.json").read_text(encoding="utf-8")
            if f'"version": "{ver}"' not in meta:
                errors.append(f"bunpil-pack.zip VERSION {ver} 이 meta.json 과 다름")
    idx = pub / "index.html"
    if idx.exists():
        h = idx.read_text(encoding="utf-8")
        if re.search(r"\{\{[A-Z_]+\}\}", h) or "/*@DATA@*/null" in h:
            errors.append("public/index.html: 채우지 못한 자리표시자")
    else:
        errors.append("public/index.html 없음")
    if not (ROOT / "vercel.json").exists():
        errors.append("vercel.json 없음")


def check_install_text():
    """설치 문장은 tools/make_site.py 한 곳에서 만든다. 사이트·README·설치 안내가 그 문장과 같은지,
    Windows 채팅 명령에 달러 기호가 없는지, 문서 링크와 사이트 앵커가 살아 있는지 본다."""
    import make_site  # 문장의 단일 원본
    lead, lead_un = make_site.chat_lead(), make_site.CHAT_LEAD_UNINSTALL
    docs = {"README.md": ROOT / "README.md", "docs/install.md": ROOT / "docs" / "install.md"}
    texts = {}
    for name, f in docs.items():
        if not f.exists():
            errors.append(f"{name} 없음"); continue
        t = texts[name] = f.read_text(encoding="utf-8")
        for what, sentence in (("설치 문장", lead), ("지우기 문장", lead_un)):
            if sentence not in t:
                errors.append(f"{name}: {what}이 tools/make_site.py의 문장과 다르거나 없음")
        for m in re.finditer(r"\]\(([^)\s]+)\)", t):
            target = m.group(1)
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            if not (f.parent / target.split("#")[0]).exists():
                errors.append(f"{name}: 링크 대상 없음 → {target}")
    idx = ROOT / "public" / "index.html"
    if idx.exists():
        h = texts["public/index.html"] = idx.read_text(encoding="utf-8")
        for what, sentence in (("설치 문장", lead), ("지우기 문장", lead_un)):
            if html.escape(sentence, quote=True) not in h:
                errors.append(f"public/index.html: {what}이 tools/make_site.py의 문장과 다르거나 없음")
        body = re.sub(r"<script\b.*?</script>", "", h, flags=re.S)
        ids = re.findall(r'\sid="([^"]+)"', body)
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            errors.append(f"public/index.html: id가 겹침 → {dup}")
        for a in sorted(set(re.findall(r'href="#([^"]+)"', body))):
            if a not in ids:
                errors.append(f"public/index.html: 앵커 #{a} 의 대상 id가 없음")
    for name, t in texts.items():
        for m in re.finditer(r'powershell -NoProfile -Command (?:"|&quot;)([^\n`]*?)(?:"|&quot;)(?=[`<\s]|$)', t):
            if "$" in m.group(1):
                errors.append(f"{name}: Windows 채팅 명령에 달러 기호($)가 있음(cmd·Git Bash에서 깨짐) → {m.group(1)[:60]}")


LIVE_TEXT = {".ps1", ".sh", ".html", ".xml", ".md", ".py", ".txt", ".json", ".js", ".css", ".svg"}  # 글 파일
LIVE_SCRIPTS = ("register.ps1", "unregister.ps1", "register.sh")
LIVE_OWN = LIVE_SCRIPTS + ("app.html", "manifest.xml")     # 이름만 봐도 추가 기능의 파일인 것
LIVE_EXAMPLE_HOST = re.compile(   # 시험·예시에만 쓰는 주소(실제 사이트가 될 수 없다)
    r"^https?://(?:(?:[\w-]+\.)*(?:example\.(?:com|net|org)|example|invalid|test|localhost)|127\.0\.0\.1)(?::\d+)?(?:/|$)", re.A)


def live_commands(site: str) -> dict:
    """교사가 복사해 붙여넣는 등록·지우기 한 줄 명령. 안내 페이지와 문서에 이 글자 그대로 있어야 한다."""
    base = f"{site}/live-html"
    return {"Windows 등록": f'powershell -NoProfile -Command "irm {base}/register.ps1 | iex"',
            "Mac 등록": f"curl -fsSL {base}/register.sh | sh",
            "Windows 지우기": f'powershell -NoProfile -Command "irm {base}/unregister.ps1 | iex"',
            "Mac 지우기": f"curl -fsSL {base}/register.sh | sh -s -- --remove"}


def live_command_re(cmd: str) -> str:
    """명령이 그 글자 그대로, 뒤에 다른 글자나 옵션이 붙지 않고 있는 자리를 찾는 정규식."""
    return re.escape(cmd) + r"(?![A-Za-z0-9_]|\s*-)"


def live_read(f: Path) -> str:
    """BOM 과 줄바꿈 차이를 뺀 글."""
    return f.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def live_same(a: Path, b: Path) -> bool:
    """원본(site/live-html)과 배포본(public/live-html)이 같은가. make_site.py 가 글 파일의 줄바꿈을 고쳐 쓰므로
    글 파일은 줄바꿈 차이를 빼고 견준다. BOM 은 make_site.py 가 떼어 내는 .ps1 에서만 빼고 본다."""
    if a.suffix in LIVE_TEXT:
        enc = "utf-8-sig" if a.suffix == ".ps1" else "utf-8"
        try:
            return a.read_text(encoding=enc).replace("\r\n", "\n") == b.read_text(encoding=enc).replace("\r\n", "\n")
        except UnicodeDecodeError:
            pass
    return a.read_bytes() == b.read_bytes()


def live_expand(name: str, text: str) -> str:
    """등록 스크립트가 변수(SITE, $site)에 담아 쓰는 사이트 주소를 그 값으로 풀어 쓴 글.
    이렇게 해야 "$SITE/manifest.xml" 같은 자리도 주소·명령 점검에 걸린다."""
    if name.endswith(".sh"):
        m = re.search(r"^[ \t]*SITE=[\"']?([^\s\"']+)", text, re.M)
        return re.sub(r"\$\{SITE\}|\$SITE\b", lambda _: m.group(1), text) if m else text
    if name.endswith(".ps1"):
        m = re.search(r"^[ \t]*\$site[ \t]*=[ \t]*[\"']([^\"'\n]+)[\"']", text, re.M | re.I)
        return re.sub(r"\$\{site\}|\$site\b", lambda _: m.group(1), text, flags=re.I) if m else text
    return text


def live_addresses(name: str, text: str, site: str, served: set, anchors=None):
    """글 한 편에서 추가 기능 주소가 모두 사이트(make_site.SITE)의 /live-html/ 아래 실제 파일인지,
    한 줄 명령이 정해진 글자 그대로인지 본다. anchors 는 안내 페이지의 id 모음(주소 끝의 #자리 를 견준다)."""
    base = f"{site}/live-html"
    cmds = sorted(live_commands(site).values(), key=len, reverse=True)
    if name.endswith(".html"):
        text = html.unescape(text)
        for path in re.findall(r"""(?:href|src)\s*=\s*["'](/live-html[^"'#?]*)""", text):
            if path not in ("/live-html", "/live-html/") and path[len("/live-html/"):] not in served:
                errors.append(f"{name}: 링크 대상이 site/live-html 에 없음 → {path}")
    for no, line in enumerate(text.splitlines(), 1):
        # https:// 없이 적은 주소(호스트/live-html…)도 같은 눈으로 본다
        scan = re.sub(r"(?<![\w./:@-])((?:[\w-]+\.)+[a-z]{2,}/live-html)", r"https://\1", line, flags=re.A)
        for raw in re.findall(r"https?://[\w.~:/?#@!$&*+,;=%-]+", scan, re.A):
            raw = raw.rstrip(".,;:!?*_~")              # 문장 부호와 Markdown 강조(**주소**)는 주소가 아니다
            url, _, frag = raw.partition("#")           # 안내 페이지의 한 자리(#browser)나 ?v=2 가 붙어도 같은 파일이다
            url = url.partition("?")[0]
            tail = url.rsplit("/", 1)[-1]
            if "/live-html" not in url and not (tail in LIVE_OWN and not LIVE_EXAMPLE_HOST.match(url)):
                continue  # 추가 기능 주소가 아니다(시험·예시용 example.com 따위의 주소는 보지 않는다)
            rel = url[len(base) + 1:] if url.startswith(base + "/") else None
            if url != base and (rel is None or (rel and rel not in served)):
                errors.append(f"{name}:{no}: 추가 기능 주소가 {base}/ 아래의 실제 파일이 아님 → {raw}")
            elif frag and anchors is not None and rel in (None, "", "index.html") and frag not in anchors:
                errors.append(f"{name}:{no}: 안내 페이지에 #{frag} 자리가 없음 → {raw}")
        rest = line   # 정해진 명령을 걷어 내고도 등록 스크립트를 부르는 명령이 남으면 글자가 다른 것이다
        for c in cmds:
            rest = re.sub(live_command_re(c), " ", rest)
        if re.search(r"\b(?:irm|curl)\b.*live-html/(?:un)?register\.(?:ps1|sh)", rest):
            errors.append(f"{name}:{no}: 등록·지우기 한 줄 명령이 정해진 글자와 다름(표 안의 \\| 도 안 된다) → {line.strip()[:70]}")


def live_help_page(name: str, page: str) -> set:
    """안내 페이지(index.html)의 링크를 본다. /live-html 과 /live-html/ 어느 쪽으로 열려도 살아 있으려면
    상대 주소를 쓰면 안 된다. 페이지 안 #링크는 대상 id 가 있어야 한다. id 모음을 돌려준다."""
    body = re.sub(r"<script\b.*?</script>|<!--.*?-->", " ", page, flags=re.S | re.I)
    ids = re.findall(r"""\sid\s*=\s*["']([^"']+)["']""", body)
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"{name}: id가 겹침 → {dup}")
    for link in sorted(set(re.findall(r"""\s(?:href|src)\s*=\s*["']([^"']*)["']""", body))):
        if link.startswith("#"):
            if link[1:] and link[1:] not in ids:
                errors.append(f"{name}: 앵커 {link} 의 대상 id가 없음")
        elif not re.match(r"(?:/|https?://|mailto:|data:)", link):
            errors.append(f"{name}: 상대 주소 '{link}' (슬래시 없는 /live-html 로 열리면 깨진다. /live-html/… 로 적는다)")
    return set(ids)


def live_tree(py: Path):
    """파이썬 스크립트의 구문 나무. 읽지 못하면 None."""
    import ast
    try:
        return ast.parse(py.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return None


def live_const(tree, name: str):
    """스크립트 맨 바깥에서 글자 값으로 정한 상수(NAME = "…", NAME: str = "…"). 없으면 None."""
    import ast
    for node in tree.body if tree else []:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if (any(isinstance(x, ast.Name) and x.id == name for x in targets)
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            return node.value.value
    return None


def live_settings_keys(tree):
    """변환기가 슬라이드마다 적는 설정값 이름(build_live_pptx.py 의 props 사전의 키). 읽지 못하면 None."""
    import ast
    keys = []
    for node in ast.walk(tree) if tree else []:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                and any(isinstance(x, ast.Name) and x.id == "props" for x in node.targets)):
            keys += [k.value for k in node.value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]
    return sorted(set(keys), key=keys.index) or None


def live_version_use(tree, source: str) -> list:
    """변환기가 슬라이드에 적는 버전이 ADDIN_VERSION 한 곳에서 나오는지 본다(다른 자리에 버전을 글자로 적으면
    manifest.xml 과 따로 논다). 문제를 적은 줄들을 돌려준다."""
    import ast
    lines, bad, used = source.splitlines(), [], False
    own = [n.value for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign))
           and any(isinstance(x, ast.Name) and x.id == "ADDIN_VERSION" for x in (n.targets if isinstance(n, ast.Assign) else [n.target]))]
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "ADDIN_VERSION" and isinstance(node.ctx, ast.Load):
            used = True
        if (isinstance(node, ast.Constant) and isinstance(node.value, str) and re.fullmatch(r"\d+(?:\.\d+){3}", node.value)
                and not any(node is x for x in own) and "version" in lines[node.lineno - 1].lower()):
            bad.append(f"{node.lineno}번 줄에 버전 '{node.value}' 를 글자로 적음(ADDIN_VERSION 을 쓴다)")
    if not used:
        bad.append("ADDIN_VERSION 을 쓰는 자리가 없음(슬라이드에 적는 버전이 다른 데서 나온다)")
    return bad


def live_unit_tests(scripts: Path):
    """스킬의 자동 시험(scripts/test_live_pptx.py)을 돌린다. python-pptx·Pillow 가 없으면 주의 한 줄만 남긴다."""
    import importlib.util
    import os
    import subprocess
    if not (scripts / "test_live_pptx.py").exists():
        errors.append("live-pptx: scripts/test_live_pptx.py 없음(자동 시험)")
        return
    try:
        ready = all(importlib.util.find_spec(m) for m in ("pptx", "PIL"))
    except (ImportError, ValueError):
        ready = False
    if not ready:
        warns.append("live-pptx: python-pptx·Pillow 가 없어 scripts/test_live_pptx.py 를 돌리지 않음"
                     "(pip install python-pptx Pillow 뒤에 다시 점검)")
        return
    try:
        p = subprocess.run([sys.executable, "-B", "-m", "unittest", "test_live_pptx"], cwd=scripts,
                           capture_output=True, timeout=900, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    except subprocess.TimeoutExpired:
        errors.append("live-pptx: scripts/test_live_pptx.py 가 15분 안에 끝나지 않음")
        return
    if p.returncode != 0:
        out = (p.stdout + p.stderr).decode("utf-8", "replace")
        bad = re.findall(r"^(?:FAIL|ERROR): (\S+)", out, re.M)
        last = ([x for x in out.splitlines() if x.strip()] or ["출력 없음"])[-1].strip()
        errors.append(f"live-pptx: scripts/test_live_pptx.py 실패 — {last}"
                      + (f" → {', '.join(bad[:5])}" + (" 등" if len(bad) > 5 else "") if bad else ""))


def check_live_html():
    """살아있는 PPT(live-pptx): 스킬·사이트·배포 묶음이 서로 맞는지 본다.
    추가 기능 ID·버전·주소, 등록·지우기 한 줄 명령, 변환기가 쓰는 설정값 이름과 추가 기능 페이지가 읽는 이름,
    덱을 가두는 sandbox, public/live-html 이 site/live-html 과 같은지. 끝으로 스킬의 자동 시험을 돌린다."""
    sk = SRC / "bunpil-class" / "skills" / "live-pptx"
    src = ROOT / "site" / "live-html"
    if not sk.exists():
        if src.exists():
            errors.append("site/live-html 은 있는데 live-pptx 스킬 폴더가 없음(이름을 바꿨으면 tools/check.py 도 고친다)")
        return
    import make_site
    site = make_site.SITE
    base = f"{site}/live-html"
    manifest = (sk / "assets" / "manifest.xml").read_text(encoding="utf-8")
    m = re.search(r"<Id>([0-9a-fA-F-]{36})</Id>", manifest)
    if not m:
        errors.append("live-pptx: assets/manifest.xml 에 <Id> 없음"); return
    addin = m.group(1)
    site_files = sorted(f for f in src.iterdir() if f.is_file()) if src.exists() else []
    served = {f.name for f in site_files} | {"manifest.xml"}
    # 설정 파일 안의 주소: PowerPoint 가 여는 페이지, 아이콘, 도움말이 모두 사이트의 /live-html/ 아래 실제 파일이어야 한다
    if not re.search(r"<SourceLocation\s+DefaultValue\s*=\s*\"" + re.escape(f"{base}/app.html") + "\"", manifest):
        errors.append("live-pptx: manifest.xml 의 SourceLocation 이 사이트 주소(/live-html/app.html)가 아님")
    for url in re.findall(r"DefaultValue\s*=\s*[\"'](https?://[^\"']*)[\"']", manifest):
        if not (url.startswith(base + "/") and url[len(base) + 1:].partition("#")[0].partition("?")[0] in served | {""}):
            errors.append(f"live-pptx: manifest.xml 의 주소가 {base}/ 아래의 실제 파일이 아님 → {url}")
    trees = {}
    for script in ("build_live_pptx.py", "qa_live_pptx.py"):
        trees[script] = live_tree(sk / "scripts" / script)
        if live_const(trees[script], "ADDIN_ID") != addin:
            errors.append(f"live-pptx: scripts/{script} 의 ADDIN_ID 가 manifest.xml 과 다름")
    # 버전: 변환기가 슬라이드에 적는 버전과 등록되는 설정 파일의 버전이 같아야 한다
    build_py, build = sk / "scripts" / "build_live_pptx.py", trees["build_live_pptx.py"]
    mv = re.search(r"<Version>\s*([^<\s]+)\s*</Version>", manifest)
    bv = live_const(build, "ADDIN_VERSION")
    if not mv or not bv or mv.group(1) != bv:
        errors.append(f"live-pptx: manifest.xml 의 <Version> {mv.group(1) if mv else '없음'} 이 "
                      f"scripts/build_live_pptx.py 의 ADDIN_VERSION {bv or '없음'} 과 다름")
    if build and bv:
        for bad in live_version_use(build, build_py.read_text(encoding="utf-8")):
            errors.append(f"live-pptx: scripts/build_live_pptx.py: {bad}")
    need = ("app.html", "index.html", "register.ps1", "unregister.ps1", "register.sh", "icon-32.png", "icon-64.png")
    for n in need:
        if not (src / n).exists():
            errors.append(f"site/live-html/{n} 없음")
    if (src / "manifest.xml").exists():
        errors.append("site/live-html/manifest.xml: 여기에 두지 않는다(원본은 스킬의 assets/manifest.xml, make_site.py 가 복사한다)")
    for n in LIVE_SCRIPTS:
        f = src / n
        if f.exists() and addin not in f.read_text(encoding="utf-8-sig"):
            errors.append(f"site/live-html/{n}: 추가 기능 ID 가 manifest.xml 과 다름")
    # 안내 페이지: 상대 주소·앵커, 네 가지 한 줄 명령
    anchors = None
    if (src / "index.html").exists():
        anchors = live_help_page("site/live-html/index.html", live_read(src / "index.html"))
        page = html.unescape(live_read(src / "index.html"))
        for what, cmd in live_commands(site).items():
            if not re.search(live_command_re(cmd), page):
                errors.append(f"site/live-html/index.html: {what} 명령이 없거나 정해진 글자와 다름 → {cmd}")
    # 주소와 한 줄 명령: 등록 스크립트·안내 페이지·스킬 문서·스크립트가 모두 make_site.SITE 를 쓴다
    docs = [f for f in site_files if f.suffix in (".ps1", ".sh", ".html")]
    docs += [sk / "SKILL.md"] + sorted((sk / "references").glob("*.md")) + sorted((sk / "scripts").glob("*.py"))
    for f in docs:
        if f.exists():
            name = str(f.relative_to(ROOT))
            live_addresses(name, live_expand(name, live_read(f)), site, served, anchors)
    for n, tool in (("register.ps1", r"Invoke-WebRequest|Invoke-RestMethod|iwr|irm|DownloadFile|Start-BitsTransfer"), ("register.sh", "curl")):
        if (src / n).exists() and not re.search(rf"(?im)^.*\b(?:{tool})\b.*{re.escape(base)}/manifest\.xml(?![\w.-])",
                                                 live_expand(n, live_read(src / n))):
            errors.append(f"site/live-html/{n}: 설정 파일을 받는 주소가 {base}/manifest.xml 이 아님")
    # 추가 기능 페이지: office.js, 설정값 이름, 덱을 가두는 sandbox
    app = src / "app.html"
    if app.exists():
        page = live_read(app)
        if "appsforoffice.microsoft.com/lib/1/hosted/office.js" not in page:
            errors.append("site/live-html/app.html: office.js 를 불러오지 않음")
        reads = re.findall(r"settings\.get\(\s*[\"'](\w+)[\"']\s*\)", page)
        keys = live_settings_keys(build)
        if keys is None:
            errors.append("live-pptx: scripts/build_live_pptx.py 에서 설정값 이름(props 사전)을 읽지 못함")
        else:
            for k in keys:
                if k not in reads:
                    errors.append(f"site/live-html/app.html: 변환기가 쓰는 설정값 '{k}' 를 읽지 않음(settings.get('{k}') 없음)")
            for k in sorted(set(reads) - set(keys)):
                warns.append(f"site/live-html/app.html: 설정값 '{k}' 를 읽는데 scripts/build_live_pptx.py 는 쓰지 않음(한쪽만 새 판인지 확인)")
        code = re.sub(r"<!--.*?-->|/\*.*?\*/", " ", page, flags=re.S)   # 주석은 빼고 본다
        code = re.sub(r"(^|\s)//[^\n]*", " ", code, flags=re.M)
        frames = re.findall(r"<iframe\b[^>]*>", code, re.S | re.I)
        if not frames or not all(re.search(r"\ssandbox\s*=", x, re.I) for x in frames):
            errors.append("site/live-html/app.html: 덱을 넣는 iframe 에 sandbox 속성이 없음")
        if re.search(r"allow-same-origin", code, re.I):
            errors.append("site/live-html/app.html: sandbox 에 allow-same-origin 이 있음(덱이 격리를 풀고 추가 기능 페이지를 건드릴 수 있다)")
    bom = b"\xef\xbb\xbf"
    for f in site_files:
        if f.suffix == ".sh" and f.read_bytes().startswith(bom):
            errors.append(f"site/live-html/{f.name}: BOM 있음(curl | sh 로 읽으면 첫 줄에서 오류가 난다)")
    pub = ROOT / "public" / "live-html"
    if (ROOT / "public").exists():
        for n in need + ("manifest.xml",):
            if not (pub / n).exists():
                errors.append(f"public/live-html/{n} 없음 — python3 tools/make_site.py 를 실행하세요")
        if (pub / "manifest.xml").exists() and (pub / "manifest.xml").read_text(encoding="utf-8") != manifest.replace("\r\n", "\n"):
            errors.append("public/live-html/manifest.xml 이 스킬의 assets/manifest.xml 과 다름")
        # site/live-html 의 모든 파일이 public/live-html 에 같은 내용으로 있어야 한다(글 파일은 줄바꿈 차이만 허용)
        for f in site_files:
            if f.name == "manifest.xml":
                continue
            if not (pub / f.name).exists():
                if f.name not in need:
                    errors.append(f"public/live-html/{f.name} 없음 — python3 tools/make_site.py 를 실행하세요")
            elif not live_same(f, pub / f.name):
                errors.append(f"public/live-html/{f.name} 이 site/live-html/{f.name} 과 다름 — python3 tools/make_site.py 를 실행하세요")
        for f in sorted(x for x in pub.iterdir() if x.is_file()) if pub.exists() else []:
            data = f.read_bytes()
            if f.name not in served:
                errors.append(f"public/live-html/{f.name}: site/live-html 에 없는 파일이 남아 있음")
            elif f.suffix == ".ps1" and data.startswith(bom):
                errors.append(f"public/live-html/{f.name}: BOM 있음(irm | iex 용은 BOM 없이 charset 헤더로 읽는다)")
            elif f.suffix == ".sh":
                if data.startswith(bom):
                    errors.append(f"public/live-html/{f.name}: BOM 있음(curl | sh 로 읽으면 첫 줄에서 오류가 난다)")
                if b"\r\n" in data:
                    errors.append(f"public/live-html/{f.name}: CRLF 줄바꿈(sh 실패)")
    vj = ROOT / "vercel.json"
    if vj.exists() and "/live-html/register.ps1" not in vj.read_text(encoding="utf-8"):
        errors.append("vercel.json: /live-html/register.ps1 의 Content-Type 헤더 없음")
    live_unit_tests(sk / "scripts")


def main():
    n = check_skills()
    check_personal_info()
    check_structure()
    check_site()
    check_install_text()
    check_live_html()
    for w in warns:
        print("주의:", w)
    for e in errors:
        print("오류:", e)
    print(f"스킬 {n}개 점검 — 오류 {len(errors)}건, 주의 {len(warns)}건")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
