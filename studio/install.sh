#!/usr/bin/env bash
# 분필팩 스튜디오 설치기 (예전 이름: 날쌤팩) — macOS / Linux / Windows WSL2. sudo 없음, 계정 정보 복사 없음.
#
# 보통은 분필팩 한 줄 설치가 이 파일을 대신 실행한다:
#   curl -fsSL https://nalssam-bunpil.vercel.app/install.sh | sh -s -- --profile studio
# 직접 실행할 때(분필팩 폴더 안에서):  bash studio/install.sh [--claude] [--profile skills] [plan|doctor|uninstall ...]
# 옵션은 그대로 pack.py 에 넘어간다.
set -euo pipefail
UV_VERSION="0.12.23"
PYTHON_VERSION="3.12.12"
# 예전 날쌤팩 v1.0.1 설치와 같은 이름. 이미 설치한 분의 스킬 연결(심볼릭 링크)이 이어서 쓰이도록 바꾸지 않는다.
INSTALLER_NAME="installer-v1.0.1"
DATA_ROOT="${NALSSAM_PACK_ROOT:-$HOME/.local/share/nalssam-pack}"

for cmd in curl tar; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "필수 도구가 없습니다: $cmd" >&2; exit 1; }
done
case "$(uname -s)" in
  Linux|Darwin) ;;
  *) echo 'Windows에서는 WSL2 Ubuntu에서 실행하세요.' >&2; exit 1 ;;
esac

# 이 파일은 분필팩 폴더(studio/) 안에서 실행된다. 옆에 pack.py 가 있어야 한다.
SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
fi
if [[ -z "$SCRIPT_DIR" || ! -f "$SCRIPT_DIR/pack.py" || ! -f "$SCRIPT_DIR/pack.lock.json" ]]; then
  echo '스튜디오 설치 파일(pack.py)을 찾지 못했습니다. 분필팩을 다시 받아 설치하세요:  curl -fsSL https://nalssam-bunpil.vercel.app/install.sh | sh -s -- --profile studio' >&2
  exit 1
fi

# 분필팩 폴더는 업데이트할 때 통째로 바뀐다. 설치 기록이 가리키는 설치기는 데이터 폴더에 따로 두고,
# 내용이 달라졌을 때만 통째로 바꿔 끼운다(복사 도중 끊겨도 반쯤 바뀐 상태가 남지 않게).
MANAGED_INSTALLER="$DATA_ROOT/$INSTALLER_NAME"
same_as_managed() {
  [[ -f "$MANAGED_INSTALLER/pack.py" ]] \
    && cmp -s "$SCRIPT_DIR/pack.py" "$MANAGED_INSTALLER/pack.py" \
    && cmp -s "$SCRIPT_DIR/pack.lock.json" "$MANAGED_INSTALLER/pack.lock.json" \
    && diff -rq "$SCRIPT_DIR/locks" "$MANAGED_INSTALLER/locks" >/dev/null 2>&1 \
    && diff -rq "$SCRIPT_DIR/skills" "$MANAGED_INSTALLER/skills" >/dev/null 2>&1
}
if [[ "$SCRIPT_DIR" != "$MANAGED_INSTALLER" ]]; then
  mkdir -p "$DATA_ROOT"
  if [[ -e "$MANAGED_INSTALLER" && ! -f "$MANAGED_INSTALLER/pack.py" ]]; then
    echo "기존 폴더 보존: $MANAGED_INSTALLER" >&2
    exit 1
  fi
  if ! same_as_managed; then
    STAGED_INSTALLER=$(mktemp -d "$DATA_ROOT/.installer-XXXXXXXX")
    for item in pack.py pack.lock.json locks skills; do
      cp -R "$SCRIPT_DIR/$item" "$STAGED_INSTALLER/$item"
    done
    if [[ -e "$MANAGED_INSTALLER" ]]; then
      OLD_INSTALLER="$STAGED_INSTALLER.old"
      mv "$MANAGED_INSTALLER" "$OLD_INSTALLER"
      if mv "$STAGED_INSTALLER" "$MANAGED_INSTALLER"; then
        rm -rf "$OLD_INSTALLER"
      else
        mv "$OLD_INSTALLER" "$MANAGED_INSTALLER"
        echo "설치기를 새 버전으로 바꾸지 못했습니다: $MANAGED_INSTALLER" >&2
        exit 1
      fi
    else
      mv "$STAGED_INSTALLER" "$MANAGED_INSTALLER"
    fi
  fi
  SCRIPT_DIR="$MANAGED_INSTALLER"
fi

# uv 자체도 시스템 Python이 아니라 이 설치 폴더 안에 둔다.
if ! command -v uv >/dev/null 2>&1; then
  mkdir -p "$DATA_ROOT/bootstrap/bin"
  curl -fsSL "https://astral.sh/uv/$UV_VERSION/install.sh" -o "$DATA_ROOT/bootstrap/uv-install.sh"
  UV_INSTALL_DIR="$DATA_ROOT/bootstrap/bin" UV_NO_MODIFY_PATH=1 sh "$DATA_ROOT/bootstrap/uv-install.sh"
  export PATH="$DATA_ROOT/bootstrap/bin:$PATH"
fi
if ! command -v git >/dev/null 2>&1; then
  echo 'Git이 필요합니다. macOS: xcode-select --install / Ubuntu·WSL: sudo apt install git' >&2
  exit 1
fi
uv python install "$PYTHON_VERSION"
# 옵션이 그대로 넘어가도록 "$@" 를 따옴표로 감싼다. 예: bash install.sh --claude --profile skills
uv run --python "$PYTHON_VERSION" --no-project python "$SCRIPT_DIR/pack.py" --root "$DATA_ROOT" "$@"
