#!/bin/sh
# 분필팩 개인정보 가드 (POSIX sh)
# 사용: guard.sh prompt|write|write-codex   — 표준입력으로 훅 JSON을 받는다.
#  - 등록번호 하이픈 형식(6자리-7자리): 입력은 차단(exit 2), 파일 쓰기는 확인 요청(ask, Claude)
#    Codex는 ask를 지원하지 않아(그대로 진행됨) write-codex 모드에서 더하는 줄만 보고 막는다(deny).
#    지우는 줄(-)은 보지 않으므로 번호를 지우는 수정은 막지 않는다.
#  - 하이픈 없는 13자리·휴대전화·"N학년 N반 N번": 경고(exit 0 + JSON)
# 끄기: BUNPIL_GUARD=off

mode="${1:-prompt}"
[ "${BUNPIL_GUARD:-on}" = "off" ] && exit 0

input=$(cat)
scan="$input"
if [ "$mode" = "write-codex" ]; then
  # apply_patch 입력 {"command":"*** Begin Patch\n...\n+더하는 줄\n-지우는 줄..."}에서 더하는 줄만 고른다
  scan=$(printf '%s' "$input" | awk '{ gsub(/\\n/, "\n"); print }' | grep '^+' | grep -v '^+++')
fi

RRN_HYPHEN='(^|[^0-9])[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])-[1-8][0-9]{6}([^0-9]|$)'
RRN_PLAIN='(^|[^0-9])[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[1-8][0-9]{6}([^0-9]|$)'
PHONE='(^|[^0-9])01[016789][- .]?[0-9]{3,4}[- .]?[0-9]{4}([^0-9]|$)'
CLASSNO='[0-9][ ]?학년[ ]?[0-9]{1,2}[ ]?반[ ]?[0-9]{1,2}[ ]?번'

has() { printf '%s' "$scan" | grep -Eq "$1"; }

if has "$RRN_HYPHEN"; then
  if [ "$mode" = "write-codex" ]; then
    printf '%s\n' '{"systemMessage":"[분필 가드] 파일에 주민등록번호 형식을 쓰려고 해서 막았습니다.","hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"분필 가드: 주민등록번호 형식(000000-0000000)은 파일에 쓰지 않습니다. 가명이나 빈칸으로 바꿔 다시 시도하세요. 실제 번호가 아니면 사용자에게 알리고 BUNPIL_GUARD=off로 잠시 끌 수 있습니다."}}'
    exit 0
  fi
  if [ "$mode" = "write" ]; then
    printf '%s\n' '{"systemMessage":"[분필 가드] 쓰려는 내용에 주민등록번호 형식이 있습니다. 실제 번호라면 거절하세요.","hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"분필 가드: 주민등록번호 형식(000000-0000000)이 파일에 들어갑니다. 실제 개인정보가 아니거나 지우는 수정일 때만 허용하세요."}}'
    exit 0
  fi
  echo "[분필 가드] 주민등록번호 형식(000000-0000000)이 있어 입력을 막았습니다. 그 부분을 지우고 다시 보내 주세요. (끄기: BUNPIL_GUARD=off)" >&2
  exit 2
fi

warn=""
add() { if [ -n "$warn" ]; then warn="$warn, $1"; else warn="$1"; fi; }
has "$RRN_PLAIN" && add "13자리 번호(주민번호일 수 있음)"
has "$PHONE" && add "휴대전화 번호"
has "$CLASSNO" && add "학년·반·번호"

if [ -n "$warn" ]; then
  if [ "$mode" = "prompt" ]; then hook_event="UserPromptSubmit"; else hook_event="PreToolUse"; fi
  ctx="분필 가드 경고: 입력 또는 쓰려는 내용에 ${warn} 형식의 정보가 있다. 실제 학생·학부모 정보일 수 있으므로 진행 전에 사용자에게 알리고 '학생A'처럼 가명 처리하자고 먼저 제안하라. 바코드·주문번호처럼 개인정보가 아니면 그대로 진행한다. 결과물에는 개인정보를 넣지 않는다."
  msg="[분필 가드] ${warn} 형식이 보입니다. 실제 개인정보라면 가명으로 바꿔 주세요."
  printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}\n' "$msg" "$hook_event" "$ctx"
fi
exit 0
