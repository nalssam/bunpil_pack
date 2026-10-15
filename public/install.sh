#!/bin/sh
# ─────────────────────────────────────────────────────────────
#  nalssam's 분필팩 — 한 줄 설치 (macOS · Linux)
#
#    Claude 쓰는 선생님   curl -fsSL https://nalssam-bunpil.vercel.app/claude.sh | sh
#    Codex 쓰는 선생님    curl -fsSL https://nalssam-bunpil.vercel.app/codex.sh | sh
#    직접 고르기          curl -fsSL https://nalssam-bunpil.vercel.app/install.sh | sh -s -- [옵션]
#    지우기               curl -fsSL https://nalssam-bunpil.vercel.app/uninstall.sh | sh
#
#  하는 일
#   1) 컴퓨터에 있는 Claude Code, Codex(ChatGPT)를 찾는다 (옵션을 주면 없을 때 설치한다)
#   2) 분필팩(플러그인 5종)을 내려받아 ~/.bunpil 에 두고 설치한다 (Git 없어도 됨)
#   3) 날쌤 추천 스킬·MCP·플러그인 묶음을 함께 설치한다 (catalog/recommended.json)
#        teacher(기본) 한글·발표 자료·문서 변환·브라우저 자동화(RPA)·하네스 / creator 웹·디자인·영상 / dev 개발자용
#        --nalssam 을 주면 날쌤팩(영상·모션·분석 도구, 고정 버전)도 함께 설치한다
#   4) 이미 설치되어 있으면 최신으로 바꾼다 (다시 실행 = 업데이트)
#  관리자 권한(sudo)이 필요 없다.
#
#  옵션
#   --profile teacher|creator|dev|all   추천 묶음(쉼표로 여러 개, 기본 teacher)
#   --claude | --codex                  한쪽에만 설치
#   --install-claude | --install-codex  없으면 Claude Code / Codex CLI까지 설치
#   --with-tools                        Node.js·uv가 없으면 함께 설치 (brew 또는 공식 배포본)
#   --bunpil-only  분필팩 5종만   --no-hwpx  한글 플러그인 빼기
#   --ask          Claude Code·Codex가 모두 없으면 무엇을 설치할지 물어보기
#   --nalssam      날쌤팩(nalssam/nalssam-pack)도 설치 — Claude Code가 있으면 --claude 로. 수 GB·10분 이상
#   --uninstall    분필팩 지우기
#  환경변수
#   BUNPIL_SITE  내려받을 주소(기본 https://nalssam-bunpil.vercel.app)
#   BUNPIL_REPO  GitHub 저장소(owner/repo)를 마켓플레이스로 직접 쓸 때
#   BUNPIL_HOME  분필팩을 둘 폴더(기본 ~/.bunpil)
#   BUNPIL_PROFILE · BUNPIL_ONLY(claude|codex) · BUNPIL_INSTALL_CLAUDE · BUNPIL_INSTALL_CODEX
#   BUNPIL_WITH_TOOLS · BUNPIL_ASK · BUNPIL_RECS(0=분필팩만) · BUNPIL_HWPX(0=빼기) · BUNPIL_NALSSAM · BUNPIL_UNINSTALL  (값 1 = 켜기)
# ─────────────────────────────────────────────────────────────
set -u
# 미리 정한 값 없음 — 옵션과 환경변수로 고른다

# 스크립트 전체를 { } 로 묶어 다 읽은 뒤에 실행한다. curl | sh 로 실행할 때 중간에 부르는
# 설치 프로그램이 표준입력(남은 스크립트)을 읽어 버려도 꼬이지 않게 하고, 표준입력은 비워 둔다.
{
[ -t 0 ] || exec </dev/null

SITE="${BUNPIL_SITE:-https://nalssam-bunpil.vercel.app}"
SITE="${SITE%/}"
REPO_DEFAULT="nalssam/bunpil_pack"
MARKET="bunpil"
PLUGINS="bunpil-start bunpil-class bunpil-school bunpil-builder bunpil-connect"
SKILLS_CLI="skills@1.7.2"
PLAYWRIGHT_MCP="@playwright/mcp@latest"
NODE_DIST="${BUNPIL_NODE_DIST:-https://nodejs.org/dist/latest-v24.x}"
PPTX_COMMIT="ae3d919005100472805bf39ddab234bd1cf72577"   # ZZombie04/pptx_maker (날쌤팩 v1.0.1과 같은 커밋)
NALSSAM_VERSION="v1.0.1"                                 # nalssam/nalssam-pack 릴리스
NALSSAM_ROOT="${NALSSAM_PACK_ROOT:-$HOME/.local/share/nalssam-pack}"
BUNPIL_HOME="${BUNPIL_HOME:-$HOME/.bunpil}"
PACK_DIR="$BUNPIL_HOME/bunpil-pack"
ENV_FILE="$BUNPIL_HOME/env"
ORIG_PATH="$PATH"

want_claude=1; want_codex=1; install_claude=0; install_codex=0; with_tools=0; ask=0
profiles="${BUNPIL_PROFILE:-teacher}"; recs=1; skip_hwpx=0; uninstall=0; nalssam=0
case "${BUNPIL_ONLY:-}" in claude) want_codex=0 ;; codex) want_claude=0 ;; esac
[ "${BUNPIL_INSTALL_CLAUDE:-0}" = 1 ] && install_claude=1
[ "${BUNPIL_INSTALL_CODEX:-0}" = 1 ] && install_codex=1
[ "${BUNPIL_WITH_TOOLS:-0}" = 1 ] && with_tools=1
[ "${BUNPIL_ASK:-0}" = 1 ] && ask=1
[ "${BUNPIL_RECS:-1}" = 0 ] && recs=0
[ "${BUNPIL_HWPX:-1}" = 0 ] && skip_hwpx=1
[ "${BUNPIL_UNINSTALL:-0}" = 1 ] && uninstall=1
[ "${BUNPIL_NALSSAM:-0}" = 1 ] && nalssam=1

usage() {
  cat <<'EOF'
분필팩 설치 옵션
  --profile teacher|creator|dev|all   추천 묶음(기본 teacher)
  --claude | --codex                  한쪽에만 설치
  --install-claude | --install-codex  Claude Code / Codex CLI까지 설치
  --with-tools                        Node.js·uv도 설치
  --nalssam                           날쌤팩(영상·모션·분석 도구)도 설치
  --bunpil-only  --no-hwpx  --ask  --uninstall
EOF
}
while [ $# -gt 0 ]; do
  case "$1" in
    --claude) want_codex=0 ;;
    --codex) want_claude=0 ;;
    --install-claude) install_claude=1 ;;
    --install-codex) install_codex=1 ;;
    --with-tools) with_tools=1 ;;
    --ask) ask=1 ;;
    --bunpil-only) recs=0 ;;
    --no-hwpx) skip_hwpx=1 ;;
    --uninstall) uninstall=1 ;;
    --nalssam) nalssam=1 ;;
    --profile) shift; profiles="${1:-teacher}" ;;
    --profile=*) profiles="${1#--profile=}" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "알 수 없는 옵션: $1 (무시합니다)" ;;
  esac
  [ $# -gt 0 ] && shift
done
case ",$profiles," in *,nalssam,*) nalssam=1 ;; esac
case ",$profiles," in *,all,*) profiles="teacher,creator,dev" ;; esac
profiles=$(printf '%s' "$profiles" | tr ',' '\n' | grep -v '^nalssam$' | grep -v '^$' | paste -sd, -)
[ -n "$profiles" ] || profiles="teacher"
in_profile() { case ",$profiles," in *",$1,"*) return 0 ;; esac; return 1; }

