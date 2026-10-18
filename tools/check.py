#!/usr/bin/env python3
"""분필팩 자동 점검 (표준 라이브러리만).

검사: SKILL.md frontmatter(name·description만, name=폴더명, 설명 길이),
개인정보 원칙 블록, 점검 절, 본문 길이, 'Claude' 표기(허용 목록 외),
금지 디렉터리(bin/), 개인정보 패턴(src·evals), 플러그인 이름 규칙, dist zip 구조,
설치 문장(채팅창에 붙여넣는 첫 문단)이 사이트·README·설치 안내에서 같은지, 문서 링크·사이트 앵커.
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


def main():
    n = check_skills()
    check_personal_info()
    check_structure()
    check_site()
    check_install_text()
    for w in warns:
        print("주의:", w)
    for e in errors:
        print("오류:", e)
    print(f"스킬 {n}개 점검 — 오류 {len(errors)}건, 주의 {len(warns)}건")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
