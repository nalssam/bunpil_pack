#!/usr/bin/env python3
"""nalssam's 분필팩 — 배포용 사이트 묶음 만들기

사용: python3 tools/make_site.py
  1) tools/build.py 로 플러그인·마켓플레이스·dist 를 새로 만든다
  2) public/ 에 설치 스크립트(claude·codex·install·uninstall × .sh·.ps1), 분필팩 zip,
     Claude 앱용 zip, version.json, 웹사이트(index.html), 아이콘, 미리보기 이미지를 만든다
  3) site/index.html (claude.ai 아티팩트용 조각 페이지)도 같은 원본(site/template.html)에서 만든다
  4) 저장소 루트의 vercel.json 을 만든다
표준 라이브러리 + segno(QR 코드, 없으면 QR 대신 주소만 보여 준다)
"""
import datetime
import hashlib
import html
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402

SITE = "https://nalssam-bunpil.vercel.app"
SITE_HOST = SITE.split("://", 1)[1]
REPO = "nalssam/bunpil_pack"
PUBLIC = ROOT / "public"
SITE_SRC = ROOT / "site"
KST = datetime.timezone(datetime.timedelta(hours=9))
MARKER = "# @BUNPIL_PRESET@"

# 미리 정한 값: (sh 환경변수, ps1 해시테이블, 설명)
PRESETS = {
    "claude": ({"BUNPIL_ONLY": "claude", "BUNPIL_INSTALL_CLAUDE": "1", "BUNPIL_WITH_TOOLS": "1"},
               {"Only": "claude", "InstallClaude": "1", "WithTools": "1"},
               "Claude용: Claude Code가 없으면 설치하고 Node.js·uv도 준비한다"),
    "codex": ({"BUNPIL_ONLY": "codex", "BUNPIL_INSTALL_CODEX": "1", "BUNPIL_WITH_TOOLS": "1"},
              {"Only": "codex", "InstallCodex": "1", "WithTools": "1"},
              "Codex용: Codex CLI가 없으면 설치하고 Node.js·uv도 준비한다"),
    "uninstall": ({"BUNPIL_UNINSTALL": "1"}, {"Uninstall": "1"}, "분필팩 지우기"),
}

# 스킬 한 줄 소개와 예시 요청 (웹사이트용)
SKILLS = {
    "setup": ("내 맞춤 지침 만들기", "설정 시작해줘"),
    "privacy-guard": ("학생 개인정보 가드", "이 파일에 개인정보 있는지 점검해줘"),
    "checkup": ("설치 점검", "분필 점검해줘"),
    "worksheet": ("수준별 학습지", "4학년 분수 덧셈 학습지를 수준별로 3장 만들어줘"),
    "lesson-plan": ("수업 지도안", "5학년 사회 '조선의 건국' 40분 지도안 써줘"),
    "class-slides": ("수업 슬라이드", "이 지도안으로 수업 슬라이드 만들어줘"),
    "papercraft": ("페이퍼크래프트 도안", "태양계 행성 페이퍼크래프트 도안 만들어줘"),
    "coloring": ("컬러링 도안", "가을 주제 컬러링 도안 만들어줘"),
    "rubric": ("평가 루브릭", "모둠 발표 평가 루브릭을 3단계로 만들어줘"),
    "gongmun": ("공문 처리 하네스", "받은 공문 정리하고 할 일 뽑아줘"),
    "newsletter": ("가정통신문", "현장체험학습 가정통신문 초안 써줘"),
    "pumui": ("품의 산출내역", "과학실 물품 품의 산출내역 만들어줘"),
    "parent-survey": ("학부모 설문 분석", "학부모 설문 결과 분석해줘"),
    "hwpx-doc": ("한글 문서·기안문", "내부 기안문 본문 써줘"),
    "skill-maker": ("나만의 스킬 만들기", "매주 쓰는 주간학습안내를 스킬로 만들어줘"),
    "harness-fix": ("실수를 규칙으로", "방금 틀린 부분을 규칙으로 남겨줘"),
    "eval-run": ("스킬 시험", "내 스킬 시험해줘"),
    "share-skill": ("동료와 나누기", "이 스킬을 동료에게 나눌 수 있게 묶어줘"),
    "harness-gallery": ("하네스 예시 100종", "하네스 예시 중에 학교에 맞는 걸 골라줘"),
    "connect": ("노션·패들렛·캔바 연결", "노션 연결해줘"),
}