if [ -t 1 ]; then B=$(printf '\033[1m'); G=$(printf '\033[32m'); Y=$(printf '\033[33m'); R=$(printf '\033[31m'); D=$(printf '\033[2m'); N=$(printf '\033[0m'); else B=""; G=""; Y=""; R=""; D=""; N=""; fi
say()  { printf '%s\n' "$*"; }
ok()   { printf '%s  ✓ %s%s\n' "$G" "$*" "$N"; }
skip() { printf '%s  - %s%s\n' "$D" "$*" "$N"; }
warn() { printf '%s  ! %s%s\n' "$Y" "$*" "$N"; }
fail() { printf '%s  ✗ %s%s\n' "$R" "$*" "$N"; errors=$((errors+1)); }
has()  { command -v "$1" >/dev/null 2>&1; }
git_ok() {  # 맥의 /usr/bin/git 은 개발자 도구가 없으면 설치 창만 띄우는 자리표시자다
  has git || return 1
  case "$(uname -s)" in Darwin) [ "$(command -v git)" != /usr/bin/git ] || xcode-select -p >/dev/null 2>&1 ;; *) return 0 ;; esac
}
errors=0
PATH_CHANGED=0

# 정확한 이름으로 찾기
c_has_market() { claude plugin marketplace list 2>/dev/null | grep -qE "^[[:space:]]*> $1\$"; }
c_has_plugin() { claude plugin list 2>/dev/null | grep -qE "^[[:space:]]*> $1\$"; }
c_market_src() { claude plugin marketplace list 2>/dev/null | awk -v m="$1" 'f { print; exit } $0 ~ "^[[:space:]]*> " m "$" { f = 1 }'; }
x_has_market() { codex plugin marketplace list 2>/dev/null | awk '{print $1}' | grep -qx "$1"; }
x_market_line() { codex plugin marketplace list 2>/dev/null | awk -v m="$1" '$1 == m { print; exit }'; }

# 내려받기·압축 풀기·받은 설치 프로그램 실행
download() { if has curl; then curl -fsSL "$1" -o "$2"; elif has wget; then wget -q -O "$2" "$1"; else return 1; fi; }
unpack() {
  if has unzip; then unzip -q -o "$1" -d "$2"
  elif has python3; then python3 -c 'import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' "$1" "$2"
  else tar -xf "$1" -C "$2"; fi
}
run_remote() {  # run_remote <주소> <셸> — 끝까지 받은 뒤에만 실행한다(받기 실패를 성공으로 오해하지 않도록)
  rr_f="$BUNPIL_HOME/.dl.$$"
  mkdir -p "$BUNPIL_HOME" 2>/dev/null
  if ! download "$1" "$rr_f" || [ ! -s "$rr_f" ]; then rm -f "$rr_f"; return 1; fi
  "$2" "$rr_f"; rr_rc=$?
  rm -f "$rr_f"
  return $rr_rc
}

# 새 터미널에서도 명령을 찾도록 PATH를 셸 설정에 남긴다 (~/.bunpil/env 한 곳에 모은다)
persist_path() {
  [ -d "$1" ] || return 0
  case ":$ORIG_PATH:" in *":$1:"*) return 0 ;; esac
  mkdir -p "$BUNPIL_HOME" 2>/dev/null || return 0
  [ -f "$ENV_FILE" ] || printf '%s\n' "# nalssam's 분필팩이 추가한 PATH. 지우려면 이 파일과 셸 설정 파일의 'bunpil-path' 줄을 지우세요." > "$ENV_FILE"
  pp_line="case \":\$PATH:\" in *\":$1:\"*) ;; *) PATH=\"$1:\$PATH\" ;; esac"
  grep -qxF "$pp_line" "$ENV_FILE" 2>/dev/null || printf '%s\n' "$pp_line" >> "$ENV_FILE"
  pp_hook="[ -f \"$ENV_FILE\" ] && . \"$ENV_FILE\"  # bunpil-path"
  pp_done=0
  for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
    [ -f "$rc" ] || continue
    grep -qF "# bunpil-path" "$rc" 2>/dev/null || printf '\n%s\n' "$pp_hook" >> "$rc"
    pp_done=1
  done
  if [ "$pp_done" = 0 ]; then
    case "${SHELL:-}" in */zsh) printf '%s\n' "$pp_hook" >> "$HOME/.zshrc" ;; *) printf '%s\n' "$pp_hook" >> "$HOME/.profile" ;; esac
  fi
  case "$(uname -s)" in Darwin) [ -f "$HOME/.zshrc" ] || printf '%s\n' "$pp_hook" >> "$HOME/.zshrc" ;; esac
  PATH_CHANGED=1
}

# Node.js를 관리자 권한 없이 ~/.bunpil/node 에 설치 (공식 배포본, SHA-256 확인)
install_node_local() {
  case "$(uname -s)" in Darwin) n_os=darwin ;; Linux) n_os=linux ;; *) return 1 ;; esac
  case "$(uname -m)" in arm64|aarch64) n_arch=arm64 ;; x86_64|amd64) n_arch=x64 ;; *) return 1 ;; esac
  n_tmp="$BUNPIL_HOME/.node.$$"
  rm -rf "$n_tmp"; mkdir -p "$n_tmp" || return 1
  if ! download "$NODE_DIST/SHASUMS256.txt" "$n_tmp/SHASUMS256.txt"; then rm -rf "$n_tmp"; return 1; fi
  n_line=$(grep -E "  node-v[0-9.]+-$n_os-$n_arch\.tar\.gz\$" "$n_tmp/SHASUMS256.txt" | head -1)
  [ -n "$n_line" ] || { rm -rf "$n_tmp"; return 1; }
  n_sum=${n_line%% *}; n_file=${n_line##* }
  if ! download "$NODE_DIST/$n_file" "$n_tmp/$n_file"; then rm -rf "$n_tmp"; return 1; fi
  if has sha256sum; then n_got=$(sha256sum "$n_tmp/$n_file" | awk '{print $1}')
  elif has shasum; then n_got=$(shasum -a 256 "$n_tmp/$n_file" | awk '{print $1}')
  elif has openssl; then n_got=$(openssl dgst -sha256 "$n_tmp/$n_file" | awk '{print $NF}')
  else warn "SHA-256 확인 도구가 없어 내려받은 Node.js 검증을 건너뜁니다"; n_got="$n_sum"; fi
  [ "$n_got" = "$n_sum" ] || { rm -rf "$n_tmp"; return 1; }
  tar -xzf "$n_tmp/$n_file" -C "$n_tmp" || { rm -rf "$n_tmp"; return 1; }
  rm -rf "$BUNPIL_HOME/node"
  mv "$n_tmp/${n_file%.tar.gz}" "$BUNPIL_HOME/node" || { rm -rf "$n_tmp"; return 1; }
  rm -rf "$n_tmp"
  PATH="$BUNPIL_HOME/node/bin:$PATH"; export PATH
  persist_path "$BUNPIL_HOME/node/bin"
  has node && has npx
}

