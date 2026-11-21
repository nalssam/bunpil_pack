#!/bin/sh
# Live HTML 추가 기능을 이 Mac의 PowerPoint에 등록한다.
# 쓰는 법:  curl -fsSL https://nalssam-bunpil.vercel.app/live-html/register.sh | sh
# 지우기:    curl -fsSL https://nalssam-bunpil.vercel.app/live-html/register.sh | sh -s -- --remove
set -e
ID=6f2b8c1e-4d7a-4e55-9a3b-2c8f5d1e7a90
SITE=https://nalssam-bunpil.vercel.app/live-html
BASE="$HOME/Library/Containers/com.microsoft.Powerpoint/Data"
DIR="$BASE/Documents/wef"
FILE="$DIR/$ID.manifest.xml"

if [ "$1" = "--remove" ]; then
  rm -f "$FILE"
  echo "지웠습니다: Live HTML 추가 기능. PowerPoint를 다시 열면 적용됩니다."
  exit 0
fi
if [ "$(uname)" != "Darwin" ]; then
  echo "이 스크립트는 Mac용입니다. Windows는 register.ps1 을 쓰세요."
  exit 1
fi
if [ ! -d "$BASE" ]; then
  echo "PowerPoint를 한 번 실행한 뒤 다시 시도하세요(PowerPoint 데이터 폴더가 아직 없습니다)."
  exit 1
fi
mkdir -p "$DIR"
curl -fsSL "$SITE/manifest.xml" -o "$FILE.tmp"
grep -q "$ID" "$FILE.tmp" || { rm -f "$FILE.tmp"; echo "manifest.xml 을 제대로 받지 못했습니다."; exit 1; }
mv "$FILE.tmp" "$FILE"
echo "등록했습니다: Live HTML 추가 기능"
echo "  설정 파일: $FILE"
echo "  PowerPoint를 완전히 종료했다가 다시 열면 살아있는 PPT의 화면이 움직입니다."
