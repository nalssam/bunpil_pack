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
ONE_LINE_WINDOWS = 'powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/live-html/register.ps1 | iex"'
ONE_LINE_MAC = "curl -fsSL https://nalssam-bunpil.vercel.app/live-html/register.sh | sh"
WEB_UPLOAD = "홈 → 추가 기능 → 기타 설정 → 내 추가 기능 업로드(Upload My Add-in)"


def read_manifest(path: Path) -> str:
    """manifest 글자. UTF-8(BOM 포함)과 UTF-16 을 읽는다. 읽지 못하면 None."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    for enc in (("utf-16",) if data[:2] in (b"\xff\xfe", b"\xfe\xff") else ()) + ("utf-8-sig",):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


def _find_id(text):
    m = re.search(r"<Id>\s*([0-9A-Fa-f-]{36})\s*</Id>", text or "")
    return m.group(1) if m else None


def manifest_id(path: Path) -> str:
    text = read_manifest(path)
    if text is None:
        sys.exit(f"{path}: 읽을 수 없습니다. manifest.xml 을 UTF-8 로 저장해 주세요.")
    found = _find_id(text)
    if not found:
        sys.exit(f"{path}: <Id> 를 찾지 못했습니다")
    return found


def manifest_url(path: Path) -> str:
    m = re.search(r'<SourceLocation\s+DefaultValue="([^"]+)"', read_manifest(path) or "")
    return m.group(1) if m else "?"


def holds(path: Path, addin: str) -> bool:
    """그 파일이 이 추가 기능(addin)의 manifest 인가."""
    found = _find_id(read_manifest(path))
    return bool(found) and found.lower() == addin.lower()


def same_file(a: Path, b: Path) -> bool:
    try:
        return a.exists() and b.exists() and os.path.samefile(a, b)
    except OSError:
        return False


def show_status(f: Path, addin: str, manifest: Path) -> int:
    """등록된 파일 f 가 이 추가 기능의 것인지 보고 알려 준다. 맞으면 0."""
    if not holds(f, addin):
        print(f"등록 기록은 있으나 그 파일은 다른 추가 기능의 것입니다: {f}")
        print("다시 등록하면 고쳐집니다:  python register_addin.py")
        return 1
    print(f"등록됨: {f}")
    print(f"추가 기능 페이지: {manifest_url(f)}")
    if manifest_url(f) != manifest_url(manifest):
        print(f"알림: 등록된 파일의 페이지 주소가 지금 manifest({manifest_url(manifest)})와 다릅니다. 다시 등록하면 맞춰집니다.")
    return 0


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
    existed = dst.exists()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not same_file(src, dst):                       # 이미 설치된 파일을 그대로 다시 등록할 때는 복사하지 않는다
        shutil.copyfile(src, dst)
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY) as k:
            winreg.SetValueEx(k, addin, 0, winreg.REG_SZ, str(dst))
    except OSError:
        if not existed:                               # 등록에 실패하면 방금 복사한 파일을 남기지 않는다
            try:
                dst.unlink()
                dst.parent.rmdir()
            except OSError:
                pass
        raise
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
    if dst.exists() and holds(dst, addin):            # 다른 추가 기능의 manifest 라면 지우지 않는다
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


def _is_wsl() -> bool:
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return False


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

    if sys.platform not in ("win32", "darwin"):
        print("이 컴퓨터에서는 등록할 수 없습니다(PowerPoint 가 있는 Windows·macOS 에서만 됩니다).")
        print("PowerPoint 를 쓰는 컴퓨터에서 아래 한 줄을 실행하면 등록됩니다.")
        print(f"  Windows: {ONE_LINE_WINDOWS}")
        print(f"  Mac:     {ONE_LINE_MAC}")
        if _is_wsl():
            print("WSL 안이라면 Windows 쪽 Python 으로 이 스크립트를 실행해도 됩니다(예: py.exe register_addin.py).")
        print(f"웹용 PowerPoint 는 {WEB_UPLOAD}에서 manifest.xml 을 올립니다.")
        return 1
    if not args.manifest.is_file():
        sys.exit(f"manifest 가 없습니다: {args.manifest}")
    addin = manifest_id(args.manifest)

    try:
        if sys.platform == "win32":
            current = win_status(addin)
            if args.status:
                if not current:
                    print("등록되지 않음")
                    return 1
                if not Path(current).is_file():
                    print("등록 기록은 있으나 파일이 없습니다: " + current)
                    return 1
                return show_status(Path(current), addin, args.manifest)
            if args.remove:
                print("등록을 해제했습니다." if win_remove(addin) else "등록되어 있지 않았습니다.")
            else:
                dst = win_register(args.manifest, addin)
                print(f"등록 완료: {dst}")
                print(f"추가 기능 페이지: {manifest_url(dst)}")
        else:
            f = mac_file(addin)
            if args.status:
                if not f.is_file():
                    print("등록되지 않음")
                    return 1
                return show_status(f, addin, args.manifest)
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
                if not same_file(args.manifest, f):
                    shutil.copyfile(args.manifest, f)
                print(f"등록 완료: {f}")
                print(f"추가 기능 페이지: {manifest_url(f)}")
    except OSError as e:
        print(f"오류: {'해제' if args.remove else '등록'}하지 못했습니다(파일이나 레지스트리에 쓸 수 없음) - {e}")
        return 1
    if not args.status:
        print("PowerPoint 를 완전히 종료했다가 다시 열어 주세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