# 이 스크립트가 압축을 푼 분필팩 폴더 안에서 실행됐는지 확인(더블클릭 설치)
LOCAL_SRC="${BUNPIL_LOCAL:-}"
if [ -z "$LOCAL_SRC" ] && [ -f "$0" ]; then
  d=$(cd "$(dirname "$0")" 2>/dev/null && pwd)
  if [ -n "$d" ] && [ -f "$d/.claude-plugin/marketplace.json" ] && [ -d "$d/plugins" ]; then LOCAL_SRC="$d"; fi
fi

say ""
say "${B}nalssam's 분필팩${N} — 선생님의 AI 조수를 한 줄로"
say "누구도 소외되지 않는 기술, 혼자 닳지 않는 교사"
say ""

# ── 지우기 ───────────────────────────────────────────────────
if [ "$uninstall" = 1 ]; then
  say "${B}분필팩을 지웁니다${N}"
  if [ "$want_claude" = 1 ] && has claude; then
    for p in $PLUGINS; do
      if c_has_plugin "$p@$MARKET"; then claude plugin uninstall "$p@$MARKET" >/dev/null 2>&1 && ok "Claude Code: $p 제거" || fail "Claude Code: $p 제거 실패"; fi
    done
    if c_has_market "$MARKET"; then claude plugin marketplace remove "$MARKET" >/dev/null 2>&1 && ok "Claude Code: 분필팩 목록 제거"; fi
  fi
  if [ "$want_codex" = 1 ] && has codex; then
    for p in $PLUGINS; do codex plugin remove "$p@$MARKET" >/dev/null 2>&1 && ok "Codex: $p 제거"; done
    if x_has_market "$MARKET"; then codex plugin marketplace remove "$MARKET" >/dev/null 2>&1 && ok "Codex: 분필팩 목록 제거"; fi
  fi
  case "$PACK_DIR" in */bunpil-pack) if [ -d "$PACK_DIR" ]; then rm -rf "$PACK_DIR" && ok "내려받은 분필팩 폴더 삭제 ($PACK_DIR)"; fi ;; esac
  say ""
  say "그대로 둔 것 (다른 곳에서도 쓰는 도구라서):"
  say "  • 추천 묶음(한글 도구·MCP 등)  Claude Code: claude plugin uninstall <이름>@<마켓> · claude mcp remove <이름>"
  say "                                 Codex: codex plugin remove <이름>@<마켓> · codex mcp remove <이름>"
  [ -d "$BUNPIL_HOME/node" ] && say "  • 분필팩이 설치한 Node.js($BUNPIL_HOME/node)"
  [ -f "$ENV_FILE" ] && say "  • PATH 설정($ENV_FILE)과 셸 설정 파일(~/.zshrc 등)의 'bunpil-path' 줄 — 지우면 Node.js 등을 찾지 못할 수 있습니다"
  [ -f "$NALSSAM_ROOT/state.json" ] && say "  • 날쌤팩 — 따로 지우려면  nalssam-pack uninstall  (날쌤팩이 만든 연결만 해제)"
  say "  • 작업 폴더의 CLAUDE.md·AGENTS.md·my-harness 폴더(선생님 파일)"
  [ "$errors" -gt 0 ] && exit 1
  exit 0
fi

# ── 아무것도 없을 때 물어보기(더블클릭 설치) ─────────────────
HAS_CLAUDE=0; HAS_CODEX=0
[ "$want_claude" = 1 ] && has claude && HAS_CLAUDE=1
[ "$want_codex" = 1 ] && has codex && HAS_CODEX=1
if [ "$HAS_CLAUDE" = 0 ] && [ "$HAS_CODEX" = 0 ] && [ "$ask" = 1 ] && [ "$install_claude" = 0 ] && [ "$install_codex" = 0 ] && [ -r /dev/tty ]; then
  say "이 컴퓨터에 Claude Code와 Codex가 모두 없습니다. 무엇을 설치할까요?"
  say "  1) Claude Code  — Claude Pro 이상 유료 요금제"
  say "  2) Codex        — ChatGPT 계정(무료 포함), Node.js가 함께 설치됩니다"
  say "  3) 둘 다"
  printf '번호를 누르고 Enter (그만두려면 그냥 Enter): '
  ans=""; read -r ans </dev/tty || ans=""
  case "$ans" in
    1) install_claude=1; want_codex=0 ;;
    2) install_codex=1; want_claude=0; with_tools=1 ;;
    3) install_claude=1; install_codex=1; with_tools=1 ;;
    *) say "그만둡니다."; exit 0 ;;
  esac
  say ""
fi

# ── 준비물 설치 ──────────────────────────────────────────────
if [ "$want_claude" = 1 ] && [ "$install_claude" = 1 ] && ! has claude; then
  say "${B}Claude Code 설치${N} (공식 설치 프로그램 · 1~2분)"
  if run_remote https://claude.ai/install.sh bash >/dev/null 2>&1; then
    PATH="$HOME/.local/bin:$PATH"; export PATH
    if has claude; then ok "Claude Code 설치 완료 ($(claude --version 2>/dev/null | head -1))"; persist_path "$HOME/.local/bin"
    else fail "Claude Code가 설치됐지만 찾지 못했습니다 — 터미널을 새로 열고 다시 실행하세요"; fi
  else
    fail "Claude Code 설치 실패 — https://claude.com/download 에서 직접 설치하세요"
  fi
  say ""
fi
if [ "$with_tools" = 1 ]; then
  say "${B}준비 도구${N} (Node.js·uv — 문서·자동화 도구에 필요)"
  if has node && has npx; then ok "Node.js $(node --version 2>/dev/null) 있음"
  elif has brew && brew install node >/dev/null 2>&1 && has node; then ok "Node.js 설치(brew)"
  elif install_node_local; then ok "Node.js $(node --version 2>/dev/null) 설치 ($BUNPIL_HOME/node · 관리자 권한 없이)"
  else warn "Node.js를 설치하지 못했습니다 — https://nodejs.org 에서 LTS를 설치한 뒤 다시 실행하세요"; fi
  if has uv && has uvx; then ok "uv 있음"
  elif has brew && brew install uv >/dev/null 2>&1 && has uv; then ok "uv 설치(brew)"
  elif run_remote https://astral.sh/uv/install.sh sh >/dev/null 2>&1; then
    PATH="$HOME/.local/bin:$PATH"; export PATH
    if has uv; then ok "uv 설치(공식 설치 프로그램)"; persist_path "$HOME/.local/bin"; else warn "uv를 설치했지만 찾지 못했습니다"; fi
  else warn "uv를 설치하지 못했습니다 — https://docs.astral.sh/uv 를 참고하세요"; fi
  if git_ok; then ok "Git 있음"
  elif has brew && brew install git >/dev/null 2>&1 && git_ok; then ok "Git 설치(brew)"
  elif [ "$(uname -s)" = Darwin ]; then
    xcode-select --install >/dev/null 2>&1
    warn "Git이 없습니다. 화면에 뜬 '개발자 도구 설치' 창에서 [설치]를 누르고, 끝나면 같은 명령을 다시 실행하세요."
  else warn "Git이 없습니다 — 배포판의 패키지 관리자로 git을 설치한 뒤 다시 실행하세요"; fi
  say ""
