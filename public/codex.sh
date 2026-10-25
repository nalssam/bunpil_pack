#!/bin/sh
# ─────────────────────────────────────────────────────────────
#  nalssam's 분필팩 — 한 줄 설치 (macOS · Linux)
#
#  가장 쉬운 길: Claude 앱(Code 탭)·ChatGPT 앱(Codex)의 채팅창에 사이트의 '설치 문장'을 붙여넣는다.
#  그 문장이 아래 명령을 대신 실행한다. 터미널·명령 프롬프트·VS Code 터미널에서 직접 실행해도 같다.
#
#    Claude 쓰는 선생님   curl -fsSL https://nalssam-bunpil.vercel.app/claude.sh | sh
#    Codex 쓰는 선생님    curl -fsSL https://nalssam-bunpil.vercel.app/codex.sh | sh
#    직접 고르기          curl -fsSL https://nalssam-bunpil.vercel.app/install.sh | sh -s -- [옵션]
#    지우기               curl -fsSL https://nalssam-bunpil.vercel.app/uninstall.sh | sh
#
#  하는 일
#   1) 컴퓨터에 있는 Claude Code, Codex(ChatGPT)를 찾는다 (옵션을 주면 없을 때 설치한다)
#   2) 분필팩(플러그인 5종)을 내려받아 ~/.bunpil 에 두고 설치한다 (Git 없어도 됨)
#   3) 추천 스킬·MCP·플러그인 묶음을 함께 설치한다 (catalog/recommended.json)
#        teacher(기본) 한글·발표 자료·문서 변환·브라우저 자동화(RPA)·웹 수집·하네스 / creator 웹·디자인·영상·인스타 / dev 개발자용
#        studio 영상·모션그래픽·발표·분석 도구를 고정 버전으로 한꺼번에 (수 GB·10~30분, macOS·Linux·WSL2) — studio/ 폴더의 설치 엔진을 쓴다
#   4) 이미 설치되어 있으면 최신으로 바꾼다 (다시 실행 = 업데이트)
#  관리자 권한(sudo)이 필요 없다.
#
#  옵션
#   --profile teacher|creator|dev|studio|full|all   추천 묶음(쉼표로 여러 개, 기본 teacher). all = 다섯 다
#   --claude | --codex                  한쪽에만 설치
#   --install-claude | --install-codex  없으면 Claude Code / Codex CLI까지 설치
#   --with-tools                        Node.js·uv가 없으면 함께 설치 (brew 또는 공식 배포본)
#   --bunpil-only  분필팩 5종만   --no-hwpx  한글 플러그인 빼기
#   --ask          Claude Code·Codex가 모두 없으면 무엇을 설치할지 물어보기
#   --uninstall    분필팩 지우기
#   (예전 이름 --nalssam · --profile nalssam · BUNPIL_NALSSAM=1 은 studio 묶음으로 받아들인다)
#  환경변수
#   BUNPIL_SITE  내려받을 주소(기본 https://nalssam-bunpil.vercel.app)
#   BUNPIL_REPO  GitHub 저장소(owner/repo)를 마켓플레이스로 직접 쓸 때
#   BUNPIL_HOME  분필팩을 둘 폴더(기본 ~/.bunpil)
#   BUNPIL_PROFILE · BUNPIL_ONLY(claude|codex) · BUNPIL_INSTALL_CLAUDE · BUNPIL_INSTALL_CODEX
#   BUNPIL_WITH_TOOLS · BUNPIL_ASK · BUNPIL_RECS(0=분필팩만) · BUNPIL_HWPX(0=빼기) · BUNPIL_UNINSTALL  (값 1 = 켜기)
#   BUNPIL_STUDIO_DIR  studio 설치 엔진 폴더(기본 ~/.bunpil/bunpil-pack/studio) · NALSSAM_PACK_ROOT  스튜디오 설치 기록 폴더(기본 ~/.local/share/nalssam-pack)
#   PERPLEXITY_API_KEY  있으면 최신 검색 Perplexity(MCP)도 연결 (유료 키, Claude Code·Codex 설정에 저장됨)
# ─────────────────────────────────────────────────────────────
set -u
# 미리 정한 값 — Codex용: Codex CLI가 없으면 설치하고 Node.js·uv도 준비한다 (환경변수로 바꿀 수 있다)
: "${BUNPIL_ONLY:=codex}"; : "${BUNPIL_INSTALL_CODEX:=1}"; : "${BUNPIL_WITH_TOOLS:=1}"

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
PERPLEXITY_MCP="@perplexity-ai/mcp-server"
FIRECRAWL_URL="https://mcp.firecrawl.dev/v2/mcp"      # 키 없이 쓰는 무료 구간(수집·검색·읽기 3종)
GLIF_URL="https://glif.app/api/mcp"
# full 묶음: 날쌤 Claude 앱(claude.ai)에 켜 둔 플러그인을 공개 마켓플레이스에서 그대로 설치한다
KWP_REPO="anthropics/knowledge-work-plugins"; KWP_MARKET="knowledge-work-plugins"
FULL_WORK="productivity enterprise-search cowork-plugin-management sales finance data legal marketing customer-support product-management bio-research engineering human-resources design operations small-business brand-voice pdf-viewer"
FULL_PARTNER="canva figma adobe-for-creativity miro zoom-plugin learn-with-coursera airtable monday-com zapier desktop-commander exa brightdata-plugin searchfit-seo postiz product-tracking-skills base44 datadog datarobot-agent-skills unity noibu grasp bigdata-com daloopa lseg sp-global carta-crm carta-investors claude-for-financial-advisors"
FULL_X_SKIP="product-tracking-skills sp-global"   # Codex가 이름 불일치(plugin.json과 마켓 이름이 다름)로 거부해 Codex에서만 건너뜀
# full 묶음: 플러그인에 들어 있지 않은 claude.ai 커넥터(원격 MCP). 한 줄에 이름|표시이름|주소
FULL_MCPS="vercel|웹 배포·관리 · Vercel|https://mcp.vercel.com
supabase|데이터베이스 · Supabase|https://mcp.supabase.com/mcp
cloudflare|Cloudflare 개발 플랫폼|https://mcp.cloudflare.com/mcp
higgsfield|이미지·영상 AI · Higgsfield|https://mcp.higgsfield.ai/mcp
hyperframes|HTML 모션그래픽·애니메이션 슬라이드 · HyperFrames(HeyGen)|https://mcp.heygen.com/mcp/hyperframes/
elevenlabs|음성·나레이션 AI · ElevenLabs|https://api.elevenlabs.io/v1/mcp
artlist|음악·효과음·영상 AI · artlist|https://mcp.artlist.io/mcp
playmcp|카카오 PlayMCP|https://playmcp.kakao.com/mcp
windsor-ai|광고·SNS 성과 데이터 · Windsor.ai|https://mcp.windsor.ai/
threejs-viewer|3D 장면 보기(데모) · Three.js|https://example-server.modelcontextprotocol.io/threejs/mcp"
NODE_DIST="${BUNPIL_NODE_DIST:-https://nodejs.org/dist/latest-v24.x}"
PPTX_COMMIT="ae3d919005100472805bf39ddab234bd1cf72577"   # ZZombie04/pptx_maker (스튜디오 엔진과 같은 커밋)
STUDIO_ROOT="${NALSSAM_PACK_ROOT:-$HOME/.local/share/nalssam-pack}"   # 스튜디오 설치 기록 폴더. 예전 날쌤팩과 같은 자리라 이미 설치한 분의 환경이 이어진다
BUNPIL_HOME="${BUNPIL_HOME:-$HOME/.bunpil}"
PACK_DIR="$BUNPIL_HOME/bunpil-pack"
ENV_FILE="$BUNPIL_HOME/env"
ORIG_PATH="$PATH"

