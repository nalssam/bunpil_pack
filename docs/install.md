# nalssam's 분필팩 설치 안내

> 그림과 함께 따라 하려면 사이트를 여세요: https://nalssam-bunpil.vercel.app
> 이 문서는 같은 내용을 글로 옮긴 것입니다.

## 시작 전에

| 확인할 것 | 이유 |
|---|---|
| **인터넷망 PC나 개인 기기** | 업무망 PC는 인터넷이 막혀 있거나 프로그램 설치가 제한됩니다. 업무망 자료를 옮길 때는 학교 규정을 따릅니다. |
| **쓸 AI의 요금제** | Claude: Claude Code와 플러그인은 유료 요금제(Pro·Max·Team·Enterprise)에서 됩니다. ChatGPT Codex: 무료 요금제를 포함한 ChatGPT 요금제에서 쓸 수 있고, 쓸 수 있는 양은 요금제마다 다릅니다. |
| **학생 실명은 넣지 않기** | 분필팩은 교사 업무용 도구입니다. 학생 이름은 '학생A'처럼 바꿔 씁니다. |
| **운영체제** | Windows 10(1809) 이상, macOS 13 이상. 관리자 권한은 필요 없습니다. |

## A. Claude Code (터미널)

1. **터미널 열기** — Windows: 시작 메뉴에서 `PowerShell`을 찾아 엽니다(관리자 아님). 맥: ⌘+Space → `터미널`.
2. **한 줄 붙여넣고 Enter**
   - Windows: `irm https://nalssam-bunpil.vercel.app/claude.ps1 | iex`
   - macOS·Linux: `curl -fsSL https://nalssam-bunpil.vercel.app/claude.sh | sh`

   Claude Code(없을 때만) → Node.js·uv·Git(없을 때만) → 분필팩 5종 → 추천 teacher 묶음 순으로 설치합니다. Windows에서 Git을 설치할 때 "변경을 허용하시겠어요?" 창이 뜨면 **예**를 누릅니다. 거절하면 Git이 필요한 일부 추천 도구(한글 편집 엔진, 하네스 팩토리 등)만 건너뛰고, 나중에 같은 줄을 다시 실행하면 채워집니다. 맥에서 Git이 없으면 "명령어 개발자 도구" 설치 창이 뜨니 **설치**를 누르고 끝나면 같은 줄을 다시 실행합니다.
3. **새 창에서 Claude 시작** — 창을 닫고 새로 연 뒤:
   - Windows: `mkdir -Force ~\분필작업 > $null; cd ~\분필작업; claude`
   - macOS·Linux: `mkdir -p ~/분필작업 && cd ~/분필작업 && claude`

   처음이면 로그인 방법에서 Claude 구독 계정을 고르고 브라우저에서 로그인합니다.
4. **설정 마법사** — 대화창에 `설정 시작해줘`. 10가지 질문에 답하면 내 맞춤 지침(`CLAUDE.md`)이 생깁니다.
5. **점검과 연결** — `분필 점검해줘`로 설치 상태를 확인하고, `/mcp`에서 노션·패들렛·캔바에 로그인합니다.

## B. ChatGPT Codex (터미널)

1. **터미널 열기** — A와 같습니다.
2. **한 줄 붙여넣고 Enter**
   - Windows: `irm https://nalssam-bunpil.vercel.app/codex.ps1 | iex`
   - macOS·Linux: `curl -fsSL https://nalssam-bunpil.vercel.app/codex.sh | sh`

   Codex CLI(없을 때만, OpenAI 공식 설치 프로그램) → Node.js·uv·Git(없을 때만) → 분필팩 5종 → 추천 teacher 묶음 순으로 설치합니다. Windows용 Codex에서는 한글 편집 엔진(hwpx-plugin)을 건너뛰고 한글 양식 보고서(hwpx_new)·kordoc이 대신 한글 문서를 맡습니다.
3. **새 창에서 Codex 시작** — `mkdir … && cd ~/분필작업 && codex` → **Sign in with ChatGPT**.
4. **개인정보 가드 켜기** — Codex는 플러그인 훅을 처음에 믿지 않습니다. 대화창에 `/hooks` → 분필 가드 → **신뢰(trust)**. 분필팩을 업데이트하면 다시 신뢰합니다.
5. **설정 마법사** — `설정 시작해줘` → 내 맞춤 지침(`AGENTS.md`)이 생깁니다.
6. **연결과 점검** — 새 터미널에서 `codex mcp login notion`(padlet, canva도 같은 방법), 대화창에서 `분필 점검해줘`.

Codex 앱(데스크톱)을 쓴다면 이 설치를 마친 뒤 앱을 다시 열고 플러그인 목록에 분필팩이 보이는지 확인하세요.

## C. Claude 앱 (채팅·Cowork, 터미널 없이)

1. 왼쪽 메뉴 **사용자 지정(Customize)** → **플러그인(Plugins)** → **추가(Add)** → **마켓플레이스 추가(Add marketplace)** → **저장소에서 추가(Add from a repository)** → `nalssam/bunpil_pack`. Cowork에서는 먼저 **Cowork** 탭을 엽니다.
2. **분필 시작 팩**을 설치하고 필요한 팩을 더합니다.
3. 새 대화에서 `설정 시작해줘`, 이어서 `분필 점검해줘`.