fi
if [ "$want_codex" = 1 ] && [ "$install_codex" = 1 ] && ! has codex; then
  say "${B}Codex CLI 설치${N} (OpenAI 공식 설치 프로그램 · 1~2분)"
  CODEX_NON_INTERACTIVE=1; export CODEX_NON_INTERACTIVE
  if run_remote https://chatgpt.com/codex/install.sh sh >/dev/null 2>&1; then PATH="$HOME/.local/bin:$PATH"; export PATH; fi
  if ! has codex && has npm; then
    npm install -g @openai/codex >/dev/null 2>&1 || npm install -g --prefix "$HOME/.local" @openai/codex >/dev/null 2>&1
    PATH="$(npm prefix -g 2>/dev/null)/bin:$HOME/.local/bin:$PATH"; export PATH
  fi
  if ! has codex && has brew; then brew install --cask codex >/dev/null 2>&1; fi
  if has codex; then ok "Codex CLI 설치 완료 ($(codex --version 2>/dev/null | head -1))"; persist_path "$(dirname "$(command -v codex)")"
  else fail "Codex CLI 설치 실패 — https://developers.openai.com/codex 의 안내로 직접 설치한 뒤 다시 실행하세요"; fi
  say ""
fi

HAS_CLAUDE=0; HAS_CODEX=0
[ "$want_claude" = 1 ] && has claude && HAS_CLAUDE=1
[ "$want_codex" = 1 ] && has codex && HAS_CODEX=1
if [ "$HAS_CLAUDE" = 0 ] && [ "$HAS_CODEX" = 0 ]; then
  fail "Claude Code도 Codex도 찾지 못했습니다."
  say ""
  say "  • Claude 쓰는 선생님:  curl -fsSL $SITE/claude.sh | sh"
  say "  • Codex 쓰는 선생님:   curl -fsSL $SITE/codex.sh | sh"
  say "  • 터미널 없이 Claude 앱에서: $SITE 의 'Claude 앱' 안내를 따르세요"
  exit 1
fi
HAS_NPX=0; has npx && HAS_NPX=1
HAS_UVX=0; has uvx && HAS_UVX=1
HAS_GIT=0; git_ok && HAS_GIT=1
GIT_SKIP="Git이 없어 건너뜀 (Git 설치 후 다시 실행)"

# ── 분필팩 내려받기 ──────────────────────────────────────────
SOURCE=""; SOURCE_IS_REPO=0; SOURCE_FALLBACK=0
pack_version() { cat "$PACK_DIR/VERSION" 2>/dev/null || echo '?'; }
has_pack() { [ -f "$PACK_DIR/.claude-plugin/marketplace.json" ]; }
prepare_pack() {
  if [ -n "${BUNPIL_REPO:-}" ]; then SOURCE="$BUNPIL_REPO"; SOURCE_IS_REPO=1; ok "분필팩 저장소: $SOURCE"; return 0; fi
  mkdir -p "$BUNPIL_HOME" || { fail "$BUNPIL_HOME 폴더를 만들 수 없습니다"; return 1; }
  # 지난 실행이 남긴 임시 폴더 정리. 분필팩 폴더가 없고 옛 사본만 남아 있으면 먼저 되돌린다
  for old_tmp in "$BUNPIL_HOME"/.tmp.*; do
    [ -d "$old_tmp" ] || continue
    if [ ! -d "$PACK_DIR" ] && [ -f "$old_tmp/old/.claude-plugin/marketplace.json" ]; then mv "$old_tmp/old" "$PACK_DIR" 2>/dev/null; fi
    if [ -d "$PACK_DIR" ] || [ ! -d "$old_tmp/old" ]; then rm -rf "$old_tmp"; fi
  done
  tmp="$BUNPIL_HOME/.tmp.$$"
  rm -rf "$tmp"; mkdir -p "$tmp/new"
  if [ -n "$LOCAL_SRC" ]; then
    if [ -d "$PACK_DIR" ] && [ "$(cd "$LOCAL_SRC" && pwd)" = "$(cd "$PACK_DIR" && pwd)" ]; then rm -rf "$tmp"; SOURCE="$PACK_DIR"; ok "분필팩 폴더 사용 ($PACK_DIR)"; return 0; fi
    mkdir -p "$tmp/new/bunpil-pack"
    for x in .claude-plugin .agents plugins catalog VERSION install.sh install.ps1 README.md LICENSE NOTICE; do
      [ -e "$LOCAL_SRC/$x" ] && cp -R "$LOCAL_SRC/$x" "$tmp/new/bunpil-pack/"
    done
  else
    # 받기·압축 풀기·내용 확인 중 하나라도 실패하면(학교 방화벽이 안내 페이지를 대신 주는 경우 포함) 같은 길로 처리한다
    if ! { download "$SITE/bunpil-pack.zip" "$tmp/pack.zip" && unpack "$tmp/pack.zip" "$tmp/new" >/dev/null 2>&1 \
           && [ -f "$tmp/new/bunpil-pack/.claude-plugin/marketplace.json" ]; }; then
      rm -rf "$tmp"
      if has_pack; then
        warn "새 분필팩을 받지 못해(인터넷·학교 방화벽 확인) 이미 있는 분필팩(v$(pack_version))을 그대로 씁니다"
        SOURCE="$PACK_DIR"; return 0
      fi
      if git_ok; then warn "분필팩을 받지 못해 GitHub 저장소($REPO_DEFAULT)를 대신 씁니다"; SOURCE="$REPO_DEFAULT"; SOURCE_IS_REPO=1; SOURCE_FALLBACK=1; return 0; fi
      fail "분필팩을 받지 못했습니다 ($SITE/bunpil-pack.zip) — 인터넷 연결이나 학교 방화벽을 확인하세요"; return 1
    fi
  fi
  if [ ! -f "$tmp/new/bunpil-pack/.claude-plugin/marketplace.json" ]; then rm -rf "$tmp"; fail "받은 분필팩이 올바르지 않습니다"; return 1; fi
  # 이전 폴더를 먼저 옆으로 옮긴 뒤 새 폴더를 놓는다. 못 바꾸면 지금 버전을 그대로 쓴다
  if [ -d "$PACK_DIR" ] && ! mv "$PACK_DIR" "$tmp/old"; then
    rm -rf "$tmp"; warn "분필팩 폴더를 새 버전으로 바꾸지 못해 지금 버전(v$(pack_version))을 그대로 씁니다 — 폴더 권한을 확인하고 다시 실행하세요"
    SOURCE="$PACK_DIR"; return 0
  fi
  if ! mv "$tmp/new/bunpil-pack" "$PACK_DIR"; then
    [ -d "$tmp/old" ] && [ ! -d "$PACK_DIR" ] && mv "$tmp/old" "$PACK_DIR"
    if has_pack; then rm -rf "$tmp"; warn "새 분필팩을 제자리에 두지 못해 지금 버전(v$(pack_version))을 그대로 씁니다"; SOURCE="$PACK_DIR"; return 0; fi
    fail "분필팩 폴더를 준비하지 못했습니다 — 같은 명령을 다시 실행해 보세요 (임시 폴더: $tmp)"; return 1
  fi
  [ -d "$PACK_DIR" ] && rm -rf "$tmp"
  SOURCE="$PACK_DIR"
  ok "분필팩 v$(cat "$PACK_DIR/VERSION" 2>/dev/null || echo '?') 준비 ($PACK_DIR)"
}

