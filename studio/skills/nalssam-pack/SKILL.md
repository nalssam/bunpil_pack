---
name: nalssam-pack
description: 분필팩 스튜디오(영상·모션·문서·분석 도구 묶음, 예전 이름 날쌤팩)의 설치 상태를 확인하고 스킬·MCP 환경을 구성하거나 복구할 때 사용한다. 사용자가 스튜디오 묶음이나 날쌤팩의 설치·진단·재설치·제거를 요청할 때만 실행한다.
---

# 분필팩 스튜디오

분필팩 스튜디오는 로컬 작업 환경 설치기다(예전 이름 날쌤팩, 명령 이름은 그대로 `nalssam-pack`). 분필팩 한 줄 설치에서 `--profile studio`를 고르면 이 설치기가 실행된다. 일반 ChatGPT 웹 채팅의 계정 전체에 로컬 MCP를 연결하는 도구가 아니다.

1. 기본 설치 위치 `~/.local/share/nalssam-pack`의 `report.json`, `state.json`을 먼저 확인한다. 다른 설치 경로를 사용했다면 사용자가 선택한 경로를 쓴다.
2. 설치 상태 확인은 `nalssam-pack doctor --verify-mcp`. MCP 초기화와 도구 목록 조회가 성공했을 때만 연결이 검증됐다고 말한다.
3. 설치·재설치 요청이면 `nalssam-pack plan`으로 고정 목록과 대상을 확인하고 `nalssam-pack install`을 실행한다. 기본 설정을 덮어쓰거나 사용자 계정·토큰을 다른 사람에게 복사하지 않는다.
4. `report.json`의 실패와 `pending`을 구분해서 보고한다. API 키, 클라우드 계정, Adobe 프로그램이 없으면 해당 기능이 준비됐다고 주장하지 않는다.
5. 특정 도구만 설치하려면 `nalssam-pack install --only owner/repository`. Claude Code 네이티브 플러그인은 사용자가 원할 때 `--claude`로 설치한다.
6. 제거 요청이면 `nalssam-pack uninstall`. 이 명령은 설치 영수증과 현재 값이 일치하는 연결만 지운다. 캐시·백업·가상환경을 임의로 재귀 삭제하지 않는다.
7. 외부 서비스 설정이 필요한 경우 실제 필요한 항목만 요청한다. 키는 채팅에 붙여 넣기보다 해당 서비스의 지원 설정 방법을 따른다.

명령이 PATH에 없으면 설치 경로의 `env.sh`를 source하거나 `bin/nalssam-pack`을 절대 경로로 실행한다.