want_claude=1; want_codex=1; install_claude=0; install_codex=0; with_tools=0; ask=0
profiles="${BUNPIL_PROFILE:-teacher}"; recs=1; skip_hwpx=0; uninstall=0; legacy_studio=0
case "${BUNPIL_ONLY:-}" in claude) want_codex=0 ;; codex) want_claude=0 ;; esac
[ "${BUNPIL_INSTALL_CLAUDE:-0}" = 1 ] && install_claude=1
[ "${BUNPIL_INSTALL_CODEX:-0}" = 1 ] && install_codex=1
[ "${BUNPIL_WITH_TOOLS:-0}" = 1 ] && with_tools=1
[ "${BUNPIL_ASK:-0}" = 1 ] && ask=1
[ "${BUNPIL_RECS:-1}" = 0 ] && recs=0
[ "${BUNPIL_HWPX:-1}" = 0 ] && skip_hwpx=1
[ "${BUNPIL_UNINSTALL:-0}" = 1 ] && uninstall=1
[ "${BUNPIL_NALSSAM:-0}" = 1 ] && legacy_studio=1   # 예전 이름(날쌤팩) 호환

usage() {
  cat <<'EOF'
분필팩 설치 옵션
  --profile teacher|creator|dev|studio|full|all   추천 묶음(기본 teacher, 쉼표로 여러 개)
  --claude | --codex                  한쪽에만 설치
  --install-claude | --install-codex  Claude Code / Codex CLI까지 설치
  --with-tools                        Node.js·uv도 설치
  --bunpil-only  --no-hwpx  --ask  --uninstall
묶음: teacher 한글·문서·자동화 / creator 웹·디자인·영상 / dev 개발자용 / studio 영상·모션·분석 도구(수 GB, 10~30분)
      full 날쌤 Claude 앱의 플러그인·커넥터 전부(업무·디자인·금융·개발 등 50여 종, 계정이 필요한 것 포함)
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
    --nalssam) legacy_studio=1 ;;
    --profile) shift; profiles="${1:-teacher}" ;;
    --profile=*) profiles="${1#--profile=}" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "알 수 없는 옵션: $1 (무시합니다)" ;;
  esac
  [ $# -gt 0 ] && shift
done
# 예전 이름(날쌤팩) 호환: --nalssam · BUNPIL_NALSSAM=1 · --profile nalssam 은 모두 studio 묶음을 고른 것으로 본다
profiles=$(printf '%s' "$profiles" | tr -d ' \t' | tr 'A-Z' 'a-z')   # 공백·대소문자 차이는 무시
[ "$legacy_studio" = 1 ] && profiles="$profiles,studio"
case ",$profiles," in *,nalssam,*) profiles="$profiles,teacher,studio" ;; esac   # 예전 nalssam = 분필팩 기본(teacher) + 날쌤팩
case ",$profiles," in *,all,*) profiles="teacher,creator,dev,studio,full" ;; esac
bad_profiles=""; good_profiles=""
set -f
for t in $(printf '%s' "$profiles" | tr ',' ' '); do
  case "$t" in
    teacher|creator|dev|studio|full) case ",$good_profiles," in *",$t,"*) ;; *) good_profiles="${good_profiles:+$good_profiles,}$t" ;; esac ;;
    nalssam|all) ;;
    *) bad_profiles="$bad_profiles $t" ;;
  esac