# ── 공통 도우미 ──────────────────────────────────────────────
c_plugin() {   # c_plugin <저장소> <플러그인@마켓> <표시이름>
  if in_nalssam "$1"; then skip "$3 — $NALSSAM_SKIP"; return; fi
  if c_has_plugin "$2"; then
    if claude plugin update "$2" >/dev/null 2>&1; then ok "$3 — 최신 확인"; else warn "$3 — 업데이트 확인 실패(지금 버전 유지)"; fi
    return
  fi
  if [ "$HAS_GIT" = 0 ]; then skip "$3 — $GIT_SKIP"; return; fi
  m="${2#*@}"
  if c_has_market "$m"; then claude plugin marketplace update "$m" >/dev/null 2>&1; else claude plugin marketplace add "$1" >/dev/null 2>&1; fi
  if claude plugin install "$2" -y >/dev/null 2>&1; then ok "$3"; else fail "$3 — 설치 실패 (claude plugin install ${2%@*} --marketplace $1)"; fi
}
c_market() {   # c_market <저장소> <마켓이름> <표시이름>
  if in_nalssam "$1"; then skip "$3 — $NALSSAM_SKIP"; return; fi
  if [ "$HAS_GIT" = 0 ]; then skip "$3 — $GIT_SKIP"; return; fi
  if c_has_market "$2"; then
    if claude plugin marketplace update "$2" >/dev/null 2>&1; then ok "$3 — 목록 갱신"; else warn "$3 — 목록 갱신 실패(지금 목록 유지)"; fi
  elif claude plugin marketplace add "$1" >/dev/null 2>&1; then ok "$3 — 목록 등록(/plugin에서 골라 설치)"
  else fail "$3 — 목록 등록 실패"; fi
}
x_plugin() {   # x_plugin <저장소> <플러그인@마켓> <표시이름>
  if in_nalssam "$1"; then skip "$3 — $NALSSAM_SKIP"; return; fi
  if [ "$HAS_GIT" = 0 ]; then skip "$3 — $GIT_SKIP"; return; fi
  m="${2#*@}"
  if x_has_market "$m"; then codex plugin marketplace upgrade "$m" >/dev/null 2>&1; else codex plugin marketplace add "$1" >/dev/null 2>&1; fi
  if codex plugin add "$2" >/dev/null 2>&1; then ok "$3"; else fail "$3 — 설치 실패 (codex plugin add $2)"; fi
}
x_market() {
  if in_nalssam "$1"; then skip "$3 — $NALSSAM_SKIP"; return; fi
  if [ "$HAS_GIT" = 0 ]; then skip "$3 — $GIT_SKIP"; return; fi
  if x_has_market "$2"; then
    if codex plugin marketplace upgrade "$2" >/dev/null 2>&1; then ok "$3 — 목록 갱신"; else warn "$3 — 목록 갱신 실패(지금 목록 유지)"; fi
  elif codex plugin marketplace add "$1" >/dev/null 2>&1; then ok "$3 — 목록 등록(/plugins에서 골라 설치)"
  else fail "$3 — 목록 등록 실패"; fi
}
skills_add() { # skills_add <저장소> <claude-code|codex> <표시이름>
  if in_nalssam "$1"; then skip "$3 — $NALSSAM_SKIP"; return; fi
  if [ "$HAS_NPX" = 0 ]; then skip "$3 — Node.js가 없어 건너뜀"; return; fi
  if [ "$HAS_GIT" = 0 ]; then skip "$3 — $GIT_SKIP"; return; fi
  if DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 npx -y "$SKILLS_CLI" add "$1" -g -a "$2" -y --copy >/dev/null 2>&1; then ok "$3"
  else fail "$3 — 스킬 설치 실패 (npx $SKILLS_CLI add $1 -g -a $2)"; fi
}
mcp_add() {    # mcp_add <claude|codex> <이름> <표시이름> <명령...>
  host="$1"; name="$2"; label="$3"; shift 3
  if [ "$NALSSAM_DONE" = 1 ]; then case "$name" in kordoc|markitdown) skip "$label — $NALSSAM_SKIP"; return ;; esac; fi
  if [ "$host" = claude ]; then
    if claude mcp get "$name" >/dev/null 2>&1; then ok "$label — 이미 연결됨"; return; fi
    if claude mcp add -s user "$name" -- "$@" >/dev/null 2>&1; then ok "$label"; else fail "$label — MCP 등록 실패"; fi
  else
    if codex mcp get "$name" >/dev/null 2>&1; then ok "$label — 이미 연결됨"; return; fi
    if codex mcp add "$name" -- "$@" >/dev/null 2>&1; then ok "$label"; else fail "$label — MCP 등록 실패"; fi
  fi
}
MD_WARM=0
warm_markitdown() {  # 첫 실행 때 내려받는 시간(30초 안팎) 때문에 MCP 연결이 시간 초과되지 않도록 미리 받아 둔다
  [ "$MD_WARM" = 1 ] && return 0; MD_WARM=1
  [ "$HAS_UVX" = 1 ] && uvx markitdown-mcp --help >/dev/null 2>&1
  return 0
}
NALSSAM_DONE=0
NALSSAM_REPOS="chrisryugj/kordoc revfactory/harness nextlevelbuilder/ui-ux-pro-max-skill Leonxlnx/taste-skill pbakaus/impeccable bradautomates/claude-video aldegad/sprite-gen obra/superpowers obra/superpowers-marketplace multica-ai/andrej-karpathy-skills JuliusBrussee/caveman openai/codex-plugin-cc Panniantong/Agent-Reach affaan-m/ECC wshobson/agents google/skills thedotmack/claude-mem"
in_nalssam() { [ "$NALSSAM_DONE" = 1 ] || return 1; case " $NALSSAM_REPOS " in *" $1 "*) return 0 ;; esac; return 1; }
NALSSAM_SKIP="날쌤팩에 들어 있어 건너뜀"

