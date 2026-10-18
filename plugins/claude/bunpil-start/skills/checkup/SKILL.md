---
name: checkup
description: "분필 점검, 설치 확인, 잘 깔렸나, 분필팩 상태, 업데이트 확인, 가드가 작동하나 같은 요청에 사용한다. 분필팩 플러그인·스킬 설치 상태, 지침 파일 위치, 개인정보 가드 작동, 자동 업데이트 설정을 표로 보여 준다. 개별 스킬의 품질 시험은 eval-run을 쓴다."
---

# 분필 점검

설치가 제대로 되었는지 5분 안에 확인한다. 결과는 표 하나와 할 일 목록으로 보여 준다. 모든 결과는 초안이며 최종 판단은 선생님이 한다.

개인정보 원칙: 학생 실명·학번·생년월일·주소·연락처·가족관계·사진 등 개인을 알아볼 수 있는 정보가 보이면 작업을 멈추고 '학생A'처럼 가명으로 바꾸자고 제안한다. 결과물에는 개인정보를 넣지 않는다.

## 절차

1. **지금 환경 판별** — 아래 중 어디인지 확인한다. 확실하지 않으면 선생님께 한 번 묻는다.
   - 데스크톱 앱의 코드 작업 화면(Claude 앱의 Code 탭, ChatGPT 앱의 Codex)과 Cowork
   - 터미널·VS Code의 코딩 에이전트(Claude Code, Codex CLI)
   - 웹·모바일 채팅
2. **설치된 분필 스킬 확인** — 지금 쓸 수 있는 스킬 목록에서 이름을 찾는다.

   | 플러그인 | 있어야 할 스킬 |
   |---|---|
   | 분필 시작 팩 | setup, privacy-guard, checkup |
   | 분필 수업자료 팩 | worksheet, lesson-plan, class-slides, class-video, papercraft, coloring, rubric |
   | 분필 학교업무 팩 | gongmun, newsletter, pumui, parent-survey, hwpx-doc |
   | 분필 하네스빌더 팩 | skill-maker, harness-fix, eval-run, share-skill, harness-gallery |
   | 분필 커넥터 팩 | connect |

   추천 묶음(설치 문장의 teacher 묶음)도 확인한다. 연결된 MCP 목록(Claude Code는 `claude mcp list`, Codex는 `codex mcp list`)에 kordoc, playwright, markitdown, hwpx_new, pptx_maker, firecrawl이 있는지 본다. perplexity는 유료 API 키가 있을 때만 연결되므로 없어도 정상이다(필요하면 키를 받아 **터미널에서** 설치 명령을 `PERPLEXITY_API_KEY`와 함께 다시 실행하라고 안내하고, 키는 채팅창에 붙여넣지 말라고 당부). creator 묶음을 설치했다면 glif가 있는지 보고, "로그인 필요"로 나오면 Claude Code는 `/mcp` → glif, Codex는 `codex mcp login glif`로 로그인하라고 안내한다. studio 묶음(예전 날쌤팩)을 함께 설치했다면 같은 도구가 `nalssam-` 이름이나 studio 이름(hwpx-new, pptx-maker, rea, motion)으로 연결돼 있어도 정상이고, 새 대화에서 "스튜디오 설치 점검해줘"(터미널은 `nalssam-pack doctor --verify-mcp`)로 실제 연결을 확인하라고 안내한다. 없으면 설치 문장을 채팅창에 다시 붙여넣으라고 안내한다(사이트 https://nalssam-bunpil.vercel.app 의 설치 안내에서 복사. 다시 실행하면 빠진 것만 채운다). Node.js·uv가 없어서 건너뛴 항목은 그 이름과 설치 방법을 적는다.
3. **지침 파일 확인** — 작업 폴더의 `CLAUDE.md`, `AGENTS.md`가 있는지, 두 파일 내용이 같은지 확인한다. 없으면 setup 실행을 권한다. 다르면 어느 쪽을 기준으로 맞출지 묻는다.
4. **가드 시험** — 선생님께 다음 문장을 그대로 입력해 보시라고 안내한다: `가드 시험: 연락처 010-0000-0000`. 경고 문구가 보이면 정상이다. 웹 채팅에서는 훅이 없어 경고가 뜨지 않는 것이 정상이며, 대신 privacy-guard 지침이 작동한다.
5. **업데이트 설정 안내** — 환경에 맞는 줄만 보여 준다.

   | 환경 | 자동 업데이트 켜기 |
   |---|---|
   | Claude 앱(Chat·Cowork) | 사용자 지정 → 플러그인 → bunpil 마켓플레이스 → 자동 동기화(Sync automatically) |
   | Claude Code (앱 Code 탭·터미널) | 앱 Code 탭은 입력창 옆 + → Plugins → Manage plugins에서 상태를 보고, 설치 문장을 다시 붙여넣어 최신으로 바꾼다. 터미널은 `/plugin` → Marketplaces → bunpil → Enable auto-update |
   | Codex (ChatGPT 앱·터미널) | 월 1회쯤 설치 문장을 채팅창에 다시 붙여넣어 최신으로 바꾼다. 터미널은 `codex plugin marketplace upgrade` 후 `codex plugin add bunpil-start@bunpil` |

6. **환경별로 안 되는 기능 알림**

   | 기능 | 웹·앱 Chat | Cowork | Claude Code (앱 Code 탭·터미널) | Codex (ChatGPT 앱·터미널) |
   |---|---|---|---|---|
   | 스킬 | ○ | ○ | ○ | ○ |
   | 자동 개인정보 점검(훅) | × | ○ | ○ | 신뢰 후 ○ (앱의 훅 안내 또는 터미널 `/hooks`) |
   | 공문 처리 서브에이전트 | × (순서대로 직접 처리) | ○ | ○ | × (순서대로 직접 처리) |
   | 노션·패들렛·캔바 커넥터 | 연결 후 ○ | 연결 후 ○ | 로그인 후 ○ (앱 Code 탭은 입력창 옆 + → Connectors, 터미널은 `/mcp`) | 로그인 후 ○ (터미널은 `codex mcp login`) |

## 결과 표 형식

| 항목 | 상태 | 할 일 |
|---|---|---|
| 시작 팩 | 설치됨 / 없음 | |
| 지침 파일 | 있음(동일) / 있음(다름) / 없음 | |
| 가드 | 작동 / 이 환경은 훅 없음 / 확인 필요 | |
| 자동 업데이트 | 켜짐 / 꺼짐 / 확인 필요 | |

확인할 수 없는 항목은 추측하지 말고 "확인 필요"로 쓴다.

## 점검

- [ ] 추측한 상태를 사실처럼 쓰지 않았는가
- [ ] 선생님 환경에 해당하는 안내만 보여 주었는가
- [ ] 할 일이 한 줄씩 구체적인가