done
set +f
profiles="$good_profiles"
[ -n "$profiles" ] || profiles="teacher"
in_profile() { case ",$profiles," in *",$1,"*) return 0 ;; esac; return 1; }
studio=0; in_profile studio && studio=1   # --bunpil-only 와 함께여도 studio 를 직접 골랐다면 설치한다

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
[ -n "$bad_profiles" ] && warn "알 수 없는 묶음 이름은 건너뜁니다:$bad_profiles  (teacher · creator · dev · studio · all 중에서 고르세요)"

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
  if [ "$want_claude" = 1 ] && has claude; then   # 스튜디오 공통 MCP로 분필팩이 연결해 둔 nalssam-* 항목(스튜디오를 지우면 연결할 곳이 없어진다)
    for n in nalssam-rea nalssam-motion nalssam-pptx nalssam-hwpx nalssam-markitdown nalssam-kordoc; do
      if claude mcp get "$n" >/dev/null 2>&1; then claude mcp remove -s user "$n" >/dev/null 2>&1 && ok "Claude Code: $n 연결 해제"; fi
    done
  fi
  case "$PACK_DIR" in */bunpil-pack) if [ -d "$PACK_DIR" ]; then rm -rf "$PACK_DIR" && ok "내려받은 분필팩 폴더 삭제 ($PACK_DIR)"; fi ;; esac
  say ""
  say "그대로 둔 것 (다른 곳에서도 쓰는 도구라서):"
  say "  • 추천 묶음(한글 도구·MCP 등)  Claude Code: claude plugin uninstall <이름>@<마켓> · claude mcp remove <이름>"
  say "                                 Codex: codex plugin remove <이름>@<마켓> · codex mcp remove <이름>"
  [ -d "$BUNPIL_HOME/node" ] && say "  • 분필팩이 설치한 Node.js($BUNPIL_HOME/node)"
  [ -f "$ENV_FILE" ] && say "  • PATH 설정($ENV_FILE)과 셸 설정 파일(~/.zshrc 등)의 'bunpil-path' 줄 — 지우면 Node.js 등을 찾지 못할 수 있습니다"
  [ -f "$STUDIO_ROOT/state.json" ] && say "  • 스튜디오 묶음 — 따로 지우려면  nalssam-pack uninstall  (스튜디오가 만든 연결만 해제, 새 터미널에서)"
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
  say "  • Claude 쓰는 선생님:  curl -fsSL $SITE/claude.sh | sh   (Claude 앱 Code 탭 채팅창에 이 줄을 붙여넣어도 됩니다)"
  say "  • Codex 쓰는 선생님:   curl -fsSL $SITE/codex.sh | sh    (ChatGPT 앱 Codex 채팅창에 붙여넣어도 됩니다)"
  say "  • 명령 없이 Claude 앱 메뉴로만: $SITE 의 'Claude 앱 메뉴' 안내를 따르세요"
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
    for x in .claude-plugin .agents plugins catalog studio VERSION install.sh install.ps1 README.md LICENSE NOTICE; do
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
  if in_studio "$1"; then skip "$3 — $STUDIO_SKIP"; return; fi
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
  if in_studio "$1"; then skip "$3 — $STUDIO_SKIP"; return; fi
  if [ "$HAS_GIT" = 0 ]; then skip "$3 — $GIT_SKIP"; return; fi
  if c_has_market "$2"; then
    if claude plugin marketplace update "$2" >/dev/null 2>&1; then ok "$3 — 목록 갱신"; else warn "$3 — 목록 갱신 실패(지금 목록 유지)"; fi
  elif claude plugin marketplace add "$1" >/dev/null 2>&1; then ok "$3 — 목록 등록(/plugin에서 골라 설치)"
  else fail "$3 — 목록 등록 실패"; fi
}
x_plugin() {   # x_plugin <저장소> <플러그인@마켓> <표시이름>
  if in_studio "$1"; then skip "$3 — $STUDIO_SKIP"; return; fi
  if [ "$HAS_GIT" = 0 ]; then skip "$3 — $GIT_SKIP"; return; fi
  m="${2#*@}"
  if x_has_market "$m"; then codex plugin marketplace upgrade "$m" >/dev/null 2>&1; else codex plugin marketplace add "$1" >/dev/null 2>&1; fi
  if codex plugin add "$2" >/dev/null 2>&1; then ok "$3"; else fail "$3 — 설치 실패 (codex plugin add $2)"; fi
}
x_market() {
  if in_studio "$1"; then skip "$3 — $STUDIO_SKIP"; return; fi
  if [ "$HAS_GIT" = 0 ]; then skip "$3 — $GIT_SKIP"; return; fi
  if x_has_market "$2"; then
    if codex plugin marketplace upgrade "$2" >/dev/null 2>&1; then ok "$3 — 목록 갱신"; else warn "$3 — 목록 갱신 실패(지금 목록 유지)"; fi
  elif codex plugin marketplace add "$1" >/dev/null 2>&1; then ok "$3 — 목록 등록(/plugins에서 골라 설치)"
  else fail "$3 — 목록 등록 실패"; fi
}
c_plugins() {  # c_plugins <저장소> <마켓> <제목> <플러그인 이름...> — 한 마켓에서 여러 개를 한 번에(목록은 한 번만 갱신)
  cp_repo="$1"; cp_m="$2"; cp_t="$3"; shift 3
  if [ "$HAS_GIT" = 0 ]; then skip "$cp_t — $GIT_SKIP"; return; fi
  if c_has_market "$cp_m"; then claude plugin marketplace update "$cp_m" >/dev/null 2>&1 || warn "$cp_t — 목록 갱신 실패(지금 목록 유지)"
  elif ! claude plugin marketplace add "$cp_repo" >/dev/null 2>&1; then fail "$cp_t — 목록 등록 실패 (claude plugin marketplace add $cp_repo)"; return; fi
  cp_list=$(claude plugin list 2>/dev/null)
  for cp_p in "$@"; do
    if printf '%s\n' "$cp_list" | grep -qE "^[[:space:]]*> $cp_p@$cp_m\$"; then
      if claude plugin update "$cp_p@$cp_m" >/dev/null 2>&1; then ok "$cp_t · $cp_p — 최신 확인"; else warn "$cp_t · $cp_p — 업데이트 확인 실패(지금 버전 유지)"; fi
    elif claude plugin install "$cp_p@$cp_m" -y >/dev/null 2>&1; then ok "$cp_t · $cp_p"
    else fail "$cp_t · $cp_p — 설치 실패 (claude plugin install $cp_p@$cp_m)"; fi
  done
}
x_plugins() {  # x_plugins <저장소> <마켓> <제목> <플러그인 이름...> — Codex용
  cp_repo="$1"; cp_m="$2"; cp_t="$3"; shift 3
  if [ "$HAS_GIT" = 0 ]; then skip "$cp_t — $GIT_SKIP"; return; fi
  if x_has_market "$cp_m"; then codex plugin marketplace upgrade "$cp_m" >/dev/null 2>&1 || warn "$cp_t — 목록 갱신 실패(지금 목록 유지)"
  elif ! codex plugin marketplace add "$cp_repo" >/dev/null 2>&1; then fail "$cp_t — 목록 등록 실패 (codex plugin marketplace add $cp_repo)"; return; fi
  for cp_p in "$@"; do
    case " $FULL_X_SKIP " in *" $cp_p "*) skip "$cp_t · $cp_p — Codex에서는 원 저장소의 이름 표기 문제로 설치되지 않아 건너뜀(Claude에는 설치)"; continue ;; esac
    if codex plugin add "$cp_p@$cp_m" >/dev/null 2>&1; then ok "$cp_t · $cp_p"; else fail "$cp_t · $cp_p — 설치 실패 (codex plugin add $cp_p@$cp_m)"; fi
  done
}
x_mcp_url() {  # x_mcp_url <이름> <표시이름> <주소> — Codex의 "codex mcp add --url"은 OAuth 서버면 그 자리에서 로그인 창을 띄우고 기다리므로, 설정 파일에 직접 적는다
  if codex mcp get "$1" >/dev/null 2>&1; then ok "$2 — 이미 연결됨"; return; fi
  xm_cfg="${CODEX_HOME:-$HOME/.codex}/config.toml"
  mkdir -p "$(dirname "$xm_cfg")" 2>/dev/null
  { [ -s "$xm_cfg" ] && [ -n "$(tail -c 1 "$xm_cfg")" ] && printf '\n'; printf '\n[mcp_servers.%s]\nurl = "%s"\n' "$1" "$3"; } >> "$xm_cfg" 2>/dev/null
  if codex mcp get "$1" >/dev/null 2>&1; then ok "$2"; else fail "$2 — MCP 등록 실패 ($xm_cfg 확인)"; fi
}
full_mcps() {  # full_mcps <claude|codex> — FULL_MCPS 목록을 원격 MCP로 등록(로그인은 처음 쓸 때)
  printf '%s\n' "$FULL_MCPS" > "$BUNPIL_HOME/.full-mcps.$$"
  while IFS='|' read -r fm_name fm_label fm_url; do
    [ -n "$fm_name" ] && [ -n "$fm_url" ] || continue
    if [ "$1" = codex ]; then x_mcp_url "$fm_name" "$fm_label(MCP)" "$fm_url"; else mcp_http "$1" "$fm_name" "$fm_label(MCP)" "$fm_url"; fi
  done < "$BUNPIL_HOME/.full-mcps.$$"
  rm -f "$BUNPIL_HOME/.full-mcps.$$"
}
skills_add() { # skills_add <저장소> <claude-code|codex> <표시이름>
  if in_studio "$1"; then skip "$3 — $STUDIO_SKIP"; return; fi
  if [ "$HAS_NPX" = 0 ]; then skip "$3 — Node.js가 없어 건너뜀"; return; fi
  if [ "$HAS_GIT" = 0 ]; then skip "$3 — $GIT_SKIP"; return; fi
  if DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 npx -y "$SKILLS_CLI" add "$1" -g -a "$2" -y --copy >/dev/null 2>&1; then ok "$3"
  else fail "$3 — 스킬 설치 실패 (npx $SKILLS_CLI add $1 -g -a $2)"; fi
}
mcp_add() {    # mcp_add <claude|codex> <이름> <표시이름> <명령...>
  host="$1"; name="$2"; label="$3"; shift 3
  if [ "$STUDIO_DONE" = 1 ]; then case "$name" in kordoc|markitdown) skip "$label — $STUDIO_SKIP"; return ;; esac; fi
  if [ "$host" = claude ]; then
    if claude mcp get "$name" >/dev/null 2>&1; then ok "$label — 이미 연결됨"; return; fi
    if claude mcp add -s user "$name" -- "$@" >/dev/null 2>&1; then ok "$label"; else fail "$label — MCP 등록 실패"; fi
  else
    if codex mcp get "$name" >/dev/null 2>&1; then ok "$label — 이미 연결됨"; return; fi
    if codex mcp add "$name" -- "$@" >/dev/null 2>&1; then ok "$label"; else fail "$label — MCP 등록 실패"; fi
  fi
}
mcp_http() {   # mcp_http <claude|codex> <이름> <표시이름> <주소>  — 원격(HTTP) MCP
  host="$1"; name="$2"; label="$3"; url="$4"
  if [ "$host" = claude ]; then
    if claude mcp get "$name" >/dev/null 2>&1; then ok "$label — 이미 연결됨"; return; fi
    if claude mcp add -s user --transport http "$name" "$url" >/dev/null 2>&1; then ok "$label"; else fail "$label — MCP 등록 실패"; fi
  else
    if codex mcp get "$name" >/dev/null 2>&1; then ok "$label — 이미 연결됨"; return; fi
    if codex mcp add "$name" --url "$url" >/dev/null 2>&1; then ok "$label"; else fail "$label — MCP 등록 실패"; fi
  fi
}
perplexity_mcp() {  # 유료 API 키가 있을 때만 연결한다
  label="최신 뉴스·문서 검색 · Perplexity(MCP)"
  if [ -z "${PERPLEXITY_API_KEY:-}" ]; then skip "$label — 유료 API 키가 있어야 해서 건너뜀 (아래 '다음 단계' 참고)"; PPLX_SKIPPED=1; return; fi
  if [ "$HAS_NPX" = 0 ]; then skip "$label — Node.js가 없어 건너뜀"; return; fi
  if [ "$1" = claude ]; then
    if claude mcp get perplexity >/dev/null 2>&1; then ok "$label — 이미 연결됨"; return; fi
    if claude mcp add -s user perplexity -e "PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY" -- npx -y "$PERPLEXITY_MCP" >/dev/null 2>&1; then ok "$label"; else fail "$label — MCP 등록 실패"; fi
  else
    if codex mcp get perplexity >/dev/null 2>&1; then ok "$label — 이미 연결됨"; return; fi
    if codex mcp add perplexity --env "PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY" -- npx -y "$PERPLEXITY_MCP" >/dev/null 2>&1; then ok "$label"; else fail "$label — MCP 등록 실패"; fi
  fi
}
PPLX_SKIPPED=0; GLIF_ON=0
MD_WARM=0
warm_markitdown() {  # 첫 실행 때 내려받는 시간(30초 안팎) 때문에 MCP 연결이 시간 초과되지 않도록 미리 받아 둔다
  [ "$MD_WARM" = 1 ] && return 0; MD_WARM=1
  [ "$HAS_UVX" = 1 ] && uvx markitdown-mcp --help >/dev/null 2>&1
  return 0
}
STUDIO_DONE=0
STUDIO_REPOS="Leonxlnx/cinetic chrisryugj/kordoc revfactory/harness nextlevelbuilder/ui-ux-pro-max-skill Leonxlnx/taste-skill pbakaus/impeccable bradautomates/claude-video aldegad/sprite-gen obra/superpowers obra/superpowers-marketplace multica-ai/andrej-karpathy-skills JuliusBrussee/caveman openai/codex-plugin-cc Panniantong/Agent-Reach affaan-m/ECC wshobson/agents google/skills thedotmack/claude-mem"
in_studio() { [ "$STUDIO_DONE" = 1 ] || return 1; case " $STUDIO_REPOS " in *" $1 "*) return 0 ;; esac; return 1; }
STUDIO_SKIP="스튜디오 묶음에 들어 있어 건너뜀"