HWPXNEW_DONE=0
hwpx_new() {   # 한 번만 설치하고 Claude Code·Codex에 MCP 연결
  [ "$HWPXNEW_DONE" = 1 ] && return; HWPXNEW_DONE=1
  if [ "$NALSSAM_DONE" = 1 ]; then skip "한글 양식 보고서(hwpx_new) — $NALSSAM_SKIP"; return; fi
  only=""; [ "$HAS_CLAUDE" = 1 ] && only="claude-code"; [ "$HAS_CODEX" = 1 ] && only="${only:+$only,}codex"
  zsrc="https://github.com/ZZombie04/hwpx_new/archive/refs/heads/main.zip"
  gsrc="git+https://github.com/ZZombie04/hwpx_new.git"
  if has uv; then
    { git_ok && uv tool install --force "hwpx-new @ $gsrc" >/dev/null 2>&1; } || uv tool install --force "hwpx-new @ $zsrc" >/dev/null 2>&1
  elif has pipx; then
    { git_ok && pipx install --force "$gsrc" >/dev/null 2>&1; } || pipx install --force "$zsrc" >/dev/null 2>&1
  else skip "한글 양식 보고서(hwpx_new) — uv가 없어 건너뜀"; return; fi
  PATH="$HOME/.local/bin:$PATH"; export PATH
  if has hwpx-new && hwpx-new setup -y --only "$only" >/dev/null 2>&1; then ok "한글 양식 보고서(hwpx_new) — 설치·MCP 연결"; persist_path "$HOME/.local/bin"
  else fail "한글 양식 보고서(hwpx_new) — 설치 실패 (pip install $zsrc)"; fi
}

PPTX_DONE=0
pptx_maker() { # 한국어 발표 자료 엔진: 고정 커밋으로 설치하고 Claude Code·Codex에 MCP·스킬 연결
  [ "$PPTX_DONE" = 1 ] && return; PPTX_DONE=1
  label="발표 자료(PPTX) 엔진 · ZZombie04/pptx_maker"
  if [ "$NALSSAM_DONE" = 1 ]; then skip "$label — $NALSSAM_SKIP"; return; fi
  targets=""; [ "$HAS_CLAUDE" = 1 ] && targets="claude-code"
  [ "$HAS_CODEX" = 1 ] && targets="${targets:+$targets,}codex,skill"
  if ! has uv; then skip "$label — uv가 없어 건너뜀"; return; fi
  psrc_git="git+https://github.com/ZZombie04/pptx_maker@$PPTX_COMMIT"
  psrc_zip="https://github.com/ZZombie04/pptx_maker/archive/$PPTX_COMMIT.zip"
  { git_ok && uv tool install --force "pptx-maker[images] @ $psrc_git" >/dev/null 2>&1; } \
    || uv tool install --force "pptx-maker[images] @ $psrc_zip" >/dev/null 2>&1
  PATH="$HOME/.local/bin:$PATH"; export PATH
  if has pptx-maker && pptx-maker setup --yes --only "$targets" >/dev/null 2>&1; then ok "$label — 설치·MCP·스킬 연결"; persist_path "$HOME/.local/bin"
  else fail "$label — 설치 실패 (uv tool install \"pptx-maker @ $psrc_zip\")"; fi
}

nalssam_pack() { # 날쌤팩: 고정 버전 설치기를 그대로 부른다(Claude Code가 있으면 --claude)
  say "${B}[날쌤팩 $NALSSAM_VERSION]${N} 영상·모션·발표·분석 도구 — 수 GB를 내려받아 10분 이상 걸릴 수 있습니다"
  case "$(uname -s)" in Darwin|Linux) ;; *) skip "날쌤팩 — macOS·Linux·WSL2에서만 설치됩니다"; return 0 ;; esac
  if ! has bash; then skip "날쌤팩 — bash가 없어 건너뜀"; return 0; fi
  if [ "$HAS_GIT" = 0 ]; then skip "날쌤팩 — $GIT_SKIP"; return 0; fi
  n_args=""; [ "$HAS_CLAUDE" = 1 ] && n_args="--claude"
  n_script="${BUNPIL_NALSSAM_INSTALLER:-}"
  if [ -z "$n_script" ]; then
    n_script="$BUNPIL_HOME/.nalssam-install.$$.sh"
    if ! download "https://raw.githubusercontent.com/nalssam/nalssam-pack/$NALSSAM_VERSION/install.sh" "$n_script"; then
      rm -f "$n_script"; fail "날쌤팩 설치 파일을 받지 못했습니다 — 인터넷 연결을 확인하세요"; return 0
    fi
  fi
  NALSSAM_PACK_ROOT="$NALSSAM_ROOT" bash "$n_script" $n_args 2>&1 | sed 's/^/    /'
  n_rc=0; [ -f "$NALSSAM_ROOT/report.json" ] && grep -q '"status": "failed"' "$NALSSAM_ROOT/report.json" && n_rc=1
  [ -z "${BUNPIL_NALSSAM_INSTALLER:-}" ] && rm -f "$n_script"
  if [ ! -f "$NALSSAM_ROOT/state.json" ]; then fail "날쌤팩 설치가 끝나지 않았습니다 — 위 메시지를 확인하세요"; return 0; fi
  if [ "$n_rc" = 0 ]; then NALSSAM_DONE=1; ok "날쌤팩 설치 — 겹치는 추천 도구는 날쌤팩 것을 씁니다"
  else warn "날쌤팩 일부 단계가 실패했습니다 — $NALSSAM_ROOT/report.json 확인 후 'nalssam-pack install'로 다시 시도하세요. 겹치는 추천 도구는 분필팩이 따로 설치합니다"; fi
}

