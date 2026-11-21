#!/usr/bin/env python3
"""Live HTML 추가 기능을 이 컴퓨터의 PowerPoint 에 등록한다 (표준 라이브러리만 사용).

    python register_addin.py            등록 (현재 사용자만, 관리자 권한 불필요)
    python register_addin.py --status   등록 상태 보기
    python register_addin.py --remove   등록 해제

Windows: manifest.xml 을 %LOCALAPPDATA%\\LiveHTML 에 복사하고
         HKCU\\SOFTWARE\\Microsoft\\Office\\16.0\\Wef\\Developer 에 경로를 적는다.
macOS:   manifest.xml 을 ~/Library/Containers/com.microsoft.Powerpoint/Data/Documents/wef 에 복사한다.
등록·해제 뒤에는 PowerPoint 를 완전히 종료했다가 다시 연다.
"""
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

DEFAULT_MANIFEST = Path(__file__).resolve().parent.parent / "assets" / "manifest.xml"
REG_KEY = r"SOFTWARE\Microsoft\Office\16.0\Wef\Developer"


def manifest_id(path: Path) -> str:
    m = re.search(r"<Id>\s*([0-9A-Fa-f-]{36})\s*</Id>", path.read_text(encoding="utf-8-sig"))
    if not m:
        sys.exit(f"{path}: <Id> 를 찾지 못했습니다")
    return m.group(1)


def manifest_url(path: Path) -> str:
    m = re.search(r'<SourceLocation\s+DefaultValue="([^"]+)"', path.read_text(encoding="utf-8-sig"))
    return m.group(1) if m else "?"


# ───────── Windows ─────────

def win_target() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "LiveHTML" / "manifest.xml"


def win_status(addin: str):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY) as k:
            return winreg.QueryValueEx(k, addin)[0]
    except OSError:
        return None


def win_register(src: Path, addin: str) -> Path:
    import winreg
    dst = win_target()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY) as k:
        winreg.SetValueEx(k, addin, 0, winreg.REG_SZ, str(dst))
    return dst


def win_remove(addin: str) -> bool:
    import winreg
    done = False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, addin)
            done = True
    except OSError:
        pass
    dst = win_target()
    if dst.exists():
        dst.unlink()
        try:
            dst.parent.rmdir()
        except OSError:
            pass
    return done


# ───────── macOS ─────────

def mac_dir() -> Path:
    return Path.home() / "Library/Containers/com.microsoft.Powerpoint/Data/Documents/wef"


def mac_file(addin: str) -> Path:
    return mac_dir() / f"{addin}.manifest.xml"



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
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="등록할 manifest.xml (기본: 스킬의 assets/manifest.xml)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--remove", action="store_true", help="등록 해제")
    g.add_argument("--status", action="store_true", help="등록 상태만 보기")
    args = ap.parse_args()
    if not args.manifest.is_file():
        sys.exit(f"manifest 가 없습니다: {args.manifest}")
    addin = manifest_id(args.manifest)

    if sys.platform == "win32":
        current = win_status(addin)
        if args.status:
            ok = bool(current) and Path(current).is_file()
            print(f"등록됨: {current}" if ok else ("등록 기록은 있으나 파일이 없습니다: " + current if current else "등록되지 않음"))
            return 0 if ok else 1
        if args.remove:
            print("등록을 해제했습니다." if win_remove(addin) else "등록되어 있지 않았습니다.")
        else:
            dst = win_register(args.manifest, addin)
            print(f"등록 완료: {dst}")
            print(f"추가 기능 페이지: {manifest_url(dst)}")
    elif sys.platform == "darwin":
        f = mac_file(addin)
        if args.status:
            print(f"등록됨: {f}" if f.is_file() else "등록되지 않음")
            return 0 if f.is_file() else 1
        if args.remove:
            if f.is_file():
                f.unlink()
                print("등록을 해제했습니다.")
            else:
                print("등록되어 있지 않았습니다.")
        else:
            if not mac_dir().parent.exists():
                print("PowerPoint 를 한 번 실행한 뒤 다시 시도하세요(PowerPoint 데이터 폴더가 아직 없습니다).")
                return 1
            mac_dir().mkdir(parents=True, exist_ok=True)
            shutil.copyfile(args.manifest, f)
            print(f"등록 완료: {f}")
            print(f"추가 기능 페이지: {manifest_url(f)}")
    else:
        print("이 운영체제의 PowerPoint 는 지원하지 않습니다(Windows·macOS 만). "
              "웹용 PowerPoint 는 삽입 → 추가 기능 → 내 추가 기능 업로드에서 manifest.xml 을 올립니다.")
        return 1
    if not args.status:
        print("PowerPoint 를 완전히 종료했다가 다시 열어 주세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
