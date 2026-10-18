# nalssam's 분필팩

> 선생님의 AI 조수, 채팅창에 붙여넣기만 하면 내 교실에 맞춰집니다.
> Claude 앱(Code 탭)과 ChatGPT 앱(Codex)에 교사용 플러그인·스킬·MCP를 한 번에 설치합니다.

**설치 안내 사이트: https://nalssam-bunpil.vercel.app** — Claude·Codex별로 1교시부터 따라 하는 설치 시간표, 묶음 고르기, 설치 문장 만들기, 문제 해결, 연수용 큰 화면이 있습니다.

**누구도 소외되지 않는 기술, 혼자 닳지 않는 교사.** — 날쌤(nalssam) · 몽당분필

## 채팅창에 붙여넣어 설치하기

터미널을 몰라도 됩니다. 앱의 채팅창에 아래 문장을 붙여넣으면 AI가 대신 설치합니다. 관리자로 실행할 필요는 없습니다(Windows에서 Git을 설치할 때 "이 앱이 디바이스를 변경할 수 있도록 허용하시겠어요?" 창이 뜨면 **예**).

1. **앱을 내려받고 로그인** — Claude는 [claude.com/download](https://claude.com/download)의 **Claude 앱**(Code 탭은 유료 요금제 Pro 이상), ChatGPT Codex는 [chatgpt.com/download](https://chatgpt.com/download)의 **ChatGPT 앱**(ChatGPT 계정. Codex는 무료 요금제를 포함한 요금제에서 쓸 수 있고, 쓸 수 있는 양은 요금제마다 다릅니다)입니다.
2. **작업 폴더 열기** — 문서 폴더 안에 `분필작업` 폴더를 만듭니다. Claude 앱은 위쪽 **Code** 탭 → **Local** → 폴더 선택, ChatGPT 앱은 새 채팅에서 **Codex**를 고르고 폴더를 엽니다. 플러그인은 Local 환경에서만 쓸 수 있습니다.
3. **설치 문장을 붙여넣고 Enter** — 아래 문장과 명령을 입력창에 붙여넣습니다. AI가 실행 허락(승인)을 물으면 명령이 아래와 같은지 확인하고 허용합니다. Claude 앱은 입력창 옆 권한 선택을 **Manual**(수동)로 두세요. **Auto**는 인터넷에서 받은 스크립트 실행을 막을 수 있습니다.
4. **새 대화에서 "설정 시작해줘"** — 10가지 질문에 답하면 내 맞춤 지침이 생깁니다. 이어서 "분필 점검해줘".

붙여넣을 문장 — 첫 줄은 모두 같고, 둘째 줄은 쓰는 AI와 컴퓨터에 따라 고릅니다.

```text
분필팩을 설치해줘. 아래 명령을 한 글자도 바꾸지 말고 그대로 실행해줘. 5~10분 걸리니 시간 제한에 걸리지 않게 백그라운드로 실행하고 끝날 때까지 기다려줘. 끝나면 설치된 것과 실패한 것을 짧게 알려줘.
```

| | Windows | macOS · Linux |
|---|---|---|
| **Claude** | `powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/claude.ps1 \| iex"` | `curl -fsSL https://nalssam-bunpil.vercel.app/claude.sh \| sh` |
| **ChatGPT Codex** | `powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/codex.ps1 \| iex"` | `curl -fsSL https://nalssam-bunpil.vercel.app/codex.sh \| sh` |

Windows용 명령은 PowerShell, 명령 프롬프트, Git Bash 어디서 실행돼도 같게 동작합니다. 일반 대화(Chat) 탭이나 웹 claude.ai의 Claude는 내 컴퓨터에서 명령을 실행할 수 없으니 꼭 **Code 탭**에서 하세요.

이 문장이 하는 일:

1. Claude Code(또는 Codex CLI)가 없으면 공식 설치 프로그램으로 설치합니다.
2. Node.js·uv가 없으면 관리자 권한 없이 설치하고, Git이 없으면 설치합니다(Windows는 winget이라 허용 창이 뜨면 **예**, 맥은 "개발자 도구 설치" 창에서 **설치**를 누른 뒤 같은 문장을 한 번 더 붙여넣기). Git이 없어도 Git이 필요한 추천 도구만 건너뛰고 나머지는 설치됩니다.
3. 분필팩을 `~/.bunpil`에 내려받아 플러그인 5종을 설치합니다. Git이 없어도 됩니다.
4. teacher 추천 묶음(한글 HWPX 도구 3종, 발표 자료 엔진, 문서 변환, 브라우저 자동화, 웹 수집, 하네스 팩토리)을 각 원 저장소에서 설치합니다.

같은 문장을 다시 붙여넣으면 빠진 것은 채우고, 설치된 것은 최신으로 바꿉니다. AI가 인터넷에서 받은 스크립트를 바로 실행하기 어렵다고 하면 "먼저 스크립트 내용을 보여 주고, 문제없으면 실행해줘"라고 답하세요. 스크립트 원문은 이 저장소의 [install.sh](install.sh)·[install.ps1](install.ps1)입니다.

### 다른 방법: 터미널·명령 프롬프트·VS Code

앱 없이 터미널(PowerShell, 명령 프롬프트, macOS 터미널, VS Code 터미널)에서도 같은 일을 합니다. 한 줄을 붙여넣고 Enter를 누르세요.

| | Windows (PowerShell) | macOS · Linux (터미널) |
|---|---|---|
| **Claude** | `irm https://nalssam-bunpil.vercel.app/claude.ps1 \| iex` | `curl -fsSL https://nalssam-bunpil.vercel.app/claude.sh \| sh` |
| **ChatGPT Codex** | `irm https://nalssam-bunpil.vercel.app/codex.ps1 \| iex` | `curl -fsSL https://nalssam-bunpil.vercel.app/codex.sh \| sh` |

Windows에서 명령 프롬프트나 Git Bash에 붙여넣을 때는 위 채팅창용 `powershell -NoProfile -Command "…"` 형태를 쓰세요. 설치가 끝나면 새 터미널에서 작업 폴더를 열고 `claude`(또는 `codex`)를 실행한 뒤 **"설정 시작해줘"**라고 입력합니다.

### 더블클릭 설치

[분필팩 zip](https://nalssam-bunpil.vercel.app/bunpil-pack.zip)을 받아 압축을 풀고 Windows는 `Install-Windows.bat`, 맥은 `Install-Mac.command`를 실행합니다. Claude Code와 Codex가 모두 없으면 무엇을 설치할지 묻습니다. 학교망에서 내려받기가 막힐 때 USB로 옮겨 설치하는 용도로도 씁니다.

### Claude 앱 메뉴만 쓰는 경우 (명령 없이, 분필팩 5종만)

Chat·Cowork만 쓰거나 명령 실행이 막힌 PC에서는 Claude 앱 → **사용자 지정(Customize) → 플러그인(Plugins) → 추가(Add) → 마켓플레이스 추가(Add marketplace) → 저장소에서 추가** → `nalssam/bunpil_pack` → **분필 시작 팩**부터 설치 → 새 대화에서 "설정 시작해줘". 플러그인은 Claude 유료 요금제(Pro·Max·Team·Enterprise)에서 쓸 수 있습니다. 마켓플레이스 추가가 막히면 사이트의 플러그인 zip을 업로드하세요.

## 분필팩 플러그인 5종

| 플러그인 | 하는 일 | 스킬 |
|---|---|---|
| **분필 시작 팩** `bunpil-start` | 내 맞춤 지침 만들기, 학생 개인정보 가드, 설치 점검 | setup · privacy-guard · checkup |
| **분필 수업자료 팩** `bunpil-class` | 수준별 학습지, 지도안, 수업 슬라이드, 수업 영상, 페이퍼크래프트, 컬러링 도안, 루브릭 | worksheet · lesson-plan · class-slides · class-video · papercraft · coloring · rubric |
| **분필 학교업무 팩** `bunpil-school` | 공문 처리 하네스, 가정통신문, 품의 산출내역, 학부모 설문 분석, 한글 문서·기안문 | gongmun · newsletter · pumui · parent-survey · hwpx-doc |
| **분필 하네스빌더 팩** `bunpil-builder` | 나만의 스킬 만들기, 실수를 규칙으로, 스킬 시험, 동료와 나누기, 하네스 예시 100종 가져오기 | skill-maker · harness-fix · eval-run · share-skill · harness-gallery |
| **분필 커넥터 팩** `bunpil-connect` | 노션·패들렛·캔바 연결 | connect |

## 묶음 고르기

분필팩 하나에 모든 도구가 들어 있습니다. 기본은 **teacher**이고, 필요한 묶음만 더합니다(사이트의 "묶음 고르기"와 "설치 문장 만들기"에서 고르면 문장이 바뀝니다). 분필팩은 아래 도구를 복사·재배포하지 않고 각 원 저장소에서 직접 설치합니다. 전체 목록과 설치 방식: [catalog/recommended.json](catalog/recommended.json), 사이트의 "무엇이 설치되나요".

- **teacher (기본)** — airmang/hwpx-plugins, chrisryugj/kordoc, ZZombie04/hwpx_new, ZZombie04/pptx_maker(한국어 발표 자료 엔진), microsoft/markitdown, microsoft/playwright, Firecrawl(웹사이트 내용 수집, 키 없이), Perplexity(최신 검색, `PERPLEXITY_API_KEY`가 있을 때만), revfactory/harness, revfactory/harness-100 · 크롬 연결(Claude in Chrome)은 설치 뒤 안내
- **creator** — ui-ux-pro-max-skill, taste-skill, impeccable, claude-video, sprite-gen, instagram-agent-skill(인스타 스킬 13종), Glif(이미지·영상 AI, 로그인 필요), Cinetic(소개·출시 영상 스킬, macOS·Linux·WSL2), Prompt Motion(모션 영상·프롬프트 모음 사이트, 링크) · 수업 영상 스킬(class-video)이 필요할 때 Manim·edge-tts를 설치
- **dev** — superpowers, andrej-karpathy-skills, caveman, codex-plugin-cc, Agent-Reach, ECC·wshobson/agents·google/skills·claude-mem(목록만 등록)
- **studio (고급, 예전 날쌤팩)** — Motion Director, Showreel, motion-graphics, REA, After Effects MCP와 Claude 네이티브 플러그인 122개 · 아래 "studio 묶음"

## studio 묶음 (고급, 예전 날쌤팩)

영상·모션그래픽·발표 자료·앱 분석·개발 도구까지 쓰는 전체 작업 환경입니다. 원본 저장소 29개를 커밋 고정으로 설치합니다(macOS·Linux·Windows는 WSL2 Ubuntu, 수 GB, 10~30분). 예전에는 [nalssam/nalssam-pack](https://github.com/nalssam/nalssam-pack)으로 따로 배포했고, 지금은 이 저장소의 [`studio/`](studio/) 폴더(MIT)가 설치 엔진입니다. 명령 이름(`nalssam-pack`)과 설치 기록 폴더(`~/.local/share/nalssam-pack`)는 이미 설치한 분의 환경과 이어지도록 그대로 둡니다.

- 설치: 위 설치 문장을 만들 때 **studio**를 골라 더하거나, macOS·Linux·WSL2 터미널에서 `curl -fsSL https://nalssam-bunpil.vercel.app/install.sh | sh -s -- --profile studio` (옛 `--nalssam`도 같은 뜻입니다). Claude Code가 있으면 `--claude`로 설치해 네이티브 플러그인까지 켜고, 겹치는 추천 도구는 studio의 고정 버전을 씁니다. studio 공통 MCP 중 분필팩에 없는 것(REA, Motion 등)은 Claude Code에 `nalssam-` 이름으로 연결합니다.
- Windows의 한 줄 설치는 studio를 직접 설치하지 않고 WSL2 안내만 보여 줍니다(`$env:BUNPIL_PROFILE="studio";`).
- 점검: 채팅창에서 "스튜디오 설치 점검해줘" 또는 터미널에서 `nalssam-pack doctor --verify-mcp`. ElevenLabs·Gemini·Google Cloud·After Effects 같은 계정·프로그램은 따로 연결합니다([docs/studio/connectors.md](docs/studio/connectors.md)).
- 엔진 설명과 검증 범위: [studio/README.md](studio/README.md), [studio/VERIFICATION.md](studio/VERIFICATION.md)

## 옵션

macOS·Linux는 `install.sh | sh -s -- <옵션>`, Windows는 같은 이름의 환경변수를 앞에 둡니다. 사이트의 **설치 문장 만들기**에서 고르면 채팅창에 붙여넣을 문장과 터미널 명령을 함께 만들어 줍니다.

| 하고 싶은 것 | macOS·Linux | Windows |
|---|---|---|
| 추천 묶음 고르기 | `--profile teacher,creator,studio` / `all`(네 묶음 모두, studio 포함이라 수 GB) | `$env:BUNPIL_PROFILE="teacher,creator";` |
| 분필팩 5종만 | `--bunpil-only` | `$env:BUNPIL_RECS="0";` |
| Claude Code에만 / Codex에만 | `--claude` / `--codex` | `$env:BUNPIL_ONLY="claude";` / `"codex"` |
| 없으면 Claude Code·Codex까지 설치 | `--install-claude` / `--install-codex` | `$env:BUNPIL_INSTALL_CLAUDE="1";` / `$env:BUNPIL_INSTALL_CODEX="1";` |
| Node.js·uv도 설치 | `--with-tools` | `$env:BUNPIL_WITH_TOOLS="1";` |
| 한글 플러그인 빼기 | `--no-hwpx` | `$env:BUNPIL_HWPX="0";` |
| studio 묶음(예전 날쌤팩) | `--profile studio` (옛 `--nalssam`) | WSL2 안내만(`$env:BUNPIL_PROFILE="studio";`) |
| 지우기 | `uninstall.sh` | `uninstall.ps1` |

## 업데이트 · 지우기

- 업데이트: 설치할 때 쓴 문장을 채팅창에 그대로 다시 붙여넣습니다(터미널은 같은 줄을 다시 실행). Codex는 업데이트 뒤 분필 가드를 다시 신뢰합니다(앱의 안내 또는 터미널의 `/hooks`).
- 지우기: 채팅창에 "분필팩을 지워줘. 아래 명령을 한 글자도 바꾸지 말고 그대로 실행하고, 지운 것과 그대로 둔 것을 짧게 알려줘."와 함께 `powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/uninstall.ps1 | iex"` (Windows) 또는 `curl -fsSL https://nalssam-bunpil.vercel.app/uninstall.sh | sh` (macOS·Linux)를 붙여넣습니다. 터미널에서는 명령만 실행합니다. 추천 도구와 선생님 작업 파일은 그대로 둡니다. studio 묶음은 "스튜디오를 지워줘" 또는 `nalssam-pack uninstall`로 따로 지웁니다.

## 환경별 차이

| 기능 | Claude Chat(웹·앱) | Cowork | Claude Code(앱 Code 탭·터미널) | Codex(ChatGPT 앱·터미널) |
|---|---|---|---|---|
| 분필팩 스킬 21종 | ○ | ○ | ○ | ○ |
| 개인정보 자동 점검(훅) | × (지침으로 대신) | ○ | ○ | 훅 신뢰 후 ○ |
| 공문 처리 서브에이전트 | × (순서대로 처리) | ○ | ○ | × (순서대로 처리) |
| 노션·패들렛·캔바 | 커넥터 연결 후 ○ | 커넥터 연결 후 ○ | 입력창 옆 + → Connectors·`/mcp` 로그인 후 ○ | `codex mcp login` 후 ○ |
| 추천 MCP(한글·문서 변환·브라우저 자동화) | × | 컴퓨터에서 실행 시 | ○ | ○ |

## 원칙

- 모든 결과물은 **초안**입니다. 발송·제출·결재는 선생님이 합니다.
- 학생 실명·연락처는 넣지 않습니다. 넣으려 하면 분필팩이 먼저 알려 드립니다.
- 생활기록부 서술형 문구는 만들지 않습니다(2026 기재요령).
- 교사의 수업 준비·행정 업무용입니다. 학생이 직접 쓰는 도구가 아닙니다.
- 추천 도구는 각 저장소 작성자의 것입니다. 업데이트·라이선스는 원 저장소를 따릅니다.

## 개발자용

```bash
python3 tools/build.py       # src → plugins/claude, plugins/codex, 마켓플레이스, dist
python3 tools/make_site.py   # build + public/(설치 스크립트·zip·웹사이트) + site/index.html + vercel.json
python3 tools/check.py       # 형식·개인정보·구조·배포 묶음 점검
python3 tests/guard_test.py  # 개인정보 가드 102문장 시험
claude plugin validate . --strict
```

- 원본은 `src/plugins/`, `install.sh`, `install.ps1`, `studio/`, `site/template.html`만 고칩니다. `plugins/`, `.claude-plugin/`, `.agents/`, `public/`, `site/index.html`, `vercel.json`은 빌드 산출물입니다.
- `claude.sh`·`codex.sh`·`uninstall.sh`(와 `.ps1`)는 `install.sh`·`install.ps1`의 `# @BUNPIL_PRESET@` 줄에 기본값을 넣어 만듭니다.
- 사이트는 Vercel이 `public/`을 그대로 배포합니다(`vercel.json`: 스크립트는 `text/plain; charset=utf-8`, 캐시 없음). `main`에 올리면 자동 배포됩니다.
- 추천 묶음을 바꿀 때는 `catalog/recommended.json`, `install.sh`, `install.ps1`을 함께 고칩니다. studio 엔진은 `studio/`에서 `python3 -m unittest discover -s tests`로 시험합니다.
- 사이트의 모든 설치 문장은 `tools/make_site.py`의 `CHAT_LEAD` 한 곳의 문구를 씁니다. README·docs/install.md의 문장도 `tools/check.py`가 같은지 점검합니다.

## 만든 사람 · 라이선스

- 기획·원안·추천 묶음 선정: 날쌤(nalssam), 몽당분필
- 코드·스킬: MIT, 문서·템플릿·도안 예시: CC BY 4.0 — [LICENSE](LICENSE), [NOTICE](NOTICE). studio/ 설치 엔진은 예전 날쌤팩 v1.0.1(MIT)에서 화면에 보이는 문구만 고쳐 가져온 것입니다.
- "몽당분필" 이름과 로고는 상표이며 라이선스 대상이 아닙니다. "Claude"는 Anthropic, "ChatGPT"·"Codex"는 OpenAI의 상표이며, 분필팩은 두 회사와 제휴하지 않은 독립 프로젝트입니다.