nalssam_claude_mcp() { # 날쌤팩 공통 MCP 중 분필팩에 없는 것을 Claude Code에 연결(겹치는 이름은 건너뜀)
  [ -d "$NALSSAM_ROOT/bin" ] || return 0
  for spec in "rea|nalssam-rea|-|rea mcp|앱·바이너리 분석 REA" "motion-mcp|nalssam-motion|-|motion-mcp|모션그래픽 Motion Director" \
              "pptx-maker-mcp|nalssam-pptx|pptx_maker|pptx-maker-mcp|발표 자료 엔진" "hwpx-new-mcp|nalssam-hwpx|hwpx_new|hwpx-new-mcp|한글 양식 보고서" \
              "markitdown-mcp|nalssam-markitdown|markitdown|markitdown-mcp|파일 → 텍스트 변환" "kordoc-mcp|nalssam-kordoc|kordoc|kordoc-mcp|한글·PDF 문서 도구"; do
    n_bin=${spec%%|*}; rest=${spec#*|}; n_name=${rest%%|*}; rest=${rest#*|}; n_have=${rest%%|*}; rest=${rest#*|}; n_cmd=${rest%%|*}; n_label=${rest#*|}
    [ -x "$NALSSAM_ROOT/bin/$n_bin" ] || continue
    if [ "$n_have" != "-" ] && claude mcp get "$n_have" >/dev/null 2>&1; then continue; fi
    set -- $n_cmd; n_first="$NALSSAM_ROOT/bin/$1"; shift
    mcp_add claude "$n_name" "$n_label(MCP, 날쌤팩)" "$n_first" "$@"
  done
}

# ── 분필팩 설치 ──────────────────────────────────────────────
bunpil_claude() {
  if c_has_market "$MARKET"; then
    src_line=$(c_market_src "$MARKET")
    case "$src_line" in
      *"$SOURCE"*)
        if claude plugin marketplace update "$MARKET" >/dev/null 2>&1; then ok "분필팩 목록 최신으로 갱신"; else warn "분필팩 목록 갱신 실패(지금 버전 유지)"; fi ;;
      *) if [ "$SOURCE_FALLBACK" = 1 ]; then
           # 내려받기에 실패해 저장소를 쓰는 경우: 이미 설치된 분필팩을 지우지 않는다
           claude plugin marketplace update "$MARKET" >/dev/null 2>&1; warn "분필팩 목록은 그대로 두었습니다(내려받기 실패)"
         else
           claude plugin marketplace remove "$MARKET" >/dev/null 2>&1
           claude plugin marketplace add "$SOURCE" >/dev/null 2>&1 && ok "분필팩 목록 위치 변경" || { fail "분필팩 목록 등록 실패"; return 1; }
         fi ;;
    esac
  elif claude plugin marketplace add "$SOURCE" >/dev/null 2>&1; then ok "분필팩 목록 등록"
  else fail "분필팩 목록 등록 실패"; return 1; fi
  for p in $PLUGINS; do
    if c_has_plugin "$p@$MARKET"; then
      if claude plugin update "$p@$MARKET" >/dev/null 2>&1; then ok "$p — 최신 확인"; else warn "$p — 업데이트 확인 실패(지금 버전 유지)"; fi
    elif claude plugin install "$p@$MARKET" -y >/dev/null 2>&1; then ok "$p"
    else fail "$p — 설치 실패"; fi
  done
}
bunpil_codex() {
  if x_has_market "$MARKET"; then
    case "$(x_market_line "$MARKET")" in
      *"$SOURCE"*)
        if [ "$SOURCE_IS_REPO" = 1 ]; then
          if codex plugin marketplace upgrade "$MARKET" >/dev/null 2>&1; then ok "분필팩 목록 최신으로 갱신"; else warn "분필팩 목록 갱신 실패(지금 버전 유지)"; fi
        else ok "분필팩 목록 확인"; fi ;;   # 폴더 목록은 plugin add 가 새 내용을 읽는다(upgrade는 Git 목록 전용)
      *) if [ "$SOURCE_FALLBACK" = 1 ]; then warn "분필팩 목록은 그대로 두었습니다(내려받기 실패)"
         else codex plugin marketplace remove "$MARKET" >/dev/null 2>&1
           codex plugin marketplace add "$SOURCE" >/dev/null 2>&1 && ok "분필팩 목록 위치 변경" || { fail "분필팩 목록 등록 실패"; return 1; }; fi ;;
    esac
  elif codex plugin marketplace add "$SOURCE" >/dev/null 2>&1; then ok "분필팩 목록 등록"
  else fail "분필팩 목록 등록 실패"; return 1; fi
  for p in $PLUGINS; do
    if codex plugin add "$p@$MARKET" >/dev/null 2>&1; then ok "$p"; else fail "$p — 설치 실패"; fi
  done
}

# ── 추천 묶음 (catalog/recommended.json과 같게 유지) ─────────
recs_claude() {
  if in_profile teacher; then
    say "  ${D}[teacher] 한글·문서·자동화·하네스${N}"
    [ "$skip_hwpx" = 1 ] || c_plugin airmang/hwpx-plugins hwpx-plugin@hwpx "한글(HWPX) 편집 엔진 · airmang/hwpx-plugins"
    c_plugin chrisryugj/kordoc kordoc@kordoc "한글·PDF 읽기·공문 프리셋 · chrisryugj/kordoc"
    if [ "$HAS_NPX" = 1 ]; then
      mcp_add claude kordoc "kordoc 문서 도구 17종(MCP)" npx -y kordoc mcp
      mcp_add claude playwright "브라우저 자동화 RPA(MCP) · microsoft/playwright" npx -y "$PLAYWRIGHT_MCP"
    else skip "kordoc MCP·브라우저 자동화 — Node.js가 없어 건너뜀"; fi
    if [ "$HAS_UVX" = 1 ]; then mcp_add claude markitdown "파일 → 텍스트 변환(MCP) · microsoft/markitdown" uvx markitdown-mcp; warm_markitdown
    else skip "파일 → 텍스트 변환(markitdown) — uv가 없어 건너뜀"; fi
    c_plugin revfactory/harness harness@harness-marketplace "하네스 팩토리 · revfactory/harness"
  fi
  if in_profile creator; then
    say "  ${D}[creator] 웹·디자인·영상${N}"
    c_plugin nextlevelbuilder/ui-ux-pro-max-skill ui-ux-pro-max@ui-ux-pro-max-skill "UI·UX 디자인 · ui-ux-pro-max"
    c_plugin Leonxlnx/taste-skill taste-skill@taste-skill "디자인 감각 · taste-skill"
    c_plugin pbakaus/impeccable impeccable@impeccable "디자인 다듬기 · impeccable"
    c_plugin bradautomates/claude-video watch@claude-video "영상 보고 요약 · claude-video(watch)"
    skills_add aldegad/sprite-gen claude-code "스프라이트 이미지 · sprite-gen"
  fi
  if in_profile dev; then
    say "  ${D}[dev] 개발자용${N}"
    c_plugin obra/superpowers-marketplace superpowers@superpowers-marketplace "개발 습관 스킬 · superpowers"
    c_plugin multica-ai/andrej-karpathy-skills andrej-karpathy-skills@karpathy-skills "카파시식 코딩 지침"
    c_plugin JuliusBrussee/caveman caveman@caveman "토큰 절약 · caveman"
    if has codex; then c_plugin openai/codex-plugin-cc codex@openai-codex "Claude에서 Codex에게 맡기기 · codex-plugin-cc"
    else skip "codex-plugin-cc — Codex가 없어 건너뜀"; fi
    skills_add Panniantong/Agent-Reach claude-code "웹·SNS 읽기 · Agent-Reach (도구 설치는 에이전트가 안내)"
    c_market affaan-m/ECC ecc "Everything Claude Code(ECC)"
    c_market wshobson/agents claude-code-workflows "개발 워크플로 모음 · wshobson/agents"
    c_market google/skills google-plugins "Google Cloud 스킬 · google/skills"
    c_market thedotmack/claude-mem thedotmack "세션 기억 · claude-mem"
  fi
}
recs_codex() {
  if in_profile teacher; then
    say "  ${D}[teacher] 한글·문서·자동화·하네스${N}"
    [ "$skip_hwpx" = 1 ] || x_plugin airmang/hwpx-plugins hwpx-plugin@hwpx "한글(HWPX) 편집 엔진 · airmang/hwpx-plugins"
    if [ "$HAS_NPX" = 1 ]; then
      mcp_add codex kordoc "kordoc 문서 도구 17종(MCP) · chrisryugj/kordoc" npx -y kordoc mcp
      mcp_add codex playwright "브라우저 자동화 RPA(MCP) · microsoft/playwright" npx -y "$PLAYWRIGHT_MCP"
    else skip "kordoc·브라우저 자동화 — Node.js가 없어 건너뜀"; fi
    if [ "$HAS_UVX" = 1 ]; then mcp_add codex markitdown "파일 → 텍스트 변환(MCP) · microsoft/markitdown" uvx markitdown-mcp; warm_markitdown
    else skip "파일 → 텍스트 변환(markitdown) — uv가 없어 건너뜀"; fi
    skills_add revfactory/harness codex "하네스 팩토리 · revfactory/harness"
  fi
  if in_profile creator; then
    say "  ${D}[creator] 웹·디자인·영상${N}"
    skills_add nextlevelbuilder/ui-ux-pro-max-skill codex "UI·UX 디자인 · ui-ux-pro-max"
    skills_add Leonxlnx/taste-skill codex "디자인 감각 · taste-skill"
    skills_add pbakaus/impeccable codex "디자인 다듬기 · impeccable"
    x_plugin bradautomates/claude-video watch@claude-video "영상 보고 요약 · claude-video(watch)"
    skills_add aldegad/sprite-gen codex "스프라이트 이미지 · sprite-gen"
  fi
  if in_profile dev; then
    say "  ${D}[dev] 개발자용${N}"
    skills_add obra/superpowers codex "개발 습관 스킬 · superpowers"
    skills_add multica-ai/andrej-karpathy-skills codex "카파시식 코딩 지침"
    skills_add JuliusBrussee/caveman codex "토큰 절약 · caveman"
    skills_add Panniantong/Agent-Reach codex "웹·SNS 읽기 · Agent-Reach (도구 설치는 에이전트가 안내)"
    x_market affaan-m/ECC ecc "Everything Claude Code(ECC)"
    x_market wshobson/agents claude-code-workflows "개발 워크플로 모음 · wshobson/agents"
    x_market google/skills google-plugins "Google Cloud 스킬 · google/skills"
    x_market thedotmack/claude-mem claude-mem-local "세션 기억 · claude-mem"
  fi
}