def now_kst() -> datetime.datetime:
    return datetime.datetime.now(KST)


def sh_preset(env: dict, note: str) -> str:
    assigns = "; ".join(f': "${{{k}:={v}}}"' for k, v in env.items())
    return f"# 미리 정한 값 — {note} (환경변수로 바꿀 수 있다)\n{assigns}"


def ps_preset(d: dict, note: str) -> str:
    items = "; ".join(f"{k} = '{v}'" for k, v in d.items())
    return f"# 미리 정한 값 — {note} (환경변수로 바꿀 수 있다)\n$bunpilPreset = @{{ {items} }}"


def lf(text: str) -> str:
    return text.replace("\r\n", "\n")


def crlf(text: str) -> str:
    return lf(text).replace("\n", "\r\n")


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def zinfo(name: str, dt, mode: int = 0o644) -> zipfile.ZipInfo:
    zi = zipfile.ZipInfo(name, date_time=dt)
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.create_system = 3
    zi.external_attr = (0o100000 | mode) << 16
    return zi


def human(n: int) -> str:
    return f"{n / 1024 / 1024:.1f}MB" if n >= 1024 * 1024 else f"{max(1, round(n / 1024))}KB"


def ps_unicode_echo(text: str, color: str = "Yellow") -> str:
    """한글 안내를 ASCII만으로 쓴 PowerShell 출력 명령으로 바꾼다(.bat 파일의 코드 페이지 문제를 피한다)."""
    esc_text = "".join(ch if ch.isascii() and ch not in "'\\" else f"\\u{ord(ch):04x}" for ch in text)
    return f"Write-Host ([regex]::Unescape('{esc_text}')) -ForegroundColor {color}"


def windows_bat() -> bytes:
    """더블클릭 설치 파일. ASCII만 쓰고, 같은 폴더의 install.ps1을 -File로 실행한다(인코딩된 명령·내려받아 실행 없음)."""
    msg = "; ".join([
        ps_unicode_echo("[!] 압축을 먼저 풀어 주세요."),
        ps_unicode_echo("    zip 파일을 오른쪽 클릭 -> [모두 압축 풀기] -> 풀린 폴더에서 Install-Windows.bat 을 다시 실행합니다."),
        ps_unicode_echo("    또는 PowerShell에 붙여넣기:  irm " + SITE + "/install.ps1 | iex", "Gray"),
    ])
    bat = (
        "@echo off\n"
        "setlocal\n"
        "rem nalssam's bunpil-pack : Windows double-click installer (ASCII only on purpose)\n"
        "set \"BUNPIL_ASK=1\"\n"
        "set \"BUNPIL_WITH_TOOLS=1\"\n"
        "if not exist \"%~dp0install.ps1\" goto notextracted\n"
        "powershell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0install.ps1\"\n"
        "goto done\n"
        ":notextracted\n"
        f"powershell -NoProfile -Command \"{msg}\"\n"
        ":done\n"
        "echo.\n"
        "pause\n"
    )
    assert bat.isascii()
    return crlf(bat).encode("ascii")


MAC_COMMAND = """#!/bin/sh
# nalssam's 분필팩 — 맥에서 더블클릭으로 설치
cd "$(dirname "$0")" || exit 1
BUNPIL_ASK=1 BUNPIL_WITH_TOOLS=1 sh ./install.sh
echo ""
printf '%s' "창을 닫으려면 Enter 키를 누르세요... "
read -r _ || true
"""


def readme_first(version: str) -> str:
    return f"""nalssam's 분필팩 v{version} — 먼저 읽어 주세요

[Windows]
  1. 이 zip 파일을 오른쪽 클릭 → [모두 압축 풀기]
  2. 풀린 폴더에서 Install-Windows.bat 을 더블클릭
     - 보안 경고 창이 뜨면 [실행], "Windows의 PC 보호" 창이면 [추가 정보] → [실행]
  3. Claude Code·Codex가 없으면 무엇을 설치할지 번호로 고릅니다

[macOS]
  터미널에 아래 한 줄을 붙여넣는 방법이 가장 쉽습니다.
    Claude 쓰는 선생님:  curl -fsSL {SITE}/claude.sh | sh
    Codex 쓰는 선생님:   curl -fsSL {SITE}/codex.sh | sh
  또는 Install-Mac.command 를 오른쪽 클릭 → [열기].
  (막히면 [시스템 설정 → 개인정보 보호 및 보안]에서 [그래도 열기])

[Claude 앱(채팅·Cowork)만 쓰는 경우]
  Claude 앱 → 사용자 지정 → 플러그인 → 추가 → 마켓플레이스 추가 → {REPO}

원칙: 결과물은 모두 초안입니다. 학생 이름은 '학생A'처럼 바꿔 쓰세요.
자세한 안내: {SITE}
"""


