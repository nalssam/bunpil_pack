#!/bin/sh
# Live HTML 추가 기능을 이 Mac의 PowerPoint에 등록한다.
# 쓰는 법:  curl -fsSL https://nalssam-bunpil.vercel.app/live-html/register.sh | sh
# 지우기:    curl -fsSL https://nalssam-bunpil.vercel.app/live-html/register.sh | sh -s -- --remove
# 현재 사용자 계정의 PowerPoint 데이터 폴더에 설정 파일 하나를 둘 뿐이다. 관리자 권한이 필요 없다.
set -e

# 옵션은 여기서 받아 둔다. 일은 모두 main 안에서 하고 맨 끝 줄에서 부른다
# (내려받다 끊긴 스크립트가 중간까지만 실행되거나, 지우기가 등록으로 바뀌는 일이 없게).
NARGS=$#
ARGS="$*"

main() {
  ID=6f2b8c1e-4d7a-4e55-9a3b-2c8f5d1e7a90
  SITE=https://nalssam-bunpil.vercel.app/live-html
  BASE="$HOME/Library/Containers/com.microsoft.Powerpoint/Data"
  DIR="$BASE/Documents/wef"
  FILE="$DIR/$ID.manifest.xml"
  TMP="$FILE.tmp"

  MODE=register
  if [ "$NARGS" -gt 0 ]; then
    if [ "$NARGS" -eq 1 ] && [ "$ARGS" = "--remove" ]; then
      MODE=remove
    else
      echo "알 수 없는 옵션입니다: $ARGS" >&2
      echo "아무것도 바꾸지 않았습니다. 아래 두 줄 가운데 하나를 그대로 붙여넣으세요." >&2
      echo "  등록:   curl -fsSL $SITE/register.sh | sh" >&2
      echo "  지우기: curl -fsSL $SITE/register.sh | sh -s -- --remove" >&2
      exit 2
    fi
  fi

  if [ "$MODE" = remove ]; then
    if [ -e "$FILE" ]; then
      rm -f "$FILE"
      echo "지웠습니다: Live HTML 추가 기능. PowerPoint를 다시 열면 적용됩니다."
    else
      echo "지울 것이 없습니다. 이 계정에는 Live HTML 추가 기능이 등록되어 있지 않습니다."
    fi
    exit 0
  fi

  if [ "$(uname)" != "Darwin" ]; then
    echo "이 명령은 Mac용입니다. Windows에서는 안내 페이지의 Windows 명령을 쓰세요: $SITE/" >&2
    exit 1
  fi
  if [ ! -d "$BASE" ]; then
    echo "PowerPoint를 한 번 실행한 뒤 다시 시도하세요(PowerPoint 데이터 폴더가 아직 없습니다)." >&2
    exit 1
  fi
  mkdir -p "$DIR"
  trap 'rm -f "$TMP"' EXIT
  trap 'exit 130' INT TERM HUP
  if ! curl -fsSL "$SITE/manifest.xml" -o "$TMP"; then
    echo "설정 파일을 내려받지 못했습니다. 인터넷 연결을 확인하고 다시 실행하세요. 등록 상태는 그대로입니다." >&2
    exit 1
  fi
  # 받은 것이 온전한 설정 파일인지 본다(차단 안내 페이지나 중간에 끊긴 파일은 쓰지 않는다).
  if ! { grep -q "<Id>$ID</Id>" "$TMP" && grep -q "</OfficeApp>" "$TMP"; }; then
    echo "설정 파일을 제대로 받지 못했습니다(다른 내용이 왔거나 중간에 끊겼습니다). 등록 상태는 그대로입니다." >&2
    echo "학교망이 이 사이트를 막는지 확인하고 다시 실행하세요." >&2
    exit 1
  fi
  mv "$TMP" "$FILE"
  echo "등록했습니다: Live HTML 추가 기능"
  echo "  설정 파일: $FILE"
  echo "  PowerPoint를 완전히 종료했다가 다시 연 뒤 파일을 여세요."
  echo "  Mac의 PowerPoint에서는 아직 실제로 확인하지 못했습니다. 눌러지지 않으면 안내 페이지를 보세요: $SITE/"
  echo "  지우려면: curl -fsSL $SITE/register.sh | sh -s -- --remove"
}

main