# ── 실행 ─────────────────────────────────────────────────────
[ "$recs" = 1 ] && say "추천 묶음: $profiles" || say "추천 묶음: 설치 안 함"
say ""
say "${B}[분필팩 준비]${N}"
if ! prepare_pack; then say ""; warn "분필팩을 준비하지 못해 멈춥니다."; exit 1; fi
say ""
if [ "$nalssam" = 1 ]; then nalssam_pack; say ""; fi
if [ "$HAS_CLAUDE" = 1 ]; then
  say "${B}[Claude Code]${N} $(claude --version 2>/dev/null | head -1)"
  if bunpil_claude && [ "$recs" = 1 ]; then recs_claude; fi
  say ""
fi
if [ "$HAS_CODEX" = 1 ]; then
  say "${B}[Codex]${N} $(codex --version 2>/dev/null | head -1)"
  if bunpil_codex && [ "$recs" = 1 ]; then recs_codex; fi
  say ""
fi
if [ "$recs" = 1 ] && in_profile teacher; then
  say "${B}[공통]${N}"
  hwpx_new
  pptx_maker
  say ""
fi
if [ "$nalssam" = 1 ] && [ "$HAS_CLAUDE" = 1 ] && [ -f "$NALSSAM_ROOT/state.json" ]; then
  say "${B}[날쌤팩 → Claude Code MCP]${N}"
  nalssam_claude_mcp
  say ""
fi

say "${B}다음 단계${N}"
if [ "$PATH_CHANGED" = 1 ]; then
  say "  ※ 새로 설치한 명령이 잡히도록 ${B}지금 터미널 창을 닫고 새 창을 여세요${N}."
fi
if [ "$HAS_CLAUDE" = 1 ]; then
  say "  Claude Code"
  say "   1. 작업 폴더를 만들고 실행:  mkdir -p ~/분필작업 && cd ~/분필작업 && claude"
  say "   2. 처음이면 브라우저에서 로그인 → 대화창에 \"설정 시작해줘\""
  say "   3. 노션·패들렛·캔바 연결: 대화창에서  /mcp  → 서비스 선택 → 로그인"
fi
if [ "$HAS_CODEX" = 1 ]; then
  say "  Codex"
  say "   1. 작업 폴더를 만들고 실행:  mkdir -p ~/분필작업 && cd ~/분필작업 && codex"
  say "   2. 처음이면 'Sign in with ChatGPT'로 로그인 → /hooks 에서 분필 가드 신뢰(trust)"
  say "   3. 대화창에 \"설정 시작해줘\"  ·  노션 연결:  codex mcp login notion"
fi
if [ "$recs" = 1 ] && { [ "$HAS_NPX" = 0 ] || [ "$HAS_UVX" = 0 ]; }; then
  if [ "$with_tools" = 1 ]; then say "  Node.js·uv를 준비하지 못해 일부 도구를 건너뛰었습니다. 인터넷 연결을 확인하고 같은 명령을 다시 실행하세요."
  else say "  건너뛴 도구를 채우려면 --with-tools 를 붙여 다시 실행하세요."; fi
fi
if [ "$recs" = 1 ] && [ "$HAS_GIT" = 0 ]; then
  case "$(uname -s)" in
    Darwin) say "  Git(개발자 도구)을 설치하면 건너뛴 추천 도구도 설치됩니다:  xcode-select --install   (끝나면 같은 명령 다시 실행)" ;;
    *) say "  Git을 설치하면 건너뛴 추천 도구도 설치됩니다. 설치 후 같은 명령을 다시 실행하세요." ;;
  esac
fi
if [ "$nalssam" = 1 ] && [ -f "$NALSSAM_ROOT/state.json" ]; then
  say "  날쌤팩: 설치 기록 $NALSSAM_ROOT/report.json · 연결 점검  nalssam-pack doctor --verify-mcp"
  say "         계정이 필요한 것(ElevenLabs·Gemini·Google Cloud·After Effects 등)은 각자 연결해야 합니다."
fi
say "  업데이트는 같은 명령을 다시 실행하면 됩니다. 자세한 안내: $SITE"
say ""
if [ "$errors" -gt 0 ]; then
  warn "일부 항목($errors건)이 실패했습니다. 위 메시지를 확인하고 다시 실행해 보세요."
  exit 1
fi
ok "분필팩 설치 완료. 학생 이름은 '학생A'처럼 바꿔 쓰세요. 결과물은 모두 초안입니다."
}