def make_scripts(version: str):
    sh_src = lf((ROOT / "install.sh").read_text(encoding="utf-8"))
    ps_src = lf((ROOT / "install.ps1").read_text(encoding="utf-8-sig"))
    assert sh_src.count(MARKER) == 1 and ps_src.count(MARKER) == 1, "설치 스크립트에 프리셋 표시가 하나씩 있어야 한다"
    generic_sh = sh_src.replace(MARKER, "# 미리 정한 값 없음 — 옵션과 환경변수로 고른다")
    generic_ps = ps_src.replace(MARKER, "$bunpilPreset = $null  # 미리 정한 값 없음(멈춘 실행이 남긴 값도 지운다)")
    out = {"install.sh": generic_sh.encode("utf-8"), "install.ps1": crlf(generic_ps).encode("utf-8")}
    for name, (env, d, note) in PRESETS.items():
        out[f"{name}.sh"] = sh_src.replace(MARKER, sh_preset(env, note)).encode("utf-8")
        out[f"{name}.ps1"] = crlf(ps_src.replace(MARKER, ps_preset(d, note))).encode("utf-8")
    for fn, data in out.items():
        write(PUBLIC / fn, data)
    return out, generic_sh, generic_ps


def make_pack_zip(version: str, dt, sh_src: str, ps_src: str) -> Path:
    out = PUBLIC / "bunpil-pack.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        def add(name: str, data: bytes, mode: int = 0o644):
            z.writestr(zinfo(f"bunpil-pack/{name}", dt, mode), data)
        for base in (".claude-plugin", ".agents", "plugins", "catalog"):
            for f in sorted((ROOT / base).rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts:
                    rel = f.relative_to(ROOT).as_posix()
                    add(rel, f.read_bytes(), 0o755 if f.suffix == ".sh" else 0o644)
        add("VERSION", (version + "\n").encode())
        add("install.sh", sh_src.encode("utf-8"), 0o755)
        add("install.ps1", crlf(ps_src).encode("utf-8-sig"))
        add("Install-Mac.command", MAC_COMMAND.encode("utf-8"), 0o755)
        add("Install-Windows.bat", windows_bat())
        add("READ-ME-FIRST.txt", crlf(readme_first(version)).encode("utf-8-sig"))
        for extra in ("README.md", "LICENSE", "NOTICE"):
            if (ROOT / extra).exists():
                add(extra, (ROOT / extra).read_bytes())
    return out


def copy_app_zips() -> dict:
    app = PUBLIC / "app"
    if app.exists():
        shutil.rmtree(app)
    (app / "skills").mkdir(parents=True)
    plugins = {}
    for z in sorted((ROOT / "dist" / "claude-app").glob("*.zip")):
        shutil.copy2(z, app / z.name)
        plugins[z.stem] = z.stat().st_size
    for z in sorted((ROOT / "dist" / "skills").glob("*.zip")):
        shutil.copy2(z, app / "skills" / z.name)
    return plugins


def qr_svg(url: str) -> str:
    try:
        import segno  # type: ignore
    except ImportError:
        return ""
    q = segno.make(url, error="m", micro=False)
    rows = list(q.matrix_iter(scale=1, border=2))
    n = len(rows)
    path = []
    for y, row in enumerate(rows):
        x = 0
        while x < n:
            if row[x]:
                start = x
                while x < n and row[x]:
                    x += 1
                path.append(f"M{start} {y}h{x - start}v1h-{x - start}z")
            else:
                x += 1
    return (f'<svg class="qr" viewBox="0 0 {n} {n}" role="img" aria-label="{SITE_HOST} QR 코드" '
            f'shape-rendering="crispEdges"><rect width="{n}" height="{n}" fill="#ffffff"/>'
            f'<path fill="#14211b" d="{"".join(path)}"/></svg>')


def site_data(version: str) -> dict:
    plugins = []
    for name in build.ORDER:
        m = build.load_meta(build.SRC / name)
        skills = []
        order = list(SKILLS)
        dirs = [d for d in (build.SRC / name / "skills").iterdir() if d.is_dir()]
        for sk in sorted(dirs, key=lambda d: (order.index(d.name) if d.name in order else 99, d.name)):
            if (sk / "SKILL.md").exists():
                label, prompt = SKILLS.get(sk.name, (sk.name, ""))
                skills.append({"id": sk.name, "label": label, "prompt": prompt})
        plugins.append({"id": name, "name": m["displayName"], "short": m["shortDescription"],
                        "desc": m["description"], "skills": skills})
    cat = json.loads((ROOT / "catalog" / "recommended.json").read_text(encoding="utf-8"))
    return {"version": version, "plugins": plugins, "catalog": cat["items"], "linksOnly": cat["links_only"],
            "profiles": cat["profiles"]}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def pack_card(p: dict) -> str:
    rows = "".join(
        f'<li><span class="nm">{esc(s["label"])}</span>'
        f'<button class="say" type="button" data-copy="{esc(s["prompt"])}">“{esc(s["prompt"])}”</button></li>'
        for s in p["skills"])
    return (f'<article class="pack sheet"><header><h3>{esc(p["name"])}</h3><code>{esc(p["id"])}</code></header>'
            f'<p>{esc(p["desc"])}</p><ul class="sk">{rows}</ul></article>')


def plugins_html(data: dict) -> str:
    by = {p["id"]: p for p in data["plugins"]}
    first = (f'<div class="pack-stack">{pack_card(by["bunpil-start"])}{pack_card(by["bunpil-connect"])}</div>')
    rest = "".join(pack_card(by[k]) for k in ("bunpil-class", "bunpil-school", "bunpil-builder"))
    return first + rest


def kind(s: str) -> str:
    s = s.strip()
    if s in ("-", ""):
        return '<span class="kind none">—</span>'
    if s.startswith("plugin") and "+ mcp" in s:
        k = "플러그인 + MCP"
    elif s.startswith("plugin"):
        k = "플러그인"
    elif s.startswith("mcp"):
        k = "MCP"
    elif s.startswith("skills add"):
        k = "스킬"
    elif s.startswith("marketplace"):
        k = "목록만 등록"
    elif "uv tool install" in s:
        k = "MCP"
    elif "가져오기" in s:
        k = "골라 가져오기"
    else:
        k = s
    extra = " (Codex가 있을 때)" if "Codex가 있을 때" in s else ""
    return f'<span class="kind">{esc(k)}</span>{esc(extra)}'


PROFILE_TITLES = {"teacher": "teacher · 기본", "creator": "creator", "dev": "dev"}


def catalog_html(data: dict) -> str:
    out = []
    for prof in ("teacher", "creator", "dev"):
        items = [i for i in data["catalog"] if i["profile"] == prof]
        rows = []
        for i in items:
            need = "" if i.get("needs", "-") in ("-", "") else f'<span class="need">필요: {esc(i["needs"])}</span>'
            rows.append(f'<tr><td class="repo"><a href="https://github.com/{esc(i["repo"])}" rel="noopener">{esc(i["repo"])}</a></td>'
                        f'<td>{esc(i["label"])}{need}</td><td>{kind(i["claude"])}</td><td>{kind(i["codex"])}</td></tr>')
        table = ('<div class="table-wrap"><table><thead><tr><th scope="col">저장소</th><th scope="col">하는 일</th>'
                 '<th scope="col">Claude Code</th><th scope="col">Codex</th></tr></thead><tbody>'
                 + "".join(rows) + "</tbody></table></div>")
        head = (f'<h4><code>{esc(prof)}</code> {esc(data["profiles"][prof])}'
                f' <span class="muted small">{len(items)}개</span></h4>')
        if prof == "teacher":
            out.append(f'<div class="prof">{head}</div>{table}')
        else:
            out.append(f'<details class="prof-more"><summary class="prof">{head}</summary>{table}</details>')
    links = " · ".join(f'<a href="https://github.com/{esc(l["repo"])}" rel="noopener">{esc(l["repo"])}</a>'
                       for l in data["linksOnly"] if "awesome" in l["repo"])
    if links:
        out.append(f'<p class="muted small" style="margin-top:14px">함께 보면 좋은 곳: {links} (추천 목록, 링크로만 안내)</p>')
    return "\n".join(out)


def render(template: str, values: dict, data: dict) -> str:
    out = template
    for k, v in values.items():
        out = out.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    assert not left, f"채우지 못한 자리표시자: {left}"
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    assert out.count("/*@DATA@*/null") == 1
    return out.replace("/*@DATA@*/null", blob)


def full_document(fragment: str, version: str) -> str:
    desc = ("교사용 AI 하네스 팩. Claude Code와 ChatGPT Codex에 학습지·지도안·공문·가정통신문 스킬, "
            "한글(HWPX)·문서 변환·브라우저 자동화 도구를 한 줄로 설치합니다.")
    head = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{desc}">
<meta name="theme-color" content="#27473c">
<link rel="canonical" href="{SITE}/">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="nalssam's 분필팩">
<meta property="og:title" content="nalssam's 분필팩 v{version}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{SITE}/">
<meta property="og:image" content="{SITE}/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
"""
    m = re.search(r"</style>\s*", fragment)
    assert m, "template에 <style>이 있어야 한다"
    head_part, body_part = fragment[:m.end()], fragment[m.end():]
    return head + head_part + "</head>\n<body>\n" + body_part + "\n</body>\n</html>\n"


def vercel_json() -> dict:
    text_files = [f"/{n}.{ext}" for n in ("install", "claude", "codex", "uninstall") for ext in ("sh", "ps1")]
    nocache = {"key": "Cache-Control", "value": "public, max-age=0, must-revalidate"}
    headers = [{"source": p, "headers": [{"key": "Content-Type", "value": "text/plain; charset=utf-8"}, nocache]}
               for p in text_files]
    headers.append({"source": "/bunpil-pack.zip", "headers": [nocache]})
    headers.append({"source": "/version.json", "headers": [nocache, {"key": "Access-Control-Allow-Origin", "value": "*"}]})
    return {"$schema": "https://openapi.vercel.sh/vercel.json", "framework": None, "outputDirectory": "public",
            "cleanUrls": False, "headers": headers}


def main() -> None:
    build.main()
    meta = build.load_meta(build.SRC / "bunpil-start")
    version = meta["version"]
    now = now_kst()
    dt = (now.year, now.month, now.day, 0, 0, 0)
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir()

    scripts, sh_src, ps_src = make_scripts(version)
    pack = make_pack_zip(version, dt, sh_src, ps_src)
    app_plugins = copy_app_zips()
    write(PUBLIC / "VERSION", (version + "\n").encode())
    for asset in sorted((SITE_SRC / "assets").glob("*")) if (SITE_SRC / "assets").exists() else []:
        shutil.copy2(asset, PUBLIC / asset.name)
    write(PUBLIC / "robots.txt", b"User-agent: *\nAllow: /\n")

    files = {}
    for f in sorted(PUBLIC.rglob("*")):
        if f.is_file():
            b = f.read_bytes()
            files[f.relative_to(PUBLIC).as_posix()] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    n_skills = sum(len(p["skills"]) for p in site_data(version)["plugins"])
    version_info = {"name": "nalssam's 분필팩", "version": version, "date": now.strftime("%Y-%m-%d"),
                    "site": SITE, "repo": REPO, "plugins": list(app_plugins), "skills": n_skills, "files": files}
    write(PUBLIC / "version.json", (json.dumps(version_info, ensure_ascii=False, indent=2) + "\n").encode())

    template = (SITE_SRC / "template.html").read_text(encoding="utf-8")
    values = {
        "VERSION": version, "DATE": now.strftime("%Y. %m. %d.").replace(". 0", ". "), "SITE": SITE,
        "SITE_HOST": SITE_HOST, "REPO": REPO, "ZIP_SIZE": human(pack.stat().st_size),
        "SKILL_COUNT": str(n_skills), "PLUGIN_COUNT": str(len(build.ORDER)),
        "TOOL_COUNT": str(len(site_data(version)["catalog"])), "QR_SVG": qr_svg(SITE + "/"),
        "PLUGINS_HTML": plugins_html(site_data(version)), "CATALOG_HTML": catalog_html(site_data(version)),
    }
    fragment = render(template, values, site_data(version))
    write(SITE_SRC / "index.html", fragment.encode("utf-8"))
    write(PUBLIC / "index.html", full_document(fragment, version).encode("utf-8"))
    write(ROOT / "vercel.json", (json.dumps(vercel_json(), ensure_ascii=False, indent=2) + "\n").encode())

    print(f"site: v{version} · {len(scripts)} scripts · bunpil-pack.zip {human(pack.stat().st_size)} · "
          f"{len(app_plugins)} app zips · {n_skills} skills · public/ {len(files) + 2} files")


if __name__ == "__main__":
    main()