HWPXNEW_DONE=0
hwpx_new() {   # 한 번만 설치하고 Claude Code·Codex에 MCP 연결
  [ "$HWPXNEW_DONE" = 1 ] && return; HWPXNEW_DONE=1
  if [ "$STUDIO_DONE" = 1 ]; then skip "한글 양식 보고서(hwpx_new) — $STUDIO_SKIP"; return; fi
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
  if [ "$STUDIO_DONE" = 1 ]; then skip "$label — $STUDIO_SKIP"; return; fi
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

studio_pack() { # 스튜디오 묶음: 분필팩 폴더 안의 studio/install.sh(고정 버전 설치 엔진)를 부른다(Claude Code가 있으면 --claude)
  say "${B}[스튜디오]${N} 영상·모션·발표·분석 도구 — 수 GB를 내려받아 10분 이상 걸릴 수 있습니다"
  case "$(uname -s)" in Darwin|Linux) ;; *) fail "스튜디오 — macOS·Linux·WSL2에서만 설치됩니다"; return 0 ;; esac
  if ! has bash; then fail "스튜디오 — bash가 없어 설치하지 못했습니다"; return 0; fi
  if [ "$HAS_GIT" = 0 ]; then fail "스튜디오 — Git이 없어 설치하지 못했습니다 (Git 설치 후 같은 명령을 다시 실행)"; return 0; fi
  s_dir="${BUNPIL_STUDIO_DIR:-}"; s_tmp=""
  if [ -z "$s_dir" ]; then
    if [ -f "$PACK_DIR/studio/pack.py" ]; then s_dir="$PACK_DIR/studio"
    elif [ -f "$SOURCE/studio/pack.py" ]; then s_dir="$SOURCE/studio"       # BUNPIL_REPO 에 폴더를 준 경우
    elif [ "$SOURCE_IS_REPO" = 1 ]; then                                    # 저장소로 받은 경우: studio 폴더만 얻으려고 얕게 복제
      s_tmp="$BUNPIL_HOME/.studio-src.$$"; rm -rf "$s_tmp"
      if git clone --depth 1 -q "https://github.com/$SOURCE.git" "$s_tmp" >/dev/null 2>&1 && [ -f "$s_tmp/studio/pack.py" ]; then s_dir="$s_tmp/studio"; fi
    fi
  fi
  if [ -z "$s_dir" ] || [ ! -f "$s_dir/install.sh" ] || [ ! -f "$s_dir/pack.py" ]; then
    [ -n "$s_tmp" ] && rm -rf "$s_tmp"
    fail "스튜디오 설치 파일(studio/)을 찾지 못했습니다 — 인터넷 연결을 확인하고 같은 명령을 다시 실행해 분필팩을 새로 받으세요"; return 0
  fi
  s_args=""; [ "$HAS_CLAUDE" = 1 ] && s_args="--claude"
  s_rcf="$BUNPIL_HOME/.studio-rc.$$"; rm -f "$s_rcf"
  # 엔진의 종료 코드를 파일에 남긴다(뒤의 파이프가 종료 코드를 가리므로). 출력은 한 줄씩 바로 들여써서 내보낸다
  # (sed 는 출력이 파이프로 이어지면 모아서 내보내, AI 채팅창에서는 진행 상황이 한참 뒤에야 보인다)
  { NALSSAM_PACK_ROOT="$STUDIO_ROOT" bash "$s_dir/install.sh" $s_args; echo $? > "$s_rcf"; } 2>&1 | while IFS= read -r s_line || [ -n "$s_line" ]; do printf '    %s\n' "$s_line"; done
  s_rc=1; [ -f "$s_rcf" ] && s_rc=$(cat "$s_rcf" 2>/dev/null); rm -f "$s_rcf"
  [ -n "$s_tmp" ] && rm -rf "$s_tmp"
  if [ ! -f "$STUDIO_ROOT/state.json" ]; then fail "스튜디오 설치가 끝나지 않았습니다 — 위 메시지를 확인하세요"; return 0; fi
  s_bad=0; [ -f "$STUDIO_ROOT/report.json" ] && grep -q '"status": "failed"' "$STUDIO_ROOT/report.json" && s_bad=1
  if [ "$s_rc" = 0 ] && [ "$s_bad" = 0 ]; then STUDIO_DONE=1; ok "스튜디오 설치 — 겹치는 추천 도구는 스튜디오 것(고정 버전)을 씁니다"
  else fail "스튜디오 일부 단계가 실패했습니다 — $STUDIO_ROOT/report.json 확인 후 'nalssam-pack install'로 다시 시도하세요. 겹치는 추천 도구는 분필팩이 따로 설치합니다"; fi
}

