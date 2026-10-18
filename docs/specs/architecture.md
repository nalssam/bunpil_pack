# 분필팩 아키텍처 명세 (WP1)

버전 0.1 · 2026-10-13 · Opus 5.5

## 1. 이름

| 항목 | 값 | 비고 |
|---|---|---|
| 저장소 | `nalssam/bunpil_pack` | 0.3.0부터. 배포 사이트 https://nalssam-bunpil.vercel.app |
| 마켓플레이스 `name` | `bunpil` | ASCII 필수, `claude-` 접두어 금지 |
| 플러그인 | `bunpil-start`, `bunpil-class`, `bunpil-school`, `bunpil-builder`, `bunpil-connect` | 변경 불가 식별자, kebab-case |

## 2. 플러그인과 스킬

| 플러그인(표시명) | 스킬 | Claude 전용 요소 | 공통 요소 |
|---|---|---|---|
| bunpil-start (분필 시작 팩) | `setup`, `privacy-guard`, `checkup` | 훅(Claude Code·Cowork) | 훅(Codex, 신뢰 필요), Codex onboardingSkill=setup |
| bunpil-class (수업자료 팩) | `worksheet`, `lesson-plan`, `class-slides`, `class-video`, `papercraft`, `coloring`, `rubric` | — | — |
| bunpil-school (학교업무 팩) | `gongmun`, `newsletter`, `pumui`, `parent-survey`, `hwpx-doc` | 서브에이전트 5종(gongmun용) | — |
| bunpil-builder (하네스빌더 팩) | `skill-maker`, `harness-fix`, `eval-run`, `share-skill` | 서브에이전트 `skill-auditor` | — |
| bunpil-connect (커넥터 팩) | `connect` | — | 원격 MCP 3종(Notion·Padlet·Canva) |

## 3. 공통 작성 규칙 (모든 SKILL.md)

1. **frontmatter는 `name`, `description` 두 개만** 쓴다(claude.ai·Codex 호환). `name`은 폴더명과 같다.
2. `description`은 한국어, 앞부분에 트리거 단어를 둔다. 언제 쓰는지와 언제 쓰지 않는지를 함께 적는다. 600자 이내.
3. 본문은 이다체, 5,000토큰 미만. 긴 예시·서식은 `references/`, 템플릿 파일은 `assets/`, 스크립트는 `scripts/`.
4. 본문에서 "Claude"라는 모델명을 쓰지 않는다(Codex 호환). "AI", "에이전트"로 쓴다.
5. 하네스 고유 도구명에 의존하지 않는다. "파일을 읽는다/쓴다", "사용자에게 묻는다"처럼 행위로 적는다.
6. 시작할 때 작업 폴더의 `CLAUDE.md` 또는 `AGENTS.md`를 읽어 학교급·학년·교과·문체를 반영하라고 적는다. 없으면 필요한 것만 짧게 묻는다.
7. **개인정보 원칙 블록을 반드시 포함한다**(아래 문구 그대로):
   > 학생 실명·학번·생년월일·주소·연락처·가족관계·사진 등 개인을 알아볼 수 있는 정보가 보이면 작업을 멈추고 '학생A'처럼 가명으로 바꾸자고 제안한다. 결과물에는 개인정보를 넣지 않는다.
8. 결과물은 모두 **초안**이며, 최종 발송·제출·결재·출력은 교사가 한다고 명시한다.
9. 원본 파일은 수정하지 않는다. 결과는 `outputs/` 아래 새 파일로 저장한다(채팅 전용 환경이면 대화에 제시).
10. 끝에 "점검" 절을 둔다: 결과물을 내기 전에 스스로 확인할 체크리스트 3~6개.
11. 생활기록부 서술형 문구 생성, 학생 직접 사용, NEIS·K-에듀파인 자동 입력은 하지 않는다.

## 4. 파일 형식 정책

| 산출물 | 기본 | 대안 |
|---|---|---|
| 학습지·지도안·가정통신문 | 인쇄용 HTML(A4 CSS) → 가능하면 PDF·DOCX 변환 | 마크다운 |
| 수업 슬라이드 | 플랫폼의 PPTX 생성 기능 사용 | 슬라이드별 HTML |
| 페이퍼크래프트·컬러링 | SVG(A4, 재단선·접는선 규약) → PDF | PNG |
| 한글 문서 | hwpx-plugin(airmang) 설치 시 HWPX | DOCX 또는 서식 항목표(.md) |
| 표 | XLSX(가능 시) | CSV |

## 5. 저장소 구조

