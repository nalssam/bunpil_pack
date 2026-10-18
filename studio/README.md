# 분필팩 스튜디오 설치 엔진 (`studio/`)

영상·모션그래픽·발표 자료·앱 분석·개발 도구를 **고정 버전**으로 한꺼번에 준비하는 설치기입니다. 분필팩의 `studio` 묶음이 이 엔진을 실행합니다. 예전에는 따로 배포하던 **날쌤팩**(`nalssam/nalssam-pack` v1.0.1)이며, 지금은 분필팩 저장소 한 곳에서 함께 관리합니다. 명령 이름(`nalssam-pack`), 설치 기록 폴더(`~/.local/share/nalssam-pack`), 플러그인 목록 이름은 이미 설치한 분들의 환경과 이어지도록 그대로 둡니다.

## 쓰는 법

분필팩 한 줄 설치에서 `studio` 묶음을 고르면 됩니다. Claude 데스크톱 앱의 Code 탭이나 ChatGPT 앱의 Codex 채팅창에 붙여넣는 방법은 [사이트](https://nalssam-bunpil.vercel.app)의 "묶음 고르기"에 있습니다.

```bash
# 터미널에서 직접 (macOS · Linux · Windows는 WSL2 Ubuntu)
curl -fsSL https://nalssam-bunpil.vercel.app/install.sh | sh -s -- --profile studio
```

분필팩 폴더(`~/.bunpil/bunpil-pack`)나 zip을 푼 폴더 안에서는 엔진만 따로 실행할 수도 있습니다.

```bash
bash studio/install.sh --claude          # Claude Code 스킬·네이티브 플러그인 122개까지
bash studio/install.sh --profile skills  # 스킬·원본만 (런타임 다운로드와 MCP 등록 생략)
bash studio/install.sh plan              # 설치 전에 목록만 보기
```

설치한 뒤에는 새 터미널에서:

```bash
nalssam-pack plan
nalssam-pack install                         # 다시 실행해 빠진 단계 채우기
nalssam-pack install --only ZZombie04/motion # 특정 저장소만
nalssam-pack doctor --verify-mcp             # 실제 MCP 연결·도구 목록 검사
nalssam-pack uninstall                       # 스튜디오가 만든 연결만 해제
```

## 들어 있는 것

| 파일 | 내용 |
|---|---|
| `pack.py` | 설치·진단·제거 엔진(Python 3.11+, 표준 라이브러리만) |
| `pack.lock.json` | 저장소 47곳의 40자리 커밋, Claude Code 네이티브 플러그인 122개, Node·Python·Codex 버전 |
| `locks/` | npm·Python 의존성 고정 파일 |
| `skills/nalssam-pack/` | 설치 상태를 점검하고 복구하는 관리 스킬 |
| `install.sh` | uv·Python을 사용자 폴더에 준비하고 `pack.py`를 실행하는 래퍼 |
| `tests/` | 회귀 시험 8개(`python3 -m unittest discover -s tests`) |
| `VERIFICATION.md` | 검증한 범위와 한계 |

## 지키는 원칙

- 저장소는 브랜치 최신값이 아니라 **40자리 커밋**으로 받습니다.
- 기존 스킬·MCP·셸 설정은 보존하고, 겹치면 별도 이름(`nalssam-` 접두사)으로 연결합니다.
- 설치 영수증(`state.json`)에 적은 연결만 제거합니다. 소스·캐시·가상환경·백업은 남깁니다.
- 계정·쿠키·API 키는 복사하거나 저장하지 않습니다. 설치가 끝난 것과 서비스 계정이 연결된 것은 다릅니다.
- `sudo`를 실행하지 않습니다. ffmpeg가 없으면 macOS는 `brew install ffmpeg`, Ubuntu/WSL은 `sudo apt install ffmpeg`로 직접 준비합니다.

크기는 수 GB, 시간은 10~30분입니다. 지원 대상은 macOS와 Linux/WSL2이며 네이티브 Windows는 지원하지 않습니다. 자세한 검증 범위는 [VERIFICATION.md](VERIFICATION.md), 서비스 계정 연결 순서는 [docs/studio/connectors.md](../docs/studio/connectors.md)를 보세요.

MIT 라이선스. 포함 도구는 각 원본 저장소에서 내려받으며 각각의 라이선스를 따릅니다.