studio_claude_mcp() { # 스튜디오 공통 MCP 중 분필팩에 없는 것을 Claude Code에 연결(겹치는 이름은 건너뜀)
  [ -d "$STUDIO_ROOT/bin" ] || return 0
  for spec in "rea|nalssam-rea|-|rea mcp|앱·바이너리 분석 REA" "motion-mcp|nalssam-motion|-|motion-mcp|모션그래픽 Motion Director" \
              "pptx-maker-mcp|nalssam-pptx|pptx_maker|pptx-maker-mcp|발표 자료 엔진" "hwpx-new-mcp|nalssam-hwpx|hwpx_new|hwpx-new-mcp|한글 양식 보고서" \
              "markitdown-mcp|nalssam-markitdown|markitdown|markitdown-mcp|파일 → 텍스트 변환" "kordoc-mcp|nalssam-kordoc|kordoc|kordoc-mcp|한글·PDF 문서 도구"; do
    n_bin=${spec%%|*}; rest=${spec#*|}; n_name=${rest%%|*}; rest=${rest#*|}; n_have=${rest%%|*}; rest=${rest#*|}; n_cmd=${rest%%|*}; n_label=${rest#*|}
    [ -x "$STUDIO_ROOT/bin/$n_bin" ] || continue
    if [ "$n_have" != "-" ] && claude mcp get "$n_have" >/dev/null 2>&1; then continue; fi
    set -- $n_cmd; n_first="$STUDIO_ROOT/bin/$1"; shift
    mcp_add claude "$n_name" "$n_label(MCP, 스튜디오)" "$n_first" "$@"
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
    say "  ${D}[teacher] 한글·문서·자동화·웹 수집·하네스${N}"
    [ "$skip_hwpx" = 1 ] || c_plugin airmang/hwpx-plugins hwpx-plugin@hwpx "한글(HWPX) 편집 엔진 · airmang/hwpx-plugins"
    c_plugin chrisryugj/kordoc kordoc@kordoc "한글·PDF 읽기·공문 프리셋 · chrisryugj/kordoc"
    if [ "$HAS_NPX" = 1 ]; then
      mcp_add claude kordoc "kordoc 문서 도구 17종(MCP)" npx -y kordoc mcp
      mcp_add claude playwright "브라우저 자동화 RPA(MCP) · microsoft/playwright" npx -y "$PLAYWRIGHT_MCP"
    else skip "kordoc MCP·브라우저 자동화 — Node.js가 없어 건너뜀"; fi
    mcp_http claude firecrawl "웹사이트 내용 수집 · Firecrawl(MCP, 키 없이)" "$FIRECRAWL_URL"
    perplexity_mcp claude
    if [ "$HAS_UVX" = 1 ]; then mcp_add claude markitdown "파일 → 텍스트 변환(MCP) · microsoft/markitdown" uvx markitdown-mcp; warm_markitdown
    else skip "파일 → 텍스트 변환(markitdown) — uv가 없어 건너뜀"; fi
    c_plugin revfactory/harness harness@harness-marketplace "하네스 팩토리 · revfactory/harness"
    c_plugin leeandev/stop-slop-ko stop-slop-ko@stop-slop-ko "한국어 문서 AI 티 걷어내기 · stop-slop-ko"
  fi
  if in_profile creator; then
    say "  ${D}[creator] 웹·디자인·영상·인스타${N}"
    c_plugin nextlevelbuilder/ui-ux-pro-max-skill ui-ux-pro-max@ui-ux-pro-max-skill "UI·UX 디자인 · ui-ux-pro-max"
    c_plugin Leonxlnx/taste-skill taste-skill@taste-skill "디자인 감각 · taste-skill"
    c_plugin pbakaus/impeccable impeccable@impeccable "디자인 다듬기 · impeccable"
    c_plugin bradautomates/claude-video watch@claude-video "영상 보고 요약 · claude-video(watch)"
    skills_add Leonxlnx/cinetic claude-code "소개·출시 영상 만들기 · Cinetic (영상 만들 때 ffmpeg·Node 22·Python 3.11 필요)"
    skills_add aldegad/sprite-gen claude-code "스프라이트 이미지 · sprite-gen"
    c_plugin Jakeschincariol/instagram-agent-skill instagram-agent@instagram-agent-skill "인스타그램 스킬 13종(훅·대본·캡션) · instagram-agent-skill"
    c_plugin glifxyz/glif-mcp-server glif@glif "이미지·영상 AI · Glif 플러그인"
    mcp_http claude glif "Glif 연결(MCP, /mcp에서 로그인)" "$GLIF_URL"
    GLIF_ON=1
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
  if in_profile full; then
    say "  ${D}[full] 날쌤 Claude 앱의 플러그인·커넥터 전부 — 50여 종이라 몇 분 걸립니다. 계정이 있어야 쓰는 것도 들어 있습니다${N}"
    # shellcheck disable=SC2086
    c_plugins "$KWP_REPO" "$KWP_MARKET" "업무 플러그인(Anthropic)" $FULL_WORK
    # shellcheck disable=SC2086
    c_plugins "$KWP_REPO" "$KWP_MARKET" "서비스 연동 플러그인" $FULL_PARTNER
    c_plugins leeandev/stop-slop-ko stop-slop-ko "한국어 글쓰기" stakeholder-brief jasoseo
    skip "3D CAD 변환 · contentasoft-cad-converter — Windows 전용이라 건너뜀"
    full_mcps claude
  fi
}
recs_codex() {
  if in_profile teacher; then
    say "  ${D}[teacher] 한글·문서·자동화·웹 수집·하네스${N}"
    [ "$skip_hwpx" = 1 ] || x_plugin airmang/hwpx-plugins hwpx-plugin@hwpx "한글(HWPX) 편집 엔진 · airmang/hwpx-plugins"
    if [ "$HAS_NPX" = 1 ]; then
      mcp_add codex kordoc "kordoc 문서 도구 17종(MCP) · chrisryugj/kordoc" npx -y kordoc mcp
      mcp_add codex playwright "브라우저 자동화 RPA(MCP) · microsoft/playwright" npx -y "$PLAYWRIGHT_MCP"
    else skip "kordoc·브라우저 자동화 — Node.js가 없어 건너뜀"; fi
    mcp_http codex firecrawl "웹사이트 내용 수집 · Firecrawl(MCP, 키 없이)" "$FIRECRAWL_URL"
    perplexity_mcp codex
    if [ "$HAS_UVX" = 1 ]; then mcp_add codex markitdown "파일 → 텍스트 변환(MCP) · microsoft/markitdown" uvx markitdown-mcp; warm_markitdown
    else skip "파일 → 텍스트 변환(markitdown) — uv가 없어 건너뜀"; fi
    skills_add revfactory/harness codex "하네스 팩토리 · revfactory/harness"
    x_plugin leeandev/stop-slop-ko stop-slop-ko@stop-slop-ko "한국어 문서 AI 티 걷어내기 · stop-slop-ko"
  fi
  if in_profile creator; then
    say "  ${D}[creator] 웹·디자인·영상·인스타${N}"
    skills_add nextlevelbuilder/ui-ux-pro-max-skill codex "UI·UX 디자인 · ui-ux-pro-max"
    skills_add Leonxlnx/taste-skill codex "디자인 감각 · taste-skill"
    skills_add pbakaus/impeccable codex "디자인 다듬기 · impeccable"
    x_plugin bradautomates/claude-video watch@claude-video "영상 보고 요약 · claude-video(watch)"
    skills_add Leonxlnx/cinetic codex "소개·출시 영상 만들기 · Cinetic (영상 만들 때 ffmpeg·Node 22·Python 3.11 필요)"
    skills_add aldegad/sprite-gen codex "스프라이트 이미지 · sprite-gen"
    x_plugin Jakeschincariol/instagram-agent-skill instagram-agent@instagram-agent-skill "인스타그램 스킬 13종(훅·대본·캡션) · instagram-agent-skill"
    x_plugin glifxyz/glif-mcp-server glif@glif "이미지·영상 AI · Glif(MCP 포함)"
    GLIF_ON=1
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
  if in_profile full; then
    say "  ${D}[full] 날쌤 Claude 앱의 플러그인·커넥터 전부 — 50여 종이라 몇 분 걸립니다. 계정이 있어야 쓰는 것도 들어 있습니다${N}"
    # shellcheck disable=SC2086
    x_plugins "$KWP_REPO" "$KWP_MARKET" "업무 플러그인(Anthropic)" $FULL_WORK
    # shellcheck disable=SC2086
    x_plugins "$KWP_REPO" "$KWP_MARKET" "서비스 연동 플러그인" $FULL_PARTNER
    x_plugins leeandev/stop-slop-ko stop-slop-ko "한국어 글쓰기" stakeholder-brief jasoseo
    full_mcps codex
  fi
}

# ── 실행 ─────────────────────────────────────────────────────
[ "$recs" = 1 ] && say "추천 묶음: $profiles" || say "추천 묶음: 설치 안 함"
say ""
say "${B}[분필팩 준비]${N}"
if ! prepare_pack; then say ""; warn "분필팩을 준비하지 못해 멈춥니다."; exit 1; fi
say ""
if [ "$studio" = 1 ]; then studio_pack; say ""; fi
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
if [ "$studio" = 1 ] && [ "$HAS_CLAUDE" = 1 ] && [ -f "$STUDIO_ROOT/state.json" ]; then
  say "${B}[스튜디오 → Claude Code MCP]${N}"
  studio_claude_mcp
  say ""
fi

say "${B}다음 단계${N}"
if [ "$PATH_CHANGED" = 1 ]; then
  say "  ※ 새로 설치한 명령이 잡히도록 ${B}Claude·ChatGPT 앱을 완전히 종료했다가 다시 여세요${N}. 터미널을 쓰는 중이면 창을 닫고 새 창을 여세요."
fi
if [ "$HAS_CLAUDE" = 1 ]; then
  say "  Claude (Claude 앱의 Code 탭이 기본 · 터미널은 다른 방법)"
  say "   1. ${B}새 대화${N}를 시작하세요. 방금 설치한 플러그인은 새 대화부터 보입니다"
  say "   2. 작업 폴더(예: 분필작업)를 만들어 Code 탭에서 [Local]로 열고 \"설정 시작해줘\""
  say "      터미널이면:  mkdir -p ~/분필작업 && cd ~/분필작업 && claude"
  say "   3. 노션·패들렛·캔바 연결: Code 탭 입력창 옆 [+] → [Connectors]에서 로그인 (터미널은 대화창에서  /mcp)"
  [ "$GLIF_ON" = 1 ] && say "      Glif(이미지·영상 AI)도 같은 곳에서 glif → 로그인"
  say "   4. 크롬 연결(선택): 크롬 웹스토어에서 'Claude' 확장 설치. Claude Code에서 쓰려면 터미널에서  claude --chrome"
  say "      늘 켜 두려면 대화창에서  /chrome  → Enabled by default  (유료 요금제 필요, WSL은 지원 안 함)"
fi
if [ "$HAS_CODEX" = 1 ]; then
  say "  Codex (ChatGPT 앱의 Codex가 기본 · 터미널은 다른 방법)"
  say "   1. ${B}새 대화${N}를 시작하세요. 방금 연결한 플러그인·MCP는 앱을 껐다 켜면 확실히 잡힙니다 (앱과 터미널은 같은 설정을 씁니다)"
  say "   2. 작업 폴더(예: 분필작업)를 만들어 Codex에서 폴더로 열고 \"설정 시작해줘\""
  say "      터미널이면:  mkdir -p ~/분필작업 && cd ~/분필작업 && codex   (처음이면 'Sign in with ChatGPT')"
  say "   3. 분필 가드(훅)를 신뢰하라는 안내가 나오면 허용하세요. 안 보이면 터미널에서 codex 를 열고  /hooks"
  say "   4. 노션 연결(터미널):  codex mcp login notion"
  [ "$GLIF_ON" = 1 ] && say "      Glif(이미지·영상 AI) 로그인:  codex mcp login glif"
fi
if [ "$PPLX_SKIPPED" = 1 ]; then
  say "  Perplexity(최신 검색)는 유료 API 키가 필요합니다. console.perplexity.ai 에서 키를 받은 뒤, 키는 채팅에 붙여넣지 말고"
  say "   터미널에서 같은 명령의  | sh  부분을  | PERPLEXITY_API_KEY=받은키 sh  로 바꿔 다시 실행하세요."
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
if [ "$studio" = 1 ] && [ -f "$STUDIO_ROOT/state.json" ]; then
  say "  스튜디오 점검: 새 대화에서 \"스튜디오 설치 점검해줘\" (터미널은  nalssam-pack doctor --verify-mcp) · 설치 기록 $STUDIO_ROOT/report.json"
  say "         계정이 필요한 것(ElevenLabs·Gemini·Google Cloud·After Effects 등)은 각자 연결해야 합니다."
fi
if [ "$recs" = 1 ] && in_profile full; then
  say "  full 묶음: 각 서비스는 처음 쓸 때 로그인합니다(Claude는 /mcp, Codex는 codex mcp login <이름>). 계정이 없는 플러그인은 꺼 두어도 됩니다."
  say "         Gmail·Google 문서·Microsoft 365는 공용 연결 주소가 없어 Claude 앱 설정 → 커넥터에서 켜세요. 목록: https://github.com/nalssam/bunpil_pack/blob/main/docs/full-bundle.md"
fi
say "  업데이트는 같은 명령을 다시 실행하면 됩니다. 자세한 안내: $SITE"
say ""
if [ "$errors" -gt 0 ]; then
  warn "일부 항목($errors건)이 실패했습니다. 위 메시지를 확인하고 다시 실행해 보세요."
  exit 1
fi
ok "분필팩 설치 완료. 학생 이름은 '학생A'처럼 바꿔 쓰세요. 결과물은 모두 초안입니다."
}