```
bunpil-pack/
├── .claude-plugin/marketplace.json      # 빌드 산출물
├── .agents/plugins/marketplace.json     # 빌드 산출물
├── src/plugins/<plugin>/                # 단일 원본
│   ├── meta.json                        # 이름·표시명·설명·버전·키워드·카테고리·codex 설정
│   ├── skills/<skill>/SKILL.md (+references/ assets/ scripts/)
│   ├── agents/*.md                      # Claude 전용
│   ├── hooks/ (hooks.claude.json, hooks.codex.json, 스크립트)
│   └── mcp.json                         # 원격 MCP 정의(공통)
├── plugins/claude/<plugin>/             # 빌드 산출물(커밋)
├── plugins/codex/<plugin>/              # 빌드 산출물(커밋)
├── dist/                                # 업로드용 zip
├── tools/build.py, tools/check.py
├── evals/cases/<skill>.yaml
├── site/                                # 랜딩페이지
└── docs/
```

## 6. 빌드 규칙 (tools/build.py)

- Claude: `plugins/claude/<p>/.claude-plugin/plugin.json`(name, displayName, version, description, author, homepage, repository, license, keywords) + `skills/` + `agents/` + `hooks/hooks.json`(hooks.claude.json 복사) + 훅 스크립트 + `.mcp.json`(type http).
- Codex: `plugins/codex/<p>/.codex-plugin/plugin.json`(name, version, description, author, license, keywords, `skills: "./skills/"`, 있으면 `mcpServers: "./.mcp.json"`, `hooks: "./hooks/hooks.json"`, `interface{displayName, shortDescription(30자), longDescription, developerName, category, capabilities, defaultPrompt, brandColor}`, start 팩은 `extensions.com.openai.onboardingSkill`) + `skills/` + 훅 + `.mcp.json`. `agents/`는 복사하지 않는다.
- 마켓플레이스 두 개 생성. 버전은 meta.json 한 곳에서만 관리.
- `dist/`(빌드 산출물, 저장소에는 올리지 않고 `tools/make_site.py`가 웹사이트 `public/app/`으로 복사): 플러그인별 Claude zip(`bunpil-start.zip`, 아카이브 안 `.claude-plugin/plugin.json` 정확히 1개), 스킬별 zip(claude.ai 스킬 업로드용), 전체 묶음 zip.
- `bin/` 디렉터리 금지(Chat·Cowork 설치 거부).

## 7. 훅 설계(bunpil-start)

- 스크립트: `hooks/guard.sh`(POSIX sh + grep), `hooks/guard.ps1`(PowerShell). 같은 규칙.
- 이벤트: `UserPromptSubmit`(입력 점검), `PreToolUse` 매처 `Write|Edit`(쓰기 전 점검).
- 규칙: 주민등록번호 패턴 → 차단(exit 2, stderr 사유). 휴대전화·"N학년 N반 N번 + 이름" 패턴 → 경고(`hookSpecificOutput.additionalContext` + `systemMessage`), 진행은 허용.
- Claude hooks.json: `"command": "sh \"${CLAUDE_PLUGIN_ROOT}/hooks/guard.sh\" prompt"`. Windows Claude Code는 Git Bash 경유(확인 필요 — WP10 실측).
- Codex hooks.json: `command`는 sh, `commandWindows`는 `powershell -NoProfile -ExecutionPolicy Bypass -File "%PLUGIN_ROOT%\\hooks\\guard.ps1" prompt`.
- 끄는 법: 환경변수 `BUNPIL_GUARD=off` 또는 플러그인 비활성화.

## 8. MCP(bunpil-connect)

| 이름 | URL | 근거 |
|---|---|---|
| notion | https://mcp.notion.com/mcp | developers.notion.com |
| padlet | https://mcp.padlet.com | padlet.help |
| canva | https://mcp.canva.com/mcp | openai/plugins 공식 저장소(Canva 게시) — 부분 확인 |

설치만 해서는 로그인하지 않는다. Claude Code는 `/mcp`, Chat·Cowork는 Connectors 탭, Codex는 `codex mcp login <name>`으로 연결한다. `connect` 스킬이 이 과정을 안내한다.

## 9. 미확인 사항과 검증 방법

| 항목 | 검증 |
|---|---|
| Windows Claude Code에서 `sh` 훅 실행 | WP10에서 Windows 실측, 실패 시 `shell: powershell` 별도 플러그인 변형 |
| Codex가 훅 JSON 출력(additionalContext)을 Claude와 같게 해석 | Codex 설치 후 실측 |
| Codex가 `.codex-plugin/plugin.json`의 `hooks` 경로 필드 인식 | 실측 |
| Cowork 훅 실행 환경(Linux VM 여부) | 실측 |
