# 검증 기록

> 이 기록은 날쌤팩 v1.0.1(2026-10-15) 때의 것입니다. 분필팩 저장소 안으로 옮기면서 **화면에 보이는 문구와 실행 래퍼(`install.sh`가 분필팩 폴더의 `pack.py`를 바로 실행)만** 바꿨고 설치 로직(`pack.py`의 설치·진단·제거 동작)과 고정 목록(`pack.lock.json`, `locks/`)은 그대로입니다. 옮긴 뒤 새로 확인한 내용은 맨 아래 "분필팩 연동 확인"에 적습니다.

2026-10-15 기준, Linux x86_64의 별도 임시 HOME / CODEX_HOME에서 검증했습니다. 실제 사용자 설정·로그인 정보를 복제하지 않았습니다.

## 통과

- Python 회귀 테스트 8개: 기존 스킬 보존, 중복 재설치, 수정된 스킬·실행 파일 보존, 셸 백업·복원, 셸 인자 이스케이프, 실패한 다운로드 재시도, 기존 MCP 이름 충돌, 사용자 수정 MCP 보존.
- 전체 Codex 구성 실제 설치: 실패 0개. 원본을 고정 커밋으로 별도 복제하고 Python 가상환경·npm 런타임·스킬 연결·Codex 메모리 플러그인 설치.
- 동일 설치 폴더에 전체 설치 재실행: 실패 0개.
- 실제 MCP 초기화와 `tools/list`: REA 207개, HWPX New 22개, Kordoc 17개, MarkItDown 1개, Motion 22개, PPTX Maker 16개.
- 등록된 스킬 연결 검사: 깨진 링크 0개.
- 설치된 전용 실행 파일로 PPTX Maker 샘플 67장 생성: 오류·경고 0, 100점. MarkItDown HTML→Markdown 변환 정상. Motion 환경 검사 정상.
- Claude Code 네이티브 플러그인 경로: 별도 HOME에서 Harness 플러그인 설치·제거 통과.
- 전체 제거: 설치 영수증의 스킬·MCP·플러그인·실행 파일 연결 0개, 소스와 가상환경은 보존.
- 부트스트랩에서 관리 Python 3.12.12 다운로드 및 `plan` 실행 통과.
- Node 24.19.0 배포 체크섬 URL과 버전 고정 uv 설치 URL 접근 확인.
- Bash 구문 검사·Python 컴파일 통과.

검증 요약 수치는 `tests/verified-linux.json`에 포함합니다. MCP 도구 수는 위에 고정한 버전 기준이며 새 버전에서 달라질 수 있습니다.

## 검증 범위의 한계

- macOS와 Windows/WSL2의 실제 전체 설치는 아직 수행하지 않았습니다. GitHub Actions에 Linux/macOS 회귀 검사를 구성했습니다.
- Claude Code 옵션의 122개 플러그인 전체를 새 기기에 재설치하는 조합은 미검증입니다. 전체 목록·소스 커밋을 고정하고 대표 네이티브 설치 경로를 검증했습니다.
- 외부 API·계정·클라우드 프로젝트, Adobe 프로그램, 메모리 관찰 서비스의 실제 데이터 수집은 검증하지 않았습니다.
- 브라우저와 ffmpeg가 이미 있는 Linux에서 영상 실행 환경을 확인했습니다. 관리 Node를 새로 내려받는 경로와 Chromium이 없는 OS의 공유 라이브러리 조합 전체는 미검증입니다.
- 고정 커밋은 소스 버전을 재현합니다. 모든 OS·폰트·계정·하드웨어까지 동일한 컨테이너 이미지를 재현하는 제품은 아닙니다.

## 분필팩 연동 확인 (v0.6.0, 2026-10-18)

날쌤팩을 분필팩 저장소로 옮긴 뒤 새로 확인한 내용입니다. Linux x86_64 클라우드 환경에서 별도 임시 HOME을 쓰고 실제 사용자 설정·로그인 정보는 쓰지 않았습니다.

### 옮긴 파일이 원본과 같은지

- `pack.lock.json`, `locks/`, `tests/`는 날쌤팩 저장소(`nalssam/nalssam-pack`, main 커밋 `0128200`)의 파일과 글자까지 같습니다.
- `pack.py`는 `diff`로 비교해 화면에 보이는 문구·주석·Codex 로컬 마켓플레이스의 표시 이름(`name`은 그대로)만 다릅니다. 설치·진단·제거 로직, 설치기 이름 `installer-v1.0.1`, 셸 설정의 `# 날쌤팩` 표시는 그대로입니다.

### 이번에 확인한 것

- 회귀 시험 8개: `python3 -m unittest discover -s tests` 통과.
- 실제 래퍼와 실제 엔진으로 `bash studio/install.sh plan --claude`: 관리 Python 3.12.12 설치, 설치기를 `~/.local/share/nalssam-pack/installer-v1.0.1`로 복사, 저장소 47곳 계획 출력, 종료 코드 0. 전체 설치는 수 GB라 다시 하지 않았습니다.
- 분필팩 `install.sh`와의 연결은 파일 모양만 흉내 내는 가짜 엔진으로 시험했습니다(실제 엔진은 실행하지 않음). `curl …/claude.sh | sh`와 같은 방식으로 로컬 서버에서 받아 실행했습니다.
  - `--profile studio`: 엔진에 `--claude`를 넘기고, `nalssam-` 이름의 Claude Code MCP 6개를 연결합니다.
  - 옛 이름 `--nalssam`, `--profile nalssam`, `BUNPIL_NALSSAM=1`: 같은 결과입니다.
  - Codex만(`codex.sh`): 엔진에 `--claude`를 넘기지 않습니다.
  - 엔진 실패: 오류를 표시하고 종료 코드 1로 끝나며, 분필팩 5종은 그대로 설치됩니다.
  - Git 없음: studio를 건너뛰고 안내합니다.
  - teacher + studio: kordoc·markitdown·harness·hwpx_new·pptx_maker는 studio 것을 쓰고, hwpx-plugin·playwright·firecrawl은 분필팩이 설치합니다.
- 기본(teacher) 설치: `claude.sh`(bash)와 `claude.ps1`(PowerShell 7, `powershell -NoProfile -Command "irm … | iex"` 형태)로 각각 분필팩 5종, 추천 플러그인 3종, MCP 6종 연결과 종료 코드 0을 확인했습니다.
- `install.ps1`: `[Environment]::SetEnvironmentVariable` 형태, 옛 `BUNPIL_NALSSAM`·`nalssam` 프로필 이름, studio 안내 출력을 PowerShell 7에서 확인했습니다. PowerShell 5.1·7.0 문법·호환성 분석 지적은 0건입니다.

### 확인하지 못한 것

- Windows 실제 기기와 macOS 실기기, 실제 Claude·ChatGPT 데스크톱 앱의 화면 순서와 승인 버튼 이름(공식 문서를 근거로 적었습니다).
- 분필팩 경로에서 실제 studio 엔진을 끝까지 설치하는 조합(수 GB)과 그 MCP 실행.
- 앞 절의 "검증 범위의 한계"는 그대로 유효합니다.
