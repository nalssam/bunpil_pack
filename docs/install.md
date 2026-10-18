# nalssam's 분필팩 설치 안내

> 그림과 함께 따라 하려면 사이트를 여세요: https://nalssam-bunpil.vercel.app
> 이 문서는 같은 내용을 글로 옮긴 것입니다. 기본은 **앱의 채팅창에 문장을 붙여넣는 방법**(A·B)이고, 앱 메뉴만 쓰는 방법·터미널·VS Code·zip은 "다른 방법"에 있습니다.

## 시작 전에

| 확인할 것 | 이유 |
|---|---|
| **인터넷망 PC나 개인 기기** | 업무망 PC는 인터넷이 막혀 있거나 프로그램 설치가 제한됩니다. 업무망 자료를 옮길 때는 학교 규정을 따릅니다. |
| **쓸 AI와 요금제** | Claude 앱의 Code 탭과 플러그인은 유료 요금제(Pro·Max·Team·Enterprise)에서 됩니다. ChatGPT Codex는 무료 요금제를 포함한 ChatGPT 요금제에서 쓸 수 있고, 쓸 수 있는 양은 요금제마다 다릅니다. 무료로 시작하려면 Codex(B)를 고르세요. |
| **학생 실명은 넣지 않기** | 분필팩은 교사 업무용 도구입니다. 학생 이름은 '학생A'처럼 바꿔 씁니다. |
| **컴퓨터** | Windows 10(1809) 이상, macOS 13 이상(앱 자체의 사양은 내려받는 페이지의 안내를 따릅니다). 관리자로 실행할 필요는 없습니다. |

## 붙여넣을 문장

채팅창에 붙여넣을 문장은 **안내 한 문단 + 명령 한 줄**입니다. 첫 문단은 모두 같고, 명령은 쓰는 AI와 컴퓨터에 따라 고릅니다.

```text
분필팩을 설치해줘. 아래 명령을 한 글자도 바꾸지 말고 그대로 실행해줘. 5~10분 걸리니 시간 제한에 걸리지 않게 백그라운드로 실행하고 끝날 때까지 기다려줘. 끝나면 설치된 것과 실패한 것을 짧게 알려줘.
```

| | Windows | macOS · Linux |
|---|---|---|
| **Claude** | `powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/claude.ps1 \| iex"` | `curl -fsSL https://nalssam-bunpil.vercel.app/claude.sh \| sh` |
| **ChatGPT Codex** | `powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/codex.ps1 \| iex"` | `curl -fsSL https://nalssam-bunpil.vercel.app/codex.sh \| sh` |

Windows용 명령은 PowerShell, 명령 프롬프트, Git Bash 어디서 실행돼도 같게 동작합니다. 그래서 채팅창의 AI가 어떤 셸로 실행하든 문제가 없습니다.

## A. Claude 앱의 Code 탭 (기본)