마켓플레이스 추가가 막히면 사이트의 플러그인 zip(`/app/bunpil-start.zip` 등)을 받아 추가 메뉴의 업로드로 올립니다. 앱에서 추가한 플러그인은 계정에 저장되어 같은 계정으로 로그인한 Claude Code에서도 쓸 수 있습니다. 채팅에서는 자동 점검(훅)과 서브에이전트가 회색으로 보이며, 정상입니다.

## D. 더블클릭 설치 (zip)

1. https://nalssam-bunpil.vercel.app/bunpil-pack.zip 을 받아 **모두 압축 풀기**.
2. Windows: `Install-Windows.bat` 더블클릭("Windows의 PC 보호" 창이 뜨면 **추가 정보 → 실행**). 맥: `Install-Mac.command`를 오른쪽 클릭 → **열기**(막히면 시스템 설정 → 개인정보 보호 및 보안 → **그래도 열기**).
3. Claude Code와 Codex가 모두 없으면 무엇을 설치할지 번호로 고릅니다.

분필팩 5종은 인터넷 없이도 설치되고, 추천 도구는 인터넷이 필요합니다.

## E. 날쌤팩도 함께 (고급, macOS·Linux·WSL2)

영상·모션·발표·분석·개발 도구까지 담은 [날쌤팩](https://github.com/nalssam/nalssam-pack)을 분필팩과 함께 설치합니다. 수 GB를 내려받아 10~30분이 걸립니다.

```bash
curl -fsSL https://nalssam-bunpil.vercel.app/install.sh | sh -s -- --nalssam
```

- Claude Code가 있으면 날쌤팩을 `--claude`로 설치합니다(스킬과 네이티브 플러그인 122개, 개발·Google Cloud 플러그인 포함).
- 겹치는 추천 도구는 날쌤팩의 고정 버전을 쓰고, 분필팩은 그 항목을 건너뜁니다.
- 설치 후 `nalssam-pack doctor --verify-mcp`로 연결을 점검합니다. 나레이션(ElevenLabs)·음성 인식(Gemini 등)·Google Cloud·After Effects는 각자 계정·프로그램을 연결해야 합니다.
- Windows는 WSL2 Ubuntu 터미널에서 실행합니다. 이때는 WSL 안의 Claude Code·Codex에 설치됩니다.

## 업데이트 · 지우기

- 업데이트: 설치할 때 쓴 한 줄을 다시 실행합니다.
- 지우기: `irm https://nalssam-bunpil.vercel.app/uninstall.ps1 | iex` (Windows), `curl -fsSL https://nalssam-bunpil.vercel.app/uninstall.sh | sh` (macOS·Linux).

## 문제 해결

| 증상 | 해결 |
|---|---|
| `'irm'은(는) 내부 또는 외부 명령이 아닙니다` | 명령 프롬프트가 아니라 PowerShell(`PS C:\>`)을 엽니다. |
| "이 시스템에서 스크립트를 실행할 수 없으므로…" | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`를 한 번 실행합니다. 학교 관리 PC라 안 바뀌면 정보 담당 선생님께 문의합니다. |
| `claude`·`codex` 명령을 찾을 수 없음 | 터미널을 닫고 새로 엽니다. 그래도 안 되면 설치 줄을 다시 실행합니다. |
| 빨간 `[x]`·`✗` 줄 | 같은 줄을 다시 실행합니다. 실패한 것만 다시 시도합니다. |
| 학교 인터넷에서 내려받기 실패 | 휴대폰 핫스팟으로 연결하거나 집에서 zip을 받아 USB로 옮겨 더블클릭 설치합니다. |
| Claude 앱에 플러그인 메뉴가 없음 | 유료 요금제가 필요합니다. 무료로 시작하려면 Codex를 씁니다. |
| Codex에서 가드가 안 돎 | `/hooks`에서 분필 가드를 신뢰합니다. |
| 가짜 번호에도 경고 | 형식만 보고 판단합니다. 실제 정보가 아니면 그대로 진행합니다. |
| 가드를 잠시 끄기 | 환경변수 `BUNPIL_GUARD=off` 또는 분필 시작 팩 비활성화. |
| 브라우저 자동화 첫 실행이 느림 | 처음 한 번 구성 요소를 내려받습니다. 정상입니다. |

## 설치하면 바뀌는 것

- 홈 폴더의 `.bunpil` 폴더: 분필팩(`bunpil-pack`), 관리자 권한 없이 설치한 Node.js(`node`), PATH 설정(`env`, macOS·Linux)
- Claude Code·Codex 설정: 분필팩·추천 플러그인, MCP 연결(kordoc, playwright, markitdown, hwpx_new, pptx_maker, firecrawl, 키가 있으면 perplexity, creator 묶음이면 glif)
- 없을 때만: Claude Code·Codex CLI·Node.js·uv·Git, PATH 추가(macOS·Linux는 `~/.bunpil/env`와 셸 설정 파일의 `# bunpil-path` 한 줄, Windows는 사용자 PATH)
- Windows에서 Codex를 npm으로 설치한 경우에만: 현재 사용자 PowerShell 실행 정책을 RemoteSigned로(`$env:BUNPIL_KEEP_POLICY="1"`이면 바꾸지 않음)

문의: GitHub Issues — https://github.com/nalssam/bunpil_pack/issues
