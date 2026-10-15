#!/usr/bin/env python3
"""분필팩 빌드: src/plugins/* → plugins/claude/*, plugins/codex/*, 마켓플레이스 2종, dist/*.zip

사용: python3 tools/build.py
표준 라이브러리만 사용한다.
"""
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "plugins"
OUT_CLAUDE = ROOT / "plugins" / "claude"
OUT_CODEX = ROOT / "plugins" / "codex"
DIST = ROOT / "dist"

MARKETPLACE = "bunpil"
ORDER = ["bunpil-start", "bunpil-class", "bunpil-school", "bunpil-builder", "bunpil-connect"]
OWNER = {"name": "nalssam(날쌤) · 몽당분필", "url": "https://nalssam-bunpil.vercel.app"}
BRAND = "#E8583A"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "test_*.py")


def load_meta(p: Path) -> dict:
    return json.loads((p / "meta.json").read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_common(src: Path, dst: Path) -> None:
    if (src / "skills").is_dir():
        shutil.copytree(src / "skills", dst / "skills", ignore=IGNORE)
    hooks = src / "hooks"
    if hooks.is_dir():
        (dst / "hooks").mkdir(parents=True, exist_ok=True)
        for f in hooks.iterdir():
            if f.suffix == ".sh":  # LF 고정 (CRLF면 sh가 모든 입력을 막는다)
                t = f.read_text(encoding="utf-8").replace("\r\n", "\n")
                (dst / "hooks" / f.name).write_bytes(t.encode("utf-8"))
            elif f.suffix == ".ps1":  # BOM 붙은 UTF-8 + CRLF (Windows PowerShell 5.1 한글 호환)
                t = f.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\n", "\r\n")
                (dst / "hooks" / f.name).write_bytes(t.encode("utf-8-sig"))


def mcp_for(src: Path):
    f = src / "mcp.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def build_claude(name: str, src: Path, m: dict) -> Path:
    dst = OUT_CLAUDE / name
    copy_common(src, dst)
    if (src / "agents").is_dir():
        shutil.copytree(src / "agents", dst / "agents", ignore=IGNORE)
    hooks_src = src / "hooks" / "hooks.claude.json"
    if hooks_src.exists():
        shutil.copy2(hooks_src, dst / "hooks" / "hooks.json")
    # Windows용 훅(Git Bash 없어도 PowerShell로 실행). install.ps1이 내려받은 팩에서 hooks.json과 바꿔 끼운다.
    hooks_win = src / "hooks" / "hooks.claude.windows.json"
    if hooks_win.exists():
        shutil.copy2(hooks_win, dst / "hooks" / "hooks.windows.json")
    mcp = mcp_for(src)
    if mcp:
        write_json(dst / ".mcp.json", mcp)
    manifest = {
        "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
        "name": name,
        "displayName": m["displayName"],
        "version": m["version"],
        "description": m["description"],
        "author": m["author"],
        "homepage": m["homepage"],
        "repository": m["repository"],
        "license": m["license"],
        "keywords": m["keywords"],
    }
    write_json(dst / ".claude-plugin" / "plugin.json", manifest)
    return dst


def build_codex(name: str, src: Path, m: dict) -> Path:
    dst = OUT_CODEX / name
    copy_common(src, dst)
    manifest = {
        "name": name,
        "version": m["version"],
        "description": m["description"],
        "author": m["author"],
        "homepage": m["homepage"],
        "repository": m["repository"],
        "license": m["license"],
        "keywords": m["keywords"],
        "skills": "./skills/",
        "interface": {
            "displayName": m["displayName"],
            "shortDescription": m["shortDescription"],
            "longDescription": m["description"],
            "developerName": OWNER["name"],
            "category": "Productivity",
            "capabilities": ["Interactive", "Write"],
            "defaultPrompt": m.get("defaultPrompt", []),
            "brandColor": BRAND,
        },
    }
    hooks_src = src / "hooks" / "hooks.codex.json"
    if hooks_src.exists():
        shutil.copy2(hooks_src, dst / "hooks" / "hooks.json")
        manifest["hooks"] = "./hooks/hooks.json"
    mcp = mcp_for(src)
    if mcp:
        write_json(dst / ".mcp.json", mcp)
        manifest["mcpServers"] = "./.mcp.json"
    codex = m.get("codex", {})
    if codex.get("onboardingSkill"):
        manifest["extensions"] = {"com.openai": {"onboardingSkill": codex["onboardingSkill"]}}
    write_json(dst / ".codex-plugin" / "plugin.json", manifest)
    return dst


def zip_dir(folder: Path, out: Path, arc_root: str = "") -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                arc = Path(arc_root) / f.relative_to(folder) if arc_root else f.relative_to(folder)
                z.write(f, arc.as_posix())


def main() -> None:
    for d in (OUT_CLAUDE, OUT_CODEX, DIST):
        if d.exists():
            shutil.rmtree(d)
    claude_entries, codex_entries = [], []
    metas = {}
    for name in ORDER:
        src = SRC / name
        m = load_meta(src)
        assert m["name"] == name, f"meta name mismatch: {name}"
        metas[name] = m
        cdir = build_claude(name, src, m)
        build_codex(name, src, m)
        claude_entries.append({
            "name": name,
            "displayName": m["displayName"],
            "source": f"./plugins/claude/{name}",
            "description": m["description"],
            "version": m["version"],
            "category": m["category"],
            "tags": m["keywords"],
        })
        codex_entries.append({
            "name": name,
            "version": m["version"],
            "source": {"source": "local", "path": f"./plugins/codex/{name}"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        })
        # Claude 앱 업로드용 플러그인 zip (아카이브 안 .claude-plugin/plugin.json 1개)
        zip_dir(cdir, DIST / "claude-app" / f"{name}.zip", arc_root=name)
        # claude.ai 스킬 단독 업로드용 zip
        for sk in sorted((cdir / "skills").iterdir()):
            if sk.is_dir():
                zip_dir(sk, DIST / "skills" / f"{sk.name}.zip", arc_root=sk.name)

    write_json(ROOT / ".claude-plugin" / "marketplace.json", {
        "name": MARKETPLACE,
        "description": "nalssam's 분필팩 — 교사용 하네스 팩: 학습지·지도안·공문·가정통신문·품의·설문과 나만의 스킬 만들기",
        "owner": OWNER,
        "plugins": claude_entries,
    })
    write_json(ROOT / ".agents" / "plugins" / "marketplace.json", {
        "name": MARKETPLACE,
        "interface": {"displayName": "nalssam's 분필팩"},
        "plugins": codex_entries,
    })
    # 전체 묶음 (오프라인 배포용)
    bundle = DIST / "bunpil-pack-all.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        for base in (ROOT / ".claude-plugin", ROOT / ".agents", OUT_CLAUDE, OUT_CODEX):
            for f in sorted(base.rglob("*")):
                if f.is_file():
                    z.write(f, ("bunpil-pack" / f.relative_to(ROOT)).as_posix())
        for extra in ("README.md", "LICENSE", "NOTICE"):
            if (ROOT / extra).exists():
                z.write(ROOT / extra, f"bunpil-pack/{extra}")

    n_sk = len(list((DIST / "skills").glob("*.zip")))
    print(f"built {len(ORDER)} plugins × 2 hosts, {n_sk} skill zips, version {metas['bunpil-start']['version']}")


if __name__ == "__main__":
    main()