1. **준비물** — Claude 유료 요금제 계정. 앱의 Code 탭은 유료 요금제에서 쓸 수 있습니다.
2. **Claude 앱 내려받고 로그인** — [claude.com/download](https://claude.com/download)에서 내 컴퓨터용 앱을 설치하고 로그인합니다. 위쪽에 **Chat · Cowork · Code** 탭이 보이면 준비 완료입니다. 일반 대화(**Chat**) 탭의 Claude는 내 컴퓨터에 프로그램을 설치할 수 없으니, 설치는 꼭 **Code** 탭에서 합니다.
   - Code 탭이 안 보이거나 잠겨 있으면 앱을 최신 버전으로 업데이트하세요. 무료 요금제에서는 쓸 수 없으니 B(Codex)를 하거나, 아래 "다른 방법"의 앱 메뉴만 쓰는 방법을 하세요.
3. **작업 폴더 만들고 Code 탭에서 열기** — 문서 폴더 안에 `분필작업` 폴더를 하나 만듭니다. Code 탭에서 환경을 **Local**(내 컴퓨터)로 고르고 **폴더 선택**으로 `분필작업`을 엽니다. 아래쪽에 입력창이 보이면 준비 끝입니다. 입력창 옆의 권한 선택은 **Manual**(수동. 예전 이름 Ask permissions, 실행 전에 물어봄)로 둡니다. **Auto**가 선택되어 있으면 인터넷에서 받은 스크립트 실행을 자동 판단이 막을 수 있습니다. 분필팩 같은 플러그인은 Local 환경에서만 쓸 수 있고, 클라우드(원격) 환경이나 WSL 세션에서는 보이지 않습니다.
4. **설치 문장을 붙여넣고 Enter** — 위 "붙여넣을 문장"의 Claude 줄을 입력창에 붙여넣습니다. Claude가 명령 실행 **허락**을 물으면 내용이 위 명령과 같은지 확인하고 **허용**합니다. 그다음은 Claude가 알아서 설치하고 결과를 알려 줍니다. 순서는 Claude Code(없을 때만) → Node.js·uv·Git(없을 때만) → 분필팩 5종 → 추천 teacher 묶음입니다.
   - Windows에서 Git을 설치할 때 "이 앱이 디바이스를 변경할 수 있도록 허용하시겠어요?" 창이 뜨면 **예**를 누릅니다. 거절하면 Git이 필요한 일부 추천 도구(한글 편집 엔진, 하네스 팩토리 등)만 건너뛰고, 나중에 같은 문장을 다시 붙여넣으면 채워집니다.
   - 맥에서 Git이 없으면 "명령어 개발자 도구를 설치하겠습니까?" 창이 뜹니다. **설치**를 누르고 끝나면 같은 문장을 한 번 더 붙여넣습니다. 그사이 Git이 필요 없는 항목은 먼저 설치됩니다.
   - Claude가 인터넷에서 받은 스크립트를 바로 실행하기를 망설이면 "먼저 스크립트 내용을 보여 주고, 문제없으면 실행해줘"라고 답하세요. 스크립트 원문은 이 저장소의 [install.sh](../install.sh)·[install.ps1](../install.ps1)입니다.
   - Claude가 실행하지 못했다고 하거나 아무것도 실행되지 않으면 입력창 옆 권한 선택이 **Auto**인지 확인합니다. **Manual**로 바꾸고 같은 문장을 다시 붙여넣은 뒤 허락 창에서 **허용**합니다.
   - Claude가 **분필팩 설치 완료**라고 알려 주면 끝입니다. 빨간 줄이 있거나 10분이 넘도록 끝나지 않으면 같은 문장을 다시 붙여넣습니다. 이미 설치된 것은 건너뛰고 빠진 것만 채웁니다.
5. **새 대화에서 설정 마법사** — 방금 설치한 플러그인은 새 대화부터 보입니다. Code 탭에서 새 대화를 시작하고(같은 폴더, Local) `설정 시작해줘`라고 입력합니다. 10가지 질문에 답하면 내 맞춤 지침(`CLAUDE.md`)이 작업 폴더에 생깁니다. 새 대화에서도 분필팩이 보이지 않으면 앱을 완전히 종료했다가 다시 엽니다.
6. **점검과 연결** — `분필 점검해줘`로 설치 상태를 확인합니다. `가드 시험: 연락처 010-0000-0000`을 보내 경고가 뜨면 개인정보 가드가 작동하는 것입니다. 노션·패들렛·캔바는 입력창 옆 **+** 버튼 → **Connectors(커넥터)**에서 서비스를 골라 로그인합니다(목록에서 찾기 어려우면 왼쪽 **사용자 지정**의 커넥터도 확인). 필요 없는 플러그인은 **+** → **Plugins** → **Manage plugins**에서 끌 수 있습니다.

## B. ChatGPT 앱의 Codex (기본)

1. **준비물** — ChatGPT 계정.
2. **ChatGPT 앱 내려받고 로그인** — [chatgpt.com/download](https://chatgpt.com/download)에서 내 컴퓨터용 앱을 설치하고 로그인합니다(Windows는 Microsoft Store 설치 화면으로 이어질 수 있습니다). 새 채팅을 열고 위쪽의 **ChatGPT** 이름을 눌러 **Codex**를 고르면 코드 작업 화면이 나옵니다. 앱 버전에 따라 위치가 조금 다를 수 있고, 안 보이면 앱을 최신 버전으로 업데이트하세요.
3. **작업 폴더 만들고 Codex에서 열기** — 문서 폴더 안에 `분필작업` 폴더를 만들고, Codex 화면의 **폴더 열기**(프로젝트 추가)로 엽니다. 권한은 **승인 요청(Ask for approval)**을 권장합니다. 명령을 실행하기 전에 물어봅니다.
4. **설치 문장을 붙여넣고 Enter** — 위 "붙여넣을 문장"의 Codex 줄을 입력창에 붙여넣습니다. Codex가 **승인**을 요청하면 내용이 위 명령과 같은지 확인하고 승인합니다. 순서는 Codex 명령(없을 때만, OpenAI 공식 설치 프로그램) → Node.js·uv·Git(없을 때만) → 분필팩 5종 → 추천 teacher 묶음입니다. Git 허용 창과 실패했을 때의 대처는 A의 4번과 같고, 인터넷 접근이나 폴더 쓰기를 막아서 실패했다면 승인 요청에 허용했는지 확인합니다. Windows용 Codex에서는 한글 편집 엔진(hwpx-plugin)을 건너뛰고 한글 양식 보고서(hwpx_new)·kordoc이 대신 한글 문서를 맡습니다.
5. **새 대화에서 개인정보 가드 켜고 설정 마법사** — 방금 설치한 플러그인은 새 대화부터 쓰이고, 앱을 한 번 껐다 켜면 가장 확실합니다. 앱과 터미널은 같은 설정 파일을 씁니다. Codex는 플러그인의 자동 점검(훅)을 처음에 믿지 않으므로, 훅을 신뢰할지 묻는 안내가 나오면 **분필 가드**를 확인하고 **신뢰(trust)**를 고릅니다. 안내가 보이지 않으면 터미널에서 `codex`를 열고 `/hooks`로 확인합니다. 분필팩을 업데이트한 뒤에는 한 번 더 신뢰해야 합니다. 그다음 `설정 시작해줘`를 입력하면 10가지 질문으로 내 맞춤 지침(`AGENTS.md`)을 만들어 줍니다.
6. **연결과 점검** — `분필 점검해줘`로 설치 상태를 확인합니다. 노션·패들렛·캔바 연결 위치는 앱 버전에 따라 달라서, 채팅창에 "노션 연결하는 방법 알려줘"라고 물으면 지금 화면에 맞춰 안내합니다. 터미널을 쓴다면 `codex mcp login notion`(`padlet`, `canva`도 같은 방법)을 실행하고 브라우저에서 로그인합니다.

## 다른 방법

### C. Claude 앱 메뉴만 쓰기 (명령 없이, 분필팩 5종만)

Chat·Cowork만 쓰거나 학교 PC에서 명령 실행이 막혀 있을 때의 방법입니다. 분필팩 5종(스킬)만 들어가고, 추천 도구(한글 편집·문서 변환·브라우저 자동화 같은 MCP)는 들어가지 않습니다. 플러그인은 유료 요금제에서 쓸 수 있습니다.

1. 왼쪽 메뉴 **사용자 지정(Customize)** → **플러그인(Plugins)** → **추가(Add)** → **마켓플레이스 추가(Add marketplace)** → **저장소에서 추가(Add from a repository)** → `nalssam/bunpil_pack`. Cowork에서는 먼저 **Cowork** 탭을 엽니다.
2. **분필 시작 팩**을 설치하고 필요한 팩을 더합니다.
3. 새 대화에서 `설정 시작해줘`, 이어서 `분필 점검해줘`.

마켓플레이스 추가가 막히면 사이트의 플러그인 zip(`/app/bunpil-start.zip` 등)을 받아 추가 메뉴의 업로드로 올립니다. 앱에서 추가한 플러그인은 계정에 저장되어 같은 계정으로 로그인한 Claude Code에서도 쓸 수 있습니다. 채팅에서는 자동 점검(훅)과 서브에이전트가 회색으로 보이며, 정상입니다.

### D. 터미널·명령 프롬프트·VS Code

앱 대신 터미널에서 합니다. 하는 일은 A·B와 같고 붙여넣는 곳만 다릅니다. 터미널은 Windows는 시작 메뉴에서 `PowerShell`(관리자 아님) 또는 명령 프롬프트, 맥은 ⌘+Space → `터미널`, VS Code는 메뉴 **터미널 → 새 터미널**로 엽니다.

1. **한 줄 붙여넣고 Enter**

   | | Windows (PowerShell) | macOS · Linux |
   |---|---|---|
   | **Claude** | `irm https://nalssam-bunpil.vercel.app/claude.ps1 \| iex` | `curl -fsSL https://nalssam-bunpil.vercel.app/claude.sh \| sh` |
   | **ChatGPT Codex** | `irm https://nalssam-bunpil.vercel.app/codex.ps1 \| iex` | `curl -fsSL https://nalssam-bunpil.vercel.app/codex.sh \| sh` |

   명령 프롬프트나 Git Bash에 붙여넣을 때는 "붙여넣을 문장"의 `powershell -NoProfile -Command "…"` 형태를 씁니다(PowerShell이 아닌 창에서 `irm`을 그대로 쓰면 `'irm'은(는) 내부 또는 외부 명령이 아닙니다`가 뜹니다). 설치되는 것과 Git 허용 창은 A의 4번과 같습니다.
2. **새 창에서 시작** — 창을 닫고 새로 연 뒤 작업 폴더에서 실행합니다.
   - Claude, Windows: `mkdir -Force ~\분필작업 > $null; cd ~\분필작업; claude`
   - Claude, macOS·Linux: `mkdir -p ~/분필작업 && cd ~/분필작업 && claude`
   - Codex는 마지막의 `claude`를 `codex`로 바꾸고 **Sign in with ChatGPT**로 로그인합니다.

   처음이면 Claude는 로그인 방법에서 Claude 구독 계정을 고르고 브라우저에서 로그인합니다.
3. **설정 마법사와 점검** — 대화창에 `설정 시작해줘`, 이어서 `분필 점검해줘`. Claude는 `/mcp`에서 노션·패들렛·캔바에 로그인하고, Codex는 `/hooks`에서 분필 가드를 **신뢰(trust)**한 뒤 새 터미널에서 `codex mcp login notion`(`padlet`, `canva`도 같은 방법)을 실행합니다.

### E. 더블클릭 설치 (zip)

1. https://nalssam-bunpil.vercel.app/bunpil-pack.zip 을 받아 **모두 압축 풀기**.
2. Windows: `Install-Windows.bat` 더블클릭("Windows의 PC 보호" 창이 뜨면 **추가 정보 → 실행**). 맥: `Install-Mac.command`를 오른쪽 클릭 → **열기**(막히면 시스템 설정 → 개인정보 보호 및 보안 → **그래도 열기**).
3. Claude Code와 Codex가 모두 없으면 무엇을 설치할지 번호로 고릅니다.

분필팩 5종은 인터넷 없이도 설치되고, 추천 도구는 인터넷이 필요합니다. 학교망에서 내려받기가 막힐 때 USB로 옮겨 설치하는 용도로도 씁니다.

## F. 묶음 더하기 (creator · dev · studio)

기본은 teacher 묶음입니다. 웹·디자인·영상·인스타 자료를 만들 creator, 개발자용 dev, 영상·모션그래픽·발표 자료까지 쓰는 studio를 더하려면 사이트의 **설치 문장 만들기**에서 묶음을 골라 바뀐 문장을 붙여넣습니다. 터미널에서는 `--profile`(Windows는 환경변수 `BUNPIL_PROFILE`)을 씁니다. 옵션 전체 표는 [README](../README.md#옵션)에 있습니다.

```bash
curl -fsSL https://nalssam-bunpil.vercel.app/claude.sh | sh -s -- --profile teacher,creator
```

### studio 묶음 — 예전 날쌤팩 (고급)

영상·모션그래픽·발표 자료·앱 분석·개발 도구까지 쓰는 전체 작업 환경입니다. 예전에는 [nalssam/nalssam-pack](https://github.com/nalssam/nalssam-pack)으로 따로 배포했고, 지금은 분필팩의 한 묶음이며 설치 엔진은 이 저장소의 [`studio/`](../studio/) 폴더입니다. 수 GB를 내려받아 10~30분이 걸리고, macOS·Linux에서 설치합니다.

- **채팅창에서**: 사이트의 "설치 문장 만들기"에서 studio를 더하면 첫 문단이 "수 GB를 받아 10~30분 걸리니…"로 바뀝니다. 그 문장을 A·B처럼 붙여넣습니다. Claude 앱(macOS)에서 teacher와 studio를 함께 설치하는 명령은 다음과 같습니다.

  ```bash
  curl -fsSL https://nalssam-bunpil.vercel.app/install.sh | sh -s -- --claude --profile teacher,studio --install-claude --with-tools
  ```
- **Windows**는 바로 설치되지 않습니다. 나머지를 설치한 뒤 화면에 나오는 WSL2 Ubuntu 안내를 따르고, Ubuntu 터미널에서 `curl -fsSL https://nalssam-bunpil.vercel.app/install.sh | sh -s -- --profile studio --install-claude`를 실행합니다(Codex를 쓰면 `--install-codex`). WSL 안에는 Claude Code·Codex가 따로 없으므로 이 옵션이 WSL 안에 설치해 줍니다.
- Claude Code가 있으면 스킬과 네이티브 플러그인 122개(개발·Google Cloud 플러그인 포함)까지 설치합니다. 겹치는 추천 도구는 studio의 고정 버전을 쓰고 분필팩은 그 항목을 건너뜁니다. 분필팩에 없는 studio MCP(REA, Motion 등)는 Claude Code에 `nalssam-` 이름으로 연결합니다.
- **점검**: 채팅창에서 `스튜디오 설치 점검해줘`, 터미널에서 `nalssam-pack doctor --verify-mcp`. 나레이션(ElevenLabs)·음성 인식(Gemini 등)·Google Cloud·After Effects는 각자 계정·프로그램을 연결해야 합니다([연결 안내](studio/connectors.md)).
- 예전에 날쌤팩을 설치했다면 그대로 이어집니다. 명령 이름(`nalssam-pack`)과 설치 기록 폴더(`~/.local/share/nalssam-pack`)를 바꾸지 않았고, 옛 옵션 `--nalssam`도 `--profile studio`와 같은 뜻입니다.

## 업데이트 · 지우기

- **업데이트**: 설치할 때 쓴 문장을 채팅창에 그대로 다시 붙여넣습니다(터미널이면 같은 명령을 다시 실행). 빠진 것은 채우고 설치된 것은 최신으로 바꿉니다. Codex는 업데이트 뒤 분필 가드를 다시 신뢰합니다.
- **지우기**: 채팅창에 아래 문장과 명령을 붙여넣습니다.

  ```text
  분필팩을 지워줘. 아래 명령을 한 글자도 바꾸지 말고 그대로 실행하고, 지운 것과 그대로 둔 것을 짧게 알려줘.
  ```

  Windows: `powershell -NoProfile -Command "irm https://nalssam-bunpil.vercel.app/uninstall.ps1 | iex"` · macOS·Linux: `curl -fsSL https://nalssam-bunpil.vercel.app/uninstall.sh | sh`. 터미널에서는 명령만 실행합니다(Windows PowerShell은 `irm https://nalssam-bunpil.vercel.app/uninstall.ps1 | iex`). 분필팩 5종과 내려받은 분필팩 폴더를 지우고, 다른 곳에서도 쓰는 추천 도구와 설치한 Node.js·uv·Git, 선생님 작업 폴더의 파일(`CLAUDE.md`·`AGENTS.md` 등)은 그대로 둡니다.
- **studio 묶음**은 따로 지웁니다. 채팅창에 `스튜디오를 지워줘`라고 하거나 터미널에서 `nalssam-pack uninstall`을 실행하세요. 스튜디오가 만든 연결만 해제하고 내려받은 소스와 캐시는 남깁니다.

## 문제 해결

| 증상 | 해결 |
|---|---|
| Claude 앱에 Code 탭이 없거나 잠겨 있음 | 앱을 최신 버전으로 업데이트합니다. Code 탭은 유료 요금제에서만 쓸 수 있으니, 무료로 시작하려면 Codex(B)를 쓰거나 앱 메뉴만 쓰는 방법(C)을 합니다. |
| Codex가 앱에 보이지 않음 | 앱을 최신 버전으로 업데이트합니다. 그래도 없으면 [내려받는 페이지](https://chatgpt.com/download)의 안내를 확인하고, 터미널 방법(D)을 씁니다. |
| AI가 "인터넷에서 받은 스크립트를 바로 실행하기는 어렵다"며 망설임 | "먼저 스크립트 내용을 보여 주고, 문제없으면 실행해줘"라고 답합니다. 원문은 `install.sh`·`install.ps1`입니다. |
| Claude가 실행하지 않거나 "권한 때문에 못 했다"고 함 | 입력창 옆 권한 선택이 **Auto**이면 인터넷에서 받은 스크립트 실행을 막을 수 있습니다. **Manual**로 바꾸고 같은 문장을 다시 붙여넣어 허락 창에서 허용합니다. |
| 승인 요청이 계속 뜸 | 매번 내용이 붙여넣은 명령과 같은지 확인하고 허용합니다. 다른 명령이면 허용하지 않습니다. |
| `'irm'은(는) 내부 또는 외부 명령이 아닙니다` | 명령 프롬프트에 붙여넣은 것입니다. PowerShell(`PS C:\>`)을 열거나 `powershell -NoProfile -Command "…"` 형태의 명령을 씁니다. |
| "이 시스템에서 스크립트를 실행할 수 없으므로…" | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`를 한 번 실행합니다. 학교 관리 PC라 안 바뀌면 정보 담당 선생님께 문의합니다. |
| `claude`·`codex` 명령을 찾을 수 없음 | 터미널을 닫고 새로 엽니다. 그래도 안 되면 같은 문장(또는 명령)을 다시 실행합니다. |
| 빨간 `[x]`·`✗` 줄 | 같은 문장을 다시 붙여넣습니다. 실패한 것만 다시 시도합니다. |
| 새 대화에서도 분필팩이 보이지 않음 | 앱을 완전히 종료했다가 다시 엽니다. Claude 앱은 Code 탭에서 환경이 **Local**인지 확인합니다. |
| 학교 인터넷에서 내려받기 실패 | 휴대폰 핫스팟으로 연결하거나 집에서 zip을 받아 USB로 옮겨 더블클릭 설치합니다. |
| Codex에서 가드가 안 돎 | 앱의 훅 신뢰 안내에서 분필 가드를 신뢰합니다. 안내가 없으면 터미널의 `/hooks`에서 합니다. |
| 가짜 번호에도 경고 | 형식만 보고 판단합니다. 실제 정보가 아니면 그대로 진행합니다. |
| 가드를 잠시 끄기 | 환경변수 `BUNPIL_GUARD=off` 또는 분필 시작 팩 비활성화. |
| 브라우저 자동화 첫 실행이 느림 | 처음 한 번 구성 요소를 내려받습니다. 정상입니다. |

## 설치하면 바뀌는 것

- 홈 폴더의 `.bunpil` 폴더: 분필팩(`bunpil-pack`), 관리자 권한 없이 설치한 Node.js(`node`), PATH 설정(`env`, macOS·Linux)
- Claude Code·Codex 설정: 분필팩·추천 플러그인, MCP 연결(kordoc, playwright, markitdown, hwpx_new, pptx_maker, firecrawl, 키가 있으면 perplexity, creator 묶음이면 glif). Claude 앱의 Code 탭과 ChatGPT 앱의 Codex는 터미널의 Claude Code·Codex CLI와 같은 설정 파일을 씁니다.
- 없을 때만: Claude Code·Codex CLI·Node.js·uv(Git은 Windows·macOS만 자동 안내, Linux·WSL은 직접 설치), PATH 추가(macOS·Linux는 `~/.bunpil/env`와 셸 설정 파일의 `# bunpil-path` 한 줄, Windows는 사용자 PATH)
- Windows에서 Codex를 npm으로 설치한 경우에만: 현재 사용자 PowerShell 실행 정책을 RemoteSigned로(`$env:BUNPIL_KEEP_POLICY="1"`이면 바꾸지 않음)
- studio 묶음을 고른 경우에만: `~/.local/share/nalssam-pack`(설치 기록·소스·캐시), `~/.agents/skills`, Claude Code가 있으면 `~/.claude/skills`와 네이티브 플러그인, Codex 설정의 MCP 연결, 셸 설정 파일(`.bashrc`·`.zshrc`·`.profile`)의 `# 날쌤팩` 표시가 붙은 한 줄(이 줄은 PATH 앞쪽에 studio의 python·node를 두므로, 새 터미널에서 `python3`·`node`가 studio 것으로 잡힐 수 있습니다. 내 파이썬 스크립트가 패키지를 못 찾으면 이 한 줄을 지우거나 가상환경을 쓰세요)

문의: GitHub Issues — https://github.com/nalssam/bunpil_pack/issues
